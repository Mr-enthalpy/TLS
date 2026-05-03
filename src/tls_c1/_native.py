"""Native ctypes bindings for the Zolix spectrometer SDK."""

from __future__ import annotations

import ctypes
import os
import struct
from dataclasses import dataclass
from pathlib import Path

from .errors import TLSC1LibraryLoadError
from .types import SpecInfo


@dataclass(frozen=True)
class FunctionSpec:
    argtypes: tuple[object, ...]
    restype: object | None


FUNCTION_SPECS: dict[str, FunctionSpec] = {
    "spec_get_dll_ver": FunctionSpec(argtypes=(ctypes.c_char_p, ctypes.c_int), restype=None),
    "spec_set_usb_mode": FunctionSpec(argtypes=(ctypes.c_bool,), restype=None),
    "spec_enum_dev_count": FunctionSpec(argtypes=(), restype=ctypes.c_int),
    "spec_enum_dev_sn": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_char_p, ctypes.c_int), restype=ctypes.c_bool),
    "spec_open": FunctionSpec(argtypes=(ctypes.c_char_p,), restype=ctypes.c_int),
    "spec_close": FunctionSpec(argtypes=(ctypes.c_int,), restype=ctypes.c_bool),
    "spec_get_is_open": FunctionSpec(argtypes=(ctypes.c_int,), restype=ctypes.c_bool),
    "spec_get_error": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_char_p, ctypes.c_int), restype=None),
    "spec_set_timeout": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_set_dev_info": FunctionSpec(argtypes=(ctypes.c_int, SpecInfo), restype=ctypes.c_bool),
    "spec_get_dev_info": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(SpecInfo)), restype=ctypes.c_bool),
    "spec_backup": FunctionSpec(argtypes=(ctypes.c_int,), restype=ctypes.c_bool),
    "spec_restore": FunctionSpec(argtypes=(ctypes.c_int,), restype=ctypes.c_bool),
    "spec_set_total_steps": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_long), restype=ctypes.c_bool),
    "spec_get_total_steps": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_long)), restype=ctypes.c_bool),
    "spec_set_io_output": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_short), restype=ctypes.c_bool),
    "spec_get_io_output": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_short)), restype=ctypes.c_bool),
    "spec_set_turret": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_get_turret": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_set_zero_offset": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_long), restype=ctypes.c_bool),
    "spec_get_zero_offset": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_long)), restype=ctypes.c_bool),
    "spec_set_zero_pos": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long), restype=ctypes.c_bool),
    "spec_get_zero_pos": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_long)), restype=ctypes.c_bool),
    "spec_set_adjustment": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_float), restype=ctypes.c_bool),
    "spec_get_adjustment": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_float)), restype=ctypes.c_bool),
    "spec_get_max_wavelength": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_float)), restype=ctypes.c_bool),
    "spec_adjusting": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)), restype=ctypes.c_bool),
    "spec_set_grating_info": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long), restype=ctypes.c_bool),
    "spec_get_grating_info": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_long)), restype=ctypes.c_bool),
    "spec_set_init_grating": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_get_init_grating": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_set_init_wave": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_float), restype=ctypes.c_bool),
    "spec_get_init_wave": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_float)), restype=ctypes.c_bool),
    "spec_set_dispersion": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_float), restype=ctypes.c_bool),
    "spec_get_dispersion": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_float)), restype=ctypes.c_bool),
    "spec_set_grating_home": FunctionSpec(argtypes=(ctypes.c_int,), restype=ctypes.c_bool),
    "spec_get_grating_count": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_short)), restype=ctypes.c_bool),
    "spec_set_grating": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_get_grating": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_move_wave": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_float), restype=ctypes.c_bool),
    "spec_move_to_wave": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_float), restype=ctypes.c_bool),
    "spec_get_curr_steps": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_float)), restype=ctypes.c_bool),
    "spec_move_steps": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_float), restype=ctypes.c_bool),
    "spec_move_to_steps": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_float), restype=ctypes.c_bool),
    "spec_get_curr_wave": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_float)), restype=ctypes.c_bool),
    "spec_set_move_speed": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_get_move_speed": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_set_filter_status": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_bool), restype=ctypes.c_bool),
    "spec_get_filter_status": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_bool)), restype=ctypes.c_bool),
    "spec_set_filter": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_get_filter": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_set_filter_home": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_set_filter_model": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_char_p), restype=ctypes.c_bool),
    "spec_get_filter_model": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_char_p), restype=ctypes.c_bool),
    "spec_set_filter_limit": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_short, ctypes.c_double), restype=ctypes.c_bool),
    "spec_get_filter_limit": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_short, ctypes.POINTER(ctypes.c_double)), restype=ctypes.c_bool),
    "spec_set_exit_port": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_bool), restype=ctypes.c_bool),
    "spec_get_exit_port": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_bool)), restype=ctypes.c_bool),
    "spec_set_side_exit_pos": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_get_side_exit_pos": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_set_entrance_port": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_bool), restype=ctypes.c_bool),
    "spec_get_entrance_port": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_bool)), restype=ctypes.c_bool),
    "spec_set_side_entrance_pos": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_get_side_entrance_pos": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_get_mirror_model": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_char_p), restype=ctypes.c_bool),
    "spec_set_mirror_model": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_char_p), restype=ctypes.c_bool),
    "spec_set_slit_width": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_get_slit_width": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_set_slit_bandpass": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_float), restype=ctypes.c_bool),
    "spec_get_slit_bandpass": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_float)), restype=ctypes.c_bool),
    "spec_set_slit_zero_pos": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_get_slit_zero_pos": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_set_slit_home": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_set_slit_model": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_char, ctypes.c_char_p), restype=ctypes.c_bool),
    "spec_get_slit_model": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_char, ctypes.c_char_p), restype=ctypes.c_bool),
    "spec_set_motor_steps": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_long), restype=ctypes.c_bool),
    "spec_get_motor_steps": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_long)), restype=ctypes.c_bool),
    "spec_set_motor_home": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_set_motor_speed": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_get_motor_speed": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_set_motor_home_dir": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_get_motor_home_dir": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_set_motor_total_steps": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_long), restype=ctypes.c_bool),
    "spec_get_motor_total_steps": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_long)), restype=ctypes.c_bool),
    "spec_set_shutter_status": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_bool), restype=ctypes.c_bool),
    "spec_get_shutter_status": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_bool)), restype=ctypes.c_bool),
    "spec_is_setup_filter": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_bool)), restype=ctypes.c_bool),
    "spec_setup_filter": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_bool), restype=ctypes.c_bool),
    "spec_is_setup_mirror": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_bool)), restype=ctypes.c_bool),
    "spec_setup_mirror": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_bool), restype=ctypes.c_bool),
    "spec_is_setup_slit": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_bool)), restype=ctypes.c_bool),
    "spec_setup_slit": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_bool), restype=ctypes.c_bool),
    "spec_is_setup_shutter": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_bool)), restype=ctypes.c_bool),
    "spec_setup_shutter": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_bool), restype=ctypes.c_bool),
    "spec_set_correct_params": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p), restype=ctypes.c_bool),
    "spec_get_correct_params": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p), restype=ctypes.c_bool),
    "spec_wave_to_step": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_float), restype=ctypes.c_float),
    "spec_pixels_to_waves": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_float, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_float)), restype=ctypes.c_bool),
    "spec_set_init_peripherals": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_ushort), restype=ctypes.c_bool),
    "spec_get_init_peripherals": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_ushort)), restype=ctypes.c_bool),
    "spec_set_peripherals_init_pos": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_ushort, ctypes.c_ubyte), restype=ctypes.c_bool),
    "spec_get_peripherals_init_pos": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_ushort, ctypes.POINTER(ctypes.c_ubyte)), restype=ctypes.c_bool),
    "spec_set_trig_out_interval": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_ushort), restype=ctypes.c_bool),
    "spec_get_trig_out_interval": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_ushort)), restype=ctypes.c_bool),
    "spec_set_trig_mode": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_bool), restype=ctypes.c_bool),
    "spec_set_trig_in_interval": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_float), restype=ctypes.c_bool),
    "spec_get_trig_in_interval": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_float)), restype=ctypes.c_bool),
    "spec_range_move": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_int), restype=ctypes.c_bool),
    "spec_range_move2": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_int), restype=ctypes.c_bool),
    "spec_set_turret_enbale": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_short), restype=ctypes.c_bool),
    "spec_get_enbaled_turret": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_short)), restype=ctypes.c_bool),
    "spec_set_ccd_mode": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_bool), restype=ctypes.c_bool),
    "spec_get_ccd_mode": FunctionSpec(argtypes=(ctypes.c_int,), restype=ctypes.c_bool),
    "spec_init_spectral_splice": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_float, ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_int, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_init_spectral_splice2": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_float, ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_spectral_splice": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_set_user_data": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_short, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_short), restype=ctypes.c_bool),
    "spec_get_user_data": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_short, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_short), restype=ctypes.c_bool),
    "spec_set_diaphragm": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_get_diaphragm": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_set_diaphragm_steps": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long), restype=ctypes.c_bool),
    "spec_get_diaphragm_steps": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_long)), restype=ctypes.c_bool),
    "spec_set_focus_mirror": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int), restype=ctypes.c_bool),
    "spec_get_focus_mirror": FunctionSpec(argtypes=(ctypes.c_int, ctypes.POINTER(ctypes.c_int)), restype=ctypes.c_bool),
    "spec_set_focus_mirror_steps": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.c_long), restype=ctypes.c_bool),
    "spec_get_focus_mirror_steps": FunctionSpec(argtypes=(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_long)), restype=ctypes.c_bool),
}

