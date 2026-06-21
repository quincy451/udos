#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import run_action_actc_probe as rcp
import run_action_alink_seeded_runtime_probe as seeded
import run_action_command_probe as avp
import run_action_probe_fs as pfs
import vice_prg_probe as vp


ROOT = Path(__file__).resolve().parent
ACTION_ROOT = ROOT.parent.parent / "actionc64u"
ACT2SAVE_CURRENT_LABELS = ACTION_ROOT / "build/udos_tools/act2save.current.labels"
PROMPT_TIMEOUT = 30.0
FINAL_TIMEOUT = 30.0
SETTLE_SECONDS = 2.0
EXPECTED_BYTES = bytes(
    (
        0x00, 0x10, 0xA9, 0xA5, 0x8D, 0xD0, 0x03, 0xA9,
        0x00, 0x85, 0x02, 0x85, 0x03, 0xA2, 0x02, 0x4C,
        0x0F, 0xCF,
    )
)
EXPECTED_OBJECT_BYTES = b"OBJ1\rONELOAD DIAGNOSTIC\r"
SEND_TIMEOUT = 5.0
POLL_INTERVAL = 0.05
CONNECT_DELAYS = (10.0, 14.0)


def log_progress(verbose: bool, payload: dict[str, object]) -> None:
    if verbose:
        print(json.dumps(payload, sort_keys=True), file=sys.stderr, flush=True)


def load_selected_act2save_labels() -> dict[str, int]:
    wanted = {
        "file_params",
        "scan_ptr",
        "truncated_flag",
        "module_name",
        "manifest_entry",
        "manifest_buffer",
        "target_path",
        "load_buffer",
        "save_buffer",
    }
    out: dict[str, int] = {}
    if not ACT2SAVE_CURRENT_LABELS.is_file():
        return out
    for line in ACT2SAVE_CURRENT_LABELS.read_text(encoding="utf-8", errors="replace").splitlines():
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


