#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

import run_action_avmrun_probe as avp
import run_action_avmrunc_shell_probe as shell_probe
import vice_prg_probe as vp

ROOT = Path(__file__).resolve().parent
ACTION_ROOT = ROOT.parent.parent / "actionc64u"
UDOS_ROOT = ROOT.parent
AVMRUNC_LABELS = ACTION_ROOT / "build" / "udos_tools" / "avmrunc.current.labels"
RESIDENT_LABELS = UDOS_ROOT / "build" / "release" / "udos-resident.labels"

DEFAULT_PROJECT = "PROJ3"
DEFAULT_TIMEOUT = 6.0
DEFAULT_POLL_INTERVAL = 0.02

TRACE_DEBUG_BYTES = (
    ("REU_REMAIN_HI_SNAPSHOT", 0xCFE2),
    ("REU_RTS_LO_SNAPSHOT", 0xCFE3),
    ("REU_RTS_HI_SNAPSHOT", 0xCFE4),
    ("REU_ENTRY_RTS_LO_SNAPSHOT", 0xCFE5),
    ("REU_ENTRY_RTS_HI_SNAPSHOT", 0xCFE6),
    ("REU_COPY_TRACE0", 0x03E0),
    ("REU_COPY_TRACE1", 0x03E1),
    ("REU_COPY_TRACE2", 0x03E2),
    ("REU_COPY_TRACE3", 0x03E3),
    ("RETURN_QUEUE_TRACE0", 0x03E8),
    ("RETURN_QUEUE_TRACE1", 0x03E9),
    ("RETURN_QUEUE_TRACE2", 0x03EA),
    ("RETURN_QUEUE_TRACE3", 0x03EB),
    ("LAUNCH_RESULT_FLAG", 0x03F0),
    ("LAUNCH_EXIT_STATUS", 0x03F1),
    ("LAUNCH_TRACE_STAGE", 0x03F2),
    ("LAUNCH_TRACE_CODE", 0x03F3),
    ("WRITEBACK_TRACE_STAGE", 0x03F4),
    ("WRITEBACK_TRACE_COUNT", 0x03F5),
    ("WRITEBACK_TRACE_KIND", 0x03F6),
    ("LAUNCH_PATH_TRACE0", 0x03F7),
    ("LAUNCH_PATH_TRACE1", 0x03F8),
    ("LAUNCH_PATH_TRACE2", 0x03F9),
    ("LAUNCH_PATH_TRACE3", 0x03FA),
    ("PAYLOAD_PTR_LO", 0x00ED),
    ("PAYLOAD_PTR_HI", 0x00EE),
    ("ENTRY_PTR_LO", 0x00EF),
    ("ENTRY_PTR_HI", 0x00F0),
    ("AVMRUN_INTERP_RESULT", 0x3C46),
    ("AVMRUN_INTERP_RESUME_STATE", 0x3C49),
    ("AVMRUN_INTERP_SERVICE_FAILED", 0x3C4A),
    ("AVMRUN_OVERLAY_READY", 0x3CF5),
    ("AVMRUN_OVERLAY_REQUESTED_KIND", 0x3CF6),
    ("AVMRUN_OVERLAY_LOADED_KIND", 0x3CF7),
    ("AVMRUN_OVERLAY_REQUESTED_CMD", 0x3CF8),
    ("AVMRUN_OVERLAY_LOADED_LEN_LO", 0x3CF9),
    ("AVMRUN_OVERLAY_LOADED_LEN_HI", 0x3CFA),
    ("AVMRUN_OVERLAY_SERVICE_STATUS", 0x3CFB),
    ("PROGRAM_STATE_SNAPSHOT", 0xCFF6),
    ("PROGRAM_EXIT_SNAPSHOT", 0xCFF7),
    ("STAGE_SNAPSHOT", 0xCFFD),
    ("TOOL_QUEUE_TRACE4", 0x03FF),
)


def clear_launch_debug_state(client: vp.BinaryMonitorClient) -> None:
    client.memory_set(0x03E0, bytes(0x10))
    client.memory_set(0x03F0, bytes(0x10))
    client.memory_set(0xCFE2, bytes(0x05))
    client.memory_set(0xCFF6, b"\x00\x00")
    client.memory_set(0xCFFD, b"\x00")


