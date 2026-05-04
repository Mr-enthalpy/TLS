"""Low-level safe wrapper over the vendor spectrometer SDK."""

from __future__ import annotations

import ctypes
import math
from collections.abc import Sequence
from pathlib import Path

from ._native import FUNCTION_SPECS, STRING_BUFFER_SIZE, load_library
from . import constants as sdk_constants
from .errors import TLSC1DeviceError, TLSC1ValidationError
from .types import DeviceInfo, SpecInfo

_ADVANCED_METHODS = {
    "backup",
    "restore",
    "set_correct_params",
    "get_correct_params",
    "set_dev_info",
    "set_filter_home",
    "set_grating_home",
    "set_motor_home",
    "set_motor_home_dir",
    "set_slit_home",
    "set_user_data",
}
_EXPLICIT_METHODS = {
    "spec_get_dll_ver",
    "spec_set_usb_mode",
    "spec_enum_dev_count",
    "spec_enum_dev_sn",
    "spec_open",
    "spec_close",
    "spec_get_is_open",
    "spec_get_error",
    "spec_set_dev_info",
    "spec_set_io_output",
    "spec_get_dev_info",
    "spec_set_grating",
    "spec_set_turret",
    "spec_set_turret_enbale",
    "spec_move_wave",
    "spec_move_to_wave",
    "spec_move_steps",
    "spec_move_to_steps",
    "spec_get_grating_info",
    "spec_get_max_wavelength",
    "spec_get_init_wave",
    "spec_get_move_speed",
    "spec_get_filter_limit",
    "spec_is_setup_filter",
    "spec_get_filter_status",
    "spec_set_filter_status",
    "spec_get_filter",
    "spec_set_filter",
    "spec_get_zero_offset",
    "spec_get_zero_pos",
    "spec_get_adjustment",
    "spec_set_move_speed",
    "spec_get_motor_steps",
    "spec_set_motor_steps",
    "spec_get_motor_speed",
    "spec_set_motor_speed",
    "spec_get_motor_home_dir",
    "spec_set_motor_home_dir",
    "spec_get_motor_total_steps",
    "spec_set_motor_total_steps",
    "spec_set_motor_home",
    "spec_get_init_peripherals",
    "spec_set_init_peripherals",
    "spec_get_peripherals_init_pos",
    "spec_set_peripherals_init_pos",
    "spec_get_trig_out_interval",
    "spec_get_trig_in_interval",
    "spec_set_trig_out_interval",
    "spec_set_trig_in_interval",
    "spec_set_trig_mode",
    "spec_is_setup_mirror",
    "spec_setup_mirror",
    "spec_is_setup_slit",
    "spec_setup_slit",
    "spec_is_setup_shutter",
    "spec_setup_shutter",
    "spec_get_slit_width",
    "spec_set_slit_width",
    "spec_get_slit_bandpass",
    "spec_set_slit_bandpass",
    "spec_get_slit_zero_pos",
    "spec_set_slit_zero_pos",
    "spec_get_slit_model",
    "spec_set_slit_model",
    "spec_get_shutter_status",
    "spec_set_shutter_status",
    "spec_get_diaphragm",
    "spec_set_diaphragm",
    "spec_get_diaphragm_steps",
    "spec_set_diaphragm_steps",
    "spec_get_focus_mirror",
    "spec_set_focus_mirror",
    "spec_get_focus_mirror_steps",
    "spec_set_focus_mirror_steps",
    "spec_set_correct_params",
    "spec_get_correct_params",
    "spec_wave_to_step",
    "spec_pixels_to_waves",
    "spec_get_ccd_mode",
    "spec_init_spectral_splice",
    "spec_init_spectral_splice2",
    "spec_spectral_splice",
    "spec_set_user_data",
    "spec_get_user_data",
}
_SIMPLE_OUT_TYPES = {
    ctypes.c_bool,
    ctypes.c_double,
    ctypes.c_float,
    ctypes.c_int,
    ctypes.c_long,
    ctypes.c_short,
    ctypes.c_ubyte,
    ctypes.c_ushort,
}
_MOTOR_CODES = {
    sdk_constants.MOTOR_FILTER_OUTSIDE,
    sdk_constants.MOTOR_EXPORT,
    sdk_constants.MOTOR_SLIT_SIDE_IN,
    sdk_constants.MOTOR_SLIT_SIDE_OUT,
    sdk_constants.MOTOR_SLIT_FRONT_OUT,
    sdk_constants.MOTOR_SLIT_FRONT_IN,
    sdk_constants.MOTOR_ENTRANCE,
    sdk_constants.MOTOR_FILTER_INSIDE,
    sdk_constants.MOTOR_FOCUS_MIRROR,
    sdk_constants.MOTOR_DIAPHRAGM_SIDE,
    sdk_constants.MOTOR_DIAPHRAGM_FRONT,
}
_PERIPHERAL_FLAGS = {
    sdk_constants.PERIPHERAL_FILTER_OUTSIDE,
    sdk_constants.PERIPHERAL_EXPORT,
    sdk_constants.PERIPHERAL_SLIT_SIDE_IN,
    sdk_constants.PERIPHERAL_SLIT_SIDE_OUT,
    sdk_constants.PERIPHERAL_SLIT_FRONT_OUT,
    sdk_constants.PERIPHERAL_SLIT_FRONT_IN,
    sdk_constants.PERIPHERAL_ENTRANCE,
    sdk_constants.PERIPHERAL_FILTER_INSIDE,
    sdk_constants.PERIPHERAL_SHUTTER1,
    sdk_constants.PERIPHERAL_SHUTTER2,
    sdk_constants.PERIPHERAL_FOCUS_MIRROR,
    sdk_constants.PERIPHERAL_DIAPHRAGM_SIDE,
    sdk_constants.PERIPHERAL_DIAPHRAGM_FRONT,
}


def _strip_spec_prefix(c_name: str) -> str:
    if c_name.startswith("spec_"):
        return c_name[5:]
    return c_name


def _is_pointer_type(ctype: object) -> bool:
    return isinstance(ctype, type) and issubclass(ctype, ctypes._Pointer)  # type: ignore[attr-defined]


