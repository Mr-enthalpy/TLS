# SDK API safety classification

Authority: `third_party/vendor_sdk/TLS-SDK-32&64bit/SDK/inc/spectrometer.h`.

Last updated: 2026-05-04.

The labels below are exclusive per C function. They combine observed Omni300 behavior, SDK semantics, and the current testing policy. `do-not-test-automatically` wins over broader categories when an API can persistently alter configuration, calibration, EEPROM/user data, trigger behavior, home/zero settings, backup/restore state, or range motion.

## Summary

- `dangerous-manual`: `1`
- `do-not-test-automatically`: `54`
- `experimental-raw`: `4`
- `session-breaking-observed`: `37`
- `stable-motion`: `2`
- `stable-readonly`: `18`
- `stable-reversible`: `5`
- `unsupported-on-Omni300`: `5`

## Test Policy

- `session-breaking-observed`: quarantined manual-only APIs or API groups that have already been observed in a batch after which the device remained enumerable but could no longer be reopened without a power cycle.
- `stable-readonly`: allowed in `hardware_readonly` tests.
- `stable-reversible`: allowed only in `hardware_reversible` tests with read-before-write and `finally` restore.
- `stable-motion`: allowed only in explicit motion tests with safe wavelength/grating inputs.
- `unsupported-on-Omni300`: behavior may be recorded, but not promoted to stable high-level API.
- `experimental-raw`: low-level wrapper exists; behavior or model support is not stable enough for high-level promotion.
- `dangerous-manual`: manual review and recovery plan required.
- `do-not-test-automatically`: excluded from automated hardware tests even if the wrapper exists.

## Function Lists

### session-breaking-observed (37)

- `spec_get_zero_offset` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_get_zero_pos` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_get_adjustment` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_get_filter_status` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_get_filter` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_get_filter_model` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_get_filter_limit` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_get_side_exit_pos` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_side_entrance_pos` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_slit_width` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_get_slit_bandpass` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_get_slit_zero_pos` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_get_slit_model` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_get_motor_steps` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_motor_speed` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_motor_home_dir` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_motor_total_steps` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_shutter_status` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_is_setup_filter` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_is_setup_mirror` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_is_setup_slit` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_is_setup_shutter` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_get_correct_params` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_wave_to_step` - hardware behavior recorded: `yes`; test level: `quarantined-manual`
- `spec_pixels_to_waves` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_init_peripherals` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_peripherals_init_pos` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_trig_out_interval` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_trig_in_interval` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_ccd_mode` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_init_spectral_splice` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_init_spectral_splice2` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_spectral_splice` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_diaphragm` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_diaphragm_steps` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_focus_mirror` - hardware behavior recorded: `no`; test level: `quarantined-manual`
- `spec_get_focus_mirror_steps` - hardware behavior recorded: `no`; test level: `quarantined-manual`

### stable-readonly (18)

- `spec_get_dll_ver` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_enum_dev_count` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_enum_dev_sn` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_is_open` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_error` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_dev_info` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_total_steps` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_io_output` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_turret` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_max_wavelength` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_grating_info` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_init_grating` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_init_wave` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_grating_count` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_grating` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_curr_steps` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_curr_wave` - hardware behavior recorded: `yes`; test level: `hardware_readonly`
- `spec_get_move_speed` - hardware behavior recorded: `yes`; test level: `hardware_readonly`

### stable-reversible (5)

- `spec_set_usb_mode` - hardware behavior recorded: `yes`; test level: `hardware_reversible`
- `spec_open` - hardware behavior recorded: `yes`; test level: `hardware_reversible`
- `spec_close` - hardware behavior recorded: `yes`; test level: `hardware_reversible`
- `spec_set_timeout` - hardware behavior recorded: `yes`; test level: `hardware_reversible`
- `spec_set_filter_status` - hardware behavior recorded: `yes`; test level: `hardware_reversible`

### stable-motion (2)

- `spec_set_grating` - hardware behavior recorded: `yes`; test level: `hardware_motion`
- `spec_move_to_wave` - hardware behavior recorded: `yes`; test level: `hardware_motion`

### unsupported-on-Omni300 (5)

- `spec_get_dispersion` - hardware behavior recorded: `yes`; test level: `hardware_readonly-observed-error`
- `spec_get_exit_port` - hardware behavior recorded: `yes`; test level: `hardware_readonly-observed-error`
- `spec_get_entrance_port` - hardware behavior recorded: `yes`; test level: `hardware_readonly-observed-error`
- `spec_get_mirror_model` - hardware behavior recorded: `yes`; test level: `hardware_readonly-observed-error`
- `spec_get_enbaled_turret` - hardware behavior recorded: `yes`; test level: `hardware_readonly-observed-error`

### experimental-raw (4)

- `spec_set_io_output` - hardware behavior recorded: `no`; test level: `experimental/no-hardware`
- `spec_set_turret` - hardware behavior recorded: `no`; test level: `experimental/no-hardware`
- `spec_set_move_speed` - hardware behavior recorded: `no`; test level: `experimental/no-hardware`
- `spec_set_shutter_status` - hardware behavior recorded: `no`; test level: `experimental/no-hardware`

### dangerous-manual (1)

- `spec_set_ccd_mode` - hardware behavior recorded: `no`; test level: `manual-only`

### do-not-test-automatically (54)

- `spec_set_dev_info` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_backup` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_restore` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_total_steps` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_zero_offset` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_zero_pos` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_adjustment` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_adjusting` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_grating_info` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_init_grating` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_init_wave` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_dispersion` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_grating_home` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_move_wave` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_move_steps` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_move_to_steps` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_filter` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_filter_home` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_filter_model` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_filter_limit` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_exit_port` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_side_exit_pos` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_entrance_port` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_side_entrance_pos` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_mirror_model` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_slit_width` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_slit_bandpass` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_slit_zero_pos` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_slit_home` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_slit_model` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_motor_steps` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_motor_home` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_motor_speed` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_motor_home_dir` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_motor_total_steps` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_setup_filter` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_setup_mirror` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_setup_slit` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_setup_shutter` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_correct_params` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_init_peripherals` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_peripherals_init_pos` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_trig_out_interval` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_trig_mode` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_trig_in_interval` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_range_move` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_range_move2` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_turret_enbale` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_user_data` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_get_user_data` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_diaphragm` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_diaphragm_steps` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_focus_mirror` - hardware behavior recorded: `no`; test level: `manual-only`
- `spec_set_focus_mirror_steps` - hardware behavior recorded: `no`; test level: `manual-only`
