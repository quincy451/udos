#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

import vice_prg_probe as vp


ROOT = Path(__file__).resolve().parent
ACTION_ALINK_BUILD = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "ALINK.PRG"
ACTION_ALINK_CURRENT_LABELS = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "alink.current.labels"
UDOS_RESIDENT_LABELS = ROOT.parent / "build" / "udos-resident.labels"
CONNECT_DELAYS = (14.0,)


def write_ascii(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("ascii"))


def ensure_catalog_entries(path: Path, entries: list[str]) -> None:
    directory_lines: list[str] = []
    file_lines: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="ascii", errors="ignore").splitlines():
            entry = line.strip()
            if not entry:
                continue
            if entry.startswith("D "):
                directory_lines.append(entry)
            else:
                file_lines.append(entry)
    for entry in entries:
        target = directory_lines if entry.startswith("D ") else file_lines
        if entry not in target:
            target.append(entry)
    lines = directory_lines + file_lines
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="ascii")


def case_insensitive_child(parent: Path, name: str) -> Path:
    target_name = name.lower()
    for child in parent.iterdir():
        if child.name.lower() == target_name:
            return child
    return parent / name


def detect_lowercase_workspace(fs_root: Path) -> bool:
    images = case_insensitive_child(fs_root, "IMAGES")
    action_dnp = case_insensitive_child(images, "ACTION.DNP")
    return images.name.islower() or action_dnp.name.islower()


def host_name(name: str, lowercase_workspace: bool) -> str:
    return name.lower() if lowercase_workspace else name


def read_cstr(client: vp.BinaryMonitorClient, addr: int, limit: int) -> str:
    data = client.memory_get(addr, addr + limit - 1)
    out = bytearray()
    for value in data:
        if value == 0:
            break
        out.append(value)
    return out.decode("ascii", errors="replace")


def load_selected_alink_labels() -> dict[str, int]:
    wanted = {
        "module_name",
        "target_path",
        "source_buffer",
        "debug_phase",
        "debug_phase_zp",
        "debug_sp_before_strings",
        "debug_sp_after_strings",
        "file_params",
        "main_flags_lo",
        "main_flags_hi",
    }
    out: dict[str, int] = {}
    if not ACTION_ALINK_CURRENT_LABELS.is_file():
        return out
    for line in ACTION_ALINK_CURRENT_LABELS.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) < 3 or parts[0] != "al":
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
        "save_debug_write_path_buffer",
    }
    out: dict[str, int] = {}
    if not UDOS_RESIDENT_LABELS.is_file():
        return out
    for line in UDOS_RESIDENT_LABELS.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) < 3 or parts[0] != "al":
            continue
        name = parts[2].lstrip(".")
        if name not in wanted:
            continue
        try:
            out[name] = int(parts[1], 16)
        except ValueError:
            continue
    return out