def collect_debug(client: vp.BinaryMonitorClient) -> dict[str, object]:
    data: dict[str, object] = {}
    debug_addrs = [
        (0x03D0, "POSTLOAD_MARKER"),
        (0x03E8, "RETURN0"),
        (0x03E9, "RETURN1"),
        (0x03EA, "RETURN2"),
        (0x03EB, "RETURN3"),
        (0x03EC, "RETURN4"),
        (0x03ED, "RETURN5"),
        (0x03EE, "RETURN6"),
        (0x03EF, "RETURN_SP"),
        (0x03F0, "CALL_MARKER"),
        (0x03F1, "CALL_EXIT"),
        (0x03F4, "WRITEBACK_TRACE_STAGE"),
        (0x03FB, "TOOL_QUEUE_TRACE0"),
        (0x03FC, "TOOL_QUEUE_TRACE1"),
        (0x03FD, "TOOL_QUEUE_TRACE2"),
        (0x03FE, "TOOL_QUEUE_TRACE3"),
        (0x03FF, "TOOL_QUEUE_TRACE4"),
        (0xC59E, "RES_SAVE_STAGE"),
        (0xC59F, "OPEN0"),
        (0xC5A0, "OPEN1"),
        (0xC5A1, "OPEN2"),
        (0xC5A2, "OPEN3"),
        (0xCFF8, "PROGRAM_DRIVE_SNAPSHOT"),
        (0xCFF9, "PROGRAM_DIR_SNAPSHOT"),
        (0xCDC1, "RES_SAVE_ENTRY_STAGE"),
        (0xCDC2, "RES_SAVE_RESOLVE_STAGE"),
    ]
    for addr, name in debug_addrs:
        try:
            data[name] = client.memory_get(addr, addr)[0]
        except Exception as exc:  # pragma: no cover - debug only
            data[name] = f"ERR:{exc!r}"
    labels = load_selected_act2save_labels()
    for name, addr in labels.items():
        key = f"ACT2SAVE_{name.upper()}"
        try:
            if name == "file_params":
                data[key] = list(client.memory_get(addr, addr + 8))
            elif name in {"module_name", "manifest_entry", "target_path"}:
                data[key] = seeded.read_cstr(client, addr, 40)
            elif name == "manifest_buffer":
                data[key] = seeded.read_cstr(client, addr, 120)
            elif name in {"load_buffer", "save_buffer"}:
                data[key] = list(client.memory_get(addr, addr + 15))
            elif name == "scan_ptr":
                data[key] = list(client.memory_get(addr, addr + 1))
            else:
                data[key] = client.memory_get(addr, addr)[0]
        except Exception as exc:  # pragma: no cover - debug only
            data[key] = f"ERR:{exc!r}"
    try:
        marker = data.get("POSTLOAD_MARKER")
        if marker in (0xA1, 0xA2):
            data["POSTLOAD_TARGET"] = seeded.read_ascii_bytes(client, 0x03D1, 10)
            data["POSTLOAD_MODULE"] = seeded.read_ascii_bytes(client, 0x03DB, 6)
            data["POSTLOAD_FILE_PARAMS"] = list(client.memory_get(0x03E1, 0x03E7))
        else:
            data["POSTLOAD_TARGET"] = ""
            data["POSTLOAD_MODULE"] = ""
            data["POSTLOAD_FILE_PARAMS"] = []
        if marker == 0xB1:
            data["PRESAVE_SP"] = client.memory_get(0x03D1, 0x03D1)[0]
            data["PRESAVE_FILE_PARAMS"] = list(client.memory_get(0x03D2, 0x03D8))
            data["PRESAVE_STACK_WINDOW"] = list(client.memory_get(0x03D9, 0x03E7))
        else:
            data["PRESAVE_SP"] = None
            data["PRESAVE_FILE_PARAMS"] = []
            data["PRESAVE_STACK_WINDOW"] = []
        data["CURRENT_PATH"] = seeded.read_cstr(client, 0xCD00, 64)
        data["OPEN_PATH"] = seeded.read_cstr(client, 0xCD40, 96)
        data["SAVE_PATH"] = seeded.read_cstr(client, 0xC5A3, 96)
        data["TOOL_ABI_SAVE_BLOCK"] = list(client.memory_get(0xCDC6, 0xCDCB))
        data["SAVE_CALL_BLOCK"] = list(client.memory_get(0x03E8, 0x03F1))
        data["TOOL_ABI_FILE_DEST_PTR"] = list(client.memory_get(0xCDC8, 0xCDC9))
        dest_addr = data["TOOL_ABI_FILE_DEST_PTR"][0] | (data["TOOL_ABI_FILE_DEST_PTR"][1] << 8)
        data["TOOL_ABI_FILE_DEST_HEAD"] = list(client.memory_get(dest_addr, dest_addr + 31))
        data["TOOL_ABI_FILE_LEN"] = list(client.memory_get(0xCDC4, 0xCDC5))
        data["TOOL_ABI_FILE_REMAIN"] = list(client.memory_get(0xCDC2, 0xCDC3))
        data["TOOL_ABI_FILE_LIMIT"] = list(client.memory_get(0xCDCA, 0xCDCB))
    except Exception as exc:  # pragma: no cover - debug only
        data["CURRENT_PATH"] = f"ERR:{exc!r}"
        data["OPEN_PATH"] = f"ERR:{exc!r}"
        data["SAVE_PATH"] = f"ERR:{exc!r}"
        data["TOOL_ABI_SAVE_BLOCK"] = f"ERR:{exc!r}"
        data["SAVE_CALL_BLOCK"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_DEST_PTR"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_DEST_HEAD"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_LEN"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_REMAIN"] = f"ERR:{exc!r}"
        data["TOOL_ABI_FILE_LIMIT"] = f"ERR:{exc!r}"
    try:
        regs = seeded.collect_registers(client)
        for name in ("pc", "a", "x", "y", "sp", "fl"):
            if name in regs:
                data[f"REG_{name.upper()}"] = regs[name]
    except Exception as exc:  # pragma: no cover - debug only
        data["REG_ERR"] = f"ERR:{exc!r}"
    return data


