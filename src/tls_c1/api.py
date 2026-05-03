"""Low-level safe wrapper over the vendor spectrometer SDK."""

from __future__ import annotations

import ctypes
from collections.abc import Sequence
from pathlib import Path

from ._native import FUNCTION_SPECS, STRING_BUFFER_SIZE, load_library
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
    "spec_get_dev_info",
    "spec_get_grating_info",
    "spec_get_max_wavelength",
    "spec_get_init_wave",
    "spec_get_move_speed",
    "spec_get_filter_limit",
    "spec_is_setup_filter",
    "spec_get_filter_status",
    "spec_set_filter_status",
    "spec_get_filter",
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

    def set_correct_params(self, device_id: int, turret: int, grating: int, code: int, param: object) -> None:
        ok = self.lib.spec_set_correct_params(
            int(device_id),
            int(turret),
            int(grating),
            int(code),
            self._as_void_pointer(param),
        )
        self._check(ok, "set_correct_params", device_id)

    def get_correct_params(self, device_id: int, turret: int, grating: int, code: int, param: object) -> object:
        ok = self.lib.spec_get_correct_params(
            int(device_id),
            int(turret),
            int(grating),
            int(code),
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
        result = (ctypes.c_float * int(count))()
        ok = self.lib.spec_pixels_to_waves(
            int(device_id),
            int(turret),
            int(grating),
            float(center_wave),
            float(width),
            int(count),
            int(bin_x),
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
        capacity = max(int(max_waves or pixel_count), 1)
        center_waves = (ctypes.c_float * capacity)()
        waves_count = ctypes.c_int(capacity)
        ok = self.lib.spec_init_spectral_splice(
            int(device_id),
            float(pixel_width),
            int(pixel_count),
            int(bin_x),
            float(from_nm),
            float(to_nm),
            float(ref_nm),
            int(edge),
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
        capacity = max(int(max_waves or pixel_count), 1)
        center_waves = (ctypes.c_float * capacity)()
        waves_count = ctypes.c_int(capacity)
        ok = self.lib.spec_init_spectral_splice2(
            int(device_id),
            float(pixel_width),
            int(pixel_count),
            int(bin_x),
            float(from_nm),
            float(to_nm),
            float(ref_nm),
            int(edge_left),
            int(edge_right),
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

        size1 = len(x1)
        size2 = len(x2)
        capacity = max(int(output_capacity or (size1 + size2)), 1)
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
        buffer = self._as_bytes_array(data)
        ok = self.lib.spec_set_user_data(int(device_id), int(offset), buffer, len(buffer))
        self._check(ok, "set_user_data", device_id)

    def get_user_data(self, device_id: int, offset: int, length: int) -> bytes:
        if length < 0:
            raise TLSC1ValidationError("length must be non-negative")
        buffer = (ctypes.c_ubyte * int(length))()
        ok = self.lib.spec_get_user_data(int(device_id), int(offset), buffer, int(length))
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