def _points_to_simple_value(ctype: object) -> bool:
    return _is_pointer_type(ctype) and getattr(ctype, "_type_", None) in _SIMPLE_OUT_TYPES


def _value_from_ctype(value: ctypes._SimpleCData) -> int | float | bool:  # type: ignore[attr-defined]
    return value.value


def _device_id_from_call_args(args: tuple[object, ...]) -> int | None:
    if not args:
        return None
    candidate = args[0]
    if isinstance(candidate, bool):
        return None
    if isinstance(candidate, (int, float, str, bytes, bytearray)):
        try:
            return int(candidate)
        except (TypeError, ValueError):
            return None
    return None


class SpectrometerAPI:
    """Thin Python wrapper with one method per SDK function."""

    def __init__(self, lib: ctypes.CDLL | None = None, sdk_dir: str | Path | None = None):
        self.lib = lib if lib is not None else load_library(sdk_dir=sdk_dir)

    @staticmethod
    def _buffer(size: int = STRING_BUFFER_SIZE) -> ctypes.Array[ctypes.c_char]:
        return ctypes.create_string_buffer(size)

    @staticmethod
    def _decode_c_string(raw: bytes | bytearray) -> str:
        data = bytes(raw).split(b"\x00", 1)[0]
        for encoding in ("utf-8", "gbk", "mbcs"):
            try:
                return data.decode(encoding).strip()
            except (LookupError, UnicodeDecodeError):
                continue
        return data.decode("latin1", errors="replace").strip()

    @staticmethod
    def _encode_c_string(text: str | bytes) -> bytes:
        if isinstance(text, bytes):
            return text
        return text.encode("utf-8")

    @staticmethod
    def _encode_c_char(value: str | bytes | int) -> bytes | int:
        if isinstance(value, int):
            return value
        data = value if isinstance(value, bytes) else value.encode("ascii", errors="strict")
        if len(data) != 1:
            raise TLSC1ValidationError(f"Expected exactly one byte for char argument, got {value!r}")
        return data

    @staticmethod
    def _as_spec_info(info: SpecInfo | DeviceInfo) -> SpecInfo:
        if isinstance(info, SpecInfo):
            return info
        if isinstance(info, DeviceInfo):
            return info.to_spec_info()
        raise TLSC1ValidationError(f"Expected SpecInfo or DeviceInfo, got {type(info)!r}")

    @staticmethod
    def _as_void_pointer(param: object) -> ctypes.c_void_p:
        if isinstance(param, ctypes.c_void_p):
            return param
        if isinstance(param, int):
            return ctypes.c_void_p(param)
        if isinstance(param, (ctypes.Array, ctypes.Structure)):
            return ctypes.cast(ctypes.byref(param), ctypes.c_void_p)
        if hasattr(param, "contents"):
            return ctypes.cast(param, ctypes.c_void_p)  # type: ignore[arg-type]
        try:
            return ctypes.cast(ctypes.byref(param), ctypes.c_void_p)  # type: ignore[arg-type]
        except TypeError as exc:
            raise TLSC1ValidationError(f"Unsupported pointer-like value: {type(param)!r}") from exc

    @staticmethod
    def _as_float_array(values: Sequence[float]) -> ctypes.Array[ctypes.c_float]:
        return (ctypes.c_float * len(values))(*(float(value) for value in values))

    @staticmethod
    def _as_bytes_array(data: bytes | bytearray | memoryview) -> ctypes.Array[ctypes.c_ubyte]:
        raw = bytes(data)
        return (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)

    @staticmethod
    def _positive_int(value: object, name: str) -> int:
        if isinstance(value, bool):
            raise TLSC1ValidationError(f"{name} must be a positive integer, not bool")
        try:
            converted = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise TLSC1ValidationError(f"{name} must be a positive integer") from exc
        if converted <= 0:
            raise TLSC1ValidationError(f"{name} must be a positive integer")
        return converted

    @staticmethod
    def _finite_float(value: object, name: str) -> float:
        try:
            converted = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise TLSC1ValidationError(f"{name} must be a finite number") from exc
        if not math.isfinite(converted):
            raise TLSC1ValidationError(f"{name} must be a finite number")
        return converted

    @staticmethod
    def _non_negative_int(value: object, name: str) -> int:
        if isinstance(value, bool):
            raise TLSC1ValidationError(f"{name} must be a non-negative integer, not bool")
        try:
            converted = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise TLSC1ValidationError(f"{name} must be a non-negative integer") from exc
        if converted < 0:
            raise TLSC1ValidationError(f"{name} must be a non-negative integer")
        return converted

    @staticmethod
    def _bounded_int(value: object, name: str, minimum: int, maximum: int) -> int:
        if isinstance(value, bool):
            raise TLSC1ValidationError(f"{name} must be an integer in [{minimum}, {maximum}], not bool")
        try:
            converted = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise TLSC1ValidationError(f"{name} must be an integer in [{minimum}, {maximum}]") from exc
        if converted < minimum or converted > maximum:
            raise TLSC1ValidationError(f"{name} must be an integer in [{minimum}, {maximum}]")
        return converted

    @staticmethod
    def _filter_channel(value: object) -> int:
        if isinstance(value, bool):
            raise TLSC1ValidationError("filter channel must be 0 or 1, not bool")
        try:
            converted = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise TLSC1ValidationError("filter channel must be 0 or 1") from exc
        if converted not in (0, 1):
            raise TLSC1ValidationError("filter channel must be 0 or 1")
        return converted

    @classmethod
    def _slit_index(cls, value: object) -> int:
        return cls._bounded_int(value, "slit index", 0, 3)

    @classmethod
    def _slit_char(cls, value: int | str | bytes) -> bytes | int:
        if isinstance(value, (str, bytes)):
            char = cls._encode_c_char(value)
            raw = bytes([char]) if isinstance(char, int) else char
            if raw not in (b"0", b"1", b"2", b"3"):
                raise TLSC1ValidationError("slit index char must be one of '0', '1', '2', or '3'")
            return char
        return cls._encode_c_char(str(cls._slit_index(value)))

    @classmethod
    def _shutter_index(cls, value: object) -> int:
        return cls._bounded_int(value, "shutter index", 0, 1)

    @classmethod
    def _mirror_index(cls, value: object) -> int:
        return cls._bounded_int(value, "mirror index", 0, 1)

    @classmethod
    def _binary_index(cls, value: object, name: str) -> int:
        return cls._bounded_int(value, name, 0, 1)

    @classmethod
    def _byte_value(cls, value: object, name: str) -> int:
        return cls._bounded_int(value, name, 0, 255)

    @classmethod
    def _short_non_negative(cls, value: object, name: str) -> int:
        return cls._bounded_int(value, name, 0, 32767)

    @staticmethod
    def _known_motor_code(value: object) -> int:
        if isinstance(value, bool):
            raise TLSC1ValidationError("motor code must be one of the SDK MOTOR_* constants, not bool")
        try:
            converted = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise TLSC1ValidationError("motor code must be one of the SDK MOTOR_* constants") from exc
        if converted not in _MOTOR_CODES:
            raise TLSC1ValidationError("motor code must be one of the supported SDK MOTOR_* constants")
        return converted

    @staticmethod
    def _known_peripheral_flag(value: object) -> int:
        if isinstance(value, bool):
            raise TLSC1ValidationError("peripheral flag must be one of the SDK PERIPHERAL_* constants, not bool")
        try:
            converted = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise TLSC1ValidationError("peripheral flag must be one of the SDK PERIPHERAL_* constants") from exc
        if converted not in _PERIPHERAL_FLAGS:
            raise TLSC1ValidationError("peripheral flag must be one of the supported SDK PERIPHERAL_* constants")
        return converted

    def _get_error(self, device_id: int) -> str:
        buffer = self._buffer()
        self.lib.spec_get_error(int(device_id), buffer, len(buffer))
        return self._decode_c_string(buffer.raw)

    def _check(self, ok: bool, action: str, device_id: int | None = None) -> None:
        if ok:
            return
        suffix = ""
        if device_id is not None:
            error = self._get_error(device_id)
            if error:
                suffix = f": {error}"
        raise TLSC1DeviceError(f"SDK operation failed: {action}{suffix}")

    def _prepare_scalar_arg(self, ctype: object, value: object) -> object:
        if ctype is ctypes.c_char_p:
            return self._encode_c_string(value)  # type: ignore[arg-type]
        if ctype is ctypes.c_char:
            return self._encode_c_char(value)  # type: ignore[arg-type]
        if ctype is SpecInfo:
            return self._as_spec_info(value)  # type: ignore[arg-type]
        if ctype is ctypes.c_void_p:
            return self._as_void_pointer(value)
        if ctype is ctypes.c_bool:
            return bool(value)
        return value

    def get_dll_ver(self) -> str:
        buffer = self._buffer()
        self.lib.spec_get_dll_ver(buffer, len(buffer))
        return self._decode_c_string(buffer.raw)

    def set_usb_mode(self, usb: bool) -> None:
        self.lib.spec_set_usb_mode(bool(usb))

    def enum_dev_count(self) -> int:
        return int(self.lib.spec_enum_dev_count())

    def enum_dev_sn(self, index: int) -> str:
        buffer = self._buffer()
        ok = self.lib.spec_enum_dev_sn(int(index), buffer, len(buffer))
        self._check(ok, f"enum_dev_sn({index})")
        return self._decode_c_string(buffer.raw)

    def list_device_serials(self) -> list[str]:
        count = self.enum_dev_count()
        if count < 0:
            raise TLSC1DeviceError(f"SDK operation failed: enum_dev_count() returned {count}")
        return [self.enum_dev_sn(index) for index in range(count)]

    def open(self, info: str | bytes) -> int:
        device_id = int(self.lib.spec_open(self._encode_c_string(info)))
        if device_id < 0:
            raise TLSC1DeviceError(f"SDK operation failed: open({info!r})")
        return device_id

    def close(self, device_id: int) -> None:
        self._check(bool(self.lib.spec_close(int(device_id))), f"close({device_id})", device_id)

    def get_is_open(self, device_id: int) -> bool:
        return bool(self.lib.spec_get_is_open(int(device_id)))

    def get_error(self, device_id: int) -> str:
        return self._get_error(device_id)

    def set_dev_info(self, device_id: int, info: SpecInfo | DeviceInfo) -> None:
        payload = self._as_spec_info(info)
        ok = self.lib.spec_set_dev_info(int(device_id), payload)
        self._check(ok, "set_dev_info", device_id)

    def get_dev_info(self, device_id: int) -> DeviceInfo:
        info = SpecInfo()
        ok = self.lib.spec_get_dev_info(int(device_id), ctypes.byref(info))
        self._check(ok, "get_dev_info", device_id)
        return DeviceInfo.from_spec_info(info)

    def set_io_output(self, device_id: int, value: int) -> None:
        value = self._bounded_int(value, "io output", -32768, 32767)
        ok = self.lib.spec_set_io_output(int(device_id), value)
        self._check(ok, "set_io_output", device_id)

    def set_grating(self, device_id: int, grating: int) -> None:
        grating = self._positive_int(grating, "grating")
        ok = self.lib.spec_set_grating(int(device_id), grating)
        self._check(ok, "set_grating", device_id)

    def set_turret(self, device_id: int, turret: int) -> None:
        turret = self._positive_int(turret, "turret")
        ok = self.lib.spec_set_turret(int(device_id), turret)
        self._check(ok, "set_turret", device_id)

    def set_turret_enbale(self, device_id: int, enabled_turret: int) -> None:
        enabled_turret = self._bounded_int(enabled_turret, "enabled turret mask/count", 0, 0x7FFF)
        ok = self.lib.spec_set_turret_enbale(int(device_id), enabled_turret)
        self._check(ok, "set_turret_enbale", device_id)

    def move_wave(self, device_id: int, delta_wave: float) -> None:
        delta_wave = self._finite_float(delta_wave, "delta_wave")
        ok = self.lib.spec_move_wave(int(device_id), delta_wave)
        self._check(ok, "move_wave", device_id)

    def move_to_wave(self, device_id: int, wave: float) -> None:
        wave = self._finite_float(wave, "wave")
        ok = self.lib.spec_move_to_wave(int(device_id), wave)
        self._check(ok, "move_to_wave", device_id)

    def move_steps(self, device_id: int, delta_steps: float) -> None:
        delta_steps = self._finite_float(delta_steps, "delta_steps")
        ok = self.lib.spec_move_steps(int(device_id), delta_steps)
        self._check(ok, "move_steps", device_id)

    def move_to_steps(self, device_id: int, steps: float) -> None:
        steps = self._finite_float(steps, "steps")
        ok = self.lib.spec_move_to_steps(int(device_id), steps)
        self._check(ok, "move_to_steps", device_id)

    def get_grating_info(self, device_id: int, grating: int) -> tuple[int, int]:
        grating = self._positive_int(grating, "grating")
        groove = ctypes.c_int()
        blaze = ctypes.c_long()
        ok = self.lib.spec_get_grating_info(int(device_id), grating, ctypes.byref(groove), ctypes.byref(blaze))
        self._check(ok, "get_grating_info", device_id)
        return int(groove.value), int(blaze.value)

    def get_max_wavelength(self, device_id: int, grating: int) -> float:
        grating = self._positive_int(grating, "grating")
        value = ctypes.c_float()
        ok = self.lib.spec_get_max_wavelength(int(device_id), grating, ctypes.byref(value))
        self._check(ok, "get_max_wavelength", device_id)
        return float(value.value)

    def get_init_wave(self, device_id: int, grating: int) -> float:
        grating = self._positive_int(grating, "grating")
        value = ctypes.c_float()
        ok = self.lib.spec_get_init_wave(int(device_id), grating, ctypes.byref(value))
        self._check(ok, "get_init_wave", device_id)
        return float(value.value)

    def get_move_speed(self, device_id: int, grating: int) -> int:
        grating = self._positive_int(grating, "grating")
        speed = ctypes.c_int()
        ok = self.lib.spec_get_move_speed(int(device_id), grating, ctypes.byref(speed))
        self._check(ok, "get_move_speed", device_id)
        return int(speed.value)

    def get_filter_limit(self, device_id: int, grating: int, index: int) -> float:
        grating = self._positive_int(grating, "grating")
        index = self._positive_int(index, "index")
        value = ctypes.c_double()
        ok = self.lib.spec_get_filter_limit(int(device_id), grating, index, ctypes.byref(value))
        self._check(ok, "get_filter_limit", device_id)
        return float(value.value)

    def is_setup_filter(self, device_id: int, index: int) -> bool:
        index = self._filter_channel(index)
        setup = ctypes.c_bool()
        ok = self.lib.spec_is_setup_filter(int(device_id), index, ctypes.byref(setup))
        self._check(ok, "is_setup_filter", device_id)
        return bool(setup.value)

    def get_filter_status(self, device_id: int, which: int) -> bool:
        which = self._filter_channel(which)
        automatic = ctypes.c_bool()
        ok = self.lib.spec_get_filter_status(int(device_id), which, ctypes.byref(automatic))
        self._check(ok, "get_filter_status", device_id)
        return bool(automatic.value)

    def set_filter_status(self, device_id: int, which: int, automatic: bool) -> None:
        which = self._filter_channel(which)
        ok = self.lib.spec_set_filter_status(int(device_id), which, bool(automatic))
        self._check(ok, "set_filter_status", device_id)

    def get_filter(self, device_id: int, which: int) -> int:
        which = self._filter_channel(which)
        index = ctypes.c_int()
        ok = self.lib.spec_get_filter(int(device_id), which, ctypes.byref(index))
        self._check(ok, "get_filter", device_id)
        return int(index.value)

    def set_filter(self, device_id: int, which: int, index: int) -> None:
        which = self._filter_channel(which)
        index = self._positive_int(index, "filter index")
        ok = self.lib.spec_set_filter(int(device_id), which, index)
        self._check(ok, "set_filter", device_id)

    def get_zero_offset(self, device_id: int, grating: int) -> int:
        grating = self._positive_int(grating, "grating")
        offset = ctypes.c_long()
        ok = self.lib.spec_get_zero_offset(int(device_id), grating, ctypes.byref(offset))
        self._check(ok, "get_zero_offset", device_id)
        return int(offset.value)

    def get_zero_pos(self, device_id: int, grating: int, index: int) -> int:
        grating = self._positive_int(grating, "grating")
        index = self._bounded_int(index, "zero position index", 0, 3)
        position = ctypes.c_long()
        ok = self.lib.spec_get_zero_pos(int(device_id), grating, index, ctypes.byref(position))
        self._check(ok, "get_zero_pos", device_id)
        return int(position.value)

    def get_adjustment(self, device_id: int, grating: int) -> float:
        grating = self._positive_int(grating, "grating")
        value = ctypes.c_float()
        ok = self.lib.spec_get_adjustment(int(device_id), grating, ctypes.byref(value))
        self._check(ok, "get_adjustment", device_id)
        return float(value.value)

    def set_move_speed(self, device_id: int, grating: int, speed: int) -> None:
        grating = self._positive_int(grating, "grating")
        speed = self._positive_int(speed, "speed")
        ok = self.lib.spec_set_move_speed(int(device_id), grating, speed)
        self._check(ok, "set_move_speed", device_id)

    def get_motor_steps(self, device_id: int, motor: int) -> int:
        motor = self._known_motor_code(motor)
        value = ctypes.c_long()
        ok = self.lib.spec_get_motor_steps(int(device_id), motor, ctypes.byref(value))
        self._check(ok, "get_motor_steps", device_id)
        return int(value.value)

    def set_motor_steps(self, device_id: int, motor: int, steps: int) -> None:
        motor = self._known_motor_code(motor)
        steps = self._non_negative_int(steps, "steps")
        ok = self.lib.spec_set_motor_steps(int(device_id), motor, steps)
        self._check(ok, "set_motor_steps", device_id)

    def get_motor_speed(self, device_id: int, motor: int) -> int:
        motor = self._known_motor_code(motor)
        value = ctypes.c_int()
        ok = self.lib.spec_get_motor_speed(int(device_id), motor, ctypes.byref(value))
        self._check(ok, "get_motor_speed", device_id)
        return int(value.value)

    def set_motor_speed(self, device_id: int, motor: int, speed: int) -> None:
        motor = self._known_motor_code(motor)
        speed = self._positive_int(speed, "speed")
        ok = self.lib.spec_set_motor_speed(int(device_id), motor, speed)
        self._check(ok, "set_motor_speed", device_id)

    def get_motor_home_dir(self, device_id: int, motor: int) -> int:
        motor = self._known_motor_code(motor)
        value = ctypes.c_int()
        ok = self.lib.spec_get_motor_home_dir(int(device_id), motor, ctypes.byref(value))
        self._check(ok, "get_motor_home_dir", device_id)
        return int(value.value)

    def set_motor_home_dir(self, device_id: int, motor: int, direction: int) -> None:
        motor = self._known_motor_code(motor)
        direction = self._bounded_int(direction, "home direction", -1, 1)
        ok = self.lib.spec_set_motor_home_dir(int(device_id), motor, direction)
        self._check(ok, "set_motor_home_dir", device_id)

    def get_motor_total_steps(self, device_id: int, motor: int) -> int:
        motor = self._known_motor_code(motor)
        value = ctypes.c_long()
        ok = self.lib.spec_get_motor_total_steps(int(device_id), motor, ctypes.byref(value))
        self._check(ok, "get_motor_total_steps", device_id)
        return int(value.value)

    def set_motor_total_steps(self, device_id: int, motor: int, steps: int) -> None:
        motor = self._known_motor_code(motor)
        steps = self._non_negative_int(steps, "steps")
        ok = self.lib.spec_set_motor_total_steps(int(device_id), motor, steps)
        self._check(ok, "set_motor_total_steps", device_id)

    def set_motor_home(self, device_id: int, motor: int) -> None:
        motor = self._known_motor_code(motor)
        ok = self.lib.spec_set_motor_home(int(device_id), motor)
        self._check(ok, "set_motor_home", device_id)

    def get_init_peripherals(self, device_id: int) -> int:
        value = ctypes.c_ushort()
        ok = self.lib.spec_get_init_peripherals(int(device_id), ctypes.byref(value))
        self._check(ok, "get_init_peripherals", device_id)
        return int(value.value)

    def set_init_peripherals(self, device_id: int, peripheral_flags: int) -> None:
        flags = self._bounded_int(peripheral_flags, "peripheral flags", 0, 0xFFFF)
        ok = self.lib.spec_set_init_peripherals(int(device_id), flags)
        self._check(ok, "set_init_peripherals", device_id)

    def get_peripherals_init_pos(self, device_id: int, peripheral: int) -> int:
        peripheral = self._known_peripheral_flag(peripheral)
        value = ctypes.c_ubyte()
        ok = self.lib.spec_get_peripherals_init_pos(int(device_id), peripheral, ctypes.byref(value))
        self._check(ok, "get_peripherals_init_pos", device_id)
        return int(value.value)

    def set_peripherals_init_pos(self, device_id: int, peripheral: int, position: int) -> None:
        peripheral = self._known_peripheral_flag(peripheral)
        position = self._byte_value(position, "position")
        ok = self.lib.spec_set_peripherals_init_pos(int(device_id), peripheral, position)
        self._check(ok, "set_peripherals_init_pos", device_id)

    def get_trig_out_interval(self, device_id: int) -> int:
        value = ctypes.c_ushort()
        ok = self.lib.spec_get_trig_out_interval(int(device_id), ctypes.byref(value))
        self._check(ok, "get_trig_out_interval", device_id)
        return int(value.value)

    def set_trig_out_interval(self, device_id: int, interval: int) -> None:
        interval = self._bounded_int(interval, "trigger output interval", 0, 0xFFFF)
        ok = self.lib.spec_set_trig_out_interval(int(device_id), interval)
        self._check(ok, "set_trig_out_interval", device_id)

    def get_trig_in_interval(self, device_id: int) -> float:
        value = ctypes.c_float()
        ok = self.lib.spec_get_trig_in_interval(int(device_id), ctypes.byref(value))
        self._check(ok, "get_trig_in_interval", device_id)
        return float(value.value)

    def set_trig_in_interval(self, device_id: int, interval: float) -> None:
        if float(interval) < 0:
            raise TLSC1ValidationError("trigger input interval must be non-negative")
        ok = self.lib.spec_set_trig_in_interval(int(device_id), float(interval))
        self._check(ok, "set_trig_in_interval", device_id)

    def set_trig_mode(self, device_id: int, enabled: bool) -> None:
        ok = self.lib.spec_set_trig_mode(int(device_id), bool(enabled))
        self._check(ok, "set_trig_mode", device_id)

    def is_setup_mirror(self, device_id: int, index: int) -> bool:
        index = self._mirror_index(index)
        setup = ctypes.c_bool()
        ok = self.lib.spec_is_setup_mirror(int(device_id), index, ctypes.byref(setup))
        self._check(ok, "is_setup_mirror", device_id)
        return bool(setup.value)

    def setup_mirror(self, device_id: int, index: int, enabled: bool) -> None:
        index = self._mirror_index(index)
        ok = self.lib.spec_setup_mirror(int(device_id), index, bool(enabled))
        self._check(ok, "setup_mirror", device_id)

    def is_setup_slit(self, device_id: int, index: int) -> bool:
        index = self._slit_index(index)
        setup = ctypes.c_bool()
        ok = self.lib.spec_is_setup_slit(int(device_id), index, ctypes.byref(setup))
        self._check(ok, "is_setup_slit", device_id)
        return bool(setup.value)

    def setup_slit(self, device_id: int, index: int, enabled: bool) -> None:
        index = self._slit_index(index)
        ok = self.lib.spec_setup_slit(int(device_id), index, bool(enabled))
        self._check(ok, "setup_slit", device_id)

    def is_setup_shutter(self, device_id: int, index: int) -> bool:
        index = self._shutter_index(index)
        setup = ctypes.c_bool()
        ok = self.lib.spec_is_setup_shutter(int(device_id), index, ctypes.byref(setup))
        self._check(ok, "is_setup_shutter", device_id)
        return bool(setup.value)

    def setup_shutter(self, device_id: int, index: int, enabled: bool) -> None:
        index = self._shutter_index(index)
        ok = self.lib.spec_setup_shutter(int(device_id), index, bool(enabled))
        self._check(ok, "setup_shutter", device_id)

    def get_slit_width(self, device_id: int, index: int) -> int:
        index = self._slit_index(index)
        value = ctypes.c_int()
        ok = self.lib.spec_get_slit_width(int(device_id), index, ctypes.byref(value))
        self._check(ok, "get_slit_width", device_id)
        return int(value.value)

    def set_slit_width(self, device_id: int, index: int, width: int) -> None:
        index = self._slit_index(index)
        width = self._non_negative_int(width, "slit width")
        ok = self.lib.spec_set_slit_width(int(device_id), index, width)
        self._check(ok, "set_slit_width", device_id)

    def get_slit_bandpass(self, device_id: int, index: int) -> float:
        index = self._slit_index(index)
        value = ctypes.c_float()
        ok = self.lib.spec_get_slit_bandpass(int(device_id), index, ctypes.byref(value))
        self._check(ok, "get_slit_bandpass", device_id)
        return float(value.value)

    def set_slit_bandpass(self, device_id: int, index: int, bandpass: float) -> None:
        index = self._slit_index(index)
        if float(bandpass) < 0:
            raise TLSC1ValidationError("slit bandpass must be non-negative")
        ok = self.lib.spec_set_slit_bandpass(int(device_id), index, float(bandpass))
        self._check(ok, "set_slit_bandpass", device_id)

    def get_slit_zero_pos(self, device_id: int, index: int) -> int:
        index = self._slit_index(index)
        value = ctypes.c_int()
        ok = self.lib.spec_get_slit_zero_pos(int(device_id), index, ctypes.byref(value))
        self._check(ok, "get_slit_zero_pos", device_id)
        return int(value.value)

    def set_slit_zero_pos(self, device_id: int, index: int, position: int) -> None:
        index = self._slit_index(index)
        position = self._non_negative_int(position, "slit zero position")
        ok = self.lib.spec_set_slit_zero_pos(int(device_id), index, position)
        self._check(ok, "set_slit_zero_pos", device_id)

    def get_slit_model(self, device_id: int, index: int | str | bytes) -> str:
        char = self._slit_char(index)
        buffer = self._buffer()
        ok = self.lib.spec_get_slit_model(int(device_id), char, buffer)
        self._check(ok, "get_slit_model", device_id)
        return self._decode_c_string(buffer.raw)

    def set_slit_model(self, device_id: int, index: int | str | bytes, model: str | bytes) -> None:
        char = self._slit_char(index)
        ok = self.lib.spec_set_slit_model(int(device_id), char, self._encode_c_string(model))
        self._check(ok, "set_slit_model", device_id)

    def get_shutter_status(self, device_id: int, index: int) -> bool:
        index = self._shutter_index(index)
        value = ctypes.c_bool()
        ok = self.lib.spec_get_shutter_status(int(device_id), index, ctypes.byref(value))
        self._check(ok, "get_shutter_status", device_id)
        return bool(value.value)

    def set_shutter_status(self, device_id: int, index: int, open_: bool) -> None:
        index = self._shutter_index(index)
        ok = self.lib.spec_set_shutter_status(int(device_id), index, bool(open_))
        self._check(ok, "set_shutter_status", device_id)

    def get_diaphragm(self, device_id: int, index: int) -> int:
        index = self._binary_index(index, "diaphragm index")
        value = ctypes.c_int()
        ok = self.lib.spec_get_diaphragm(int(device_id), index, ctypes.byref(value))
        self._check(ok, "get_diaphragm", device_id)
        return int(value.value)

    def set_diaphragm(self, device_id: int, index: int, position: int) -> None:
        index = self._binary_index(index, "diaphragm index")
        position = self._non_negative_int(position, "diaphragm position")
        ok = self.lib.spec_set_diaphragm(int(device_id), index, position)
        self._check(ok, "set_diaphragm", device_id)

    def get_diaphragm_steps(self, device_id: int, index: int, position: int) -> int:
        index = self._binary_index(index, "diaphragm index")
        position = self._binary_index(position, "diaphragm position index")
        value = ctypes.c_long()
        ok = self.lib.spec_get_diaphragm_steps(int(device_id), index, position, ctypes.byref(value))
        self._check(ok, "get_diaphragm_steps", device_id)
        return int(value.value)

    def set_diaphragm_steps(self, device_id: int, index: int, position: int, steps: int) -> None:
        index = self._binary_index(index, "diaphragm index")
        position = self._binary_index(position, "diaphragm position index")
        steps = self._non_negative_int(steps, "steps")
        ok = self.lib.spec_set_diaphragm_steps(int(device_id), index, position, steps)
        self._check(ok, "set_diaphragm_steps", device_id)

    def get_focus_mirror(self, device_id: int) -> int:
        value = ctypes.c_int()
        ok = self.lib.spec_get_focus_mirror(int(device_id), ctypes.byref(value))
        self._check(ok, "get_focus_mirror", device_id)
        return int(value.value)

    def set_focus_mirror(self, device_id: int, position: int) -> None:
        position = self._non_negative_int(position, "focus mirror position")
        ok = self.lib.spec_set_focus_mirror(int(device_id), position)
        self._check(ok, "set_focus_mirror", device_id)

    def get_focus_mirror_steps(self, device_id: int, position: int) -> int:
        position = self._binary_index(position, "focus mirror position index")
        value = ctypes.c_long()
        ok = self.lib.spec_get_focus_mirror_steps(int(device_id), position, ctypes.byref(value))
        self._check(ok, "get_focus_mirror_steps", device_id)
        return int(value.value)

    def set_focus_mirror_steps(self, device_id: int, position: int, steps: int) -> None:
        position = self._binary_index(position, "focus mirror position index")
        steps = self._non_negative_int(steps, "steps")
        ok = self.lib.spec_set_focus_mirror_steps(int(device_id), position, steps)
        self._check(ok, "set_focus_mirror_steps", device_id)

    def set_correct_params(self, device_id: int, turret: int, grating: int, code: int, param: object) -> None:
        turret = self._positive_int(turret, "turret")
        grating = self._positive_int(grating, "grating")
        code = self._bounded_int(code, "correction code", 0, 255)
        ok = self.lib.spec_set_correct_params(
            int(device_id),
            turret,
            grating,
            code,
            self._as_void_pointer(param),
        )
        self._check(ok, "set_correct_params", device_id)

    def get_correct_params(self, device_id: int, turret: int, grating: int, code: int, param: object) -> object:
        turret = self._positive_int(turret, "turret")
        grating = self._positive_int(grating, "grating")
        code = self._bounded_int(code, "correction code", 0, 255)
        ok = self.lib.spec_get_correct_params(
            int(device_id),
            turret,
            grating,
            code,
            self._as_void_pointer(param),
        )
        self._check(ok, "get_correct_params", device_id)
        return param

    def wave_to_step(self, device_id: int, wave: float) -> float:
        return float(self.lib.spec_wave_to_step(int(device_id), float(wave)))

    def pixels_to_waves(
        self,
        device_id: int,
        turret: int,
        grating: int,
        center_wave: float,
        width: float,
        count: int,
        bin_x: int,
    ) -> list[float]:
        turret = self._positive_int(turret, "turret")
        grating = self._positive_int(grating, "grating")
        count = self._positive_int(count, "count")
        bin_x = self._positive_int(bin_x, "bin_x")
        result = (ctypes.c_float * count)()
        ok = self.lib.spec_pixels_to_waves(
            int(device_id),
            turret,
            grating,
            float(center_wave),
            float(width),
            count,
            bin_x,
            result,
        )
        self._check(ok, "pixels_to_waves", device_id)
        return [float(value) for value in result]

    def get_ccd_mode(self, device_id: int) -> bool:
        return bool(self.lib.spec_get_ccd_mode(int(device_id)))

    def init_spectral_splice(
        self,
        device_id: int,
        pixel_width: float,
        pixel_count: int,
        bin_x: int,
        from_nm: float,
        to_nm: float,
        ref_nm: float,
        edge: int,
        overlap: float,
        max_waves: int | None = None,
    ) -> list[float]:
        pixel_count = self._positive_int(pixel_count, "pixel_count")
        bin_x = self._positive_int(bin_x, "bin_x")
        edge = self._non_negative_int(edge, "edge")
        if float(to_nm) < float(from_nm):
            raise TLSC1ValidationError("to_nm must be greater than or equal to from_nm")
        capacity = max(self._positive_int(max_waves, "max_waves") if max_waves is not None else pixel_count, 1)
        center_waves = (ctypes.c_float * capacity)()
        waves_count = ctypes.c_int(capacity)
        ok = self.lib.spec_init_spectral_splice(
            int(device_id),
            float(pixel_width),
            pixel_count,
            bin_x,
            float(from_nm),
            float(to_nm),
            float(ref_nm),
            edge,
            float(overlap),
            center_waves,
            ctypes.byref(waves_count),
        )
        self._check(ok, "init_spectral_splice", device_id)
        return [float(center_waves[index]) for index in range(waves_count.value)]

    def init_spectral_splice2(
        self,
        device_id: int,
        pixel_width: float,
        pixel_count: int,
        bin_x: int,
        from_nm: float,
        to_nm: float,
        ref_nm: float,
        edge_left: int,
        edge_right: int,
        overlap: float,
        max_waves: int | None = None,
    ) -> list[float]:
        pixel_count = self._positive_int(pixel_count, "pixel_count")
        bin_x = self._positive_int(bin_x, "bin_x")
        edge_left = self._non_negative_int(edge_left, "edge_left")
        edge_right = self._non_negative_int(edge_right, "edge_right")
        if float(to_nm) < float(from_nm):
            raise TLSC1ValidationError("to_nm must be greater than or equal to from_nm")
        capacity = max(self._positive_int(max_waves, "max_waves") if max_waves is not None else pixel_count, 1)
        center_waves = (ctypes.c_float * capacity)()
        waves_count = ctypes.c_int(capacity)
        ok = self.lib.spec_init_spectral_splice2(
            int(device_id),
            float(pixel_width),
            pixel_count,
            bin_x,
            float(from_nm),
            float(to_nm),
            float(ref_nm),
            edge_left,
            edge_right,
            float(overlap),
            center_waves,
            ctypes.byref(waves_count),
        )
        self._check(ok, "init_spectral_splice2", device_id)
        return [float(center_waves[index]) for index in range(waves_count.value)]

    def spectral_splice(
        self,
        device_id: int,
        x1: Sequence[float],
        y1: Sequence[float],
        x2: Sequence[float],
        y2: Sequence[float],
        output_capacity: int | None = None,
    ) -> tuple[list[float], list[float]]:
        if len(x1) != len(y1):
            raise TLSC1ValidationError("x1 and y1 must have the same length")
        if len(x2) != len(y2):
            raise TLSC1ValidationError("x2 and y2 must have the same length")
        if len(x1) == 0 or len(x2) == 0:
            raise TLSC1ValidationError("spectral splice inputs must not be empty")

        size1 = len(x1)
        size2 = len(x2)
        capacity = max(
            self._positive_int(output_capacity, "output_capacity") if output_capacity is not None else size1 + size2,
            1,
        )
        x3 = (ctypes.c_float * capacity)()
        y3 = (ctypes.c_float * capacity)()
        size3 = ctypes.c_int(capacity)

        ok = self.lib.spec_spectral_splice(
            int(device_id),
            self._as_float_array(x1),
            self._as_float_array(y1),
            size1,
            self._as_float_array(x2),
            self._as_float_array(y2),
            size2,
            x3,
            y3,
            ctypes.byref(size3),
        )
        self._check(ok, "spectral_splice", device_id)
        count = size3.value
        return (
            [float(x3[index]) for index in range(count)],
            [float(y3[index]) for index in range(count)],
        )

    def set_user_data(self, device_id: int, offset: int, data: bytes | bytearray | memoryview) -> None:
        offset = self._short_non_negative(offset, "offset")
        buffer = self._as_bytes_array(data)
        self._short_non_negative(len(buffer), "data length")
        ok = self.lib.spec_set_user_data(int(device_id), offset, buffer, len(buffer))
        self._check(ok, "set_user_data", device_id)

    def get_user_data(self, device_id: int, offset: int, length: int) -> bytes:
        offset = self._short_non_negative(offset, "offset")
        length = self._short_non_negative(length, "length")
        buffer = (ctypes.c_ubyte * length)()
        ok = self.lib.spec_get_user_data(int(device_id), offset, buffer, length)
        self._check(ok, "get_user_data", device_id)
        return bytes(buffer)