def prepare_workspace(fs_root: Path, project_name: str) -> tuple[Path, Path]:
    project_root = rcp.prepare_workspace(fs_root, project_name)
    lowercase_workspace = pfs.detect_lowercase_workspace(fs_root)
    images_root = pfs.case_insensitive_child(fs_root, pfs.host_name("IMAGES", lowercase_workspace))
    action_root = pfs.case_insensitive_child(images_root, pfs.host_name("ACTION.DNP", lowercase_workspace))
    act2save_prg = ACTION_ROOT / "build" / "udos_tools" / "ACT2SAVE.PRG"
    if not act2save_prg.is_file():
        raise FileNotFoundError(f"missing ACT2SAVE build at {act2save_prg}")
    tool_entries: list[str] = []
    for tool_name in ("ACT2SAVE.PRG", "ACTSAVE.PRG"):
        root_target = action_root / pfs.host_name(tool_name, lowercase_workspace)
        shutil.copy2(act2save_prg, root_target)
        pfs.sync_case_siblings(root_target)
        project_target = project_root / pfs.host_name(tool_name, lowercase_workspace)
        shutil.copy2(root_target, project_target)
        pfs.sync_case_siblings(project_target)
        tool_entries.append(f"F {tool_name}")
    pfs.ensure_catalog_entries(
        action_root / pfs.host_name("UDOSDIR.TXT", lowercase_workspace),
        [f"D {project_name.upper()}", *tool_entries],
    )
    pfs.ensure_catalog_entries(project_root / pfs.host_name("UDOSDIR.TXT", lowercase_workspace), tool_entries)
    obj_root = pfs.case_insensitive_child(project_root, "OBJ")
    obj_root.mkdir(exist_ok=True)
    (obj_root / pfs.host_name("MAIN.OBJ", lowercase_workspace)).write_bytes(EXPECTED_OBJECT_BYTES)
    pfs.ensure_catalog_entries(obj_root / pfs.host_name("UDOSDIR.TXT", lowercase_workspace), ["F MAIN.OBJ"])
    pfs.add_case_aliases(project_root)
    output_path = pfs.project_output_path(project_root, "BIN", "MAIN.PRG")
    output_path.unlink(missing_ok=True)
    return project_root, output_path


