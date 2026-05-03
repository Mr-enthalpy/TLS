# SDK audit notes

Input snapshot in this repository:

- vendor SDK root: [`./ third_party/vendor_sdk/TLS-SDK-32&64bit`](</C:/Users/hanni/PycharmProjects/TLS/ third_party/vendor_sdk/TLS-SDK-32&64bit>)
- authoritative header: [`SDK/inc/spectrometer.h`](</C:/Users/hanni/PycharmProjects/TLS/ third_party/vendor_sdk/TLS-SDK-32&64bit/SDK/inc/spectrometer.h>)

Note: the checked-in directory name in this workspace currently has a leading space (`./ third_party/...`). Runtime package code does not depend on that path, but local audit scripts need to account for it.

## Relevant contents

- `SDK/inc/spectrometer.h`: authoritative C ABI and macro constants.
- `SDK/x64/spectrometer_x64.dll`, `SDK/x64/ftd2xx.dll`: 64-bit runtime binaries.
- `SDK/x86/spectrometer_x86.dll`, `SDK/x86/ftd2xx.dll`: 32-bit runtime binaries.
- `Spectrometer SDK info_ch.docx`, `Spectrometer SDK info_en.docx`: semantic documentation.
- `Demo/vs2015`: practical usage patterns only.
- `Demo/python/devices_spectrometer.py`: hints only; not ABI authority.

## Verified consistency

Verified on 2026-05-01 with local export parsing against both packaged DLLs in `src/tls_c1/vendor/`:

- `spectrometer.h`: `126 spec_*` prototypes.
- `spectrometer_x64.dll`: `126 spec_*` exports.
- `spectrometer_x86.dll`: `126 spec_*` exports.
- Header vs x64 diff: none.
- Header vs x86 diff: none.

The export check is now scriptable from Python through `tls_c1._native.read_exported_symbol_names()`.

## Vendor demo issues

- Hard-coded DLL path tied to a developer machine.
- Incomplete and partially wrong `ctypes` prototypes.
- `spec_get_error` in the demo omits the `len` argument required by the header.
- `spec_get_dev_info` handling is broken; `ctypes.Structure` does not expose `.value`.
- Demo/doc material references `spec_get_cur_steps`; actual ABI name is `spec_get_curr_steps`.
- Demo/doc material references `spec_set_slit_factor` / `spec_get_slit_factor`; these are absent from the header and both DLLs.
- Several valid header exports were omitted or stubbed in the demo, including USB mode, trigger, mirror-model, turret-enable, and spectral-splice APIs.

## Binding policy used in this package

- `spectrometer.h` wins over the vendor Python demo.
- `_native.py` binds exact ABI spellings, including:
  - `spec_set_turret_enbale`
  - `spec_get_enbaled_turret`
- `api.py` exposes low-level wrappers for every header function.
- `device.py` keeps hardware motion explicit: `connect()` does not move hardware; `move()` performs the wavelength move.
- In USB mode, `device.py` now preflights device visibility through SDK enumeration and raises an explicit FTDI/connection diagnostic when no device is visible.
- DLL loading is lazy and architecture-aware; no import-time DLL load occurs.

## Remaining validation work

Structural coverage is complete. Remaining work is hardware validation of advanced write/calibration APIs:

- restore/backup and device-info writes
- EEPROM/user-data writes
- correction-parameter writes
- motor/slit/grating home or calibration operations
- spectral-splice behavior on real acquisition data
