#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import struct
import shutil
import sys
import time
from pathlib import Path

import run_action_alink_probe as rap
import run_action_avmrun_probe as avp
import vice_prg_probe as vp


ROOT = Path(__file__).resolve().parent
ACTION_ROOT = ROOT.parent.parent / "actionc64u"
ALINK_CURRENT_LABELS = ACTION_ROOT / "build/udos_tools/alink.current.labels"
ALINK_DIAG_LABELS = ACTION_ROOT / "build/udos_tools/alink.diag.labels"
RESIDENT_LABELS = ROOT.parent / "build/release/udos-resident.labels"
PROMPT_TIMEOUT = 30.0
FINAL_TIMEOUT = 30.0
SETTLE_SECONDS = 2.0
SEND_TIMEOUT = 5.0


def seeded_main_object_text() -> str:
    return (
        "AVO1\n"
        "x main 0 30\n"
        "b e0u0p0p1ayp2p3gzr\n"
        "u w\n"
        "s HELLO\n"
        "i 120\n"
        "i 4\n"
        "i 57\n"
        "i 57\n"
        "k 7\n"
        "n main\n"
    )


def seeded_work_object_text() -> str:
    return (
        "AVO1\n"
        "x w 0 13\n"
        "b s0i0r\n"
        "s TOOL\n"
        "i 7\n"
        "n w\n"
    )


def prepare_workspace(fs_root: Path, project_name: str) -> Path:
    project_root = fs_root / "IMAGES" / "ACTION.DNP" / project_name.upper()
    lower_project_root = project_root.parent / project_root.name.lower()
    shutil.rmtree(project_root, ignore_errors=True)
    shutil.rmtree(lower_project_root, ignore_errors=True)
    (project_root / "src").mkdir(parents=True, exist_ok=True)
    (project_root / "bin").mkdir(exist_ok=True)
    (project_root / "obj").mkdir(exist_ok=True)

    rap.write_ascii(project_root / "readme.txt", "ACTION PROJECT READY\n")
    rap.write_ascii(project_root / "ACTION.PROJ", "ACTION PROJECT\rMAIN.ACT\r")
    rap.write_ascii(project_root / "UDOSDIR.TXT", "D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF README.TXT\n")
    rap.write_ascii(project_root / "src" / "UDOSDIR.TXT", "F MAIN.ACT\n")
    rap.write_ascii(project_root / "bin" / "UDOSDIR.TXT", "")
    obj_dir = project_root / "obj"
    rap.write_ascii(obj_dir / "UDOSDIR.TXT", "F MAIN.OBJ\nF W.OBJ\n")
    rap.write_ascii(obj_dir / "main.obj", seeded_main_object_text())
    rap.write_ascii(obj_dir / "w.obj", seeded_work_object_text())

    if rap.ACTION_ALINK_BUILD.is_file():
        root_target = fs_root / "IMAGES" / "ACTION.DNP" / "ALINK.PRG"
        shutil.copy2(rap.ACTION_ALINK_BUILD, root_target)
        shutil.copy2(root_target, project_root / "ALINK.PRG")
        rap.ensure_catalog_entries(
            fs_root / "IMAGES" / "ACTION.DNP" / "UDOSDIR.TXT",
            [f"D {project_name.upper()}", "F ALINK.PRG"],
        )
        rap.ensure_catalog_entries(project_root / "UDOSDIR.TXT", ["F ALINK.PRG"])
    return project_root


def read_cstr(client: vp.BinaryMonitorClient, addr: int, limit: int) -> str:
    data = client.memory_get(addr, addr + limit - 1)
    out = bytearray()
    for value in data:
        if value == 0:
            break
        out.append(value)
    return out.decode("ascii", errors="replace")


def read_ascii_bytes(client: vp.BinaryMonitorClient, addr: int, length: int) -> str:
    data = client.memory_get(addr, addr + length - 1)
    out = bytearray()
    for value in data:
        if value == 0:
            break
        out.append(value)
    return out.decode("ascii", errors="replace")


def load_selected_alink_labels() -> dict[str, int]:
    wanted = {
        "compare_char",
        "main_flags_lo",
        "main_flags_hi",
        "file_params",
        "src_ptr",
        "scan_ptr",
        "content_ptr",
        "const_ptr",
        "target_path",
        "content_buffer",
        "source_buffer",
        "module_name",
        "saved_module_name",
        "pending_name_buffer",
        "debug_phase",
        "debug_phase_zp",
        "output_chunk_len",
        "output_chunk_buffer",
    }
    out: dict[str, int] = {}
    labels_path = ALINK_CURRENT_LABELS if ALINK_CURRENT_LABELS.is_file() else ALINK_DIAG_LABELS
    if not labels_path.is_file():
        return out
    for line in labels_path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        name = parts[2].lstrip(".")
        if name not in wanted:
            continue
        try:
            out[name] = int(parts[1], 16)
        except ValueError:
            continue
    return out


def load_selected_resident_labels() -> dict[str, int]:
    wanted = {
        "save_debug_stage_byte",
        "save_debug_open_status0",
        "save_debug_open_status1",
        "save_debug_open_status2",
        "save_debug_open_status3",
        "uci_cmd_buffer",
        "vice_tree_content_src_lo",
        "vice_tree_content_src_hi",
        "vice_lfn",
        "vice_secondary",
        "file_index",
        "temp_dir_id",
        "mount_flag_table",
        "current_drive",
        "temp_drive",
        "dir_state_table",
        "save_debug_write_path_buffer",
        "path_name_buffer",
        "arg_buffer",
        "program_image_buffer",
        "launch_load_cache_lo",
        "launch_load_cache_hi",
        "vice_read_length",
        "program_image_len_lo",
        "program_image_len_hi",
        "parse_scan_index",
        "cmd_length",
        "dir_walk_count",
        "dir_walk_id",
        "dir_walk_bytes",
        "dir_ptr_save_lo",
        "dir_ptr_save_hi",
        "source_fullpath_buffer",
        "dest_fullpath_buffer",
        "desired_path_buffer",
        "flat_dir_sector_buffer",
        "vice_dir_names_b",
        "vice_dir_parent_b",
        "vice_dir_state_b",
        "reu_init",
        "tool_abi_open_program_read_path",
        "tool_abi_seed_program_mount_snapshot",
        "tool_abi_fixed_template",
        "tool_abi_file_stage_reu_sc0",
        "tool_abi_file_write_chunk_sc0",
        "tool_abi_file_write_chunk_current",
        "vice_open_read_from_ptr",
    }
    out: dict[str, int] = {}
    if not RESIDENT_LABELS.is_file():
        return out
    for line in RESIDENT_LABELS.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        name = parts[2].lstrip(".")
        if name not in wanted:
            continue
        try:
            out[name] = int(parts[1], 16)
        except ValueError:
            continue
    return out


def load_script_labels() -> dict[str, int]:
    if not RESIDENT_LABELS.is_file():
        return {}
    labels = vp.load_ld65_labels(RESIDENT_LABELS)
    required = (
        "input_mode",
        "script_index",
        "script_line_count",
        "script_line_data",
        "batch_mode",
        "script_abort_on_error",
        "command_status",
    )
    return {name: labels[name] for name in required if name in labels}


