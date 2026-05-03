# SDK API coverage

Authority: `third_party/vendor_sdk/TLS-SDK-32&64bit/SDK/inc/spectrometer.h`.

Last verified: 2026-05-03.

## Summary

- Header prototypes: `126 spec_*` functions.
- `spectrometer_x64.dll` exports: `126`.
- `spectrometer_x86.dll` exports: `126`.
- Header vs registered signatures: missing `0`, extra `0`.
- Header vs x64 DLL exports: missing `0`, extra `0`.
- Header vs x86 DLL exports: missing `0`, extra `0`.
- `src/tls_c1/_native.py`: `126/126` ctypes signatures registered.
- `src/tls_c1/api.py`: `126/126` low-level wrappers exposed on `SpectrometerAPI`.
- Hardware behavior recorded SDK functions: `44/126`.

## High-Level Device API

`tls_c1` remains the narrow user-facing control class. It exposes:

- Connection/state: `connect`, `disconnect`, `renew`, `is_connected`, `device_id`.
- Motion: `set_grating`, `set_wavelength`, `get_target_wavelength`, `move`, `wait_until_idle`.
- Diagnostics: `get_wavelength`, `get_grating`, `device_info`, `last_error`, `is_moving`, `get_status`.
- Cleanup: `__del__`, context-manager `with tls_c1().connect(...) as spec`.

State rules:

- Construction does not load hardware motion or open a device.
- `connect` is required before hardware reads/writes.
- `set_wavelength` only stores the target; `move` is the explicit motion command.
- `move` is blocking and raises `TLSC1MoveTimeoutError` if the target is not reached before timeout.
- `is_moving` is derived from this object's pending motion target and `spec_get_curr_wave`; the SDK header does not expose a separate busy/idle function.

## Hardware Smoke Status

Last hardware smoke run: 2026-05-03 on Windows with `py -3.12` 64-bit.

- DLL version: `v24.5.0`
- Enumerated devices: `OM319069`
- Connected device id: `0`
- Device info: manufacturer `Zolix`, model `Omni300`, serial `19069`, firmware `V2.7`
- Movement: grating `1`, wavelength reached `546.0009765625` nm
- High-level diagnostics: `get_target_wavelength`, `is_moving`, and `get_status` passed
- Repeated connect/disconnect: passed

The 32-bit default `python` environment was also checked for DLL load, USB enumeration, connect, and disconnect using the packaged `win32` DLLs.

Hardware tests remain opt-in:

```powershell
$env:TLS_C1_RUN_HARDWARE_TESTS = "1"
$env:TLS_C1_SERIAL = "OM319069"
py -3.12 -m pytest tests\test_hardware_smoke.py -s
```

## API Coverage Matrix

