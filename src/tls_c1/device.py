"""User-facing device wrapper for the Zolix spectrometer SDK."""

from __future__ import annotations

import math
import re
import time
from typing import Union

from .api import SpectrometerAPI
from .errors import (
    TLSC1ConnectionError,
    TLSC1DeviceError,
    TLSC1DeviceNotFoundError,
    TLSC1MoveTimeoutError,
    TLSC1NotConnectedError,
    TLSC1StateError,
    TLSC1ValidationError,
)
from .types import DeviceStatus

_WAVELENGTH_RE = re.compile(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(?:nm)?\s*$", re.IGNORECASE)
_USB_PORT_TYPES = {"USB"}
_SERIAL_PORT_TYPES = {"SERIAL", "COM", "RS232"}
_DEFAULT_MOVE_TIMEOUT_SECONDS = 60.0
_DEFAULT_POLL_INTERVAL_SECONDS = 0.25
_DEFAULT_WAVELENGTH_TOLERANCE_NM = 0.2


def parse_wavelength_nm(wavelength: Union[int, str, float]) -> float:
    if isinstance(wavelength, bool):
        raise TLSC1ValidationError("wavelength must be numeric, not bool")
    if isinstance(wavelength, (int, float)):
        value = float(wavelength)
    elif isinstance(wavelength, str):
        match = _WAVELENGTH_RE.match(wavelength)
        if not match:
            raise TLSC1ValidationError(f"Invalid wavelength: {wavelength!r}")
        value = float(match.group(1))
    else:
        raise TLSC1ValidationError(f"wavelength must be int, float, or str, got {type(wavelength)!r}")
    if not math.isfinite(value) or value < 0:
        raise TLSC1ValidationError("wavelength must be a finite non-negative value in nm")
    return value


def _normalize_port_type(port_type: str) -> str:
    normalized = str(port_type).strip().upper()
    if normalized in _USB_PORT_TYPES:
        return "USB"
    if normalized in _SERIAL_PORT_TYPES:
        return "SERIAL"
    raise TLSC1ValidationError(f"Unsupported port_type {port_type!r}; expected USB or SERIAL/COM/RS232")


def _validate_grating_number(num: object) -> int:
    if isinstance(num, bool):
        raise TLSC1ValidationError("grating number must be an integer, not bool")
    if isinstance(num, float):
        if not num.is_integer():
            raise TLSC1ValidationError("grating number must be an integer value")
        value = int(num)
        if value <= 0:
            raise TLSC1ValidationError("grating number must be a positive integer")
        return value
    if not isinstance(num, (int, str)):
        raise TLSC1ValidationError(f"Invalid grating number: {num!r}")
    try:
        value = int(num)
    except (TypeError, ValueError) as exc:
        raise TLSC1ValidationError(f"Invalid grating number: {num!r}") from exc
    if value <= 0:
        raise TLSC1ValidationError("grating number must be a positive integer")
    return value


def _validate_timeout_seconds(timeout: float | int) -> float:
    if isinstance(timeout, bool):
        raise TLSC1ValidationError("timeout must be numeric, not bool")
    value = float(timeout)
    if not math.isfinite(value) or value <= 0:
        raise TLSC1ValidationError("timeout must be a finite positive value in seconds")
    return value


def _validate_poll_interval_seconds(poll_interval: float | int) -> float:
    if isinstance(poll_interval, bool):
        raise TLSC1ValidationError("poll_interval must be numeric, not bool")
    value = float(poll_interval)
    if not math.isfinite(value) or value <= 0:
        raise TLSC1ValidationError("poll_interval must be a finite positive value in seconds")
    return value


def _validate_tolerance_nm(tolerance_nm: float | int) -> float:
    if isinstance(tolerance_nm, bool):
        raise TLSC1ValidationError("tolerance_nm must be numeric, not bool")
    value = float(tolerance_nm)
    if not math.isfinite(value) or value < 0:
        raise TLSC1ValidationError("tolerance_nm must be a finite non-negative value in nm")
    return value


class tls_c1:
    def __init__(self):
        self._api: SpectrometerAPI | None = None
        self._device_id: int | None = None
        self._target_wavelength_nm: float | None = None
        self._move_in_progress = False
        self._last_connect_kwargs = {
            "Mono": "Omni",
            "port_type": "USB",
            "serial_number": "OM319069",
        }
        self.mono = self._last_connect_kwargs["Mono"]
        self.port_type = self._last_connect_kwargs["port_type"]
        self.serial_number = self._last_connect_kwargs["serial_number"]

    @property
    def device_id(self) -> int | None:
        return self._device_id

    @property
    def target_wavelength_nm(self) -> float | None:
        return self._target_wavelength_nm

    def get_target_wavelength(self) -> float | None:
        return self._target_wavelength_nm

    def _require_api(self) -> SpectrometerAPI:
        if self._api is None:
            self._api = SpectrometerAPI()
        return self._api

    @staticmethod
    def _check_usb_visibility(api: SpectrometerAPI, serial_number: str) -> list[str]:
        visible_serials = api.list_device_serials()
        if not visible_serials:
            raise TLSC1DeviceNotFoundError(
                "DLL loaded, but no device found; check FTDI driver/device connection.",
            )
        if serial_number not in visible_serials:
            visible_text = ", ".join(visible_serials)
            raise TLSC1DeviceNotFoundError(
                f"DLL loaded and {len(visible_serials)} device(s) are visible, "
                f"but target serial {serial_number!r} was not found. "
                f"Visible serial numbers: {visible_text}. "
                "Check the requested serial number, FTDI driver, and device connection.",
            )
        return visible_serials

    @staticmethod
    def _raise_open_failure(
        port_type: str,
        connection_target: str,
        visible_serials: list[str] | None = None,
    ) -> None:
        if port_type == "USB":
            suffix = ""
            if visible_serials:
                suffix = f" Visible serial numbers: {', '.join(visible_serials)}."
            raise TLSC1ConnectionError(
                f"DLL loaded and device enumeration succeeded, but open({connection_target!r}) failed. "
                "Check whether the requested device is already in use, and verify the FTDI driver/device connection."
                f"{suffix}",
            )
        raise TLSC1ConnectionError(
            f"DLL loaded, but open({connection_target!r}) failed. "
            "Check the COM port value, driver, and device connection.",
        )

    def _require_connected_device_id(self) -> int:
        if self._device_id is None or not self.is_connected:
            raise TLSC1NotConnectedError("Device is not connected")
        return self._device_id

    @property
    def is_connected(self) -> bool:
        if self._device_id is None or self._api is None:
            return False
        try:
            return bool(self._api.get_is_open(self._device_id))
        except TLSC1DeviceError:
            return False

    def __del__(self):
        try:
            self.disconnect()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.disconnect()
        return False

    def renew(self):
        kwargs = dict(self._last_connect_kwargs)
        self.disconnect()
        return self.connect(**kwargs)

    def set_wavelength(self, wavelength: Union[int, str, float]):
        self._target_wavelength_nm = parse_wavelength_nm(wavelength)
        return self

    def move(self, timeout: float | int = _DEFAULT_MOVE_TIMEOUT_SECONDS):
        device_id = self._require_connected_device_id()
        if self._target_wavelength_nm is None:
            raise TLSC1StateError("Target wavelength is not set")
        timeout_seconds = _validate_timeout_seconds(timeout)
        api = self._require_api()
        if hasattr(api, "set_timeout"):
            timeout_ms = min(int(timeout_seconds * 1000), 2_147_483_647)
            api.set_timeout(device_id, timeout_ms, timeout_ms)
        try:
            api.move_to_wave(device_id, self._target_wavelength_nm)
        except TLSC1DeviceError as exc:
            text = str(exc).lower()
            if "timeout" in text or "time out" in text:
                raise TLSC1MoveTimeoutError(str(exc)) from exc
            raise
        self._move_in_progress = True
        self.wait_until_idle(timeout=timeout_seconds)
        return self

    def set_grating(self, num):
        device_id = self._require_connected_device_id()
        grating = _validate_grating_number(num)
        self._require_api().set_grating(device_id, grating)
        return self

    def connect(self, Mono="Omni", port_type="USB", serial_number="OM319069"):
        normalized_port_type = _normalize_port_type(port_type)
        connection_target = str(serial_number).strip()
        if not connection_target:
            raise TLSC1ValidationError("serial_number must not be empty")

        same_request = (
            self.mono == Mono
            and self.port_type == normalized_port_type
            and self.serial_number == connection_target
        )

        requested = {
            "Mono": Mono,
            "port_type": normalized_port_type,
            "serial_number": connection_target,
        }
        self._last_connect_kwargs = dict(requested)
        self.mono = Mono
        self.port_type = normalized_port_type
        self.serial_number = connection_target

        api = self._require_api()
        if self.is_connected:
            if same_request:
                return self
            self.disconnect()

        api.set_usb_mode(normalized_port_type == "USB")
        visible_serials: list[str] | None = None
        if normalized_port_type == "USB":
            visible_serials = self._check_usb_visibility(api, connection_target)
        try:
            device_id = api.open(connection_target)
        except TLSC1DeviceError as exc:
            try:
                self._raise_open_failure(normalized_port_type, connection_target, visible_serials)
            except TLSC1ConnectionError as connection_exc:
                raise connection_exc from exc
        if device_id < 0:
            self._raise_open_failure(normalized_port_type, connection_target, visible_serials)
        if not api.get_is_open(device_id):
            if device_id >= 0:
                try:
                    api.close(device_id)
                except TLSC1DeviceError:
                    pass
            self._raise_open_failure(normalized_port_type, connection_target, visible_serials)
        self._device_id = device_id
        return self

    def disconnect(self):
        if self._device_id is None:
            return self

        device_id = self._device_id
        self._device_id = None
        self._move_in_progress = False
        if self._api is None:
            return self

        try:
            was_open = self._api.get_is_open(device_id)
        except TLSC1DeviceError:
            was_open = True
        if was_open:
            self._api.close(device_id)
        return self

    def get_wavelength(self) -> float:
        device_id = self._require_connected_device_id()
        return float(self._require_api().get_curr_wave(device_id))

    def get_grating(self) -> int:
        device_id = self._require_connected_device_id()
        return int(self._require_api().get_grating(device_id))

    def device_info(self):
        device_id = self._require_connected_device_id()
        return self._require_api().get_dev_info(device_id)

    def last_error(self) -> str:
        device_id = self._require_connected_device_id()
        return self._require_api().get_error(device_id)

    def is_moving(self, tolerance_nm: float | int = _DEFAULT_WAVELENGTH_TOLERANCE_NM) -> bool:
        self._require_connected_device_id()
        tolerance = _validate_tolerance_nm(tolerance_nm)
        target = self._target_wavelength_nm
        if target is None or not self._move_in_progress:
            return False
        current = self.get_wavelength()
        if abs(current - target) <= tolerance:
            self._move_in_progress = False
            return False
        return True

    def get_status(self) -> DeviceStatus:
        connected = self.is_connected
        current_wavelength: float | None = None
        grating: int | None = None
        last_error: str | None = None
        moving = False

        if connected and self._device_id is not None:
            api = self._require_api()
            try:
                current_wavelength = float(api.get_curr_wave(self._device_id))
            except TLSC1DeviceError as exc:
                last_error = str(exc)
            try:
                grating = int(api.get_grating(self._device_id))
            except TLSC1DeviceError as exc:
                last_error = str(exc)
            if self._target_wavelength_nm is not None and self._move_in_progress and current_wavelength is not None:
                moving = abs(current_wavelength - self._target_wavelength_nm) > _DEFAULT_WAVELENGTH_TOLERANCE_NM
                if not moving:
                    self._move_in_progress = False
            try:
                error_text = api.get_error(self._device_id)
                last_error = error_text or last_error
            except TLSC1DeviceError as exc:
                last_error = str(exc)

        return DeviceStatus(
            connected=connected,
            device_id=self._device_id,
            mono=str(self.mono),
            port_type=str(self.port_type),
            connection_target=str(self.serial_number),
            target_wavelength_nm=self._target_wavelength_nm,
            current_wavelength_nm=current_wavelength,
            grating=grating,
            moving=moving,
            last_error=last_error,
        )

    def wait_until_idle(
        self,
        timeout: float | int = _DEFAULT_MOVE_TIMEOUT_SECONDS,
        poll_interval: float | int = _DEFAULT_POLL_INTERVAL_SECONDS,
        tolerance_nm: float | int = _DEFAULT_WAVELENGTH_TOLERANCE_NM,
    ):
        device_id = self._require_connected_device_id()
        timeout_seconds = _validate_timeout_seconds(timeout)
        poll_seconds = _validate_poll_interval_seconds(poll_interval)
        tolerance = _validate_tolerance_nm(tolerance_nm)
        target = self._target_wavelength_nm
        deadline = time.monotonic() + timeout_seconds

        while True:
            current = float(self._require_api().get_curr_wave(device_id))
            if target is None:
                self._move_in_progress = False
                return self
            if abs(current - target) <= tolerance:
                self._move_in_progress = False
                return self
            if time.monotonic() >= deadline:
                raise TLSC1MoveTimeoutError(
                    f"Timed out waiting for wavelength {target:g} nm; last reading was {current:g} nm.",
                )
            time.sleep(min(poll_seconds, max(deadline - time.monotonic(), 0.0)))


TLSC1 = tls_c1