def collect_debug(client: vp.BinaryMonitorClient) -> dict[str, object]:
    labels = load_selected_alink_labels()
    resident_labels = load_selected_resident_labels()
    module_name_addr = labels.get("module_name", 0x28C9)
    target_path_addr = labels.get("target_path", 0x28E2)
    source_buffer_addr = labels.get("source_buffer", 0x294B)
    main_flags_lo_addr = labels.get("main_flags_lo")
    main_flags_hi_addr = labels.get("main_flags_hi")
    file_params_addr = labels.get("file_params")
    save_stage_addr = resident_labels.get("save_debug_stage_byte")
    save_status0_addr = resident_labels.get("save_debug_open_status0")
    save_status1_addr = resident_labels.get("save_debug_open_status1")
    save_status2_addr = resident_labels.get("save_debug_open_status2")
    save_status3_addr = resident_labels.get("save_debug_open_status3")
    save_path_addr = resident_labels.get("save_debug_write_path_buffer")
    data: dict[str, object] = {
        "launch_bytes": {hex(addr): client.memory_get(addr, addr)[0] for addr in range(0x03FA, 0x0400)},
        "resident_queue_bytes": {
            "0x03f4": client.memory_get(0x03F4, 0x03F4)[0],
            "0x03f5": client.memory_get(0x03F5, 0x03F5)[0],
            "0x03f6": client.memory_get(0x03F6, 0x03F6)[0],
            "0x03fb": client.memory_get(0x03FB, 0x03FB)[0],
            "0x03fc": client.memory_get(0x03FC, 0x03FC)[0],
            "0x03fd": client.memory_get(0x03FD, 0x03FD)[0],
            "0x03fe": client.memory_get(0x03FE, 0x03FE)[0],
        },
        "save_call_bytes": {hex(addr): client.memory_get(addr, addr)[0] for addr in range(0x03F0, 0x03F4)},
        "snapshot_bytes": list(client.memory_get(0x03D0, 0x03EF)),
        "preexit_source_head": list(client.memory_get(0x03D0, 0x03DF)),
        "preexit_text": read_cstr(client, 0x03D0, 16),
        "preexit_target_path": read_cstr(client, 0x03E0, 16),
        "tool_file_block": list(client.memory_get(0xCDC0, 0xCDCB)),
        "current_path": read_cstr(client, 0xCD00, 64),
        "open_path": read_cstr(client, 0xCD40, 96),
        "module_name": read_cstr(client, module_name_addr, 32),
        "target_path": read_cstr(client, target_path_addr, 64),
        "source_head": list(client.memory_get(source_buffer_addr, source_buffer_addr + 31)),
        "TOOL_ABI_FILE_STATUS": client.memory_get(0xCDC1, 0xCDC1)[0],
    }
    if save_stage_addr is not None:
        data["RESIDENT_SAVE_STAGE"] = client.memory_get(save_stage_addr, save_stage_addr)[0]
    if None not in (save_status0_addr, save_status1_addr, save_status2_addr, save_status3_addr):
        data["RESIDENT_SAVE_STATUS"] = [
            client.memory_get(save_status0_addr, save_status0_addr)[0],
            client.memory_get(save_status1_addr, save_status1_addr)[0],
            client.memory_get(save_status2_addr, save_status2_addr)[0],
            client.memory_get(save_status3_addr, save_status3_addr)[0],
        ]
    if save_path_addr is not None:
        data["RESIDENT_SAVE_PATH"] = read_cstr(client, save_path_addr, 96)
    if main_flags_lo_addr is not None and main_flags_hi_addr is not None:
        data["MAIN_FLAGS"] = [
            client.memory_get(main_flags_lo_addr, main_flags_lo_addr)[0],
            client.memory_get(main_flags_hi_addr, main_flags_hi_addr)[0],
        ]
    if file_params_addr is not None:
        data["FILE_PARAMS"] = list(client.memory_get(file_params_addr, file_params_addr + 8))
    try:
        if "debug_phase" in labels:
            data["DEBUG_PHASE"] = client.memory_get(labels["debug_phase"], labels["debug_phase"])[0]
        if "debug_phase_zp" in labels:
            data["DEBUG_PHASE_ZP"] = client.memory_get(labels["debug_phase_zp"], labels["debug_phase_zp"])[0]
        data["DEBUG_SP_BEFORE_STRINGS"] = client.memory_get(0x03FA, 0x03FA)[0]
        data["DEBUG_SP_AFTER_STRINGS"] = client.memory_get(0x03FB, 0x03FB)[0]
    except Exception as exc:
        data["DEBUG_PHASE"] = f"ERR:{exc!r}"
        data["DEBUG_PHASE_ZP"] = f"ERR:{exc!r}"
        data["DEBUG_SP_BEFORE_STRINGS"] = f"ERR:{exc!r}"
        data["DEBUG_SP_AFTER_STRINGS"] = f"ERR:{exc!r}"
    try:
        registers = client.registers_get()
        data["REGISTERS"] = registers
        if "SP" in registers:
            sp = int(registers["SP"]) & 0xFF
            stack_start = 0x0100 + ((sp + 1) & 0xFF)
            stack_end = min(0x01FF, stack_start + 15)
            data["STACK_WINDOW"] = list(client.memory_get(stack_start, stack_end))
            data["STACK_WINDOW_ADDR"] = stack_start
    except Exception as exc:
        data["REGISTERS"] = f"ERR:{exc!r}"
        data["STACK_WINDOW"] = f"ERR:{exc!r}"
        data["STACK_WINDOW_ADDR"] = f"ERR:{exc!r}"
    return data


def main_object_text() -> str:
    return (
        'AVO1\n'
        'x main 0 31\n'
        'b s0e1u0u1j0i1r\n'
        'u h\n'
        'u t\n'
        's HELLO\n'
        's WORLD\n'
        'i 123\n'
        'i 42\n'
        'k 7\n'
        'n main\n'
    )


def helper_object_text() -> str:
    return (
        'AVO1\n'
        'x h 0 7\n'
        'x z 7 1\n'
        'b u0c1r\n'
        'b r\n'
        'u u\n'
        'n h\n'
    )


def tool_object_text() -> str:
    return (
        'AVO1\n'
        'x t 0 16\n'
        'b s0i0u0r\n'
        's TOOL\n'
        'i 7\n'
        'u u\n'
        'n t\n'
    )


def util_object_text() -> str:
    return (
        'AVO1\n'
        'x u 0 4\n'
        'x v 4 1\n'
        'b c1r\n'
        'b r\n'
        'n u\n'
    )


