# tls-c1-spectrometer

Python wrapper for the Zolix/Omni spectrometer SDK used by the TLS-C1 hardware setup.

The project has moved past the initial handoff stage. The current internal branch contains a complete ctypes ABI table for the vendor SDK, a low-level Python wrapper for all SDK functions, a narrow high-level `tls_c1` control class, hardware smoke tests, low-risk behavior tests, and a generated-public-branch workflow.

This is not a public pip release yet.

## Current Status

- Platform: Windows. The vendor SDK ships Windows DLLs and depends on FTDI D2XX.
- Python package name: `tls_c1`; distribution name in `pyproject.toml`: `tls-c1-spectrometer`.
- Version in `pyproject.toml`: `0.0.0`; keep it pre-release until packaging and licensing are settled.
- Native binding: `126/126` `spec_*` functions registered from the vendor ABI.
- Low-level API: `126/126` functions exposed on `SpectrometerAPI`.
- High-level API: stable core workflow and diagnostics only.
- Hardware behavior recorded in this branch: `47/126` SDK functions.
- SDK API safety classification is tracked in `docs/api_safety.md` and mirrored in `docs/api_coverage.md`.
- Public branch model: `public` is generated from internal `main` by `.public-include` and `scripts/sync-public.sh`; do not edit `public` manually.

## Windows And FTDI Setup

Install the vendor USB/FTDI driver before opening the spectrometer over USB.

Architecture must match:

- 64-bit Python requires `spectrometer_x64.dll` and matching `ftd2xx.dll`.
- 32-bit Python requires `spectrometer_x86.dll` and matching `ftd2xx.dll`.
- The wrapper does not fall back between x86 and x64 DLLs.

## DLL Placement

Preferred local setup is to point `TLS_C1_SDK_DIR` at the vendor SDK DLL directory:

```powershell
$env:TLS_C1_SDK_DIR = "C:\path\to\TLS-SDK-32&64bit\SDK\x64"
```

Internal development may also place DLLs here:

```text
src/tls_c1/vendor/win_amd64/
  spectrometer_x64.dll
  ftd2xx.dll

src/tls_c1/vendor/win32/
  spectrometer_x86.dll
  ftd2xx.dll
```

The generated public branch is allowlist-based and keeps only `src/tls_c1/vendor/README.md` plus `.gitkeep` files. Vendor DLLs, LIB files, archives, and the unpacked SDK must not be published unless redistribution rights are explicitly approved.

Internal builds may bundle vendor DLLs inside the private wheel. Public/code-only builds must not bundle those DLLs and instead rely on `TLS_C1_SDK_DIR` or a local SDK installation.

## Minimal Use

```python
from tls_c1 import tls_c1

with tls_c1().connect(Mono="Omni", port_type="USB", serial_number="OM319069") as spec:
    spec.set_grating(1)
    spec.set_wavelength("546 nm")
    spec.move(timeout=60)
    print(spec.get_status())
```

`set_wavelength` accepts `int`, `float`, and simple strings such as `"546"`, `"546nm"`, and `"546.0 nm"`. It only stores the target wavelength. `move()` is the explicit hardware motion command.

## Public API

High-level class:

- `tls_c1`
- `TLSC1` alias

Core high-level methods:

- `connect(Mono="Omni", port_type="USB", serial_number="OM319069")`
- `disconnect()`
- `renew()`
- `set_grating(num)`
- `set_wavelength(wavelength)`
- `move(timeout=60)`
- `get_wavelength()`
- `get_target_wavelength()`
- `get_grating()`
- `wait_until_idle(timeout=..., poll_interval=..., tolerance_nm=...)`
- `device_info()`
- `get_status()`
- `last_error()`
- `is_connected`
- `device_id`

Low-level SDK-oriented API:

- `SpectrometerAPI`

Do not expect every SDK function to be promoted to `tls_c1`. Broad SDK coverage belongs in `SpectrometerAPI`; the high-level class stays narrow and hardware-verified.

## Exceptions

Package exceptions are exported from `tls_c1`:

- `TLSC1Error`
- `TLSC1LibraryLoadError`
- `TLSC1DeviceError`
- `TLSC1ConnectionError`
- `TLSC1DeviceNotFoundError`
- `TLSC1ValidationError`
- `TLSC1StateError`
- `TLSC1NotConnectedError`
- `TLSC1MoveTimeoutError`

