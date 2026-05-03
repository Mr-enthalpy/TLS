"""Python wrapper for the Zolix spectrometer SDK."""

from .api import SpectrometerAPI
from .device import TLSC1, tls_c1
from .errors import (
    TLSC1ConnectionError,
    TLSC1DeviceError,
    TLSC1DeviceNotFoundError,
    TLSC1Error,
    TLSC1LibraryLoadError,
    TLSC1MoveTimeoutError,
    TLSC1NotConnectedError,
    TLSC1StateError,
    TLSC1ValidationError,
)
from .types import DeviceInfo, DeviceStatus, SpecInfo

__all__ = [
    "tls_c1",
    "TLSC1",
    "SpectrometerAPI",
    "SpecInfo",
    "DeviceInfo",
    "DeviceStatus",
    "TLSC1Error",
    "TLSC1LibraryLoadError",
    "TLSC1DeviceError",
    "TLSC1ConnectionError",
    "TLSC1DeviceNotFoundError",
    "TLSC1ValidationError",
    "TLSC1StateError",
    "TLSC1NotConnectedError",
    "TLSC1MoveTimeoutError",
]