| C function | Python wrapper | ctypes signature | Return semantics | Bound | Low-level wrapped | User-level exposed | Hardware verified | Notes |
|---|---|---|---|---|---|---|---|---|
| `spec_get_dll_ver` | `SpectrometerAPI.get_dll_ver` | `argtypes=(c_char_p, c_int); restype=None` | fills caller buffer; Python returns decoded string or None | yes | yes | no | yes | device discovery / connection |
| `spec_set_usb_mode` | `SpectrometerAPI.set_usb_mode` | `argtypes=(c_bool); restype=None` | void; Python returns None | yes | yes | tls_c1.connect | yes | device discovery / connection |
| `spec_enum_dev_count` | `SpectrometerAPI.enum_dev_count` | `argtypes=(); restype=c_int` | int visible device count | yes | yes | tls_c1.connect | yes | device discovery / connection |
| `spec_enum_dev_sn` | `SpectrometerAPI.enum_dev_sn` | `argtypes=(c_int, c_char_p, c_int); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | tls_c1.connect | yes | device discovery / connection |
| `spec_open` | `SpectrometerAPI.open` | `argtypes=(c_char_p); restype=c_int` | int device id; negative means open failed | yes | yes | tls_c1.connect | yes | device discovery / connection |
| `spec_close` | `SpectrometerAPI.close` | `argtypes=(c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | tls_c1.disconnect | yes | device discovery / connection |
| `spec_get_is_open` | `SpectrometerAPI.get_is_open` | `argtypes=(c_int); restype=c_bool` | bool state value returned directly | yes | yes | tls_c1.is_connected/connect/disconnect/get_status | yes | device discovery / connection |
| `spec_get_error` | `SpectrometerAPI.get_error` | `argtypes=(c_int, c_char_p, c_int); restype=None` | fills caller buffer; Python returns decoded string or None | yes | yes | tls_c1.last_error/get_status | yes | device discovery / connection |
| `spec_set_timeout` | `SpectrometerAPI.set_timeout` | `argtypes=(c_int, c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | tls_c1.move(timeout=...) | yes | device discovery / connection |
| `spec_set_dev_info` | `SpectrometerAPI.set_dev_info` | `argtypes=(c_int, SpecInfo); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | device metadata / serial / EEPROM; advanced/write API; hardware validation required before routine use |
| `spec_get_dev_info` | `SpectrometerAPI.get_dev_info` | `argtypes=(c_int, POINTER(SpecInfo)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | tls_c1.device_info/get_status | yes | device metadata / serial / EEPROM |
| `spec_backup` | `SpectrometerAPI.backup` | `argtypes=(c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | device metadata / serial / EEPROM; advanced/write API; hardware validation required before routine use |
| `spec_restore` | `SpectrometerAPI.restore` | `argtypes=(c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | device metadata / serial / EEPROM; advanced/write API; hardware validation required before routine use |
| `spec_set_total_steps` | `SpectrometerAPI.set_total_steps` | `argtypes=(c_int, c_long); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_total_steps` | `SpectrometerAPI.get_total_steps` | `argtypes=(c_int, POINTER(c_long)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | wavelength / grating / movement |
| `spec_set_io_output` | `SpectrometerAPI.set_io_output` | `argtypes=(c_int, c_short); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | low-level debug / escape APIs |
| `spec_get_io_output` | `SpectrometerAPI.get_io_output` | `argtypes=(c_int, POINTER(c_short)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | low-level debug / escape APIs |
| `spec_set_turret` | `SpectrometerAPI.set_turret` | `argtypes=(c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement |
| `spec_get_turret` | `SpectrometerAPI.get_turret` | `argtypes=(c_int, POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | wavelength / grating / movement |
| `spec_set_zero_offset` | `SpectrometerAPI.set_zero_offset` | `argtypes=(c_int, c_int, c_long); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_zero_offset` | `SpectrometerAPI.get_zero_offset` | `argtypes=(c_int, c_int, POINTER(c_long)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | wavelength / grating / movement |
| `spec_set_zero_pos` | `SpectrometerAPI.set_zero_pos` | `argtypes=(c_int, c_int, c_int, c_long); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_zero_pos` | `SpectrometerAPI.get_zero_pos` | `argtypes=(c_int, c_int, c_int, POINTER(c_long)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | wavelength / grating / movement |
| `spec_set_adjustment` | `SpectrometerAPI.set_adjustment` | `argtypes=(c_int, c_int, c_float); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_adjustment` | `SpectrometerAPI.get_adjustment` | `argtypes=(c_int, c_int, POINTER(c_float)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | wavelength / grating / movement |
| `spec_get_max_wavelength` | `SpectrometerAPI.get_max_wavelength` | `argtypes=(c_int, c_int, POINTER(c_float)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | wavelength / grating / movement |
| `spec_adjusting` | `SpectrometerAPI.adjusting` | `argtypes=(c_int, c_int, c_float, c_float, POINTER(c_float)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_set_grating_info` | `SpectrometerAPI.set_grating_info` | `argtypes=(c_int, c_int, c_int, c_long); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_grating_info` | `SpectrometerAPI.get_grating_info` | `argtypes=(c_int, c_int, POINTER(c_int), POINTER(c_long)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | wavelength / grating / movement |
| `spec_set_init_grating` | `SpectrometerAPI.set_init_grating` | `argtypes=(c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_init_grating` | `SpectrometerAPI.get_init_grating` | `argtypes=(c_int, POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | wavelength / grating / movement |
| `spec_set_init_wave` | `SpectrometerAPI.set_init_wave` | `argtypes=(c_int, c_int, c_float); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_init_wave` | `SpectrometerAPI.get_init_wave` | `argtypes=(c_int, c_int, POINTER(c_float)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | wavelength / grating / movement |
| `spec_set_dispersion` | `SpectrometerAPI.set_dispersion` | `argtypes=(c_int, c_float); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_dispersion` | `SpectrometerAPI.get_dispersion` | `argtypes=(c_int, POINTER(c_float)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | wavelength / grating / movement |
| `spec_set_grating_home` | `SpectrometerAPI.set_grating_home` | `argtypes=(c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_grating_count` | `SpectrometerAPI.get_grating_count` | `argtypes=(c_int, POINTER(c_short)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | wavelength / grating / movement |
| `spec_set_grating` | `SpectrometerAPI.set_grating` | `argtypes=(c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | tls_c1.set_grating | yes | wavelength / grating / movement |
| `spec_get_grating` | `SpectrometerAPI.get_grating` | `argtypes=(c_int, POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | tls_c1.get_grating/get_status | yes | wavelength / grating / movement |
| `spec_move_wave` | `SpectrometerAPI.move_wave` | `argtypes=(c_int, c_float); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement |
| `spec_move_to_wave` | `SpectrometerAPI.move_to_wave` | `argtypes=(c_int, c_float); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | tls_c1.move | yes | wavelength / grating / movement |
| `spec_get_curr_steps` | `SpectrometerAPI.get_curr_steps` | `argtypes=(c_int, POINTER(c_float)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | wavelength / grating / movement |
| `spec_move_steps` | `SpectrometerAPI.move_steps` | `argtypes=(c_int, c_float); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement |
| `spec_move_to_steps` | `SpectrometerAPI.move_to_steps` | `argtypes=(c_int, c_float); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement |
| `spec_get_curr_wave` | `SpectrometerAPI.get_curr_wave` | `argtypes=(c_int, POINTER(c_float)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | tls_c1.get_wavelength/is_moving/wait_until_idle/get_status | yes | wavelength / grating / movement |
| `spec_set_move_speed` | `SpectrometerAPI.set_move_speed` | `argtypes=(c_int, c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement |
| `spec_get_move_speed` | `SpectrometerAPI.get_move_speed` | `argtypes=(c_int, c_int, POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | wavelength / grating / movement |
| `spec_set_filter_status` | `SpectrometerAPI.set_filter_status` | `argtypes=(c_int, c_int, c_bool); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | yes | slit / shutter / filter wheel |
| `spec_get_filter_status` | `SpectrometerAPI.get_filter_status` | `argtypes=(c_int, c_int, POINTER(c_bool)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | slit / shutter / filter wheel |
| `spec_set_filter` | `SpectrometerAPI.set_filter` | `argtypes=(c_int, c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | slit / shutter / filter wheel |
| `spec_get_filter` | `SpectrometerAPI.get_filter` | `argtypes=(c_int, c_int, POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | slit / shutter / filter wheel |
| `spec_set_filter_home` | `SpectrometerAPI.set_filter_home` | `argtypes=(c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | slit / shutter / filter wheel; advanced/write API; hardware validation required before routine use |
| `spec_set_filter_model` | `SpectrometerAPI.set_filter_model` | `argtypes=(c_int, c_char_p); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | slit / shutter / filter wheel; advanced/write API; hardware validation required before routine use |
| `spec_get_filter_model` | `SpectrometerAPI.get_filter_model` | `argtypes=(c_int, c_char_p); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | slit / shutter / filter wheel |
| `spec_set_filter_limit` | `SpectrometerAPI.set_filter_limit` | `argtypes=(c_int, c_int, c_short, c_double); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | slit / shutter / filter wheel; advanced/write API; hardware validation required before routine use |
| `spec_get_filter_limit` | `SpectrometerAPI.get_filter_limit` | `argtypes=(c_int, c_int, c_short, POINTER(c_double)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | slit / shutter / filter wheel |
| `spec_set_exit_port` | `SpectrometerAPI.set_exit_port` | `argtypes=(c_int, c_bool); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | advanced configuration |
| `spec_get_exit_port` | `SpectrometerAPI.get_exit_port` | `argtypes=(c_int, POINTER(c_bool)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | advanced configuration |
| `spec_set_side_exit_pos` | `SpectrometerAPI.set_side_exit_pos` | `argtypes=(c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | low-level debug / escape APIs; advanced/write API; hardware validation required before routine use |
| `spec_get_side_exit_pos` | `SpectrometerAPI.get_side_exit_pos` | `argtypes=(c_int, POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | low-level debug / escape APIs |
| `spec_set_entrance_port` | `SpectrometerAPI.set_entrance_port` | `argtypes=(c_int, c_bool); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | advanced configuration |
| `spec_get_entrance_port` | `SpectrometerAPI.get_entrance_port` | `argtypes=(c_int, POINTER(c_bool)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | advanced configuration |
| `spec_set_side_entrance_pos` | `SpectrometerAPI.set_side_entrance_pos` | `argtypes=(c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | low-level debug / escape APIs; advanced/write API; hardware validation required before routine use |
| `spec_get_side_entrance_pos` | `SpectrometerAPI.get_side_entrance_pos` | `argtypes=(c_int, POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | low-level debug / escape APIs |
| `spec_get_mirror_model` | `SpectrometerAPI.get_mirror_model` | `argtypes=(c_int, c_char_p); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | advanced configuration |
| `spec_set_mirror_model` | `SpectrometerAPI.set_mirror_model` | `argtypes=(c_int, c_char_p); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | advanced configuration; advanced/write API; hardware validation required before routine use |
| `spec_set_slit_width` | `SpectrometerAPI.set_slit_width` | `argtypes=(c_int, c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | slit / shutter / filter wheel |
| `spec_get_slit_width` | `SpectrometerAPI.get_slit_width` | `argtypes=(c_int, c_int, POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | slit / shutter / filter wheel |
| `spec_set_slit_bandpass` | `SpectrometerAPI.set_slit_bandpass` | `argtypes=(c_int, c_int, c_float); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | slit / shutter / filter wheel |
| `spec_get_slit_bandpass` | `SpectrometerAPI.get_slit_bandpass` | `argtypes=(c_int, c_int, POINTER(c_float)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | slit / shutter / filter wheel |
| `spec_set_slit_zero_pos` | `SpectrometerAPI.set_slit_zero_pos` | `argtypes=(c_int, c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_slit_zero_pos` | `SpectrometerAPI.get_slit_zero_pos` | `argtypes=(c_int, c_int, POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | wavelength / grating / movement |
| `spec_set_slit_home` | `SpectrometerAPI.set_slit_home` | `argtypes=(c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | slit / shutter / filter wheel; advanced/write API; hardware validation required before routine use |
| `spec_set_slit_model` | `SpectrometerAPI.set_slit_model` | `argtypes=(c_int, c_char, c_char_p); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | slit / shutter / filter wheel; advanced/write API; hardware validation required before routine use |
| `spec_get_slit_model` | `SpectrometerAPI.get_slit_model` | `argtypes=(c_int, c_char, c_char_p); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | slit / shutter / filter wheel |
| `spec_set_motor_steps` | `SpectrometerAPI.set_motor_steps` | `argtypes=(c_int, c_int, c_long); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_motor_steps` | `SpectrometerAPI.get_motor_steps` | `argtypes=(c_int, c_int, POINTER(c_long)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | wavelength / grating / movement |
| `spec_set_motor_home` | `SpectrometerAPI.set_motor_home` | `argtypes=(c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | low-level debug / escape APIs; advanced/write API; hardware validation required before routine use |
| `spec_set_motor_speed` | `SpectrometerAPI.set_motor_speed` | `argtypes=(c_int, c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | low-level debug / escape APIs; advanced/write API; hardware validation required before routine use |
| `spec_get_motor_speed` | `SpectrometerAPI.get_motor_speed` | `argtypes=(c_int, c_int, POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | low-level debug / escape APIs |
| `spec_set_motor_home_dir` | `SpectrometerAPI.set_motor_home_dir` | `argtypes=(c_int, c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | low-level debug / escape APIs; advanced/write API; hardware validation required before routine use |
| `spec_get_motor_home_dir` | `SpectrometerAPI.get_motor_home_dir` | `argtypes=(c_int, c_int, POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | low-level debug / escape APIs |
| `spec_set_motor_total_steps` | `SpectrometerAPI.set_motor_total_steps` | `argtypes=(c_int, c_int, c_long); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_motor_total_steps` | `SpectrometerAPI.get_motor_total_steps` | `argtypes=(c_int, c_int, POINTER(c_long)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | wavelength / grating / movement |
| `spec_set_shutter_status` | `SpectrometerAPI.set_shutter_status` | `argtypes=(c_int, c_int, c_bool); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | slit / shutter / filter wheel |
| `spec_get_shutter_status` | `SpectrometerAPI.get_shutter_status` | `argtypes=(c_int, c_int, POINTER(c_bool)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | slit / shutter / filter wheel |
| `spec_is_setup_filter` | `SpectrometerAPI.is_setup_filter` | `argtypes=(c_int, c_int, POINTER(c_bool)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | slit / shutter / filter wheel |
| `spec_setup_filter` | `SpectrometerAPI.setup_filter` | `argtypes=(c_int, c_int, c_bool); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | slit / shutter / filter wheel |
| `spec_is_setup_mirror` | `SpectrometerAPI.is_setup_mirror` | `argtypes=(c_int, c_int, POINTER(c_bool)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | advanced configuration |
| `spec_setup_mirror` | `SpectrometerAPI.setup_mirror` | `argtypes=(c_int, c_int, c_bool); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | advanced configuration |
| `spec_is_setup_slit` | `SpectrometerAPI.is_setup_slit` | `argtypes=(c_int, c_int, POINTER(c_bool)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | slit / shutter / filter wheel |
| `spec_setup_slit` | `SpectrometerAPI.setup_slit` | `argtypes=(c_int, c_int, c_bool); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | slit / shutter / filter wheel |
| `spec_is_setup_shutter` | `SpectrometerAPI.is_setup_shutter` | `argtypes=(c_int, c_int, POINTER(c_bool)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | slit / shutter / filter wheel |
| `spec_setup_shutter` | `SpectrometerAPI.setup_shutter` | `argtypes=(c_int, c_int, c_bool); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | slit / shutter / filter wheel |
| `spec_set_correct_params` | `SpectrometerAPI.set_correct_params` | `argtypes=(c_int, c_int, c_int, c_int, c_void_p); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | calibration / correction; advanced/write API; hardware validation required before routine use; void* remains intentionally low-level |
| `spec_get_correct_params` | `SpectrometerAPI.get_correct_params` | `argtypes=(c_int, c_int, c_int, c_int, c_void_p); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | calibration / correction; void* remains intentionally low-level |
| `spec_wave_to_step` | `SpectrometerAPI.wave_to_step` | `argtypes=(c_int, c_float); restype=c_float` | float conversion result | yes | yes | no | yes | wavelength / grating / movement |
| `spec_pixels_to_waves` | `SpectrometerAPI.pixels_to_waves` | `argtypes=(c_int, c_int, c_int, c_float, c_float, c_int, c_int, POINTER(c_float)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | wavelength / grating / movement |
| `spec_set_init_peripherals` | `SpectrometerAPI.set_init_peripherals` | `argtypes=(c_int, c_ushort); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | advanced configuration; advanced/write API; hardware validation required before routine use |
| `spec_get_init_peripherals` | `SpectrometerAPI.get_init_peripherals` | `argtypes=(c_int, POINTER(c_ushort)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | advanced configuration |
| `spec_set_peripherals_init_pos` | `SpectrometerAPI.set_peripherals_init_pos` | `argtypes=(c_int, c_ushort, c_ubyte); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | advanced configuration; advanced/write API; hardware validation required before routine use |
| `spec_get_peripherals_init_pos` | `SpectrometerAPI.get_peripherals_init_pos` | `argtypes=(c_int, c_ushort, POINTER(c_ubyte)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | advanced configuration |
| `spec_set_trig_out_interval` | `SpectrometerAPI.set_trig_out_interval` | `argtypes=(c_int, c_ushort); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | advanced configuration |
| `spec_get_trig_out_interval` | `SpectrometerAPI.get_trig_out_interval` | `argtypes=(c_int, POINTER(c_ushort)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | advanced configuration |
| `spec_set_trig_mode` | `SpectrometerAPI.set_trig_mode` | `argtypes=(c_int, c_bool); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | advanced configuration |
| `spec_set_trig_in_interval` | `SpectrometerAPI.set_trig_in_interval` | `argtypes=(c_int, c_float); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | advanced configuration |
| `spec_get_trig_in_interval` | `SpectrometerAPI.get_trig_in_interval` | `argtypes=(c_int, POINTER(c_float)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | advanced configuration |
| `spec_range_move` | `SpectrometerAPI.range_move` | `argtypes=(c_int, c_float, c_float, c_float, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | low-level debug / escape APIs; advanced/write API; hardware validation required before routine use |
| `spec_range_move2` | `SpectrometerAPI.range_move2` | `argtypes=(c_int, c_float, c_float, c_float, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | low-level debug / escape APIs; advanced/write API; hardware validation required before routine use |
| `spec_set_turret_enbale` | `SpectrometerAPI.set_turret_enbale / set_turret_enable` | `argtypes=(c_int, c_short); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use; ABI spelling is vendor typo; alias set_turret_enable exists |
| `spec_get_enbaled_turret` | `SpectrometerAPI.get_enbaled_turret / get_enabled_turret` | `argtypes=(c_int, POINTER(c_short)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | yes | wavelength / grating / movement; ABI spelling is vendor typo; alias get_enabled_turret exists |
| `spec_set_ccd_mode` | `SpectrometerAPI.set_ccd_mode` | `argtypes=(c_int, c_bool); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | advanced configuration; advanced/write API; hardware validation required before routine use |
| `spec_get_ccd_mode` | `SpectrometerAPI.get_ccd_mode` | `argtypes=(c_int); restype=c_bool` | bool state value returned directly | yes | yes | no | no | advanced configuration; header returns bool directly, not bool success with output pointer |
| `spec_init_spectral_splice` | `SpectrometerAPI.init_spectral_splice` | `argtypes=(c_int, c_float, c_int, c_int, c_float, c_float, c_float, c_int, c_float, POINTER(c_float), POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | calibration / correction |
| `spec_init_spectral_splice2` | `SpectrometerAPI.init_spectral_splice2` | `argtypes=(c_int, c_float, c_int, c_int, c_float, c_float, c_float, c_int, c_int, c_float, POINTER(c_float), POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | calibration / correction |
| `spec_spectral_splice` | `SpectrometerAPI.spectral_splice` | `argtypes=(c_int, POINTER(c_float), POINTER(c_float), c_int, POINTER(c_float), POINTER(c_float), c_int, POINTER(c_float), POINTER(c_float), POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | calibration / correction |
| `spec_set_user_data` | `SpectrometerAPI.set_user_data` | `argtypes=(c_int, c_short, POINTER(c_ubyte), c_short); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | device metadata / serial / EEPROM; advanced/write API; hardware validation required before routine use |
| `spec_get_user_data` | `SpectrometerAPI.get_user_data` | `argtypes=(c_int, c_short, POINTER(c_ubyte), c_short); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | device metadata / serial / EEPROM |
| `spec_set_diaphragm` | `SpectrometerAPI.set_diaphragm` | `argtypes=(c_int, c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | advanced configuration |
| `spec_get_diaphragm` | `SpectrometerAPI.get_diaphragm` | `argtypes=(c_int, c_int, POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | advanced configuration |
| `spec_set_diaphragm_steps` | `SpectrometerAPI.set_diaphragm_steps` | `argtypes=(c_int, c_int, c_int, c_long); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_diaphragm_steps` | `SpectrometerAPI.get_diaphragm_steps` | `argtypes=(c_int, c_int, c_int, POINTER(c_long)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | wavelength / grating / movement |
| `spec_set_focus_mirror` | `SpectrometerAPI.set_focus_mirror` | `argtypes=(c_int, c_int); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | advanced configuration |
| `spec_get_focus_mirror` | `SpectrometerAPI.get_focus_mirror` | `argtypes=(c_int, POINTER(c_int)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | advanced configuration |
| `spec_set_focus_mirror_steps` | `SpectrometerAPI.set_focus_mirror_steps` | `argtypes=(c_int, c_int, c_long); restype=c_bool` | bool success; Python returns None and raises on false | yes | yes | no | no | wavelength / grating / movement; advanced/write API; hardware validation required before routine use |
| `spec_get_focus_mirror_steps` | `SpectrometerAPI.get_focus_mirror_steps` | `argtypes=(c_int, c_int, POINTER(c_long)); restype=c_bool` | bool success with output pointer; Python returns decoded value and raises on false | yes | yes | no | no | wavelength / grating / movement |

## Known Stale Vendor-Doc Entries

These names are mentioned in vendor Python/doc material but are not present in the authoritative header or DLL exports:

- `spec_set_slit_factor`
- `spec_get_slit_factor`
- `spec_get_cur_steps` (actual ABI name: `spec_get_curr_steps`)

## Remaining Risk

- The ctypes layer is structurally covered, but many advanced write/calibration APIs are not hardware-validated.
- User-level `tls_c1` intentionally exposes only the stable core workflow and diagnostics.
- Full behavioral validation should continue by function group before any pip packaging work.
- Detailed low-risk hardware behavior notes live in `docs/hardware_behavior.md`.
