#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

import run_action_actc_alink_avmrunc_probe_direct as direct
import run_action_actc_probe as rcp
import run_action_avmrun_probe as avp
import vice_prg_probe as vp

DEFAULT_PROJECT = "PROJ3"
DEFAULT_MODE = "shelladd"


def prepare_shell_workspace(fs_root: Path, project_name: str) -> Path:
    project_root = rcp.prepare_workspace(fs_root, project_name)
    direct.stage_shell_sanity_avm(project_root)
    direct.install_program(fs_root, project_root, direct.ACTION_AVMRUNC_BUILD, "AVMRUNC.PRG")
    direct.install_runtime_support_artifacts(fs_root, project_root)
    return project_root


def wait_for_ready_escape(
    client: vp.BinaryMonitorClient,
    timeout: float,
    *,
    retry_echo: str | None = None,
    poll_interval: float = 0.2,
) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    retry_count = 0
    while time.monotonic() < deadline:
        last_screen = avp.screen_text(client)
        if vp.screen_contains(avp.last_nonempty_line(last_screen), "READY."):
            return last_screen
        retry_count = avp.maybe_retry_command_enter(
            client,
            last_screen=last_screen,
            retry_echo=retry_echo,
            retry_count=retry_count,
        )
        time.sleep(poll_interval)
    raise vp.ViceError(f"expected READY escape, got {avp.last_nonempty_line(last_screen)!r}:\n{last_screen}")


def run_shell_avm(
    client: vp.BinaryMonitorClient,
    project_prompt: str,
    avm_name: str,
    *,
    expect: str,
    timeout: float,
) -> str:
    command = f"AVMRUNC BIN/{avm_name}.AVM"
    avp.type_command(client, command, 30.0)
    avp.wait_for_screen_fragment(
        client,
        "RUN AVMRUNC.PRG",
        30.0,
        retry_echo=command,
        poll_interval=0.2,
    )
    if expect == "prompt":
        return direct.wait_for_stable_project_prompt(client, project_prompt, timeout)
    if expect == "ready":
        return wait_for_ready_escape(client, timeout, retry_echo=command)
    raise RuntimeError(f"unknown expectation: {expect}")


def run_once(image: Path, fs_root: Path, project_name: str, work_root: Path, mode: str, expect: str) -> None:
    shutil.rmtree(work_root, ignore_errors=True)
    shutil.copytree(fs_root, work_root, copy_function=shutil.copy)
    prepare_shell_workspace(work_root, project_name)

    vp.cleanup_stale_vice(settle_seconds=2.0)
    port = vp.reserve_tcp_port()
    process = vp.launch_vice(
        image,
        port,
        extra_args=["-iecdevice9", "-fs9", str(work_root), "-fslongnames"],
    )
    client = vp.BinaryMonitorClient("127.0.0.1", port, timeout=5.0)
    try:
        if direct.AVMRUN_CONNECT_DELAY > 0.0:
            time.sleep(direct.AVMRUN_CONNECT_DELAY)
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

        if mode == "shelladd":
            run_shell_avm(client, project_prompt, direct.SHELL_SANITY_NAME, expect="prompt", timeout=12.0)
            screen = run_shell_avm(client, project_prompt, direct.SHELL_NONTRIV_NAME, expect=expect, timeout=20.0)
        elif mode == "shellmin":
            screen = run_shell_avm(client, project_prompt, direct.SHELL_SANITY_NAME, expect=expect, timeout=12.0)
        else:
            raise RuntimeError(f"unknown mode: {mode}")

        print(screen)
        print(direct.collect_vice_debug_dump(client))
    finally:
        try:
            client.quit_emulator()
        except Exception:
            pass
        client.close()
        vp.terminate_process_tree(process)


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe live shell-launched AVMRUNC sanity AVMs under VICE")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--mode", choices=["shellmin", "shelladd"], default=DEFAULT_MODE)
    parser.add_argument("--expect", choices=["auto", "prompt", "ready"], default="auto")
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--attempt-delay", type=float, default=4.0)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    work_root = fs_root.with_name(f"{fs_root.name}-avmrunc-shell-{args.mode}")
    expect = args.expect
    if expect == "auto":
        expect = "prompt"

    last_error: Exception | None = None
    for attempt in range(1, args.attempts + 1):
        try:
            run_once(image, fs_root, args.project, work_root, args.mode, expect)
            return 0
        except Exception as exc:
            last_error = exc
            if attempt == args.attempts:
                break
            time.sleep(args.attempt_delay)
    if last_error is None:
        raise SystemExit("shell probe failed without an exception")
    raise SystemExit(str(last_error))


if __name__ == "__main__":
    raise SystemExit(main())