def inject_script_lines(client: vp.BinaryMonitorClient, lines: list[str]) -> None:
    labels = load_script_labels()
    required = (
        "input_mode",
        "script_index",
        "script_line_count",
        "script_line_data",
        "batch_mode",
        "script_abort_on_error",
        "command_status",
    )
    missing = [name for name in required if name not in labels]
    if missing:
        raise vp.ViceError(f"resident labels missing script symbols: {', '.join(missing)}")
    if len(lines) > vp.SCRIPT_LINE_MAX:
        raise vp.ViceError(f"too many script lines: {len(lines)} > {vp.SCRIPT_LINE_MAX}")
    blob = bytearray(vp.SCRIPT_LINE_STRIDE * vp.SCRIPT_LINE_MAX)
    for index, line in enumerate(lines):
        encoded = line.encode("ascii", errors="strict")
        if len(encoded) > vp.SCRIPT_LINE_STRIDE - 1:
            raise vp.ViceError(f"script line too long: {line!r}")
        start = index * vp.SCRIPT_LINE_STRIDE
        blob[start : start + len(encoded)] = encoded
    client.memory_set(labels["script_line_data"], bytes(blob))
    client.memory_set(labels["script_index"], b"\x00")
    client.memory_set(labels["script_line_count"], bytes((len(lines),)))
    client.memory_set(labels["batch_mode"], b"\x00")
    client.memory_set(labels["script_abort_on_error"], b"\x00")
    client.memory_set(labels["command_status"], b"\x00")
    client.memory_set(labels["input_mode"], bytes((vp.INPUT_MODE_SCRIPT,)))


