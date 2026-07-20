#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import time
from pathlib import Path

import run_action_alink_seeded_runtime_probe as seeded
import run_action_command_probe as avp
import run_action_probe_fs as pfs
import vice_prg_probe as vp


ROOT = Path(__file__).resolve().parent
ACTION_ACTC_BUILD = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "ACTC.PRG"
ACTION_ACTC_CURRENT_LABELS = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "actc.current.labels"
if ACTION_ACTC_BUILD.is_file():
    ACTC_BODY_HEAD = list(ACTION_ACTC_BUILD.read_bytes()[2:34])
else:
    ACTC_BODY_HEAD = []
CONNECT_DELAYS = (10.0,) + tuple(delay for delay in avp.WORKSPACE_CONNECT_DELAYS if delay != 10.0)
ACTC_RESIDENT_DEBUG = (
    ("ACTC_LAST_TRACE", 0x03E7),
    ("RETURN0", 0x03E8),
    ("RETURN1", 0x03E9),
    ("RETURN2", 0x03EA),
    ("RETURN3", 0x03EB),
    ("QUEUE1", 0xCFF1),
    ("QUEUE2", 0xCFF2),
    ("QUEUE3", 0xCFF3),
    ("QUEUE4", 0xCFF4),
    ("REU_COPY0", 0x03E0),
    ("REU_COPY1", 0x03E1),
    ("REU_COPY2", 0x03E2),
    ("REU_COPY3", 0x03E3),
    ("RETURN8", 0x03F0),
    ("RETURN9", 0x03F1),
    ("LAUNCH_STAGE", 0x03F2),
    ("LAUNCH_CODE", 0x03F3),
    ("WRITEBACK_STAGE", 0x03F4),
    ("WRITEBACK_COUNT", 0x03F5),
    ("WRITEBACK_KIND", 0x03F6),
    ("SAVE_STAGE", 0xC59E),
    ("SAVE_OPEN0", 0xC59F),
    ("SAVE_OPEN1", 0xC5A0),
    ("SAVE_OPEN2", 0xC5A1),
    ("SAVE_OPEN3", 0xC5A2),
)
ACTC_SAVE_PATH_ADDR = 0xC5A3
ACTC_SAVE_PATH_LEN = 96
LAUNCH_DRIVE_SNAPSHOT_ADDR = 0xCFFC
LAUNCH_DIR_SNAPSHOT_ADDR = 0xCFFE
TOOL_ABI_OPEN_PATH = 0xCD40
TOOL_ABI_LAUNCH_PATH = 0xCD20
TOOL_WRITEBACK_NAME_MAX = 32
TOOL_WRITEBACK_MAX_RECORDS = 10
TOOL_WRITEBACK_RECORD_SIZE = 71
TOOL_WRITEBACK_COUNT_ADDR = TOOL_ABI_OPEN_PATH + (TOOL_WRITEBACK_MAX_RECORDS * TOOL_WRITEBACK_RECORD_SIZE)
TOOL_WRITEBACK_DIRMAP_ADDR = TOOL_WRITEBACK_COUNT_ADDR + 1
TOOL_WRITEBACK_COUNT_SHADOW_ADDR = 0x03E6
TOOL_STREAM_SHADOW_BUF_ADDR = 0xCDD0
VICE_DIR_DYNAMIC_MAX = 6
VICE_DIR_NAME_STRIDE = 21
VICE_TREE_DYNAMIC_MAX = 6
HW_DIR_CACHE_MAX = 6


write_ascii = pfs.write_ascii
ensure_catalog_entries = pfs.ensure_catalog_entries
case_insensitive_child = pfs.case_insensitive_child
detect_lowercase_workspace = pfs.detect_lowercase_workspace
host_name = pfs.host_name
sync_case_siblings = pfs.sync_case_siblings
project_output_path = pfs.project_output_path
ensure_relative_symlink = pfs.ensure_relative_symlink


def log_progress(verbose: bool, payload: dict[str, object]) -> None:
    if verbose:
        print(payload, flush=True)


def source_text() -> str:
    return (
        'MODULE MAIN\r'
        'CARD X\r'
        'PROC MAIN()\r'
        'PrintE("HELLO")\r'
        'W()\r'
        'X=50\r'
        'X=X + 7 - 3\r'
        'PrintI(X)\r'
        'X=60\r'
        'X=X - 3 + 2\r'
        'PrintIE(X)\r'
        'RETURN\r'
    )


def prepare_workspace(fs_root: Path, project_name: str) -> Path:
    lowercase_workspace = detect_lowercase_workspace(fs_root)
    images_root = case_insensitive_child(fs_root, host_name("IMAGES", lowercase_workspace))
    action_root = case_insensitive_child(images_root, host_name("ACTION.DNP", lowercase_workspace))
    project_root = action_root / project_name.upper()
    lower_project_root = project_root.parent / project_root.name.lower()
    shutil.rmtree(project_root, ignore_errors=True)
    shutil.rmtree(lower_project_root, ignore_errors=True)
    src_root = project_root / "src"
    project_bin_root = project_root / "bin"
    obj_root = project_root / "obj"
    src_root.mkdir(parents=True, exist_ok=True)
    project_bin_root.mkdir(exist_ok=True)
    obj_root.mkdir(exist_ok=True)
    ensure_relative_symlink(project_root / "SRC", "src", is_dir=True)
    ensure_relative_symlink(project_root / "BIN", "bin", is_dir=True)
    ensure_relative_symlink(project_root / "OBJ", "obj", is_dir=True)

    write_ascii(project_root / "readme.txt", "ACTION PROJECT READY\n", sync_case=False)
    ensure_relative_symlink(project_root / "README.TXT", "readme.txt")
    write_ascii(project_root / "action.proj", "ACTION PROJECT\rMAIN.ACT\r", sync_case=False)
    ensure_relative_symlink(project_root / "ACTION.PROJ", "action.proj")
    write_ascii(
        project_root / "UDOSDIR.TXT",
        "D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF README.TXT\n",
        sync_case=False,
    )
    ensure_relative_symlink(project_root / "udosdir.txt", "UDOSDIR.TXT")
    write_ascii(src_root / "UDOSDIR.TXT", "F MAIN.ACT\n", sync_case=False)
    ensure_relative_symlink(src_root / "udosdir.txt", "UDOSDIR.TXT")
    write_ascii(project_bin_root / "UDOSDIR.TXT", "", sync_case=False)
    ensure_relative_symlink(project_bin_root / "udosdir.txt", "UDOSDIR.TXT")
    write_ascii(obj_root / "UDOSDIR.TXT", "", sync_case=False)
    ensure_relative_symlink(obj_root / "udosdir.txt", "UDOSDIR.TXT")
    write_ascii(src_root / "main.act", source_text(), sync_case=False)
    ensure_relative_symlink(src_root / "MAIN.ACT", "main.act")

    if ACTION_ACTC_BUILD.is_file():
        root_target = action_root / host_name("ACTC.PRG", lowercase_workspace)
        shutil.copy2(ACTION_ACTC_BUILD, root_target)
        sync_case_siblings(root_target)
        ensure_catalog_entries(action_root / host_name("UDOSDIR.TXT", lowercase_workspace), [f"D {project_name.upper()}", "F ACTC.PRG"])

    if lower_project_root != project_root and not lower_project_root.exists():
        lower_project_root.symlink_to(project_root.name, target_is_directory=True)
    return project_root