STRING_BUFFER_SIZE = 256
EXPORTED_FUNCTIONS = tuple(FUNCTION_SPECS)
_DLL_DIRECTORY_HANDLES: list[object] = []


def _vendor_arch_dir() -> str:
    if ctypes.sizeof(ctypes.c_void_p) == 8:
        return "win_amd64"
    if ctypes.sizeof(ctypes.c_void_p) == 4:
        return "win32"
    raise TLSC1LibraryLoadError("Unsupported Python pointer size")


def _dll_name() -> str:
    return "spectrometer_x64.dll" if _vendor_arch_dir() == "win_amd64" else "spectrometer_x86.dll"


def candidate_sdk_dirs(sdk_dir: str | os.PathLike[str] | None = None) -> list[Path]:
    candidates: list[Path] = []
    if sdk_dir is not None:
        candidates.append(Path(sdk_dir))
    env_sdk_dir = os.getenv("TLS_C1_SDK_DIR")
    if env_sdk_dir:
        candidates.append(Path(env_sdk_dir))
    candidates.append(Path(__file__).resolve().parent / "vendor" / _vendor_arch_dir())
    candidates.append(Path.cwd())
    return candidates


def candidate_dll_paths(sdk_dir: str | os.PathLike[str] | None = None) -> list[Path]:
    return [directory / _dll_name() for directory in candidate_sdk_dirs(sdk_dir)]