def collect_stage_b_snapshot(client: vp.BinaryMonitorClient) -> dict[str, object]:
    labels = load_selected_resident_labels()
    dir_name_stride = 21
    data: dict[str, object] = {}
    try:
        data["RES_SCREEN_PTR"] = list(client.memory_get(0x00F9, 0x00FA))
        data["RES_PTR"] = list(client.memory_get(0x00FB, 0x00FC))
    except Exception as exc:  # pragma: no cover - debug only
        data["RES_SCREEN_PTR"] = f"ERR:{exc!r}"
        data["RES_PTR"] = f"ERR:{exc!r}"
    for name in (
        "save_debug_stage_byte",
        "vice_lfn",
        "vice_secondary",
        "file_index",
        "temp_dir_id",
        "current_drive",
        "temp_drive",
        "parse_scan_index",
        "cmd_length",
        "dir_walk_count",
        "dir_walk_id",
        "dir_walk_bytes",
        "dir_ptr_save_lo",
        "dir_ptr_save_hi",
    ):
        addr = labels.get(name)
        if addr is None:
            continue
        try:
            data[name.upper()] = client.memory_get(addr, addr)[0]
        except Exception as exc:  # pragma: no cover - debug only
            data[name.upper()] = f"ERR:{exc!r}"
    addr = labels.get("uci_cmd_buffer")
    if addr is not None:
        try:
            data["UCI_CMD_BUFFER"] = read_cstr(client, addr, 96)
        except Exception as exc:  # pragma: no cover - debug only
            data["UCI_CMD_BUFFER"] = f"ERR:{exc!r}"
    addr = labels.get("path_name_buffer")
    if addr is not None:
        try:
            data["PATH_NAME_BUFFER"] = read_cstr(client, addr, 64)
        except Exception as exc:  # pragma: no cover - debug only
            data["PATH_NAME_BUFFER"] = f"ERR:{exc!r}"
    addr = labels.get("arg_buffer")
    if addr is not None:
        try:
            data["ARG_BUFFER"] = read_cstr(client, addr, 64)
            data["ARG_BUFFER_RAW"] = list(client.memory_get(addr, addr + 15))
        except Exception as exc:  # pragma: no cover - debug only
            data["ARG_BUFFER"] = f"ERR:{exc!r}"
            data["ARG_BUFFER_RAW"] = f"ERR:{exc!r}"
    addr = labels.get("source_fullpath_buffer")
    if addr is not None:
        try:
            data["SOURCE_FULLPATH_BUFFER"] = read_cstr(client, addr, 96)
        except Exception as exc:  # pragma: no cover - debug only
            data["SOURCE_FULLPATH_BUFFER"] = f"ERR:{exc!r}"
    addr = labels.get("dest_fullpath_buffer")
    if addr is not None:
        try:
            data["DEST_FULLPATH_BUFFER"] = read_cstr(client, addr, 96)
        except Exception as exc:  # pragma: no cover - debug only
            data["DEST_FULLPATH_BUFFER"] = f"ERR:{exc!r}"
    base = labels.get("vice_dir_names_b")
    if base is not None:
        try:
            data["VICE_DIR_NAMES_B"] = [
                read_cstr(client, base + (dir_name_stride * index), dir_name_stride)
                for index in range(3)
            ]
        except Exception as exc:  # pragma: no cover - debug only
            data["VICE_DIR_NAMES_B"] = f"ERR:{exc!r}"
    base = labels.get("vice_dir_parent_b")
    if base is not None:
        try:
            data["VICE_DIR_PARENT_B"] = list(client.memory_get(base, base + 5))
        except Exception as exc:  # pragma: no cover - debug only
            data["VICE_DIR_PARENT_B"] = f"ERR:{exc!r}"
    base = labels.get("vice_dir_state_b")
    if base is not None:
        try:
            data["VICE_DIR_STATE_B"] = list(client.memory_get(base, base + 5))
        except Exception as exc:  # pragma: no cover - debug only
            data["VICE_DIR_STATE_B"] = f"ERR:{exc!r}"
    lo = labels.get("vice_tree_content_src_lo")
    hi = labels.get("vice_tree_content_src_hi")
    if lo is not None and hi is not None:
        try:
            data["VICE_TREE_CONTENT_SRC"] = [
                client.memory_get(lo, lo)[0],
                client.memory_get(hi, hi)[0],
            ]
        except Exception as exc:  # pragma: no cover - debug only
            data["VICE_TREE_CONTENT_SRC"] = f"ERR:{exc!r}"
    mount_addr = labels.get("mount_flag_table")
    dir_addr = labels.get("dir_state_table")
    temp_drive_addr = labels.get("temp_drive")
    current_drive_addr = labels.get("current_drive")
    if temp_drive_addr is not None and mount_addr is not None:
        try:
            temp_drive = client.memory_get(temp_drive_addr, temp_drive_addr)[0]
            data["MOUNT_FLAG_AT_TEMP_DRIVE"] = client.memory_get(mount_addr + temp_drive, mount_addr + temp_drive)[0]
        except Exception as exc:  # pragma: no cover - debug only
            data["MOUNT_FLAG_AT_TEMP_DRIVE"] = f"ERR:{exc!r}"
    if current_drive_addr is not None and dir_addr is not None:
        try:
            current_drive = client.memory_get(current_drive_addr, current_drive_addr)[0]
            data["DIR_STATE_AT_CURRENT_DRIVE"] = client.memory_get(dir_addr + current_drive, dir_addr + current_drive)[0]
        except Exception as exc:  # pragma: no cover - debug only
            data["DIR_STATE_AT_CURRENT_DRIVE"] = f"ERR:{exc!r}"
    for name in (
        "save_debug_open_status0",
        "save_debug_open_status1",
        "save_debug_open_status2",
        "save_debug_open_status3",
    ):
        addr = labels.get(name)
        if addr is None:
            continue
        try:
            data[name.upper()] = client.memory_get(addr, addr)[0]
        except Exception as exc:  # pragma: no cover - debug only
            data[name.upper()] = f"ERR:{exc!r}"
    addr = labels.get("vice_read_length")
    if addr is not None:
        try:
            data["VICE_READ_LENGTH"] = client.memory_get(addr, addr)[0]
        except Exception as exc:  # pragma: no cover - debug only
            data["VICE_READ_LENGTH"] = f"ERR:{exc!r}"
    addr = labels.get("flat_dir_sector_buffer")
    if addr is not None:
        try:
            head = bytes(client.memory_get(addr, addr + 63))
            data["FLAT_DIR_HEAD_BYTES"] = list(head[:32])
            data["FLAT_DIR_HEAD_TEXT"] = head.split(b"\x00", 1)[0].decode("ascii", errors="replace")
        except Exception as exc:  # pragma: no cover - debug only
            data["FLAT_DIR_HEAD_BYTES"] = f"ERR:{exc!r}"
            data["FLAT_DIR_HEAD_TEXT"] = f"ERR:{exc!r}"
    try:
        data["TOOL_QUEUE_TRACE3"] = client.memory_get(0x03FE, 0x03FE)[0]
        data["TOOL_QUEUE_TRACE4"] = client.memory_get(0x03FF, 0x03FF)[0]
        data["CURRENT_PATH"] = read_cstr(client, 0xCD00, 64)
        data["OPEN_PATH"] = read_cstr(client, 0xCD40, 96)
        data["SAVE_PATH"] = read_cstr(client, 0xC5A3, 96)
        data["TOOL_ABI_OPEN_LFN"] = client.memory_get(0xCDC0, 0xCDC0)[0]
        data["TOOL_ABI_FILE_STATUS"] = client.memory_get(0xCDC1, 0xCDC1)[0]
        data["TOOL_ABI_FILE_REMAIN"] = list(client.memory_get(0xCDC2, 0xCDC3))
        data["TOOL_ABI_FILE_LEN"] = list(client.memory_get(0xCDC4, 0xCDC5))
        data["TOOL_ABI_FILE_NAME_PTR"] = list(client.memory_get(0xCDC6, 0xCDC7))
        data["TOOL_ABI_FILE_DEST_PTR"] = list(client.memory_get(0xCDC8, 0xCDC9))
        data["TOOL_ABI_FILE_LIMIT"] = list(client.memory_get(0xCDCA, 0xCDCB))
        dest_addr = data["TOOL_ABI_FILE_DEST_PTR"][0] | (data["TOOL_ABI_FILE_DEST_PTR"][1] << 8)
        data["TOOL_ABI_FILE_DEST_HEAD"] = list(client.memory_get(dest_addr, dest_addr + 31))
        data["TOOL_ABI_SAVE_BLOCK"] = list(client.memory_get(0xCDC6, 0xCDCB))
        data["STACK_F0_FF"] = list(client.memory_get(0x01F0, 0x01FF))
        data["STACK_E0_EF"] = list(client.memory_get(0x01E0, 0x01EF))
    except Exception as exc:  # pragma: no cover - debug only
        data["CURRENT_PATH"] = f"ERR:{exc!r}"
        data["OPEN_PATH"] = f"ERR:{exc!r}"
        data["SAVE_PATH"] = f"ERR:{exc!r}"
        data["TOOL_ABI_OPEN_LFN"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_STATUS"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_REMAIN"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_LEN"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_NAME_PTR"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_DEST_PTR"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_LIMIT"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_DEST_HEAD"] = f"ERR:{exc!r}"
        data["TOOL_ABI_SAVE_BLOCK"] = f"ERR:{exc!r}"
        data["STACK_F0_FF"] = f"ERR:{exc!r}"
        data["STACK_E0_EF"] = f"ERR:{exc!r}"
    buffer_addr = labels.get("save_debug_write_path_buffer")
    if buffer_addr is not None:
        try:
            head = list(client.memory_get(buffer_addr, buffer_addr + 31))
            data["LOAD_DEBUG_BUFFER_HEAD"] = head
            data["LOAD_DEBUG_SETNAM_ARGS"] = head[:3]
            tail = list(client.memory_get(buffer_addr + 80, buffer_addr + 92))
            data["STAGE_D_BUFFER_TAIL"] = tail
        except Exception as exc:  # pragma: no cover - debug only
            data["LOAD_DEBUG_BUFFER_HEAD"] = f"ERR:{exc!r}"
            data["LOAD_DEBUG_SETNAM_ARGS"] = f"ERR:{exc!r}"
            data["STAGE_D_BUFFER_TAIL"] = f"ERR:{exc!r}"
    try:
        regs = collect_registers(client)
        data["REGS"] = {k: regs.get(k) for k in ("pc", "a", "x", "y", "sp", "fl")}
    except Exception as exc:  # pragma: no cover - debug only
        data["REGS"] = f"ERR:{exc!r}"
    return data


def last_nonempty_line(screen: str) -> str:
    lines = [line.rstrip() for line in screen.splitlines()]
    for line in reversed(lines):
        if line.strip():
            return line
    return ""


def feed_command_and_wait(
    client: vp.BinaryMonitorClient,
    process,
    command: str,
    expected_fragment: str,
    timeout: float,
) -> str:
    before_screen, _d018, _dd00 = vp.read_active_screen_text(client)
    client.keyboard_type(command)
    time.sleep(0.75)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise vp.ViceError(f"x64sc exited early while waiting for command result\nstdout:\n{stdout}\nstderr:\n{stderr}")
        screen, _d018, _dd00 = vp.read_active_screen_text(client)
        if screen != before_screen and vp.screen_contains(last_nonempty_line(screen), expected_fragment):
            return screen
        time.sleep(0.2)
    raise vp.ViceError(
        f"timed out waiting for command result {expected_fragment!r}; last screen was:\n{screen}"
    )


def collect_registers(client: vp.BinaryMonitorClient) -> dict[str, int]:
    regs_available = client.command(0x83, bytes((0x00,)))
    reg_count = struct.unpack_from("<H", regs_available, 0)[0]
    reg_names: dict[int, str] = {}
    offset = 2
    for _ in range(reg_count):
        item_size = regs_available[offset]
        reg_id = regs_available[offset + 1]
        name_len = regs_available[offset + 3]
        name = regs_available[offset + 4 : offset + 4 + name_len].decode("ascii", errors="replace").lower()
        reg_names[reg_id] = name
        offset += 1 + item_size
    regs_data = client.command(0x31, bytes((0x00,)))
    value_count = struct.unpack_from("<H", regs_data, 0)[0]
    regs: dict[str, int] = {}
    offset = 2
    for _ in range(value_count):
        item_size = regs_data[offset]
        reg_id = regs_data[offset + 1]
        value = struct.unpack_from("<H", regs_data, offset + 2)[0]
        name = reg_names.get(reg_id, f"id_{reg_id}")
        regs[name] = value
        offset += 1 + item_size
    return regs


def collect_debug(client: vp.BinaryMonitorClient) -> dict[str, object]:
    debug_addrs = [
        (0x03D0, "POSTLOAD_MARKER"),
        (0x03E0, "REU_C64_LO"),
        (0x03E1, "REU_C64_HI"),
        (0x03E2, "REU_REU_LO"),
        (0x03E3, "REU_REU_HI"),
        (0x03E8, "RETURN0"),
        (0x03E9, "RETURN1"),
        (0x03EA, "RETURN2"),
        (0x03EB, "RETURN3"),
        (0x03F0, "LAUNCH_RESULT"),
        (0x03F1, "LAUNCH_EXIT"),
        (0x03F2, "LAUNCH_STAGE"),
        (0x03F3, "LAUNCH_CODE"),
        (0x03F4, "WRITEBACK_STAGE"),
        (0x03F5, "WRITEBACK_COUNT"),
        (0x03F6, "WRITEBACK_KIND"),
        (0x03F7, "PATH0"),
        (0x03F8, "PATH1"),
        (0x03F9, "PATH2"),
        (0x03FA, "PATH3"),
        (0xCFE3, "REU_RTS_LO_SNAPSHOT"),
        (0xCFE4, "REU_RTS_HI_SNAPSHOT"),
        (0xCFE5, "REU_ENTRY_RTS_LO_SNAPSHOT"),
        (0xCFE6, "REU_ENTRY_RTS_HI_SNAPSHOT"),
        (0xCFE7, "REU_ENTRY_SP_SNAPSHOT"),
        (0xCFE9, "REU_RTS_SP_SNAPSHOT"),
        (0xCFEF, "DIRECT_HOSTLOAD_STAGE_SNAPSHOT"),
        (0xC59E, "LOAD_STAGE"),
        (0xC59F, "OPEN0"),
        (0xC5A0, "OPEN1"),
        (0xC5A1, "OPEN2"),
        (0xC5A2, "OPEN3"),
        (0x03FC, "ALINK_TRACE"),
        (0x03FD, "DBG_FD"),
        (0x03FE, "DBG_FE"),
        (0x03FF, "DBG_FF"),
    ]
    data: dict[str, object] = {}
    for addr, name in debug_addrs:
        try:
            data[name] = client.memory_get(addr, addr)[0]
        except Exception as exc:  # pragma: no cover - debug only
            data[name] = f"ERR:{exc!r}"
    for name, addr in load_selected_alink_labels().items():
        key = f"ALINK_{name.upper()}"
        try:
            if name == "file_params":
                params = list(client.memory_get(addr, addr + 8))
                data[key] = params
                name_addr = params[0] | (params[1] << 8)
                dest_addr = params[2] | (params[3] << 8)
                try:
                    data["ALINK_FILE_NAME"] = read_cstr(client, name_addr, 64)
                except Exception as exc:  # pragma: no cover - debug only
                    data["ALINK_FILE_NAME"] = f"ERR:{exc!r}"
                try:
                    data["ALINK_FILE_DEST_HEAD"] = list(client.memory_get(dest_addr, dest_addr + 31))
                except Exception as exc:  # pragma: no cover - debug only
                    data["ALINK_FILE_DEST_HEAD"] = f"ERR:{exc!r}"
            elif name == "target_path":
                data[key] = read_cstr(client, addr, 40)
            elif name in {"content_buffer", "source_buffer"}:
                data[key] = list(client.memory_get(addr, addr + 15))
                if name == "content_buffer":
                    labels = load_selected_alink_labels()
                    lo_addr = labels.get("main_flags_lo")
                    hi_addr = labels.get("main_flags_hi")
                    if lo_addr is not None and hi_addr is not None:
                        size_lo = client.memory_get(lo_addr, lo_addr)[0]
                        size_hi = client.memory_get(hi_addr, hi_addr)[0]
                        if size_hi == 0:
                            total_len = min(size_lo + 12, 255)
                            data["ALINK_OUTPUT_BYTES"] = list(
                                client.memory_get(addr, addr + total_len - 1)
                            )
            elif name in {"module_name", "saved_module_name", "pending_name_buffer"}:
                data[key] = read_cstr(client, addr, 25)
            elif name == "output_chunk_buffer":
                data[key] = list(client.memory_get(addr, addr + 31))
            elif name in {"src_ptr", "scan_ptr", "content_ptr", "const_ptr"}:
                data[key] = list(client.memory_get(addr, addr + 1))
            else:
                data[key] = client.memory_get(addr, addr)[0]
        except Exception as exc:  # pragma: no cover - debug only
            data[key] = f"ERR:{exc!r}"
    resident_labels = load_selected_resident_labels()
    try:
        marker = data.get("POSTLOAD_MARKER")
        if marker in (0xA1, 0xA2):
            data["POSTLOAD_TARGET"] = read_ascii_bytes(client, 0x03D1, 10)
            data["POSTLOAD_MODULE"] = read_ascii_bytes(client, 0x03DB, 6)
            data["POSTLOAD_FILE_PARAMS"] = list(client.memory_get(0x03E1, 0x03E7))
        else:
            data["POSTLOAD_TARGET"] = ""
            data["POSTLOAD_MODULE"] = ""
            data["POSTLOAD_FILE_PARAMS"] = []
        binary_raw = data.get("ALINK_BINARY_TARGET_RAW")
        if isinstance(binary_raw, list) and binary_raw and binary_raw[0] == 0xB3:
            data["PRESAVE_CALL_SP"] = binary_raw[1]
            data["PRESAVE_CALL_TARGET"] = bytes(binary_raw[2:12]).split(b"\x00", 1)[0].decode("ascii", errors="replace")
            data["PRESAVE_CALL_BUFFER_PTR"] = binary_raw[12:14]
            data["PRESAVE_CALL_LIMIT"] = binary_raw[14:16]
            data["PRESAVE_CALL_STACK_WINDOW"] = binary_raw[16:31]
            data["PRESAVE_SP"] = None
            data["PRESAVE_FILE_PARAMS"] = []
            data["PRESAVE_STACK_WINDOW"] = []
        elif isinstance(binary_raw, list) and binary_raw and binary_raw[0] in (0xB1, 0xB2):
            data["PRESAVE_SP"] = binary_raw[1]
            data["PRESAVE_FILE_PARAMS"] = binary_raw[2:9]
            data["PRESAVE_STACK_WINDOW"] = binary_raw[9:24]
            data["PRESAVE_CALL_SP"] = None
            data["PRESAVE_CALL_TARGET"] = ""
            data["PRESAVE_CALL_BUFFER_PTR"] = []
            data["PRESAVE_CALL_LIMIT"] = []
            data["PRESAVE_CALL_STACK_WINDOW"] = []
            data["ALINK_SAVE_STAGE"] = None
            data["ALINK_SAVE_FILE_PARAMS"] = []
        elif isinstance(binary_raw, list) and len(binary_raw) >= 24 and binary_raw[16] in (0xC1, 0xC2, 0xC3, 0xC4):
            data["ALINK_SAVE_STAGE"] = binary_raw[16]
            data["ALINK_SAVE_FILE_PARAMS"] = binary_raw[17:24]
            if len(binary_raw) >= 31:
                data["ALINK_PRESAVE_RES_STATE"] = {
                    "current_drive_state": binary_raw[24],
                    "mount_flags": binary_raw[25:27],
                    "dir_states": binary_raw[27:29],
                    "program_drive_snapshot": binary_raw[29],
                    "program_dir_snapshot": binary_raw[30],
                }
            else:
                data["ALINK_PRESAVE_RES_STATE"] = {}
            data["PRESAVE_SP"] = None
            data["PRESAVE_FILE_PARAMS"] = []
            data["PRESAVE_STACK_WINDOW"] = []
            data["PRESAVE_CALL_SP"] = None
            data["PRESAVE_CALL_TARGET"] = ""
            data["PRESAVE_CALL_BUFFER_PTR"] = []
            data["PRESAVE_CALL_LIMIT"] = []
            data["PRESAVE_CALL_STACK_WINDOW"] = []
        else:
            data["PRESAVE_SP"] = None
            data["PRESAVE_FILE_PARAMS"] = []
            data["PRESAVE_STACK_WINDOW"] = []
            data["PRESAVE_CALL_SP"] = None
            data["PRESAVE_CALL_TARGET"] = ""
            data["PRESAVE_CALL_BUFFER_PTR"] = []
            data["PRESAVE_CALL_LIMIT"] = []
            data["PRESAVE_CALL_STACK_WINDOW"] = []
            data["ALINK_SAVE_STAGE"] = None
            data["ALINK_SAVE_FILE_PARAMS"] = []
            data["ALINK_PRESAVE_RES_STATE"] = {}
        data["CURRENT_PATH"] = read_cstr(client, 0xCD00, 64)
        data["OPEN_PATH"] = read_cstr(client, 0xCD40, 96)
        data["SAVE_PATH"] = read_cstr(client, 0xC5A3, 96)
        stage_addr = resident_labels.get("save_debug_stage_byte")
        if stage_addr is not None:
            data["RESIDENT_STAGE_BYTE"] = client.memory_get(stage_addr, stage_addr)[0]
        data["UCI_CMD_BUFFER"] = read_cstr(client, 0xC423, 96)
        data["PROGRAM_DRIVE_SNAPSHOT"] = client.memory_get(0xCFF8, 0xCFF8)[0]
        data["PROGRAM_DIR_SNAPSHOT"] = client.memory_get(0xCFF9, 0xCFF9)[0]
        data["CURRENT_DRIVE_SNAPSHOT"] = client.memory_get(0xCFEC, 0xCFEC)[0]
        data["CURRENT_FLAGS_SNAPSHOT"] = client.memory_get(0xCFEE, 0xCFEE)[0]
        data["MOUNT_SNAPSHOT"] = client.memory_get(0xCFF2, 0xCFF2)[0]
        data["SERVICE_STAGE_SNAPSHOT"] = client.memory_get(0xCFF1, 0xCFF1)[0]
        data["SERVICE_STAGE_SP_SNAPSHOT"] = client.memory_get(0xCFF3, 0xCFF3)[0]
        data["SERVICE_STAGE_X_SNAPSHOT"] = client.memory_get(0xCFF5, 0xCFF5)[0]
        data["CURRENT_DRIVE_STATE"] = client.memory_get(0x9580, 0x9580)[0]
        data["MOUNT_FLAGS"] = list(client.memory_get(0x9614, 0x9615))
        data["DIR_STATES"] = list(client.memory_get(0x9616, 0x9617))
        data["RES_SCREEN_PTR"] = list(client.memory_get(0x00F9, 0x00FA))
        data["RES_PTR"] = list(client.memory_get(0x00FB, 0x00FC))
        data["TOOL_ABI_SAVE_BLOCK"] = list(client.memory_get(0xCDC6, 0xCDCB))
        data["RES_SAVE_ENTRY_STAGE"] = client.memory_get(0xCDC1, 0xCDC1)[0]
        data["RES_SAVE_RESOLVE_STAGE"] = client.memory_get(0xCDC2, 0xCDC2)[0]
        data["SAVE_CALL_BLOCK"] = list(client.memory_get(0x03E8, 0x03EF))
    except Exception as exc:  # pragma: no cover - debug only
        data["POSTLOAD_TARGET"] = f"ERR:{exc!r}"
        data["POSTLOAD_MODULE"] = f"ERR:{exc!r}"
        data["POSTLOAD_FILE_PARAMS"] = f"ERR:{exc!r}"
        data["PRESAVE_SP"] = f"ERR:{exc!r}"
        data["PRESAVE_FILE_PARAMS"] = f"ERR:{exc!r}"
        data["PRESAVE_STACK_WINDOW"] = f"ERR:{exc!r}"
        data["PRESAVE_CALL_SP"] = f"ERR:{exc!r}"
        data["PRESAVE_CALL_TARGET"] = f"ERR:{exc!r}"
        data["PRESAVE_CALL_BUFFER_PTR"] = f"ERR:{exc!r}"
        data["PRESAVE_CALL_LIMIT"] = f"ERR:{exc!r}"
        data["PRESAVE_CALL_STACK_WINDOW"] = f"ERR:{exc!r}"
        data["ALINK_SAVE_STAGE"] = f"ERR:{exc!r}"
        data["ALINK_SAVE_FILE_PARAMS"] = f"ERR:{exc!r}"
        data["CURRENT_PATH"] = f"ERR:{exc!r}"
        data["OPEN_PATH"] = f"ERR:{exc!r}"
        data["SAVE_PATH"] = f"ERR:{exc!r}"
        data["RESIDENT_STAGE_BYTE"] = f"ERR:{exc!r}"
        data["UCI_CMD_BUFFER"] = f"ERR:{exc!r}"
        data["PROGRAM_DRIVE_SNAPSHOT"] = f"ERR:{exc!r}"
        data["PROGRAM_DIR_SNAPSHOT"] = f"ERR:{exc!r}"
        data["CURRENT_DRIVE_SNAPSHOT"] = f"ERR:{exc!r}"
        data["CURRENT_FLAGS_SNAPSHOT"] = f"ERR:{exc!r}"
        data["MOUNT_SNAPSHOT"] = f"ERR:{exc!r}"
        data["SERVICE_STAGE_SNAPSHOT"] = f"ERR:{exc!r}"
        data["SERVICE_STAGE_SP_SNAPSHOT"] = f"ERR:{exc!r}"
        data["SERVICE_STAGE_X_SNAPSHOT"] = f"ERR:{exc!r}"
        data["CURRENT_DRIVE_STATE"] = f"ERR:{exc!r}"
        data["MOUNT_FLAGS"] = f"ERR:{exc!r}"
        data["DIR_STATES"] = f"ERR:{exc!r}"
        data["RES_SCREEN_PTR"] = f"ERR:{exc!r}"
        data["RES_PTR"] = f"ERR:{exc!r}"
        data["TOOL_ABI_SAVE_BLOCK"] = f"ERR:{exc!r}"
        data["RES_SAVE_ENTRY_STAGE"] = f"ERR:{exc!r}"
        data["RES_SAVE_RESOLVE_STAGE"] = f"ERR:{exc!r}"
        data["SAVE_CALL_BLOCK"] = f"ERR:{exc!r}"
    try:
        file_name_ptr_bytes = client.memory_get(0xCDC6, 0xCDC7)
        file_name_ptr = file_name_ptr_bytes[0] | (file_name_ptr_bytes[1] << 8)
        data["TOOL_ABI_FILE_NAME_TEXT"] = read_cstr(client, file_name_ptr, 96)
    except Exception as exc:  # pragma: no cover - debug only
        data["TOOL_ABI_FILE_NAME_TEXT"] = f"ERR:{exc!r}"
    reu_init_addr = resident_labels.get("reu_init")
    if reu_init_addr is not None:
        try:
            data["REU_INIT_BYTES"] = list(client.memory_get(reu_init_addr, reu_init_addr + 31))
        except Exception as exc:  # pragma: no cover - debug only
            data["REU_INIT_BYTES"] = f"ERR:{exc!r}"
    tool_abi_file_stage_reu_addr = resident_labels.get("tool_abi_file_stage_reu_sc0")
    if tool_abi_file_stage_reu_addr is not None:
        try:
            data["TOOL_ABI_FILE_STAGE_REU_BYTES"] = list(
                client.memory_get(tool_abi_file_stage_reu_addr, tool_abi_file_stage_reu_addr + 31)
            )
        except Exception as exc:  # pragma: no cover - debug only
            data["TOOL_ABI_FILE_STAGE_REU_BYTES"] = f"ERR:{exc!r}"
    open_path_addr = resident_labels.get("tool_abi_open_program_read_path")
    if open_path_addr is not None:
        try:
            data["TOOL_ABI_OPEN_PROGRAM_READ_PATH_BYTES"] = list(
                client.memory_get(open_path_addr, open_path_addr + 31)
            )
        except Exception as exc:  # pragma: no cover - debug only
            data["TOOL_ABI_OPEN_PROGRAM_READ_PATH_BYTES"] = f"ERR:{exc!r}"
    seed_mount_addr = resident_labels.get("tool_abi_seed_program_mount_snapshot")
    if seed_mount_addr is not None:
        try:
            data["TOOL_ABI_SEED_PROGRAM_MOUNT_BYTES"] = list(
                client.memory_get(seed_mount_addr, seed_mount_addr + 15)
            )
        except Exception as exc:  # pragma: no cover - debug only
            data["TOOL_ABI_SEED_PROGRAM_MOUNT_BYTES"] = f"ERR:{exc!r}"
    vice_open_addr = resident_labels.get("vice_open_read_from_ptr")
    if vice_open_addr is not None:
        try:
            data["VICE_OPEN_READ_FROM_PTR_BYTES"] = list(
                client.memory_get(vice_open_addr, vice_open_addr + 31)
            )
        except Exception as exc:  # pragma: no cover - debug only
            data["VICE_OPEN_READ_FROM_PTR_BYTES"] = f"ERR:{exc!r}"
    for name in ("source_fullpath_buffer", "dest_fullpath_buffer", "path_name_buffer", "arg_buffer"):
        addr = resident_labels.get(name)
        if addr is None:
            continue
        key = name.upper()
        try:
            data[key] = read_cstr(client, addr, 96 if "fullpath" in name else 64)
        except Exception as exc:  # pragma: no cover - debug only
            data[key] = f"ERR:{exc!r}"
    try:
        regs = collect_registers(client)
        for name in ("pc", "a", "x", "y", "sp", "fl"):
            if name in regs:
                data[f"REG_{name.upper()}"] = regs[name]
    except Exception as exc:  # pragma: no cover - debug only
        data["REG_ERR"] = f"ERR:{exc!r}"
    try:
        data["MEM_0900"] = list(client.memory_get(0x0900, 0x091F))
        data["MEM_0801"] = list(client.memory_get(0x0801, 0x0810))
    except Exception as exc:  # pragma: no cover - debug only
        data["MEM_0900"] = f"ERR:{exc!r}"
        data["MEM_0801"] = f"ERR:{exc!r}"
    launch_load_cache_lo_addr = resident_labels.get("launch_load_cache_lo")
    launch_load_cache_hi_addr = resident_labels.get("launch_load_cache_hi")
    if launch_load_cache_lo_addr is not None and launch_load_cache_hi_addr is not None:
        try:
            launch_load_cache = list(client.memory_get(launch_load_cache_lo_addr, launch_load_cache_hi_addr))
            data["LAUNCH_LOAD_CACHE"] = launch_load_cache
            if len(launch_load_cache) == 2:
                load_addr = launch_load_cache[0] | (launch_load_cache[1] << 8)
                data["PROGRAM_RAM_HEAD"] = list(client.memory_get(load_addr, load_addr + 31))
        except Exception as exc:  # pragma: no cover - debug only
            data["LAUNCH_LOAD_CACHE"] = f"ERR:{exc!r}"
            data["PROGRAM_RAM_HEAD"] = f"ERR:{exc!r}"
    program_image_buffer_addr = resident_labels.get("program_image_buffer")
    if program_image_buffer_addr is not None:
        try:
            data["PROGRAM_IMAGE_BUFFER_HEAD"] = list(client.memory_get(program_image_buffer_addr, program_image_buffer_addr + 31))
        except Exception as exc:  # pragma: no cover - debug only
            data["PROGRAM_IMAGE_BUFFER_HEAD"] = f"ERR:{exc!r}"
    program_image_len_lo_addr = resident_labels.get("program_image_len_lo")
    program_image_len_hi_addr = resident_labels.get("program_image_len_hi")
    if program_image_len_lo_addr is not None and program_image_len_hi_addr is not None:
        try:
            data["PROGRAM_IMAGE_LEN_STATE"] = list(client.memory_get(program_image_len_lo_addr, program_image_len_hi_addr))
        except Exception as exc:  # pragma: no cover - debug only
            data["PROGRAM_IMAGE_LEN_STATE"] = f"ERR:{exc!r}"
    try:
        data["PROGRAM_IMAGE_LEN_SNAPSHOT"] = list(client.memory_get(0xCFFA, 0xCFFB))
    except Exception as exc:  # pragma: no cover - debug only
        data["PROGRAM_IMAGE_LEN_SNAPSHOT"] = f"ERR:{exc!r}"
    try:
        data["UDOS_SERVICE_BLOCK_CF00"] = list(client.memory_get(0xCF00, 0xCF3F))
        data["UDOS_SERVICE_FILE_LOAD_CF12"] = list(client.memory_get(0xCF12, 0xCF1A))
        data["UDOS_SERVICE_FILE_STAGE_REU_CF36"] = list(client.memory_get(0xCF36, 0xCF3E))
    except Exception as exc:  # pragma: no cover - debug only
        data["UDOS_SERVICE_BLOCK_CF00"] = f"ERR:{exc!r}"
        data["UDOS_SERVICE_FILE_LOAD_CF12"] = f"ERR:{exc!r}"
        data["UDOS_SERVICE_FILE_STAGE_REU_CF36"] = f"ERR:{exc!r}"
    try:
        data["ALINK_LOADED_OBJECT_STATUS"] = client.memory_get(0xCF9E, 0xCF9E)[0]
    except Exception as exc:  # pragma: no cover - debug only
        data["ALINK_LOADED_OBJECT_STATUS"] = f"ERR:{exc!r}"
    try:
        data["ALINK_LOADED_OBJECT_PHASE"] = client.memory_get(0xCF9F, 0xCF9F)[0]
    except Exception as exc:  # pragma: no cover - debug only
        data["ALINK_LOADED_OBJECT_PHASE"] = f"ERR:{exc!r}"
    try:
        data["ALINK_SOURCE_LOAD_PHASE"] = client.memory_get(0xCF9C, 0xCF9C)[0]
    except Exception as exc:  # pragma: no cover - debug only
        data["ALINK_SOURCE_LOAD_PHASE"] = f"ERR:{exc!r}"
    try:
        data["ALINK_SOURCE_LOAD_STATUS"] = client.memory_get(0xCF9D, 0xCF9D)[0]
    except Exception as exc:  # pragma: no cover - debug only
        data["ALINK_SOURCE_LOAD_STATUS"] = f"ERR:{exc!r}"
    try:
        data["ALINK_PENDING_LOAD_BRANCH"] = client.memory_get(0xCF9B, 0xCF9B)[0]
    except Exception as exc:  # pragma: no cover - debug only
        data["ALINK_PENDING_LOAD_BRANCH"] = f"ERR:{exc!r}"
    try:
        data["ALINK_PENDING_LOAD_SOURCE_HEAD"] = list(client.memory_get(0xCF90, 0xCF93))
    except Exception as exc:  # pragma: no cover - debug only
        data["ALINK_PENDING_LOAD_SOURCE_HEAD"] = f"ERR:{exc!r}"
    try:
        data["ALINK_WRITE_CHUNK_RAW"] = list(client.memory_get(0xCF44, 0xCF4F))
    except Exception as exc:  # pragma: no cover - debug only
        data["ALINK_WRITE_CHUNK_RAW"] = f"ERR:{exc!r}"
    try:
        data["ALINK_OUTPUT_PHASE_RAW"] = client.memory_get(0xCF50, 0xCF50)[0]
    except Exception as exc:  # pragma: no cover - debug only
        data["ALINK_OUTPUT_PHASE_RAW"] = f"ERR:{exc!r}"
    try:
        data["ALINK_SOURCE_RETURN_RAW"] = list(client.memory_get(0xCF40, 0xCF43))
    except Exception as exc:  # pragma: no cover - debug only
        data["ALINK_SOURCE_RETURN_RAW"] = f"ERR:{exc!r}"
    try:
        data["ALINK_PENDING_COPY_RAW"] = list(client.memory_get(0xCF60, 0xCF65))
    except Exception as exc:  # pragma: no cover - debug only
        data["ALINK_PENDING_COPY_RAW"] = f"ERR:{exc!r}"
    try:
        loaded_source = list(client.memory_get(0xCFA0, 0xCFAF))
        data["ALINK_LOADED_SOURCE_RAW"] = loaded_source
        data["ALINK_LOADED_SOURCE_TEXT"] = bytes(v for v in loaded_source if v != 0).decode("ascii", errors="replace")
    except Exception as exc:  # pragma: no cover - debug only
        data["ALINK_LOADED_SOURCE_RAW"] = f"ERR:{exc!r}"
        data["ALINK_LOADED_SOURCE_TEXT"] = f"ERR:{exc!r}"
    try:
        loaded_target = list(client.memory_get(0xCFB0, 0xCFBF))
        data["ALINK_LOADED_TARGET_RAW"] = loaded_target
        data["ALINK_LOADED_TARGET_TEXT"] = bytes(v for v in loaded_target if v != 0).decode("ascii", errors="replace")
    except Exception as exc:  # pragma: no cover - debug only
        data["ALINK_LOADED_TARGET_RAW"] = f"ERR:{exc!r}"
        data["ALINK_LOADED_TARGET_TEXT"] = f"ERR:{exc!r}"
    try:
        bad_avo_source = list(client.memory_get(0xCFD0, 0xCFDF))
        data["BAD_AVO_SOURCE_RAW"] = bad_avo_source
        data["BAD_AVO_SOURCE_TEXT"] = bytes(v for v in bad_avo_source if v != 0).decode("ascii", errors="replace")
    except Exception as exc:  # pragma: no cover - debug only
        data["BAD_AVO_SOURCE_RAW"] = f"ERR:{exc!r}"
        data["BAD_AVO_SOURCE_TEXT"] = f"ERR:{exc!r}"
    try:
        bad_avo_target = list(client.memory_get(0xCFC0, 0xCFCF))
        data["BAD_AVO_TARGET_RAW"] = bad_avo_target
        data["BAD_AVO_TARGET_TEXT"] = bytes(v for v in bad_avo_target if v != 0).decode("ascii", errors="replace")
    except Exception as exc:  # pragma: no cover - debug only
        data["BAD_AVO_TARGET_RAW"] = f"ERR:{exc!r}"
        data["BAD_AVO_TARGET_TEXT"] = f"ERR:{exc!r}"
    return data


def run_once(image: Path, work_root: Path, project_name: str, connect_delay: float) -> tuple[str, dict[str, object]]:
    port = vp.reserve_tcp_port()
    process = vp.launch_vice(
        image,
        port,
        extra_args=[
            "-iecdevice9",
            "-fs9",
            str(work_root),
            "-fslongnames",
        ],
    )
    client = vp.BinaryMonitorClient("127.0.0.1", port, timeout=5.0)
    alink_labels = load_selected_alink_labels()
    debug_phase_zp_addr = alink_labels.get("debug_phase_zp")
    try:
        if connect_delay > 0.0:
            time.sleep(connect_delay)
        client.connect(time.monotonic() + 20.0)
        client.ping()
        client.resume()
        avp.nudge_to_prompt(client, process, "A:D64/>", attempts=3, timeout=8.0)
        avp.wait_for_active_prompt(client, "A:D64/>", 60.0, poll_interval=0.2)
        time.sleep(5.0)
        avp.send_return(client, SEND_TIMEOUT)
        avp.wait_for_active_prompt(client, "A:D64/>", 15.0, poll_interval=0.2)
        time.sleep(1.0)

        mount_command = "MOUNT B: /IMAGES/ACTION.DNP"
        avp.type_command(client, mount_command, 30.0)
        avp.wait_for_mount_completion(client, 30.0, retry_echo=mount_command, poll_interval=0.2)

        avp.type_command(client, "B:", SEND_TIMEOUT)
        avp.wait_for_screen_fragment(client, "B:DNP/", PROMPT_TIMEOUT, retry_echo="B:")
        time.sleep(SETTLE_SECONDS)

        cd_command = f"CD {project_name}"
        avp.type_command(client, cd_command, SEND_TIMEOUT)
        avp.wait_for_screen_fragment(client, f"B:DNP/{project_name}", PROMPT_TIMEOUT, retry_echo=cd_command)
        time.sleep(SETTLE_SECONDS)

        avp.type_command(client, "ALINK MAIN", SEND_TIMEOUT)
        launch_deadline = time.monotonic() + PROMPT_TIMEOUT
        while time.monotonic() < launch_deadline:
            screen, _d018, _dd00 = vp.read_active_screen_text(client)
            if vp.screen_contains(screen, "RUN ALINK.PRG"):
                break
            if (
                vp.screen_contains(screen, "TOO LARGE")
                or vp.screen_contains(screen, "SAVE FAIL")
                or vp.screen_contains(screen, "BAD AVO")
            ):
                debug = collect_debug(client)
                raise vp.ViceError(
                    f"ALINK launch-stage failure with screen:\n{screen}\nDEBUG: {json.dumps(debug, indent=2)}"
                )
            time.sleep(0.2)
        else:
            debug = collect_debug(client)
            raise vp.ViceError(
                f"expected screen fragment 'RUN ALINK.PRG' was not present in final screen:\n{screen}\nDEBUG: {json.dumps(debug, indent=2)}"
            )
        deadline = time.monotonic() + FINAL_TIMEOUT
        screen = ""
        stage_b_snapshot: dict[str, object] | None = None
        stage_c_snapshot: dict[str, object] | None = None
        stage_d_snapshot: dict[str, object] | None = None
        live_tool_snapshot: dict[str, object] | None = None
        last_live_trace: int | None = None
        last_live_phase_zp: int | None = None
        last_output_phase: int | None = None
        while time.monotonic() < deadline:
            if stage_b_snapshot is None or stage_c_snapshot is None or stage_d_snapshot is None:
                try:
                    stage = client.memory_get(0xC59E, 0xC59E)[0]
                    if stage == ord("b"):
                        if stage_b_snapshot is None:
                            stage_b_snapshot = collect_stage_b_snapshot(client)
                    elif stage == ord("c"):
                        if stage_c_snapshot is None:
                            stage_c_snapshot = collect_stage_b_snapshot(client)
                    elif stage == ord("d"):
                        if stage_d_snapshot is None:
                            stage_d_snapshot = collect_stage_b_snapshot(client)
                except Exception:
                    pass
            try:
                live_trace = client.memory_get(0x03FC, 0x03FC)[0]
                live_phase_zp = None
                live_output_phase = client.memory_get(0xCF50, 0xCF50)[0]
                if debug_phase_zp_addr is not None:
                    live_phase_zp = client.memory_get(debug_phase_zp_addr, debug_phase_zp_addr)[0]
                if (
                    (live_trace != 0 and live_trace != last_live_trace)
                    or (
                        live_phase_zp is not None
                        and live_phase_zp != 0
                        and live_phase_zp != last_live_phase_zp
                    )
                    or (
                        live_output_phase != 0
                        and live_output_phase != last_output_phase
                    )
                ):
                    live_tool_snapshot = collect_debug(client)
                    last_live_trace = live_trace
                    last_live_phase_zp = live_phase_zp
                    last_output_phase = live_output_phase
            except Exception:
                pass
            screen, _d018, _dd00 = vp.read_active_screen_text(client)
            if vp.screen_contains(screen, "ALINK OK"):
                debug = collect_debug(client)
                if live_tool_snapshot is not None:
                    debug["LIVE_TOOL_SNAPSHOT"] = live_tool_snapshot
                if stage_b_snapshot is not None:
                    debug["STAGE_B_SNAPSHOT"] = stage_b_snapshot
                if stage_c_snapshot is not None:
                    debug["STAGE_C_SNAPSHOT"] = stage_c_snapshot
                if stage_d_snapshot is not None:
                    debug["STAGE_D_SNAPSHOT"] = stage_d_snapshot
                return screen, debug
            if (
                vp.screen_contains(screen, "TOO LARGE")
                or vp.screen_contains(screen, "SAVE FAIL")
                or vp.screen_contains(screen, "BAD AVO")
                or vp.screen_contains(screen, "LOAD FAIL")
                or vp.screen_contains(screen, "NO OBJECT")
            ):
                debug = collect_debug(client)
                if live_tool_snapshot is not None:
                    debug["LIVE_TOOL_SNAPSHOT"] = live_tool_snapshot
                if stage_b_snapshot is not None:
                    debug["STAGE_B_SNAPSHOT"] = stage_b_snapshot
                if stage_c_snapshot is not None:
                    debug["STAGE_C_SNAPSHOT"] = stage_c_snapshot
                if stage_d_snapshot is not None:
                    debug["STAGE_D_SNAPSHOT"] = stage_d_snapshot
                raise vp.ViceError(
                    f"ALINK terminal failure with screen:\n{screen}\nDEBUG: {json.dumps(debug, indent=2)}"
                )
            if vp.screen_contains(avp.last_nonempty_line(screen), f"B:DNP/{project_name}>"):
                debug = collect_debug(client)
                if live_tool_snapshot is not None:
                    debug["LIVE_TOOL_SNAPSHOT"] = live_tool_snapshot
                if stage_b_snapshot is not None:
                    debug["STAGE_B_SNAPSHOT"] = stage_b_snapshot
                if stage_c_snapshot is not None:
                    debug["STAGE_C_SNAPSHOT"] = stage_c_snapshot
                if stage_d_snapshot is not None:
                    debug["STAGE_D_SNAPSHOT"] = stage_d_snapshot
                return screen, debug
            time.sleep(0.2)
        debug = collect_debug(client)
        if live_tool_snapshot is not None:
            debug["LIVE_TOOL_SNAPSHOT"] = live_tool_snapshot
        if stage_b_snapshot is not None:
            debug["STAGE_B_SNAPSHOT"] = stage_b_snapshot
        if stage_c_snapshot is not None:
            debug["STAGE_C_SNAPSHOT"] = stage_c_snapshot
        if stage_d_snapshot is not None:
            debug["STAGE_D_SNAPSHOT"] = stage_d_snapshot
        raise vp.ViceError(
            f"timed out waiting for final ALINK screen; last screen was:\n{screen}\nDEBUG: {json.dumps(debug, indent=2)}"
        )
    finally:
        try:
            client.quit_emulator()
        finally:
            client.close()
        vp.terminate_process_tree(process)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the seeded runtime-object ALINK probe")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--attempt-delay", type=float, default=2.0)
    parser.add_argument("--connect-delay", type=float)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()
    work_root = fs_root.parent / f"{fs_root.name}-alink-seeded"

    for attempt in range(1, args.attempts + 1):
        connect_delays = (args.connect_delay,) if args.connect_delay is not None else rap.CONNECT_DELAYS
        connect_delay = connect_delays[(attempt - 1) % len(connect_delays)]
        print(
            json.dumps(
                {"attempt": attempt, "attempts": args.attempts, "connect_delay": connect_delay},
                sort_keys=True,
            ),
            file=sys.stderr,
            flush=True,
        )
        try:
            shutil.rmtree(work_root, ignore_errors=True)
            shutil.copytree(fs_root, work_root)
            project_root = prepare_workspace(work_root, project_name)
            vp.cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, args.attempt_delay)))
            screen, debug = run_once(image, work_root, project_name, connect_delay)
            output_path = project_root / "bin" / "main.prg"
            if not output_path.is_file():
                raise vp.ViceError(
                    f"expected host file {output_path} to exist after ALINK returned\n"
                    f"SCREEN:\n{screen}\nDEBUG: {json.dumps(debug, indent=2)}"
                )
            if output_path.stat().st_size <= 2:
                raise vp.ViceError(
                    f"expected direct PRG {output_path} to contain payload bytes after ALINK returned\n"
                    f"SCREEN:\n{screen}\nDEBUG: {json.dumps(debug, indent=2)}"
                )
            print(json.dumps({"screen_tail": screen[-400:], "debug": debug, "output": str(output_path)}, indent=2))
            return 0
        except vp.ViceError as exc:
            print(
                json.dumps(
                    {"attempt": attempt, "connect_delay": connect_delay, "error": str(exc)},
                    sort_keys=True,
                ),
                file=sys.stderr,
                flush=True,
            )
            if attempt == args.attempts:
                print(exc, file=sys.stderr)
                return 1
            time.sleep(args.attempt_delay)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