## Development Setup

Use an editable install for normal development:

```powershell
py -3.12 -m pip install -e .[dev]
py -3.12 -m pytest
```

If the package is not installed, run tests with `PYTHONPATH=src`:

```powershell
$env:PYTHONPATH = "src"
py -3.12 -m pytest
```

Default tests do not require hardware or vendor DLLs.

## Hardware Tests

Hardware tests are skipped by default. They use a file lock keyed by `TLS_C1_SERIAL` or `TLS_C1_PORT` so concurrent pytest workers do not open the same device at the same time.

Common settings:

```powershell
$env:TLS_C1_RUN_HARDWARE_TESTS = "1"
$env:TLS_C1_RUN_MOTION_TESTS = "1"
$env:TLS_C1_SERIAL = "OM319069"
$env:TLS_C1_SAFE_GRATING = "1"
$env:TLS_C1_SAFE_WAVELENGTH_NM = "546"
```

Smoke test. This opens the device and moves to the configured safe wavelength:

```powershell
py -3.12 -m pytest tests\test_hardware_smoke.py -s
```

Read-only behavior tests:

```powershell
py -3.12 -m pytest tests\test_hardware_read_only.py -s
```

Reversible behavior tests require a second opt-in and must restore original state:

```powershell
$env:TLS_C1_RUN_REVERSIBLE_TESTS = "1"
py -3.12 -m pytest tests\test_hardware_reversible.py -s
```

Motion tests require their own opt-in because they move mechanical axes:

```powershell
$env:TLS_C1_RUN_MOTION_TESTS = "1"
py -3.12 -m pytest -m hardware_motion -s
```

Manual/dangerous tests require separate opt-ins:

```powershell
$env:TLS_C1_RUN_MANUAL_TESTS = "1"
py -3.12 -m pytest -m hardware_manual -s
```

Destructive tests require a double opt-in:

```powershell
$env:TLS_C1_RUN_MANUAL_TESTS = "1"
$env:TLS_C1_RUN_DESTRUCTIVE_TESTS = "1"
py -3.12 -m pytest -m hardware_destructive -s
```

Do not add automatic tests for `restore`, `backup`, EEPROM/user data, calibration writes, correction-param writes, home/zero routines, range scans, trigger writes, or persistent setup flags.

The 2026-05-04 extended read-only session added behavior for `spec_get_zero_offset`, `spec_get_zero_pos`, and `spec_get_adjustment`, then the device remained enumerable but could not be reopened until the USB/FTDI session is reset. The broader extended read-only suite is present but not counted as verified until it passes end-to-end on a reset device.

## Documentation

- `docs/api_coverage.md`: generated coverage matrix and high-level API summary.
- `docs/api_safety.md`: generated SDK safety classification and automated-test policy.
- `docs/sdk_audit.md`: SDK audit findings.
- `docs/public-release.md`: generated public branch workflow.

Internal source tree only:

- `docs/hardware_behavior.md`: internal hardware behavior notes and observed SDK return behavior. This file is not currently part of the public allowlist.

Update docs when behavior changes. Do not claim additional hardware coverage until the corresponding hardware test or behavior note is committed.

## Generated Public Branch

The public branch is a generated view, not an editing branch:

```bash
scripts/sync-public.sh
```

The script:

- requires a clean internal worktree;
- reads `.public-include` as an allowlist;
- creates or updates an orphan `public` branch in a Git worktree;
- copies only approved public files;
- commits only when the public subset changes.

Publish explicitly to a public remote:

```bash
git push public-release public:main
```

Use `private` for the complete internal repository:

```bash
git push private main internal
```

Use `public-release` only for the generated public branch. Never push `main`,
`internal`, or `--all` to `public-release`, and never merge or rebase `main` /
`internal` into `public`; that would connect histories and could expose
private/vendor files through Git history.

## Licensing Boundary

This repository wraps a proprietary vendor SDK. The Python wrapper license does not grant rights to redistribute:

- `spectrometer_x64.dll`
- `spectrometer_x86.dll`
- `ftd2xx.dll`
- vendor `.lib` files
- vendor SDK archives
- unpacked vendor SDK documentation, demos, drivers, or headers

If rights are unclear, distribute code-only and require users to provide `TLS_C1_SDK_DIR`.