def load_trace_labels() -> dict[int, str]:
    labels: dict[int, str] = {}

    def add_label(addr: int, name: str) -> None:
        existing = labels.get(addr)
        if existing is None:
            labels[addr] = name
        elif name not in existing.split(","):
            labels[addr] = existing + "," + name

    if AVMRUNC_LABELS.is_file():
        avmrunc = vp.load_ld65_labels(AVMRUNC_LABELS)
        for name in ("interpreted_ok", "fail_with_ptr"):
            addr = avmrunc.get(name)
            if isinstance(addr, int):
                add_label(addr, name)
    if RESIDENT_LABELS.is_file():
        resident = vp.load_ld65_labels(RESIDENT_LABELS)
        for name in ("svc_program_exit", "tool_abi_program_exit", "svc_program_consume_launch_result"):
            addr = resident.get(name)
            if isinstance(addr, int):
                add_label(addr, name)

        entry_base = resident.get("launch_stub_entry_template")
        entry_end = resident.get("launch_stub_entry_template_end")
        return_base = resident.get("launch_stub_return_template")
        return_end = resident.get("launch_stub_return_template_end")
        restore_base = resident.get("launch_stub_restore_template")
        restore_end = resident.get("launch_stub_restore_template_end")

        if all(isinstance(v, int) for v in (entry_base, entry_end, return_base, return_end, restore_base, restore_end)):
            for name, addr in resident.items():
                if not isinstance(addr, int) or not name.startswith("launch_stub_"):
                    continue
                if entry_base <= addr < entry_end:
                    add_label(0xCC00 + (addr - entry_base), f"{name}@entry")
                elif return_base <= addr < return_end:
                    add_label(0x033C + (addr - return_base), f"{name}@return")
                elif restore_base <= addr < restore_end:
                    add_label(0xCE10 + (addr - restore_base), f"{name}@restore")

    add_label(0x033C, "launch_return_addr")
    return labels


def read_selected_debug(client: vp.BinaryMonitorClient) -> dict[str, int]:
    snapshot = vp.read_debug_bytes(client, TRACE_DEBUG_BYTES)
    return {label: value for label, _addr, value in snapshot}


def read_file_stage_context(client: vp.BinaryMonitorClient) -> tuple[str, int]:
    file_params = client.memory_get(0x00E2, 0x00EA)
    saved_memcfg = client.memory_get(0x3CD9, 0x3CD9)[0]
    return file_params.hex(), saved_memcfg


def screen_terminal_state(screen: str, project_prompt: str) -> str:
    last_line = avp.last_nonempty_line(screen)
    if vp.screen_contains(last_line, "READY."):
        return "ready"
    if vp.screen_contains(last_line, project_prompt):
        return "prompt"
    return ""