def _make_action_method(c_name: str):
    py_name = _strip_spec_prefix(c_name)
    spec = FUNCTION_SPECS[c_name]
    argtypes = spec.argtypes

    def method(self: SpectrometerAPI, *args: object) -> None:
        if len(args) != len(argtypes):
            raise TypeError(f"{py_name}() takes {len(argtypes)} positional arguments but {len(args)} were given")
        prepared = [self._prepare_scalar_arg(ctype, value) for ctype, value in zip(argtypes, args)]
        device_id = _device_id_from_call_args(args)
        ok = getattr(self.lib, c_name)(*prepared)
        self._check(bool(ok), py_name, device_id)

    method.__name__ = py_name
    prefix = "Advanced SDK operation. " if py_name in _ADVANCED_METHODS else ""
    method.__doc__ = prefix + f"Wraps `{c_name}`."
    return method


def _make_string_output_method(c_name: str):
    py_name = _strip_spec_prefix(c_name)
    spec = FUNCTION_SPECS[c_name]
    input_argtypes = spec.argtypes[:-1]

    def method(self: SpectrometerAPI, *args: object) -> str:
        if len(args) != len(input_argtypes):
            raise TypeError(
                f"{py_name}() takes {len(input_argtypes)} positional arguments but {len(args)} were given",
            )
        prepared = [self._prepare_scalar_arg(ctype, value) for ctype, value in zip(input_argtypes, args)]
        buffer = self._buffer()
        device_id = _device_id_from_call_args(args)
        ok = getattr(self.lib, c_name)(*prepared, buffer)
        self._check(bool(ok), py_name, device_id)
        return self._decode_c_string(buffer.raw)

    method.__name__ = py_name
    method.__doc__ = f"Wraps `{c_name}` and returns the decoded output string."
    return method