def verify_host_output(project_root: Path) -> None:
    output_path = project_output_path(project_root, "OBJ", "MAIN.OBJ")
    if not output_path.is_file():
        raise RuntimeError(f"expected host file {output_path} to exist")
    text = output_path.read_text(encoding="ascii", errors="ignore")
    required = [
        "OBJ1",
        "x main 0 272",
        "x __idata 262 8",
        "x __iptr 270 2",
        "b u0u1M",
        "u w",
        "u rt_print_i",
        "m A2 00 BD 00 00 85 06 E8 BD 00 00 85 07 ",
        "68 18 65 04 48 A5 03 65 05 48",
        "68 38 E5 04 48 A5 03 E5 05 48",
        "A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF",
        "r 3 x __iptr\nr 9 x __iptr\nr 35 u0\nr 137 u1\nr 239 u1\nr 270 x __idata",
        "s HELLO",
        "v x 0",
        "n main",
    ]
    missing = [fragment for fragment in required if fragment not in text]
    if missing:
        raise RuntimeError(f"expected host object {output_path} to contain {missing!r}")


def verify_output_catalog(project_root: Path) -> None:
    obj_root = case_insensitive_child(project_root, "OBJ")
    catalog_path = case_insensitive_child(obj_root, "UDOSDIR.TXT")
    if not catalog_path.is_file():
        raise RuntimeError(f"expected object catalog {catalog_path} to exist")
    catalog_text = catalog_path.read_text(encoding="ascii", errors="ignore")
    if catalog_text != "F MAIN.OBJ\n":
        raise RuntimeError(
            f"expected object catalog {catalog_path} to equal F MAIN.OBJ\\n, "
            f"got {catalog_text!r}"
        )


def verify_project_output(project_root: Path) -> None:
    verify_host_output(project_root)
    verify_output_catalog(project_root)


def wait_for_project_output(project_root: Path, timeout: float, poll_interval: float = 0.2) -> None:
    deadline = time.monotonic() + timeout
    last_error: RuntimeError | None = None
    while time.monotonic() < deadline:
        try:
            verify_project_output(project_root)
            return
        except RuntimeError as exc:
            last_error = exc
            time.sleep(poll_interval)
    if last_error is not None:
        raise last_error
    raise RuntimeError("timed out waiting for ACTC project output")


def read_cstr(client: vp.BinaryMonitorClient, addr: int, limit: int) -> str:
    data = client.memory_get(addr, addr + limit - 1)
    out = bytearray()
    for value in data:
        if value == 0:
            break
        out.append(value)
    return out.decode("ascii", errors="replace")


def printable_byte(value: int) -> str | None:
    if 32 <= value <= 126:
        return chr(value)
    return None


def load_selected_actc_labels() -> dict[str, int]:
    wanted = {
        "save_params",
        "file_params",
        "target_path",
        "content_buffer",
        "body_ops_data",
        "source_buffer",
        "actc_trace_byte",
        "debug_fail_ptr_lo",
        "debug_fail_ptr_hi",
        "manifest_buffer",
        "manifest_entry",
        "msg_no_project",
        "msg_load_fail",
        "msg_no_file",
    }
    out: dict[str, int] = {}
    if not ACTION_ACTC_CURRENT_LABELS.is_file():
        return out
    for line in ACTION_ACTC_CURRENT_LABELS.read_text(encoding="utf-8", errors="replace").splitlines():
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


def read_actc_trace(client: vp.BinaryMonitorClient) -> str:
    try:
        debug = vp.format_debug_snapshot(vp.read_debug_bytes(client, ACTC_RESIDENT_DEBUG))
        raw = client.memory_get(ACTC_SAVE_PATH_ADDR, ACTC_SAVE_PATH_ADDR + ACTC_SAVE_PATH_LEN - 1)
        path = bytes(raw).split(b"\x00", 1)[0].decode("ascii", errors="replace")
        labels = load_selected_actc_labels()
        resident_labels = seeded.load_selected_resident_labels()
        extras: list[str] = []
        save_params_addr = labels.get("save_params")
        if save_params_addr is not None:
            save_params = list(client.memory_get(save_params_addr, save_params_addr + 6))
            extras.append(f"SAVE_PARAMS={save_params!r}")
        target_path_addr = labels.get("target_path")
        if target_path_addr is not None:
            extras.append(f"TARGET_PATH={read_cstr(client, target_path_addr, 64)!r}")
        content_buffer_addr = labels.get("content_buffer")
        if content_buffer_addr is not None:
            content_head = bytes(client.memory_get(content_buffer_addr, content_buffer_addr + 15)).hex()
            extras.append(f"CONTENT_HEAD={content_head}")
        body_ops_addr = labels.get("body_ops_data")
        if body_ops_addr is not None:
            extras.append(f"BODY_OPS={read_cstr(client, body_ops_addr, 32)!r}")
        source_fullpath_addr = resident_labels.get("source_fullpath_buffer")
        if source_fullpath_addr is not None:
            extras.append(f"SOURCE_FULLPATH={read_cstr(client, source_fullpath_addr, 96)!r}")
        program_image_buffer_addr = resident_labels.get("program_image_buffer")
        if program_image_buffer_addr is not None:
            extras.append(
                f"PROGRAM_IMAGE_HEAD={list(client.memory_get(program_image_buffer_addr, program_image_buffer_addr + 7))!r}"
            )
        launch_load_cache_lo_addr = resident_labels.get("launch_load_cache_lo")
        launch_load_cache_hi_addr = resident_labels.get("launch_load_cache_hi")
        if launch_load_cache_lo_addr is not None and launch_load_cache_hi_addr is not None:
            launch_load_cache = list(
                client.memory_get(launch_load_cache_lo_addr, launch_load_cache_hi_addr)
            )
            extras.append(f"LAUNCH_LOAD_CACHE={launch_load_cache!r}")
            if len(launch_load_cache) == 2:
                load_addr = launch_load_cache[0] | (launch_load_cache[1] << 8)
                extras.append(f"PROGRAM_RAM_HEAD={list(client.memory_get(load_addr, load_addr + 31))!r}")
        vice_read_length_addr = resident_labels.get("vice_read_length")
        if vice_read_length_addr is not None:
            extras.append(f"VICE_READ_LENGTH={client.memory_get(vice_read_length_addr, vice_read_length_addr)[0]!r}")
        program_image_len_lo_addr = resident_labels.get("program_image_len_lo")
        program_image_len_hi_addr = resident_labels.get("program_image_len_hi")
        if program_image_len_lo_addr is not None and program_image_len_hi_addr is not None:
            program_image_len = list(
                client.memory_get(program_image_len_lo_addr, program_image_len_hi_addr)
            )
            extras.append(f"PROGRAM_IMAGE_LEN_STATE={program_image_len!r}")
        path_name_addr = resident_labels.get("path_name_buffer")
        if path_name_addr is not None:
            extras.append(f"PATH_NAME_BUFFER={read_cstr(client, path_name_addr, 64)!r}")
        arg_buffer_addr = resident_labels.get("arg_buffer")
        if arg_buffer_addr is not None:
            extras.append(f"ARG_BUFFER={read_cstr(client, arg_buffer_addr, 64)!r}")
        debug_path_addr = resident_labels.get("save_debug_write_path_buffer")
        if debug_path_addr is not None:
            extras.append(f"SAVE_DEBUG_PATH={read_cstr(client, debug_path_addr, 96)!r}")
        desired_path_addr = resident_labels.get("desired_path_buffer")
        if desired_path_addr is not None:
            extras.append(f"DESIRED_PATH={read_cstr(client, desired_path_addr, 96)!r}")
        dest_fullpath_addr = resident_labels.get("dest_fullpath_buffer")
        if dest_fullpath_addr is not None:
            extras.append(f"DEST_FULLPATH={read_cstr(client, dest_fullpath_addr, 96)!r}")
        extras.append(f"STREAM_SHADOW={read_cstr(client, TOOL_STREAM_SHADOW_BUF_ADDR, 64)!r}")
        extras.append(f"STREAM_SHADOW_HEAD={list(client.memory_get(TOOL_STREAM_SHADOW_BUF_ADDR, TOOL_STREAM_SHADOW_BUF_ADDR + 31))!r}")
        extras.append(f"CURRENT_PATH={read_cstr(client, 0xCD00, 64)!r}")
        extras.append(f"LAUNCH_PATH={read_cstr(client, TOOL_ABI_LAUNCH_PATH, 64)!r}")
        extras.append(f"OPEN_PATH={read_cstr(client, 0xCD40, 96)!r}")
        extras.append(f"C64_PORT={client.memory_get(0x0001, 0x0001)[0]!r}")
        extras.append(f"PROGRAM_DRIVE_SNAPSHOT={client.memory_get(0xCFF8, 0xCFF8)[0]!r}")
        extras.append(f"PROGRAM_DIR_SNAPSHOT={client.memory_get(0xCFF9, 0xCFF9)[0]!r}")
        extras.append(
            f"LAUNCH_DRIVE_SNAPSHOT={client.memory_get(LAUNCH_DRIVE_SNAPSHOT_ADDR, LAUNCH_DRIVE_SNAPSHOT_ADDR)[0]!r}"
        )
        extras.append(
            f"LAUNCH_DIR_SNAPSHOT={client.memory_get(LAUNCH_DIR_SNAPSHOT_ADDR, LAUNCH_DIR_SNAPSHOT_ADDR)[0]!r}"
        )
        extras.append(f"LAUNCH_PATH_TRACE={list(client.memory_get(0x03F7, 0x03FA))!r}")
        extras.append(f"PROGRAM_IMAGE_LEN={list(client.memory_get(0xCFFA, 0xCFFB))!r}")
        extras.append(f"TOOL_ABI_FILE_BLOCK={list(client.memory_get(0xCDC6, 0xCDCB))!r}")
        extras.append(f"ACTC_LAST_TRACE={client.memory_get(0x03E7, 0x03E7)[0]!r}")
        return_trace = list(client.memory_get(0x03E8, 0x03EF))
        extras.append(f"RETURN_TRACE={return_trace!r}")
        name_head = bytes(return_trace[4:8]).split(b"\x00", 1)[0].decode("ascii", errors="replace")
        extras.append(f"TRACE_NAME_HEAD={name_head!r}")
        extras.append(f"TRACE_DRIVE={return_trace[0]!r}")
        extras.append(f"TRACE_LFN={return_trace[1]!r}")
        extras.append(f"TRACE_SA={return_trace[2]!r}")
        extras.append(f"TRACE_PHASE={return_trace[3]!r}")
        extras.append(f"TRACE_OPEN_STAGE={client.memory_get(0x03FE, 0x03FE)[0]!r}")
        extras.append(f"TRACE_OPEN_STATUS={client.memory_get(0x03FF, 0x03FF)[0]!r}")
        save_stage = client.memory_get(0xC59E, 0xC59E)[0]
        save_stage_char = printable_byte(save_stage)
        if save_stage_char is not None:
            extras.append(f"SAVE_STAGE_CHAR={save_stage_char!r}")
        tool_status = client.memory_get(0xCDC1, 0xCDC1)[0]
        tool_status_char = printable_byte(tool_status)
        if tool_status_char is not None:
            extras.append(f"TOOL_FILE_STAGE={tool_status_char!r}")
        extras.append(f"REGISTERS={client.registers_get()!r}")
        suffix = f" {' '.join(extras)}" if extras else ""
        return f"{debug} SAVE_PATH={path!r}{suffix}"
    except Exception:
        return "ACTC_TRACE=<unavailable>"


