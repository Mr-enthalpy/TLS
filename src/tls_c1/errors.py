class TLSC1Error(Exception):
    """Base package exception."""


class TLSC1LibraryLoadError(TLSC1Error):
    """Raised when the vendor DLL cannot be loaded."""


class TLSC1DeviceError(TLSC1Error):
    """Raised when the device or SDK reports an operation failure."""


class TLSC1ConnectionError(TLSC1DeviceError):
    """Raised when discovery or connection preconditions are not satisfied."""


class TLSC1DeviceNotFoundError(TLSC1ConnectionError):
    """Raised when the SDK loads but no matching device is visible."""


class TLSC1ValidationError(TLSC1Error, ValueError):
    """Raised when a user-facing parameter is invalid."""


class TLSC1StateError(TLSC1DeviceError, RuntimeError):
    """Raised when an operation requires a connected device or prepared state."""


class TLSC1NotConnectedError(TLSC1StateError):
    """Raised when a command requires an open device."""


class TLSC1MoveTimeoutError(TLSC1DeviceError, TimeoutError):
    """Raised when motion does not reach the requested position before timeout."""