def _make_output_method(c_name: str):
    py_name = _strip_spec_prefix(c_name)
    spec = FUNCTION_SPECS[c_name]
    pointer_types: list[object] = []
    input_argtypes: list[object] = list(spec.argtypes)
    while input_argtypes and _points_to_simple_value(input_argtypes[-1]):
        pointer_types.insert(0, input_argtypes.pop())

    def method(self: SpectrometerAPI, *args: object):
        if len(args) != len(input_argtypes):
            raise TypeError(
                f"{py_name}() takes {len(input_argtypes)} positional arguments but {len(args)} were given",
            )
        prepared = [self._prepare_scalar_arg(ctype, value) for ctype, value in zip(input_argtypes, args)]
        outputs = [pointer_type._type_() for pointer_type in pointer_types]  # type: ignore[attr-defined]
        device_id = _device_id_from_call_args(args)
        ok = getattr(self.lib, c_name)(*prepared, *(ctypes.byref(value) for value in outputs))
        self._check(bool(ok), py_name, device_id)
        values = [_value_from_ctype(value) for value in outputs]
        if len(values) == 1:
            return values[0]
        return tuple(values)

    method.__name__ = py_name
    method.__doc__ = f"Wraps `{c_name}` and returns its output parameter values."
    return method


def _install_generated_methods() -> None:
    for c_name, spec in FUNCTION_SPECS.items():
        if c_name in _EXPLICIT_METHODS:
            continue
        py_name = _strip_spec_prefix(c_name)
        if hasattr(SpectrometerAPI, py_name):
            continue
        if spec.restype is not ctypes.c_bool:
            continue
        if spec.argtypes and spec.argtypes[-1] is ctypes.c_char_p and c_name.startswith("spec_get_"):
            setattr(SpectrometerAPI, py_name, _make_string_output_method(c_name))
            continue
        if any(argtype is ctypes.c_void_p for argtype in spec.argtypes):
            continue
        trailing_simple_outputs = 0
        for argtype in reversed(spec.argtypes):
            if _points_to_simple_value(argtype):
                trailing_simple_outputs += 1
                continue
            break
        if trailing_simple_outputs and not any(
            _is_pointer_type(argtype) for argtype in spec.argtypes[:-trailing_simple_outputs]
        ):
            setattr(SpectrometerAPI, py_name, _make_output_method(c_name))
            continue
        if not any(_is_pointer_type(argtype) for argtype in spec.argtypes):
            setattr(SpectrometerAPI, py_name, _make_action_method(c_name))


_install_generated_methods()


def _alias_method(alias: str, target: str, doc: str) -> None:
    def method(self: SpectrometerAPI, *args: object, **kwargs: object):
        return getattr(self, target)(*args, **kwargs)

    method.__name__ = alias
    method.__doc__ = doc
    setattr(SpectrometerAPI, alias, method)


_alias_method("set_turret_enable", "set_turret_enbale", "Correctly spelled alias for `set_turret_enbale`.")
_alias_method("get_enabled_turret", "get_enbaled_turret", "Correctly spelled alias for `get_enbaled_turret`.")