def collect_actc_debug(client: vp.BinaryMonitorClient) -> dict[str, object]:
    data: dict[str, object] = {}
    labels = load_selected_actc_labels()
    resident_labels = seeded.load_selected_resident_labels()
    try:
        data["REGISTERS"] = client.registers_get()
        registers = data["REGISTERS"]
        if isinstance(registers, dict) and "PC" in registers:
            pc = int(registers["PC"]) & 0xFFFF
            start = max(0, pc - 8)
            end = min(0xFFFF, pc + 23)
            data["PC_WINDOW_ADDR"] = start
            data["PC_WINDOW"] = list(client.memory_get(start, end))
        if isinstance(registers, dict) and "SP" in registers:
            sp = int(registers["SP"]) & 0xFF
            stack_start = 0x0100 + ((sp + 1) & 0xFF)
            stack_end = min(0x01FF, stack_start + 15)
            data["STACK_WINDOW"] = list(client.memory_get(stack_start, stack_end))
            data["STACK_WINDOW_ADDR"] = stack_start
        data["LAUNCH_STUB_ZP"] = list(client.memory_get(0x00F6, 0x00FE))
    except Exception as exc:
        data["REGISTERS"] = f"ERR:{exc!r}"
        data["PC_WINDOW"] = f"ERR:{exc!r}"
        data["PC_WINDOW_ADDR"] = f"ERR:{exc!r}"
        data["STACK_WINDOW"] = f"ERR:{exc!r}"
        data["STACK_WINDOW_ADDR"] = f"ERR:{exc!r}"
        data["LAUNCH_STUB_ZP"] = f"ERR:{exc!r}"
    try:
        data["C64_PORT"] = client.memory_get(0x0001, 0x0001)[0]
        data["ACTC_LAST_TRACE"] = client.memory_get(0x03E7, 0x03E7)[0]
        actc_trace_addr = labels.get("actc_trace_byte")
        if actc_trace_addr is not None:
            data["ACTC_TRACE"] = client.memory_get(actc_trace_addr, actc_trace_addr)[0]
        else:
            data["ACTC_TRACE"] = "<missing>"
        data["LAUNCH_STAGE"] = client.memory_get(0x03F2, 0x03F2)[0]
        data["LAUNCH_CODE"] = client.memory_get(0x03F3, 0x03F3)[0]
        data["WRITEBACK_STAGE"] = client.memory_get(0x03F4, 0x03F4)[0]
        data["WRITEBACK_COUNT"] = client.memory_get(0x03F5, 0x03F5)[0]
        data["WRITEBACK_KIND"] = client.memory_get(0x03F6, 0x03F6)[0]
        data["STREAM_SHADOW"] = read_cstr(client, TOOL_STREAM_SHADOW_BUF_ADDR, 64)
        data["STREAM_SHADOW_HEAD"] = list(
            client.memory_get(TOOL_STREAM_SHADOW_BUF_ADDR, TOOL_STREAM_SHADOW_BUF_ADDR + 31)
        )
        data["QUEUE1"] = client.memory_get(0xCFF1, 0xCFF1)[0]
        data["QUEUE2"] = client.memory_get(0xCFF2, 0xCFF2)[0]
        data["QUEUE3"] = client.memory_get(0xCFF3, 0xCFF3)[0]
        data["QUEUE4"] = client.memory_get(0xCFF4, 0xCFF4)[0]
        data["SAVE_STAGE"] = client.memory_get(0xC59E, 0xC59E)[0]
        save_stage_char = printable_byte(data["SAVE_STAGE"])
        if save_stage_char is not None:
            data["SAVE_STAGE_CHAR"] = save_stage_char
        data["SAVE_OPEN0"] = client.memory_get(0xC59F, 0xC59F)[0]
        data["SAVE_OPEN1"] = client.memory_get(0xC5A0, 0xC5A0)[0]
        data["SAVE_OPEN2"] = client.memory_get(0xC5A1, 0xC5A1)[0]
        data["SAVE_OPEN3"] = client.memory_get(0xC5A2, 0xC5A2)[0]
        data["PROGRAM_STATE_SNAPSHOT"] = client.memory_get(0xCFF6, 0xCFF6)[0]
        data["PROGRAM_EXIT_SNAPSHOT"] = client.memory_get(0xCFF7, 0xCFF7)[0]
        data["LAUNCH_RESULT_FLAG"] = client.memory_get(0x03F0, 0x03F0)[0]
        data["LAUNCH_EXIT_STATUS"] = client.memory_get(0x03F1, 0x03F1)[0]
        data["STAGE_SNAPSHOT"] = client.memory_get(0xCFFD, 0xCFFD)[0]
        data["RETURN_TRACE"] = list(client.memory_get(0x03E8, 0x03EF))
        fail_ptr_lo_addr = labels.get("debug_fail_ptr_lo")
        fail_ptr_hi_addr = labels.get("debug_fail_ptr_hi")
        if fail_ptr_lo_addr is not None and fail_ptr_hi_addr is not None:
            fail_ptr_lo = client.memory_get(fail_ptr_lo_addr, fail_ptr_lo_addr)[0]
            fail_ptr_hi = client.memory_get(fail_ptr_hi_addr, fail_ptr_hi_addr)[0]
            fail_ptr = fail_ptr_lo | (fail_ptr_hi << 8)
            data["FAIL_PTR"] = fail_ptr
            if fail_ptr:
                data["FAIL_PTR_STR"] = read_cstr(client, fail_ptr, 32)
    except Exception as exc:
        data["C64_PORT"] = f"ERR:{exc!r}"
        data["ACTC_TRACE"] = f"ERR:{exc!r}"
        data["LAUNCH_STAGE"] = f"ERR:{exc!r}"
        data["LAUNCH_CODE"] = f"ERR:{exc!r}"
        data["WRITEBACK_STAGE"] = f"ERR:{exc!r}"
        data["WRITEBACK_COUNT"] = f"ERR:{exc!r}"
        data["WRITEBACK_KIND"] = f"ERR:{exc!r}"
        data["STREAM_SHADOW"] = f"ERR:{exc!r}"
        data["STREAM_SHADOW_HEAD"] = f"ERR:{exc!r}"
        data["QUEUE4"] = f"ERR:{exc!r}"
        data["SAVE_STAGE"] = f"ERR:{exc!r}"
        data["SAVE_OPEN0"] = f"ERR:{exc!r}"
        data["SAVE_OPEN1"] = f"ERR:{exc!r}"
        data["SAVE_OPEN2"] = f"ERR:{exc!r}"
        data["SAVE_OPEN3"] = f"ERR:{exc!r}"
        data["PROGRAM_STATE_SNAPSHOT"] = f"ERR:{exc!r}"
        data["PROGRAM_EXIT_SNAPSHOT"] = f"ERR:{exc!r}"
        data["LAUNCH_RESULT_FLAG"] = f"ERR:{exc!r}"
        data["LAUNCH_EXIT_STATUS"] = f"ERR:{exc!r}"
        data["STAGE_SNAPSHOT"] = f"ERR:{exc!r}"
        data["RETURN_TRACE"] = f"ERR:{exc!r}"
        data["FAIL_PTR"] = f"ERR:{exc!r}"
        data["FAIL_PTR_STR"] = f"ERR:{exc!r}"
    try:
        file_params_addr = labels.get("file_params") or labels.get("save_params")
        if file_params_addr is not None:
            params = list(client.memory_get(file_params_addr, file_params_addr + 8))
            data["ACTC_FILE_PARAMS"] = params
            name_addr = params[0] | (params[1] << 8)
            dest_addr = params[2] | (params[3] << 8)
            data["ACTC_FILE_NAME"] = read_cstr(client, name_addr, 64)
            data["ACTC_FILE_DEST_HEAD"] = list(client.memory_get(dest_addr, dest_addr + 31))
        manifest_buffer_addr = labels.get("manifest_buffer")
        if manifest_buffer_addr is not None:
            data["MANIFEST_BUFFER"] = read_cstr(client, manifest_buffer_addr, 96)
            data["MANIFEST_BUFFER_HEAD"] = list(client.memory_get(manifest_buffer_addr, manifest_buffer_addr + 31))
        source_buffer_addr = labels.get("source_buffer")
        if source_buffer_addr is not None:
            data["SOURCE_BUFFER"] = read_cstr(client, source_buffer_addr, 128)
            data["SOURCE_BUFFER_HEAD"] = list(client.memory_get(source_buffer_addr, source_buffer_addr + 31))
        target_path_addr = labels.get("target_path")
        if target_path_addr is not None:
            data["TARGET_PATH"] = read_cstr(client, target_path_addr, 64)
            data["TARGET_PATH_HEAD"] = list(client.memory_get(target_path_addr, target_path_addr + 31))
        content_buffer_addr = labels.get("content_buffer")
        if content_buffer_addr is not None:
            data["CONTENT_BUFFER_HEAD"] = list(client.memory_get(content_buffer_addr, content_buffer_addr + 31))
        manifest_entry_addr = labels.get("manifest_entry")
        if manifest_entry_addr is not None:
            data["MANIFEST_ENTRY"] = read_cstr(client, manifest_entry_addr, 32)
    except Exception as exc:
        data["ACTC_FILE_PARAMS"] = f"ERR:{exc!r}"
        data["ACTC_FILE_NAME"] = f"ERR:{exc!r}"
        data["ACTC_FILE_DEST_HEAD"] = f"ERR:{exc!r}"
        data["MANIFEST_BUFFER"] = f"ERR:{exc!r}"
        data["MANIFEST_BUFFER_HEAD"] = f"ERR:{exc!r}"
        data["SOURCE_BUFFER"] = f"ERR:{exc!r}"
        data["SOURCE_BUFFER_HEAD"] = f"ERR:{exc!r}"
        data["TARGET_PATH"] = f"ERR:{exc!r}"
        data["TARGET_PATH_HEAD"] = f"ERR:{exc!r}"
        data["CONTENT_BUFFER_HEAD"] = f"ERR:{exc!r}"
        data["MANIFEST_ENTRY"] = f"ERR:{exc!r}"
    try:
        data["TOOL_ABI_FILE_STATUS"] = client.memory_get(0xCDC1, 0xCDC1)[0]
        tool_status_char = printable_byte(data["TOOL_ABI_FILE_STATUS"])
        if tool_status_char is not None:
            data["TOOL_ABI_FILE_STATUS_CHAR"] = tool_status_char
        data["TOOL_ABI_FILE_REMAIN"] = list(client.memory_get(0xCDC2, 0xCDC3))
        data["TOOL_ABI_FILE_LEN"] = list(client.memory_get(0xCDC4, 0xCDC5))
        data["CURRENT_PATH"] = read_cstr(client, 0xCD00, 64)
        data["LAUNCH_PATH"] = read_cstr(client, TOOL_ABI_LAUNCH_PATH, 64)
        data["OPEN_PATH"] = read_cstr(client, 0xCD40, 96)
        data["STREAM_SHADOW"] = read_cstr(client, TOOL_STREAM_SHADOW_BUF_ADDR, 64)
        data["STREAM_SHADOW_HEAD"] = list(
            client.memory_get(TOOL_STREAM_SHADOW_BUF_ADDR, TOOL_STREAM_SHADOW_BUF_ADDR + 31)
        )
        stream_lo_addr = resident_labels.get("tool_abi_stream_name_lo")
        stream_hi_addr = resident_labels.get("tool_abi_stream_name_hi")
        if stream_lo_addr is not None and stream_hi_addr is not None:
            stream_lo = client.memory_get(stream_lo_addr, stream_lo_addr)[0]
            stream_hi = client.memory_get(stream_hi_addr, stream_hi_addr)[0]
            stream_addr = stream_lo | (stream_hi << 8)
            data["TOOL_STREAM_NAME_PTR"] = stream_addr
            if stream_addr:
                data["TOOL_STREAM_NAME_PTR_STR"] = read_cstr(client, stream_addr, 64)
        desired_path_addr = resident_labels.get("desired_path_buffer")
        if desired_path_addr is not None:
            data["DESIRED_PATH"] = read_cstr(client, desired_path_addr, 96)
        dest_fullpath_addr = resident_labels.get("dest_fullpath_buffer")
        if dest_fullpath_addr is not None:
            data["DEST_FULLPATH"] = read_cstr(client, dest_fullpath_addr, 96)
    except Exception as exc:
        data["TOOL_ABI_FILE_STATUS"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_STATUS_CHAR"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_REMAIN"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_LEN"] = f"ERR:{exc!r}"
        data["CURRENT_PATH"] = f"ERR:{exc!r}"
        data["OPEN_PATH"] = f"ERR:{exc!r}"
        data["STREAM_SHADOW"] = f"ERR:{exc!r}"
        data["STREAM_SHADOW_HEAD"] = f"ERR:{exc!r}"
        data["TOOL_STREAM_NAME_PTR"] = f"ERR:{exc!r}"
        data["TOOL_STREAM_NAME_PTR_STR"] = f"ERR:{exc!r}"
        data["DESIRED_PATH"] = f"ERR:{exc!r}"
        data["DEST_FULLPATH"] = f"ERR:{exc!r}"
    try:
        data["PROGRAM_DRIVE_SNAPSHOT"] = client.memory_get(0xCFF8, 0xCFF8)[0]
        data["PROGRAM_DIR_SNAPSHOT"] = client.memory_get(0xCFF9, 0xCFF9)[0]
        data["LAUNCH_DRIVE_SNAPSHOT"] = client.memory_get(
            LAUNCH_DRIVE_SNAPSHOT_ADDR, LAUNCH_DRIVE_SNAPSHOT_ADDR
        )[0]
        data["LAUNCH_DIR_SNAPSHOT"] = client.memory_get(
            LAUNCH_DIR_SNAPSHOT_ADDR, LAUNCH_DIR_SNAPSHOT_ADDR
        )[0]
    except Exception as exc:
        data["PROGRAM_DRIVE_SNAPSHOT"] = f"ERR:{exc!r}"
        data["PROGRAM_DIR_SNAPSHOT"] = f"ERR:{exc!r}"
        data["LAUNCH_DRIVE_SNAPSHOT"] = f"ERR:{exc!r}"
        data["LAUNCH_DIR_SNAPSHOT"] = f"ERR:{exc!r}"
    try:
        data["TOOL_FIXED_WRITE_CHUNK"] = list(client.memory_get(0xCF30, 0xCF38))
        data["TOOL_FIXED_REU"] = list(client.memory_get(0xCF39, 0xCF3E))
        for label in (
            "tool_abi_fixed_template",
            "tool_abi_file_write_chunk_sc0",
            "tool_abi_file_write_chunk_current",
        ):
            addr = resident_labels.get(label)
            if addr is not None:
                data[label.upper()] = list(client.memory_get(addr, addr + 31))
    except Exception as exc:
        data["TOOL_FIXED_WRITE_CHUNK"] = f"ERR:{exc!r}"
    for name in ("current_drive", "temp_drive"):
        addr = resident_labels.get(name)
        if addr is None:
            continue
        try:
            data[name.upper()] = client.memory_get(addr, addr)[0]
        except Exception as exc:
            data[name.upper()] = f"ERR:{exc!r}"
    source_fullpath_addr = resident_labels.get("source_fullpath_buffer")
    if source_fullpath_addr is not None:
        try:
            data["SOURCE_FULLPATH"] = read_cstr(client, source_fullpath_addr, 96)
        except Exception as exc:
            data["SOURCE_FULLPATH"] = f"ERR:{exc!r}"
    try:
        data["MEM_0900"] = list(client.memory_get(0x0900, 0x091f))
        data["MEM_0801"] = list(client.memory_get(0x0801, 0x0810))
    except Exception as exc:
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
        except Exception as exc:
            data["LAUNCH_LOAD_CACHE"] = f"ERR:{exc!r}"
            data["PROGRAM_RAM_HEAD"] = f"ERR:{exc!r}"
    try:
        ptr_lo, ptr_hi = client.memory_get(0x00FB, 0x00FC)
        screen_ptr_lo, screen_ptr_hi = client.memory_get(0x00F9, 0x00FA)
        ptr_addr = ptr_lo | (ptr_hi << 8)
        screen_ptr_addr = screen_ptr_lo | (screen_ptr_hi << 8)
        data["PTR"] = ptr_addr
        data["SCREEN_PTR"] = screen_ptr_addr
        if ptr_addr:
            data["PTR_STR"] = read_cstr(client, ptr_addr, 96)
        if screen_ptr_addr:
            data["SCREEN_PTR_STR"] = read_cstr(client, screen_ptr_addr, 96)
    except Exception as exc:
        data["PTR"] = f"ERR:{exc!r}"
        data["SCREEN_PTR"] = f"ERR:{exc!r}"
        data["PTR_STR"] = f"ERR:{exc!r}"
        data["SCREEN_PTR_STR"] = f"ERR:{exc!r}"
    debug_path_addr = resident_labels.get("save_debug_write_path_buffer")
    if debug_path_addr is not None:
        try:
            data["SAVE_DEBUG_PATH"] = read_cstr(client, debug_path_addr, 96)
        except Exception as exc:
            data["SAVE_DEBUG_PATH"] = f"ERR:{exc!r}"
    try:
        data["TOOL_WRITEBACK_COUNT_SHADOW"] = client.memory_get(
            TOOL_WRITEBACK_COUNT_SHADOW_ADDR, TOOL_WRITEBACK_COUNT_SHADOW_ADDR
        )[0]
        data["TOOL_WRITEBACK_COUNT"] = client.memory_get(TOOL_WRITEBACK_COUNT_ADDR, TOOL_WRITEBACK_COUNT_ADDR)[0]
        data["TOOL_WRITEBACK_DIRMAP"] = list(
            client.memory_get(TOOL_WRITEBACK_DIRMAP_ADDR, TOOL_WRITEBACK_DIRMAP_ADDR + VICE_DIR_DYNAMIC_MAX - 1)
        )
        record = list(client.memory_get(TOOL_ABI_OPEN_PATH, TOOL_ABI_OPEN_PATH + TOOL_WRITEBACK_RECORD_SIZE - 1))
        data["TOOL_WRITEBACK_RECORD_HEAD"] = record[:16]
        data["TOOL_WRITEBACK_KIND"] = record[0]
        data["TOOL_WRITEBACK_SLOT"] = record[1]
        data["TOOL_WRITEBACK_DRIVE"] = record[2]
        data["TOOL_WRITEBACK_DIR"] = record[3]
        data["TOOL_WRITEBACK_STATE"] = record[4]
        name_raw = bytes(record[5 : 5 + TOOL_WRITEBACK_NAME_MAX]).split(b"\x00", 1)[0]
        data["TOOL_WRITEBACK_NAME"] = name_raw.decode("ascii", errors="replace")
        second_name_start = 39
        second_name_raw = bytes(record[second_name_start : second_name_start + TOOL_WRITEBACK_NAME_MAX]).split(
            b"\x00", 1
        )[0]
        data["TOOL_WRITEBACK_SECOND_NAME"] = second_name_raw.decode("ascii", errors="replace")
    except Exception as exc:
        data["TOOL_WRITEBACK_COUNT_SHADOW"] = f"ERR:{exc!r}"
        data["TOOL_WRITEBACK_COUNT"] = f"ERR:{exc!r}"
        data["TOOL_WRITEBACK_DIRMAP"] = f"ERR:{exc!r}"
        data["TOOL_WRITEBACK_RECORD_HEAD"] = f"ERR:{exc!r}"
        data["TOOL_WRITEBACK_KIND"] = f"ERR:{exc!r}"
        data["TOOL_WRITEBACK_SLOT"] = f"ERR:{exc!r}"
        data["TOOL_WRITEBACK_DRIVE"] = f"ERR:{exc!r}"
        data["TOOL_WRITEBACK_DIR"] = f"ERR:{exc!r}"
        data["TOOL_WRITEBACK_STATE"] = f"ERR:{exc!r}"
        data["TOOL_WRITEBACK_NAME"] = f"ERR:{exc!r}"
        data["TOOL_WRITEBACK_SECOND_NAME"] = f"ERR:{exc!r}"
    base = resident_labels.get("vice_dir_state_b")
    if base is not None:
        try:
            data["VICE_DIR_STATE_B"] = list(client.memory_get(base, base + VICE_DIR_DYNAMIC_MAX - 1))
        except Exception as exc:
            data["VICE_DIR_STATE_B"] = f"ERR:{exc!r}"
    base = resident_labels.get("vice_dir_parent_b")
    if base is not None:
        try:
            data["VICE_DIR_PARENT_B"] = list(client.memory_get(base, base + VICE_DIR_DYNAMIC_MAX - 1))
        except Exception as exc:
            data["VICE_DIR_PARENT_B"] = f"ERR:{exc!r}"
    base = resident_labels.get("vice_dir_names_b")
    if base is not None:
        try:
            data["VICE_DIR_NAMES_B"] = [
                read_cstr(client, base + (VICE_DIR_NAME_STRIDE * index), VICE_DIR_NAME_STRIDE)
                for index in range(VICE_DIR_DYNAMIC_MAX)
            ]
        except Exception as exc:
            data["VICE_DIR_NAMES_B"] = f"ERR:{exc!r}"
    base = resident_labels.get("vice_tree_state_b")
    if base is not None:
        try:
            data["VICE_TREE_STATE_B"] = list(client.memory_get(base, base + VICE_TREE_DYNAMIC_MAX - 1))
        except Exception as exc:
            data["VICE_TREE_STATE_B"] = f"ERR:{exc!r}"
    base = resident_labels.get("vice_tree_dir_b")
    if base is not None:
        try:
            data["VICE_TREE_DIR_B"] = list(client.memory_get(base, base + VICE_TREE_DYNAMIC_MAX - 1))
        except Exception as exc:
            data["VICE_TREE_DIR_B"] = f"ERR:{exc!r}"
    base = resident_labels.get("vice_tree_names_b")
    if base is not None:
        try:
            data["VICE_TREE_NAMES_B"] = [
                read_cstr(client, base + (VICE_DIR_NAME_STRIDE * index), VICE_DIR_NAME_STRIDE)
                for index in range(VICE_TREE_DYNAMIC_MAX)
            ]
        except Exception as exc:
            data["VICE_TREE_NAMES_B"] = f"ERR:{exc!r}"
    base = resident_labels.get("hw_dir_count_table")
    if base is not None:
        try:
            data["HW_DIR_COUNT_TABLE"] = list(client.memory_get(base, base + 1))
        except Exception as exc:
            data["HW_DIR_COUNT_TABLE"] = f"ERR:{exc!r}"
    base = resident_labels.get("hw_dir_names_b")
    if base is not None:
        try:
            data["HW_DIR_NAMES_B"] = [
                read_cstr(client, base + (VICE_DIR_NAME_STRIDE * index), VICE_DIR_NAME_STRIDE)
                for index in range(HW_DIR_CACHE_MAX)
            ]
        except Exception as exc:
            data["HW_DIR_NAMES_B"] = f"ERR:{exc!r}"
    base = resident_labels.get("flat_dir_sector_buffer")
    if base is not None:
        try:
            data["FLAT_DIR_SECTOR_BUFFER"] = read_cstr(client, base, 128)
            data["FLAT_DIR_SECTOR_HEAD"] = list(client.memory_get(base, base + 31))
        except Exception as exc:
            data["FLAT_DIR_SECTOR_BUFFER"] = f"ERR:{exc!r}"
            data["FLAT_DIR_SECTOR_HEAD"] = f"ERR:{exc!r}"
    for name in ("enum_count", "file_index", "temp_dir_id"):
        addr = resident_labels.get(name)
        if addr is None:
            continue
        try:
            data[name.upper()] = client.memory_get(addr, addr)[0]
        except Exception as exc:
            data[name.upper()] = f"ERR:{exc!r}"
    return data


def wait_for_shell_prompt(client: vp.BinaryMonitorClient, process, timeout: float) -> None:
    avp.wait_for_screen_fragment(client, "A:D64/>", timeout, poll_interval=0.2)


def run_once(
    image: Path,
    work_root: Path,
    project_name: str,
    connect_delay: float,
    command_timeout: float,
    verbose: bool = False,
) -> Path:
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
    try:
        if connect_delay > 0.0:
            time.sleep(connect_delay)
        client.connect(time.monotonic() + 20.0)
        client.ping()
        client.resume()

        wait_for_shell_prompt(client, process, 30.0)
        time.sleep(3.0)
        log_progress(verbose, {"phase": "prompt_ready"})
        project_root = prepare_workspace(work_root, project_name)
        log_progress(verbose, {"phase": "workspace_ready", "project": project_name})
        time.sleep(5.0)

        mount_command = "MOUNT B: /IMAGES/ACTION.DNP"
        log_progress(verbose, {"phase": "mount_send_start", "command": mount_command})
        avp.type_command(client, mount_command, 5.0)
        log_progress(verbose, {"phase": "mount_send_done"})
        try:
            log_progress(verbose, {"phase": "mount_wait_start"})
            avp.wait_for_mount_completion(client, 90.0, retry_echo=mount_command)
        except vp.ViceError:
            log_progress(verbose, {"phase": "mount_wait_retry"})
            avp.type_command(client, mount_command, 5.0)
            avp.wait_for_mount_completion(client, 90.0, retry_echo=mount_command)
        log_progress(verbose, {"phase": "mounted"})

        log_progress(verbose, {"phase": "drive_b_send_start"})
        avp.type_command(client, "B:", 5.0)
        log_progress(verbose, {"phase": "drive_b_send_done"})
        avp.wait_for_screen_fragment(client, "B:DNP/", 90.0, retry_echo="B:")
        log_progress(verbose, {"phase": "drive_b"})
        time.sleep(5.0)

        cd_command = f"CD {project_name}"
        log_progress(verbose, {"phase": "cd_send_start", "command": cd_command})
        avp.type_command(client, cd_command, 5.0)
        log_progress(verbose, {"phase": "cd_send_done"})
        avp.wait_for_screen_fragment(client, f"B:DNP/{project_name}", 90.0, retry_echo=cd_command)
        log_progress(verbose, {"phase": "in_project", "project": project_name})
        time.sleep(5.0)

        log_progress(verbose, {"phase": "actc_send_start"})
        avp.send_text(client, "ACTC MAIN\r", 5.0)
        log_progress(verbose, {"phase": "actc_send_done"})
        log_progress(verbose, {"phase": "actc_sent"})
        deadline = time.monotonic() + command_timeout
        screen = ""
        saw_run = False
        retry_count = 0
        stage_d_snapshot: dict[str, object] | None = None
        prelaunch_snapshot: dict[str, object] | None = None
        live_tool_snapshot: dict[str, object] | None = None
        last_live_tool_snapshot: dict[str, object] | None = None
        first_tool_signal_snapshot: dict[str, object] | None = None
        first_actc_trace_snapshot: dict[str, object] | None = None
        first_path_snapshot: dict[str, object] | None = None
        first_good_content_snapshot: dict[str, object] | None = None
        first_bad_content_snapshot: dict[str, object] | None = None
        first_program_loaded_snapshot: dict[str, object] | None = None
        first_file_complete_snapshot: dict[str, object] | None = None
        while time.monotonic() < deadline:
            screen, _d018, _dd00 = vp.read_active_screen_text(client)
            try:
                stage = client.memory_get(0xC59E, 0xC59E)[0]
                if stage_d_snapshot is None and stage == ord("d"):
                    stage_d_snapshot = seeded.collect_stage_b_snapshot(client)
            except Exception:
                pass
            try:
                launch_stage = client.memory_get(0x03F2, 0x03F2)[0]
                launch_code = client.memory_get(0x03F3, 0x03F3)[0]
                if prelaunch_snapshot is None and launch_stage == 0x90 and launch_code == 0x92:
                    prelaunch_snapshot = seeded.collect_stage_b_snapshot(client)
            except Exception:
                pass
            if vp.screen_contains(screen, "RUN ACTC.PRG"):
                saw_run = True
            try:
                if saw_run or client.memory_get(0x03F2, 0x03F2)[0] == 0xF3:
                    current_live_tool_snapshot = collect_actc_debug(client)
                    if live_tool_snapshot is None:
                        live_tool_snapshot = current_live_tool_snapshot
                    actc_trace = current_live_tool_snapshot.get("ACTC_TRACE")
                    if not isinstance(actc_trace, int) or actc_trace == 0:
                        actc_trace = current_live_tool_snapshot.get("ACTC_LAST_TRACE")
                    if first_actc_trace_snapshot is None and isinstance(actc_trace, int) and actc_trace != 0:
                        first_actc_trace_snapshot = current_live_tool_snapshot
                    if first_tool_signal_snapshot is None and (
                        current_live_tool_snapshot.get("SAVE_STAGE")
                        or current_live_tool_snapshot.get("SAVE_OPEN0")
                        or current_live_tool_snapshot.get("SAVE_OPEN1")
                        or current_live_tool_snapshot.get("SAVE_OPEN2")
                        or current_live_tool_snapshot.get("SAVE_OPEN3")
                        or current_live_tool_snapshot.get("OPEN_PATH")
                    ):
                        first_tool_signal_snapshot = current_live_tool_snapshot
                    manifest_text = current_live_tool_snapshot.get("MANIFEST_BUFFER")
                    source_text_live = current_live_tool_snapshot.get("SOURCE_BUFFER")
                    open_path = current_live_tool_snapshot.get("OPEN_PATH")
                    save_debug_path = current_live_tool_snapshot.get("SAVE_DEBUG_PATH")
                    desired_path = current_live_tool_snapshot.get("DESIRED_PATH")
                    if first_path_snapshot is None and (
                        (isinstance(open_path, str) and open_path)
                        or (isinstance(save_debug_path, str) and save_debug_path)
                        or (isinstance(desired_path, str) and desired_path)
                    ):
                        first_path_snapshot = current_live_tool_snapshot
                    if (
                        first_good_content_snapshot is None
                        and isinstance(manifest_text, str)
                        and manifest_text.startswith("ACTION PROJECT")
                        and isinstance(source_text_live, str)
                        and source_text_live.startswith("MODULE MAIN")
                    ):
                        first_good_content_snapshot = current_live_tool_snapshot
                    if (
                        first_bad_content_snapshot is None
                        and isinstance(manifest_text, str)
                        and manifest_text
                        and not manifest_text.startswith("ACTION PROJECT")
                    ):
                        first_bad_content_snapshot = current_live_tool_snapshot
                    mem_0900 = current_live_tool_snapshot.get("MEM_0900")
                    if (
                        first_program_loaded_snapshot is None
                        and ACTC_BODY_HEAD
                        and isinstance(mem_0900, list)
                        and mem_0900[: len(ACTC_BODY_HEAD)] == ACTC_BODY_HEAD[: len(mem_0900)]
                    ):
                        first_program_loaded_snapshot = current_live_tool_snapshot
                    tool_file_len = current_live_tool_snapshot.get("TOOL_ABI_FILE_LEN")
                    queue4 = current_live_tool_snapshot.get("QUEUE4")
                    if (
                        first_file_complete_snapshot is None
                        and (
                            (isinstance(tool_file_len, list) and tool_file_len != [0, 0])
                            or queue4 == 0x71
                        )
                    ):
                        first_file_complete_snapshot = current_live_tool_snapshot
                    last_live_tool_snapshot = current_live_tool_snapshot
            except Exception:
                pass
            if vp.screen_contains(screen, "ACTC OK"):
                break
            if saw_run and vp.screen_contains(screen, "READY."):
                extra = f"\nSTAGE_D_SNAPSHOT: {stage_d_snapshot!r}" if stage_d_snapshot is not None else ""
                if prelaunch_snapshot is not None:
                    extra += f"\nPRELAUNCH_SNAPSHOT: {prelaunch_snapshot!r}"
                if live_tool_snapshot is not None:
                    extra += f"\nLIVE_TOOL_SNAPSHOT: {live_tool_snapshot!r}"
                if first_tool_signal_snapshot is not None:
                    extra += f"\nFIRST_TOOL_SIGNAL_SNAPSHOT: {first_tool_signal_snapshot!r}"
                if first_actc_trace_snapshot is not None:
                    extra += f"\nFIRST_ACTC_TRACE_SNAPSHOT: {first_actc_trace_snapshot!r}"
                if first_path_snapshot is not None:
                    extra += f"\nFIRST_PATH_SNAPSHOT: {first_path_snapshot!r}"
                if first_good_content_snapshot is not None:
                    extra += f"\nFIRST_GOOD_CONTENT_SNAPSHOT: {first_good_content_snapshot!r}"
                if first_bad_content_snapshot is not None:
                    extra += f"\nFIRST_BAD_CONTENT_SNAPSHOT: {first_bad_content_snapshot!r}"
                if first_program_loaded_snapshot is not None:
                    extra += f"\nFIRST_PROGRAM_LOADED_SNAPSHOT: {first_program_loaded_snapshot!r}"
                if first_file_complete_snapshot is not None:
                    extra += f"\nFIRST_FILE_COMPLETE_SNAPSHOT: {first_file_complete_snapshot!r}"
                if last_live_tool_snapshot is not None:
                    extra += f"\nLAST_LIVE_TOOL_SNAPSHOT: {last_live_tool_snapshot!r}"
                raise vp.ViceError(f"ACTC escaped to READY ({read_actc_trace(client)}){extra} with screen:\n{screen}")
            if any(
                vp.screen_contains(screen, msg)
                for msg in ("PROGRAM LOAD FAILED", "SAVE FAIL", "BAD LITERAL", "BAD PROC", "NOT IN PROJECT", "NO FILE")
            ):
                extra = f"\nSTAGE_D_SNAPSHOT: {stage_d_snapshot!r}" if stage_d_snapshot is not None else ""
                if prelaunch_snapshot is not None:
                    extra += f"\nPRELAUNCH_SNAPSHOT: {prelaunch_snapshot!r}"
                if live_tool_snapshot is not None:
                    extra += f"\nLIVE_TOOL_SNAPSHOT: {live_tool_snapshot!r}"
                if first_tool_signal_snapshot is not None:
                    extra += f"\nFIRST_TOOL_SIGNAL_SNAPSHOT: {first_tool_signal_snapshot!r}"
                if first_actc_trace_snapshot is not None:
                    extra += f"\nFIRST_ACTC_TRACE_SNAPSHOT: {first_actc_trace_snapshot!r}"
                if first_path_snapshot is not None:
                    extra += f"\nFIRST_PATH_SNAPSHOT: {first_path_snapshot!r}"
                if first_good_content_snapshot is not None:
                    extra += f"\nFIRST_GOOD_CONTENT_SNAPSHOT: {first_good_content_snapshot!r}"
                if first_bad_content_snapshot is not None:
                    extra += f"\nFIRST_BAD_CONTENT_SNAPSHOT: {first_bad_content_snapshot!r}"
                if first_program_loaded_snapshot is not None:
                    extra += f"\nFIRST_PROGRAM_LOADED_SNAPSHOT: {first_program_loaded_snapshot!r}"
                if first_file_complete_snapshot is not None:
                    extra += f"\nFIRST_FILE_COMPLETE_SNAPSHOT: {first_file_complete_snapshot!r}"
                if last_live_tool_snapshot is not None:
                    extra += f"\nLAST_LIVE_TOOL_SNAPSHOT: {last_live_tool_snapshot!r}"
                raise vp.ViceError(f"ACTC terminal failure ({read_actc_trace(client)}){extra} with screen:\n{screen}")
            retry_count = avp.maybe_retry_command_enter(
                client,
                last_screen=screen,
                retry_echo="ACTC MAIN",
                retry_count=retry_count,
            )
            time.sleep(0.005 if saw_run else 0.2)
        else:
            extra = f"\nSTAGE_D_SNAPSHOT: {stage_d_snapshot!r}" if stage_d_snapshot is not None else ""
            if prelaunch_snapshot is not None:
                extra += f"\nPRELAUNCH_SNAPSHOT: {prelaunch_snapshot!r}"
            if live_tool_snapshot is not None:
                extra += f"\nLIVE_TOOL_SNAPSHOT: {live_tool_snapshot!r}"
            if first_tool_signal_snapshot is not None:
                extra += f"\nFIRST_TOOL_SIGNAL_SNAPSHOT: {first_tool_signal_snapshot!r}"
            if first_actc_trace_snapshot is not None:
                extra += f"\nFIRST_ACTC_TRACE_SNAPSHOT: {first_actc_trace_snapshot!r}"
            if first_path_snapshot is not None:
                extra += f"\nFIRST_PATH_SNAPSHOT: {first_path_snapshot!r}"
            if first_good_content_snapshot is not None:
                extra += f"\nFIRST_GOOD_CONTENT_SNAPSHOT: {first_good_content_snapshot!r}"
            if first_bad_content_snapshot is not None:
                extra += f"\nFIRST_BAD_CONTENT_SNAPSHOT: {first_bad_content_snapshot!r}"
            if first_program_loaded_snapshot is not None:
                extra += f"\nFIRST_PROGRAM_LOADED_SNAPSHOT: {first_program_loaded_snapshot!r}"
            if first_file_complete_snapshot is not None:
                extra += f"\nFIRST_FILE_COMPLETE_SNAPSHOT: {first_file_complete_snapshot!r}"
            if last_live_tool_snapshot is not None:
                extra += f"\nLAST_LIVE_TOOL_SNAPSHOT: {last_live_tool_snapshot!r}"
            raise vp.ViceError(f"timed out waiting for ACTC OK ({read_actc_trace(client)}){extra}; last screen was:\n{screen}")

        try:
            log_progress(verbose, {"phase": "actc_ok_wait_prompt_start"})
            avp.wait_for_screen_fragment(client, f"B:DNP/{project_name}", 30.0)
            log_progress(verbose, {"phase": "actc_returned_to_prompt"})
            wait_for_project_output(project_root, 30.0)
            log_progress(verbose, {"phase": "host_output_ready"})
            avp.type_command(client, "TYPE OBJ/MAIN.OBJ", 5.0)
            avp.wait_for_screen_fragments(
                client,
                ["obj1", "f 0 src/main.act", f"B:DNP/{project_name}"],
                45.0,
                retry_echo="TYPE OBJ/MAIN.OBJ",
            )
            log_progress(verbose, {"phase": "shell_readback_ready"})
        except RuntimeError as exc:
            extra = f"\nSTAGE_D_SNAPSHOT: {stage_d_snapshot!r}" if stage_d_snapshot is not None else ""
            if prelaunch_snapshot is not None:
                extra += f"\nPRELAUNCH_SNAPSHOT: {prelaunch_snapshot!r}"
            if live_tool_snapshot is not None:
                extra += f"\nLIVE_TOOL_SNAPSHOT: {live_tool_snapshot!r}"
            if first_tool_signal_snapshot is not None:
                extra += f"\nFIRST_TOOL_SIGNAL_SNAPSHOT: {first_tool_signal_snapshot!r}"
            if first_actc_trace_snapshot is not None:
                extra += f"\nFIRST_ACTC_TRACE_SNAPSHOT: {first_actc_trace_snapshot!r}"
            if first_path_snapshot is not None:
                extra += f"\nFIRST_PATH_SNAPSHOT: {first_path_snapshot!r}"
            if first_good_content_snapshot is not None:
                extra += f"\nFIRST_GOOD_CONTENT_SNAPSHOT: {first_good_content_snapshot!r}"
            if first_bad_content_snapshot is not None:
                extra += f"\nFIRST_BAD_CONTENT_SNAPSHOT: {first_bad_content_snapshot!r}"
            if first_program_loaded_snapshot is not None:
                extra += f"\nFIRST_PROGRAM_LOADED_SNAPSHOT: {first_program_loaded_snapshot!r}"
            if first_file_complete_snapshot is not None:
                extra += f"\nFIRST_FILE_COMPLETE_SNAPSHOT: {first_file_complete_snapshot!r}"
            if last_live_tool_snapshot is not None:
                extra += f"\nLAST_LIVE_TOOL_SNAPSHOT: {last_live_tool_snapshot!r}"
            try:
                extra += f"\nFINAL_VERIFY_SNAPSHOT: {collect_actc_debug(client)!r}"
            except Exception:
                pass
            raise vp.ViceError(f"{exc} ({read_actc_trace(client)}){extra} with screen:\n{screen}")
        return project_root
    finally:
        try:
            client.quit_emulator()
        finally:
            client.close()
        vp.terminate_process_tree(process)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a focused ACTC proof through the UDOS VICE probe harness")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--attempt-delay", type=float, default=2.0)
    parser.add_argument("--connect-delay", type=float, default=None)
    parser.add_argument("--command-timeout", type=float, default=90.0)
    parser.add_argument("--copy-fs-root", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="print progress payloads")
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()

    connect_delays = (args.connect_delay,) if args.connect_delay is not None else CONNECT_DELAYS

    for attempt in range(1, args.attempts + 1):
        connect_delay = connect_delays[(attempt - 1) % len(connect_delays)]
        try:
            log_progress(
                args.verbose,
                {
                    "attempt": attempt,
                    "attempts": args.attempts,
                    "connect_delay": connect_delay,
                    "command_timeout": args.command_timeout,
                    "copy_fs_root": args.copy_fs_root,
                },
            )
            work_root = fs_root
            temp_root = None
            if args.copy_fs_root:
                temp_root = tempfile.TemporaryDirectory(prefix="action-actc-probe-")
                work_root = Path(temp_root.name) / "fs"
                shutil.copytree(fs_root, work_root)
            try:
                vp.cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, args.attempt_delay)))
                run_once(image, work_root, project_name, connect_delay, args.command_timeout, args.verbose)
            finally:
                if temp_root is not None:
                    temp_root.cleanup()
            return 0
        except vp.ViceError as exc:
            log_progress(args.verbose, {"attempt": attempt, "connect_delay": connect_delay, "error": str(exc)})
            if attempt == args.attempts:
                print(exc, file=sys.stderr)
                return 1
            time.sleep(args.attempt_delay)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