def register_signatures(lib: ctypes.CDLL) -> ctypes.CDLL:
    for name, spec in FUNCTION_SPECS.items():
        func = getattr(lib, name)
        func.argtypes = list(spec.argtypes)
        func.restype = spec.restype
    return lib


def _track_dll_directory(directory: Path) -> None:
    if os.name != "nt" or not hasattr(os, "add_dll_directory"):
        return
    handle = os.add_dll_directory(str(directory))
    _DLL_DIRECTORY_HANDLES.append(handle)


def load_library(
    sdk_dir: str | os.PathLike[str] | None = None,
    loader: type[ctypes.CDLL] = ctypes.CDLL,
) -> ctypes.CDLL:
    attempted: list[str] = []

    for dll_path in candidate_dll_paths(sdk_dir):
        attempted.append(str(dll_path))
        if not dll_path.exists():
            continue
        try:
            _track_dll_directory(dll_path.parent)
            return register_signatures(loader(str(dll_path)))
        except OSError as exc:
            attempted.append(f"{dll_path} -> {exc}")

    attempted.append(_dll_name())
    try:
        return register_signatures(loader(_dll_name()))
    except OSError as exc:
        attempted.append(f"{_dll_name()} -> {exc}")

    message = "Could not load spectrometer SDK library. Attempted:\n- " + "\n- ".join(attempted)
    raise TLSC1LibraryLoadError(message)


def read_exported_symbol_names(dll_path: str | os.PathLike[str]) -> tuple[str, ...]:
    data = Path(dll_path).read_bytes()
    if data[:2] != b"MZ":
        raise TLSC1LibraryLoadError(f"Not a PE file: {dll_path}")

    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_offset : pe_offset + 4] != b"PE\x00\x00":
        raise TLSC1LibraryLoadError(f"Invalid PE signature: {dll_path}")

    coff_offset = pe_offset + 4
    _, section_count, _, _, _, optional_header_size, _ = struct.unpack_from("<HHIIIHH", data, coff_offset)
    optional_header_offset = coff_offset + 20
    magic = struct.unpack_from("<H", data, optional_header_offset)[0]
    if magic == 0x10B:
        data_directory_offset = optional_header_offset + 96
    elif magic == 0x20B:
        data_directory_offset = optional_header_offset + 112
    else:
        raise TLSC1LibraryLoadError(f"Unsupported PE optional-header magic {magic:#x}: {dll_path}")

    export_table_rva, _ = struct.unpack_from("<II", data, data_directory_offset)
    section_offset = optional_header_offset + optional_header_size

    sections: list[tuple[int, int, int]] = []
    for index in range(section_count):
        offset = section_offset + index * 40
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from("<IIII", data, offset + 8)
        sections.append((virtual_address, max(virtual_size, raw_size), raw_pointer))

    def rva_to_offset(rva: int) -> int:
        for virtual_address, size, raw_pointer in sections:
            if virtual_address <= rva < virtual_address + size:
                return raw_pointer + (rva - virtual_address)
        raise TLSC1LibraryLoadError(f"RVA {rva:#x} is outside PE sections for {dll_path}")

    export_offset = rva_to_offset(export_table_rva)
    _, _, _, _, _, _, _, export_name_count, _, name_pointer_rva, _ = struct.unpack_from(
        "<IIHHIIIIIII",
        data,
        export_offset,
    )
    name_pointer_offset = rva_to_offset(name_pointer_rva)

    exports: list[str] = []
    for index in range(export_name_count):
        (name_rva,) = struct.unpack_from("<I", data, name_pointer_offset + index * 4)
        name_offset = rva_to_offset(name_rva)
        end = data.index(b"\x00", name_offset)
        exports.append(data[name_offset:end].decode("ascii", errors="strict"))

    return tuple(exports)