def prepare_workspace(fs_root: Path, project_name: str) -> Path:
    lowercase_workspace = detect_lowercase_workspace(fs_root)
    images_root = case_insensitive_child(fs_root, host_name("IMAGES", lowercase_workspace))
    action_root = case_insensitive_child(images_root, host_name("ACTION.DNP", lowercase_workspace))
    project_root = action_root / host_name(project_name.upper(), lowercase_workspace)
    lower_project_root = project_root.parent / project_root.name.lower()
    shutil.rmtree(project_root, ignore_errors=True)
    shutil.rmtree(lower_project_root, ignore_errors=True)
    src_root = project_root / host_name("SRC", lowercase_workspace)
    bin_root = project_root / host_name("BIN", lowercase_workspace)
    obj_root = project_root / host_name("OBJ", lowercase_workspace)
    src_root.mkdir(parents=True, exist_ok=True)
    bin_root.mkdir(exist_ok=True)
    obj_root.mkdir(exist_ok=True)

    write_ascii(project_root / host_name("README.TXT", lowercase_workspace), "ACTION PROJECT READY\n")
    write_ascii(project_root / host_name("ACTION.PROJ", lowercase_workspace), "ACTION PROJECT\rMAIN.ACT\r")
    write_ascii(project_root / host_name("UDOSDIR.TXT", lowercase_workspace), "D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF README.TXT\n")
    write_ascii(src_root / host_name("UDOSDIR.TXT", lowercase_workspace), "F MAIN.ACT\n")
    write_ascii(bin_root / host_name("UDOSDIR.TXT", lowercase_workspace), "")
    write_ascii(obj_root / host_name("UDOSDIR.TXT", lowercase_workspace), "F H.OBJ\nF MAIN.OBJ\nF T.OBJ\nF U.OBJ\n")
    write_ascii(src_root / host_name("MAIN.ACT", lowercase_workspace), 'MODULE MAIN\rPROC MAIN()\rPrint("HELLO")\rPrintIE(42)\rRETURN\r')
    write_ascii(obj_root / host_name("MAIN.OBJ", lowercase_workspace), main_object_text())
    write_ascii(obj_root / host_name("H.OBJ", lowercase_workspace), helper_object_text())
    write_ascii(obj_root / host_name("T.OBJ", lowercase_workspace), tool_object_text())
    write_ascii(obj_root / host_name("U.OBJ", lowercase_workspace), util_object_text())

    if ACTION_ALINK_BUILD.is_file():
        root_target = action_root / host_name("ALINK.PRG", lowercase_workspace)
        shutil.copy2(ACTION_ALINK_BUILD, root_target)
        shutil.copy2(root_target, project_root / host_name("ALINK.PRG", lowercase_workspace))
        ensure_catalog_entries(action_root / host_name("UDOSDIR.TXT", lowercase_workspace), [f"D {project_name.upper()}", "F ALINK.PRG"])
        ensure_catalog_entries(project_root / host_name("UDOSDIR.TXT", lowercase_workspace), ["F ALINK.PRG"])

    return project_root


def verify_host_output(project_root: Path) -> None:
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    bin_dir = project_root / host_name("BIN", lowercase_workspace)
    prg_path = bin_dir / host_name("MAIN.PRG", lowercase_workspace)
    avm_path = bin_dir / host_name("MAIN.AVM", lowercase_workspace)
    if not avm_path.is_file():
        raise RuntimeError(f"expected host file {avm_path} to exist")
    if avm_path.stat().st_size <= 4:
        raise RuntimeError(f"expected linked AVM {avm_path} to contain payload bytes")
    if prg_path.exists():
        raise RuntimeError(f"did not expect direct PRG artifact {prg_path} to exist")


def run_once(image: Path, work_root: Path, project_name: str, connect_delay: float) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "run_action_avmrun_probe.py"),
        "--disk",
        str(image),
        "--fs-root",
        str(work_root),
        "--command",
        "ALINK MAIN.AVM",
        "--pre-command",
        f"CD {project_name}",
        "--pre-prompt",
        f"B:DNP/{project_name}",
        "--final-prompt",
        f"B:DNP/{project_name}>",
        "--run-marker",
        "RUN ALINK.PRG",
        "--done-fragment",
        "",
        "--contains",
        "ARGS MAIN.AVM",
        "--not-contains",
        "SAVE FAIL",
        "--not-contains",
        "BAD AVO",
        "--not-contains",
        "TOO LARGE",
        "--not-contains",
        "LOAD FAIL",
        "--not-contains",
        "NO OBJECT",
        "--attempts",
        "1",
        "--connect-delay",
        str(connect_delay),
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180.0,
        )
    except subprocess.TimeoutExpired as exc:
        raise vp.ViceError("ALINK phase timed out after 180s") from exc
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or "ALINK phase failed"
        raise vp.ViceError(details)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a focused ALINK proof through the generic Action VICE runner")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--attempt-delay", type=float, default=2.0)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()

    work_root = fs_root.parent / f"{fs_root.name}-alink"

    for attempt in range(1, args.attempts + 1):
        connect_delay = CONNECT_DELAYS[(attempt - 1) % len(CONNECT_DELAYS)]
        print(
            {
                "attempt": attempt,
                "attempts": args.attempts,
                "connect_delay": connect_delay,
            },
            flush=True,
        )
        try:
            shutil.rmtree(work_root, ignore_errors=True)
            shutil.copytree(fs_root, work_root)
            project_root = prepare_workspace(work_root, project_name)
            vp.cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, args.attempt_delay)))
            run_once(image, work_root, project_name, connect_delay)
            verify_host_output(project_root)
            return 0
        except vp.ViceError as exc:
            if attempt == args.attempts:
                print(exc, file=sys.stderr)
                return 1
            time.sleep(args.attempt_delay)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