def format_trace_row(
    elapsed: float,
    registers: dict[str, int],
    debug: dict[str, int],
    terminal: str,
    pc_labels: dict[int, str],
) -> str:
    pc = registers.get("PC", 0)
    sp = registers.get("SP", 0)
    pc_suffix = f" ({pc_labels[pc]})" if pc in pc_labels else ""
    tail = f" term={terminal}" if terminal else ""
    return (
        f"+{elapsed:0.3f}s "
        f"pc=${pc:04x}{pc_suffix} sp=${sp:02x} "
        f"reurem=${debug.get('REU_REMAIN_HI_SNAPSHOT', 0):02x}{debug.get('LAUNCH_PATH_TRACE2', 0):02x} "
        f"rts=${debug.get('REU_RTS_HI_SNAPSHOT', 0):02x}{debug.get('REU_RTS_LO_SNAPSHOT', 0):02x} "
        f"entry=${debug.get('REU_ENTRY_RTS_HI_SNAPSHOT', 0):02x}{debug.get('REU_ENTRY_RTS_LO_SNAPSHOT', 0):02x} "
        f"reu=${debug.get('REU_COPY_TRACE0', 0):02x}/"
        f"{debug.get('REU_COPY_TRACE1', 0):02x}/"
        f"{debug.get('REU_COPY_TRACE2', 0):02x}/"
        f"{debug.get('REU_COPY_TRACE3', 0):02x} "
        f"stagewb=${debug.get('RETURN_QUEUE_TRACE0', 0):02x}/"
        f"{debug.get('RETURN_QUEUE_TRACE3', 0):02x}"
        f"{debug.get('RETURN_QUEUE_TRACE2', 0):02x}"
        f"{debug.get('RETURN_QUEUE_TRACE1', 0):02x} "
        f"launch=${debug.get('LAUNCH_RESULT_FLAG', 0):02x}/{debug.get('LAUNCH_EXIT_STATUS', 0):02x} "
        f"trace=${debug.get('LAUNCH_TRACE_STAGE', 0):02x}/{debug.get('LAUNCH_TRACE_CODE', 0):02x} "
        f"ovl=${debug.get('AVMRUN_OVERLAY_READY', 0):02x}/"
        f"{debug.get('AVMRUN_OVERLAY_REQUESTED_KIND', 0):02x}/"
        f"{debug.get('AVMRUN_OVERLAY_LOADED_KIND', 0):02x}/"
        f"{debug.get('AVMRUN_OVERLAY_REQUESTED_CMD', 0):02x}/"
        f"{debug.get('AVMRUN_OVERLAY_LOADED_LEN_HI', 0):02x}"
        f"{debug.get('AVMRUN_OVERLAY_LOADED_LEN_LO', 0):02x} "
        f"svc=${debug.get('AVMRUN_OVERLAY_SERVICE_STATUS', 0):02x} "
        f"interp=${debug.get('AVMRUN_INTERP_RESULT', 0):02x}/"
        f"{debug.get('AVMRUN_INTERP_RESUME_STATE', 0):02x}/"
        f"{debug.get('AVMRUN_INTERP_SERVICE_FAILED', 0):02x} "
        f"ptr=${debug.get('PAYLOAD_PTR_HI', 0):02x}{debug.get('PAYLOAD_PTR_LO', 0):02x}/"
        f"{debug.get('ENTRY_PTR_HI', 0):02x}{debug.get('ENTRY_PTR_LO', 0):02x} "
        f"prog=${debug.get('PROGRAM_STATE_SNAPSHOT', 0):02x}/{debug.get('PROGRAM_EXIT_SNAPSHOT', 0):02x} "
        f"stage=${debug.get('STAGE_SNAPSHOT', 0):02x} "
        f"toolq4=${debug.get('TOOL_QUEUE_TRACE4', 0):02x}{tail}"
    )


def trace_shelladd_boundary(
    client: vp.BinaryMonitorClient,
    project_prompt: str,
    *,
    timeout: float,
    poll_interval: float,
) -> tuple[str, list[str], str]:
    pc_labels = load_trace_labels()
    deadline = time.monotonic() + timeout
    started = time.monotonic()
    last_state: tuple[int, int, int, int, int, int, int, int, int, str] | None = None
    trace_rows: list[str] = []
    final_screen = ""

    while time.monotonic() < deadline:
        registers = client.registers_get()
        debug = read_selected_debug(client)
        final_screen = avp.screen_text(client)
        terminal = screen_terminal_state(final_screen, project_prompt)
        state = (
            registers.get("PC", 0),
            registers.get("SP", 0),
            debug.get("REU_REMAIN_HI_SNAPSHOT", 0),
            debug.get("REU_RTS_LO_SNAPSHOT", 0),
            debug.get("REU_RTS_HI_SNAPSHOT", 0),
            debug.get("REU_ENTRY_RTS_LO_SNAPSHOT", 0),
            debug.get("REU_ENTRY_RTS_HI_SNAPSHOT", 0),
            debug.get("REU_COPY_TRACE0", 0),
            debug.get("REU_COPY_TRACE1", 0),
            debug.get("REU_COPY_TRACE2", 0),
            debug.get("REU_COPY_TRACE3", 0),
            debug.get("RETURN_QUEUE_TRACE0", 0),
            debug.get("RETURN_QUEUE_TRACE1", 0),
            debug.get("RETURN_QUEUE_TRACE2", 0),
            debug.get("RETURN_QUEUE_TRACE3", 0),
            debug.get("LAUNCH_RESULT_FLAG", 0),
            debug.get("LAUNCH_EXIT_STATUS", 0),
            debug.get("LAUNCH_TRACE_STAGE", 0),
            debug.get("LAUNCH_TRACE_CODE", 0),
            debug.get("PROGRAM_STATE_SNAPSHOT", 0),
            debug.get("PROGRAM_EXIT_SNAPSHOT", 0),
            debug.get("STAGE_SNAPSHOT", 0),
            terminal,
        )
        if state != last_state:
            trace_rows.append(
                format_trace_row(time.monotonic() - started, registers, debug, terminal, pc_labels)
            )
            last_state = state
        if terminal:
            return terminal, trace_rows, final_screen
        time.sleep(poll_interval)

    return "timeout", trace_rows, final_screen


