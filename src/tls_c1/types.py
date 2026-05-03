from __future__ import annotations

import ctypes
from dataclasses import dataclass


class SpecInfo(ctypes.Structure):
    _fields_ = [
        ("manufacturer", ctypes.c_char * 9),
        ("model", ctypes.c_char * 24),
        ("sn", ctypes.c_char * 24),
        ("date", ctypes.c_char * 9),
        ("firmware_ver", ctypes.c_char * 9),
    ]


@dataclass(frozen=True)
class DeviceInfo:
    manufacturer: str
    model: str
    sn: str
    date: str
    firmware_ver: str

    @classmethod
    def from_spec_info(cls, info: SpecInfo) -> DeviceInfo:
        return cls(
            manufacturer=_decode_char_array(info.manufacturer),
            model=_decode_char_array(info.model),
            sn=_decode_char_array(info.sn),
            date=_decode_char_array(info.date),
            firmware_ver=_decode_char_array(info.firmware_ver),
        )

    def to_spec_info(self) -> SpecInfo:
        info = SpecInfo()
        _write_char_array(info.manufacturer, self.manufacturer)
        _write_char_array(info.model, self.model)
        _write_char_array(info.sn, self.sn)
        _write_char_array(info.date, self.date)
        _write_char_array(info.firmware_ver, self.firmware_ver)
        return info


@dataclass(frozen=True)
class DeviceStatus:
    connected: bool
    device_id: int | None
    mono: str
    port_type: str
    connection_target: str
    target_wavelength_nm: float | None
    current_wavelength_nm: float | None
    grating: int | None
    moving: bool
    last_error: str | None


def _decode_char_array(value: bytes) -> str:
    return value.split(b"\x00", 1)[0].decode("ascii", errors="ignore").strip()


def _write_char_array(field: ctypes.Array[ctypes.c_char], value: str) -> None:
    raw = value.encode("ascii", errors="strict")
    if len(raw) >= len(field):
        raise ValueError(f"value {value!r} is too long for fixed-size C field of {len(field)} bytes")
    field.value = raw