def wait_for_host_file(path: Path, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file():
            return
        time.sleep(0.2)
    raise vp.ViceError(f"expected host file {path} to exist after {timeout:.1f} seconds")


def run_once(
    image: Path,
    work_root: Path,
    project_name: str,
    connect_delay: float,
    require_output: bool = True,
) -> tuple[str, dict[str, object]]:
    project_root, output_path = prepare_workspace(work_root, project_name)
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
        avp.wait_for_screen_fragment(client, "A:D64/>", PROMPT_TIMEOUT)
        time.sleep(SETTLE_SECONDS)

        mount_command = "MOUNT B: /IMAGES/ACTION.DNP"
        client.keyboard_feed(mount_command + "\r")
        time.sleep(1.0)
        try:
            avp.wait_for_mount_completion(client, PROMPT_TIMEOUT, retry_echo=mount_command)
        except vp.ViceError:
            avp.type_command(client, mount_command, SEND_TIMEOUT)
            avp.wait_for_mount_completion(client, PROMPT_TIMEOUT, retry_echo=mount_command)

        avp.type_command(client, "B:", SEND_TIMEOUT)
        avp.wait_for_screen_fragment(client, "B:DNP/", PROMPT_TIMEOUT, retry_echo="B:")
        time.sleep(SETTLE_SECONDS)

        cd_command = f"CD {project_name}"
        avp.type_command(client, cd_command, SEND_TIMEOUT)
        avp.wait_for_screen_fragment(client, f"B:DNP/{project_name}", PROMPT_TIMEOUT, retry_echo=cd_command)
        time.sleep(SETTLE_SECONDS)

        run_command = "ACTSAVE MAIN"
        avp.type_command(client, run_command, SEND_TIMEOUT)
        launch_deadline = time.monotonic() + PROMPT_TIMEOUT
        while time.monotonic() < launch_deadline:
            screen, _d018, _dd00 = vp.read_active_screen_text(client)
            screen_upper = screen.upper()
            if "ACT2SAVE OK" in screen_upper:
                break
            if "RUN ACTSAVE.PRG" in screen_upper:
                break
            if "PROGRAM NOT FOUND" in screen_upper or "LOAD FAIL" in screen_upper or "SAVE FAIL" in screen_upper:
                debug = collect_debug(client)
                raise vp.ViceError(
                    f"ACT2SAVE launch-stage failure with screen:\n{screen}\nDEBUG: {json.dumps(debug, indent=2)}"
                )
            time.sleep(0.2)
        else:
            debug = collect_debug(client)
            raise vp.ViceError(
                f"expected screen fragment 'RUN ACTSAVE.PRG' was not present in final screen:\n{screen}\nDEBUG: {json.dumps(debug, indent=2)}"
            )
        launch_command = run_command
        deadline = time.monotonic() + FINAL_TIMEOUT
        screen = ""
        stage_b_snapshot: dict[str, object] | None = None
        stage_d_snapshot: dict[str, object] | None = None
        stage_snapshots: dict[str, dict[str, object]] = {}
        first_stage_snapshot: dict[str, object] | None = None
        first_stage_name: str | None = None
        stage_history: list[str] = []
        saw_run_marker = False
        retry_count = 0
        program_not_found_retries = 0
        while time.monotonic() < deadline:
            actual_output_path = pfs.project_output_path(project_root, "BIN", "MAIN.PRG")
            if require_output and actual_output_path.is_file():
                try:
                    payload = actual_output_path.read_bytes()
                except Exception:
                    payload = b""
                if payload == EXPECTED_BYTES:
                    debug = collect_debug(client)
                    try:
                        debug["FILE_PARAMS"] = list(client.memory_get(0x00E2, 0x00EA))
                    except Exception as exc:  # pragma: no cover - debug only
                        debug["FILE_PARAMS"] = f"ERR:{exc!r}"
                    try:
                        debug["SAVE_CALL_BLOCK"] = list(client.memory_get(0x03E8, 0x03F1))
                    except Exception as exc:  # pragma: no cover - debug only
                        debug["SAVE_CALL_BLOCK"] = f"ERR:{exc!r}"
                    debug["OUTPUT_PATH"] = str(actual_output_path)
                    debug["OUTPUT_BYTES"] = list(payload)
                    debug["STAGE_HISTORY"] = stage_history
                    debug["SAW_RUN_MARKER"] = saw_run_marker
                    if first_stage_snapshot is not None:
                        debug["FIRST_STAGE_NAME"] = first_stage_name
                        debug["FIRST_STAGE_SNAPSHOT"] = first_stage_snapshot
                    if stage_b_snapshot is not None:
                        debug["STAGE_B_SNAPSHOT"] = stage_b_snapshot
                    if stage_d_snapshot is not None:
                        debug["STAGE_D_SNAPSHOT"] = stage_d_snapshot
                    return screen, debug
            try:
                stage = client.memory_get(0xC59E, 0xC59E)[0]
                if stage:
                    stage_char = chr(stage) if 32 <= stage <= 126 else f"0x{stage:02x}"
                    if not stage_history or stage_history[-1] != stage_char:
                        stage_history.append(stage_char)
                    if first_stage_snapshot is None:
                        first_stage_name = stage_char
                        first_stage_snapshot = seeded.collect_stage_b_snapshot(client)
                    if stage_char not in stage_snapshots and len(stage_snapshots) < 12:
                        stage_snapshots[stage_char] = seeded.collect_stage_b_snapshot(client)
                if stage_b_snapshot is None and stage == ord("b"):
                    stage_b_snapshot = seeded.collect_stage_b_snapshot(client)
                if stage_d_snapshot is None and stage == ord("d"):
                    stage_d_snapshot = seeded.collect_stage_b_snapshot(client)
            except Exception:
                pass
            screen, _d018, _dd00 = vp.read_active_screen_text(client)
            screen_upper = screen.upper()
            if "RUN ACTSAVE.PRG" in screen_upper:
                saw_run_marker = True
            if "PROGRAM NOT FOUND" in screen_upper and not saw_run_marker and program_not_found_retries < 2:
                avp.type_command(client, run_command, SEND_TIMEOUT)
                program_not_found_retries += 1
                time.sleep(0.5)
                continue
            if "ACT2SAVE OK" in screen_upper:
                debug = collect_debug(client)
                try:
                    debug["FILE_PARAMS"] = list(client.memory_get(0x00E2, 0x00EA))
                except Exception as exc:  # pragma: no cover - debug only
                    debug["FILE_PARAMS"] = f"ERR:{exc!r}"
                try:
                    debug["SAVE_CALL_BLOCK"] = list(client.memory_get(0x03E8, 0x03F1))
                except Exception as exc:  # pragma: no cover - debug only
                    debug["SAVE_CALL_BLOCK"] = f"ERR:{exc!r}"
                actual_output_path = pfs.project_output_path(project_root, "BIN", "MAIN.PRG")
                debug["OUTPUT_PATH"] = str(actual_output_path)
                debug["STAGE_HISTORY"] = stage_history
                debug["SAW_RUN_MARKER"] = saw_run_marker
                if first_stage_snapshot is not None:
                    debug["FIRST_STAGE_NAME"] = first_stage_name
                    debug["FIRST_STAGE_SNAPSHOT"] = first_stage_snapshot
                if stage_b_snapshot is not None:
                    debug["STAGE_B_SNAPSHOT"] = stage_b_snapshot
                if stage_d_snapshot is not None:
                    debug["STAGE_D_SNAPSHOT"] = stage_d_snapshot
                if stage_snapshots:
                    debug["STAGE_SNAPSHOTS"] = stage_snapshots
                if actual_output_path.is_file():
                    payload = actual_output_path.read_bytes()
                    debug["OUTPUT_BYTES"] = list(payload)
                else:
                    debug["OUTPUT_BYTES"] = None
                debug["REQUIRE_OUTPUT"] = require_output
                return screen, debug
            if "SAVE FAIL" in screen_upper or "LOAD FAIL" in screen_upper:
                debug = collect_debug(client)
                try:
                    debug["FILE_PARAMS"] = list(client.memory_get(0x00E2, 0x00EA))
                except Exception as exc:  # pragma: no cover - debug only
                    debug["FILE_PARAMS"] = f"ERR:{exc!r}"
                try:
                    debug["SAVE_CALL_BLOCK"] = list(client.memory_get(0x03E8, 0x03F1))
                except Exception as exc:  # pragma: no cover - debug only
                    debug["SAVE_CALL_BLOCK"] = f"ERR:{exc!r}"
                debug["OUTPUT_PATH"] = str(output_path)
                debug["STAGE_HISTORY"] = stage_history
                debug["SAW_RUN_MARKER"] = saw_run_marker
                if first_stage_snapshot is not None:
                    debug["FIRST_STAGE_NAME"] = first_stage_name
                    debug["FIRST_STAGE_SNAPSHOT"] = first_stage_snapshot
                if stage_b_snapshot is not None:
                    debug["STAGE_B_SNAPSHOT"] = stage_b_snapshot
                if stage_d_snapshot is not None:
                    debug["STAGE_D_SNAPSHOT"] = stage_d_snapshot
                if stage_snapshots:
                    debug["STAGE_SNAPSHOTS"] = stage_snapshots
                raise vp.ViceError(
                    f"ACT2SAVE terminal failure with screen:\n{screen}\nDEBUG: {json.dumps(debug, indent=2)}"
                )
            retry_count = avp.maybe_retry_command_enter(
                client,
                last_screen=screen,
                retry_echo=launch_command,
                retry_count=retry_count,
            )
            time.sleep(0.01 if saw_run_marker else POLL_INTERVAL)
        debug = collect_debug(client)
        try:
            debug["SAVE_CALL_BLOCK"] = list(client.memory_get(0x03E8, 0x03F1))
        except Exception as exc:  # pragma: no cover - debug only
            debug["SAVE_CALL_BLOCK"] = f"ERR:{exc!r}"
        debug["OUTPUT_PATH"] = str(output_path)
        debug["STAGE_HISTORY"] = stage_history
        if first_stage_snapshot is not None:
            debug["FIRST_STAGE_NAME"] = first_stage_name
            debug["FIRST_STAGE_SNAPSHOT"] = first_stage_snapshot
        if stage_b_snapshot is not None:
            debug["STAGE_B_SNAPSHOT"] = stage_b_snapshot
        if stage_d_snapshot is not None:
            debug["STAGE_D_SNAPSHOT"] = stage_d_snapshot
        if stage_snapshots:
            debug["STAGE_SNAPSHOTS"] = stage_snapshots
        raise vp.ViceError(
            f"timed out waiting for final ACT2SAVE screen; last screen was:\n{screen}\nDEBUG: {json.dumps(debug, indent=2)}"
        )
    finally:
        try:
            client.quit_emulator()
        finally:
            client.close()
        vp.terminate_process_tree(process)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the seeded ACT2SAVE binary-save probe")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--attempt-delay", type=float, default=2.0)
    parser.add_argument("--connect-delay", type=float)
    parser.add_argument("--screen-only-success", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="print progress payloads")
    parser.add_argument("--verbose-success", action="store_true")
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()
    work_root = fs_root.parent / f"{fs_root.name}-act2save-seeded"

    connect_delays = (args.connect_delay,) if args.connect_delay is not None else CONNECT_DELAYS
    last_error: Exception | None = None

    for attempt in range(1, args.attempts + 1):
        vp.cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, args.attempt_delay)))
        connect_delay = connect_delays[(attempt - 1) % len(connect_delays)]
        log_progress(args.verbose, {"attempt": attempt, "attempts": args.attempts, "connect_delay": connect_delay})
        try:
            shutil.rmtree(work_root, ignore_errors=True)
            shutil.copytree(fs_root, work_root, symlinks=True)
            screen, debug = run_once(
                image,
                work_root,
                project_name,
                connect_delay,
                require_output=not args.screen_only_success,
            )
            if args.screen_only_success:
                print(screen)
                print(json.dumps(debug, indent=2))
                return 0
            output_bytes = bytes(debug.get("OUTPUT_BYTES") or [])
            if output_bytes != EXPECTED_BYTES:
                raise vp.ViceError(
                    f"expected output bytes {list(EXPECTED_BYTES)!r}, got {list(output_bytes)!r}; DEBUG: {json.dumps(debug, indent=2)}"
                )
            log_progress(
                args.verbose or args.verbose_success,
                {
                    "status": "ACT2SAVE OK",
                    "output_path": debug.get("OUTPUT_PATH"),
                    "output_len": len(output_bytes),
                },
            )
            if args.verbose_success:
                print(screen, file=sys.stderr)
                print(json.dumps(debug, indent=2), file=sys.stderr)
            return 0
        except Exception as exc:
            last_error = exc
            log_progress(args.verbose, {"attempt": attempt, "connect_delay": connect_delay, "error": str(exc)})
            if attempt < args.attempts:
                time.sleep(args.attempt_delay)

    assert last_error is not None
    print(last_error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