def run_once(
    image: Path,
    fs_root: Path,
    project_name: str,
    work_root: Path,
    *,
    timeout: float,
    poll_interval: float,
) -> None:
    shutil.rmtree(work_root, ignore_errors=True)
    shutil.copytree(fs_root, work_root, copy_function=shutil.copy)
    shell_probe.prepare_shell_workspace(work_root, project_name)

    vp.cleanup_stale_vice(settle_seconds=2.0)
    port = vp.reserve_tcp_port()
    process = vp.launch_vice(
        image,
        port,
        extra_args=["-iecdevice9", "-fs9", str(work_root), "-fslongnames"],
    )
    client = vp.BinaryMonitorClient("127.0.0.1", port, timeout=5.0)
    try:
        if shell_probe.direct.AVMRUN_CONNECT_DELAY > 0.0:
            time.sleep(shell_probe.direct.AVMRUN_CONNECT_DELAY)
        client.connect(time.monotonic() + 20.0)
        client.ping()
        client.resume()

        avp.wait_for_active_prompt(client, "A:D64/>", 60.0, poll_interval=0.2)
        time.sleep(3.0)
        avp.type_command(client, "MOUNT B: /IMAGES/ACTION.DNP", 30.0)
        avp.wait_for_mount_completion(
            client,
            30.0,
            retry_echo="MOUNT B: /IMAGES/ACTION.DNP",
            poll_interval=0.2,
        )
        avp.type_command(client, "B:", 30.0)
        avp.wait_for_screen_fragment(client, "B:DNP/>", 30.0, retry_echo="B:", poll_interval=0.2)
        avp.type_command(client, f"CD {project_name}", 30.0)
        project_prompt = f"B:DNP/{project_name}>"
        avp.wait_for_screen_fragment(
            client,
            project_prompt,
            30.0,
            retry_echo=f"CD {project_name}",
            poll_interval=0.2,
        )

        shell_probe.run_shell_avm(
            client,
            project_prompt,
            shell_probe.direct.SHELL_SANITY_NAME,
            expect="prompt",
            timeout=12.0,
        )
        clear_launch_debug_state(client)

        command = f"AVMRUNC BIN/{shell_probe.direct.SHELL_NONTRIV_NAME}.AVM"
        avp.type_command(client, command, 30.0)
        avp.wait_for_screen_fragment(
            client,
            "RUN AVMRUNC.PRG",
            30.0,
            retry_echo=command,
            poll_interval=0.2,
        )

        terminal, trace_rows, final_screen = trace_shelladd_boundary(
            client,
            project_prompt,
            timeout=timeout,
            poll_interval=poll_interval,
        )
        print(f"terminal_state={terminal}")
        print("trace:")
        for row in trace_rows:
            print(row)
        print("final_screen:")
        print(final_screen)
        file_params_hex, saved_memcfg = read_file_stage_context(client)
        debug = read_selected_debug(client)
        print(f"file_params_e2_ea: {file_params_hex}")
        print(f"saved_memcfg: 0x{saved_memcfg:02x}")
        print(
            "launch_path_traces: "
            f"t0=0x{debug.get('LAUNCH_PATH_TRACE0', 0):02x} "
            f"t1=0x{debug.get('LAUNCH_PATH_TRACE1', 0):02x} "
            f"t2=0x{debug.get('LAUNCH_PATH_TRACE2', 0):02x} "
            f"t3=0x{debug.get('LAUNCH_PATH_TRACE3', 0):02x}"
        )
        print(shell_probe.direct.collect_vice_debug_dump(client))
    finally:
        try:
            client.quit_emulator()
        except Exception:
            pass
        client.close()
        vp.terminate_process_tree(process)


def main() -> int:
    parser = argparse.ArgumentParser(description="Trace live shell-launched AVMRUNC SHELLADD boundary under VICE")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--attempt-delay", type=float, default=4.0)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    work_root = fs_root.with_name(f"{fs_root.name}-avmrunc-shelladd-trace")

    last_error: Exception | None = None
    for attempt in range(1, args.attempts + 1):
        try:
            run_once(
                image,
                fs_root,
                args.project,
                work_root,
                timeout=args.timeout,
                poll_interval=args.poll_interval,
            )
            return 0
        except Exception as exc:
            last_error = exc
            if attempt == args.attempts:
                break
            time.sleep(args.attempt_delay)
    if last_error is None:
        raise SystemExit("shelladd trace failed without an exception")
    raise SystemExit(str(last_error))


if __name__ == "__main__":
    raise SystemExit(main())
