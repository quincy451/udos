#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

import run_action_alink_probe as rap
import vice_prg_probe as vp


ROOT = Path(__file__).resolve().parent
ACTION_AVMRUN_BUILD = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "AVMRUN.PRG"
CONNECT_DELAYS = rap.CONNECT_DELAYS


def install_avmrun(fs_root: Path, project_root: Path) -> None:
    if not ACTION_AVMRUN_BUILD.is_file():
        raise RuntimeError(f"missing built AVMRUN program: {ACTION_AVMRUN_BUILD}")
    root_target = fs_root / "IMAGES" / "ACTION.DNP" / "AVMRUN.PRG"
    shutil.copy2(ACTION_AVMRUN_BUILD, root_target)
    shutil.copy2(root_target, project_root / "AVMRUN.PRG")
    rap.ensure_catalog_entries(
        fs_root / "IMAGES" / "ACTION.DNP" / "UDOSDIR.TXT",
        [f"D {project_root.name.upper()}", "F AVMRUN.PRG"],
    )
    rap.ensure_catalog_entries(project_root / "UDOSDIR.TXT", ["F AVMRUN.PRG"])


def run_once(image: Path, work_root: Path, project_name: str, connect_delay: float) -> None:
    port = vp.reserve_tcp_port()
    process = vp.launch_vice(
        image,
        port,
        extra_args=[
            "-iecdevice9",
            "-device9",
            "1",
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

        vp.wait_for_screen_and_state(
            client,
            process,
            "A:D64/>",
            marker_addr=None,
            marker_value=None,
            extra_checks=[],
            timeout=90.0,
        )
        time.sleep(5.0)

        for cmd, expect in [
            ("MOUNT B: /IMAGES/ACTION.DNP\r", "A:D64/>"),
            ("B:\r", "B:DNP/"),
            (f"CD {project_name}\r", f"B:DNP/{project_name}"),
        ]:
            client.keyboard_type(cmd)
            vp.wait_for_screen_and_state(
                client,
                process,
                expect,
                marker_addr=None,
                marker_value=None,
                extra_checks=[],
                timeout=90.0,
            )
            time.sleep(5.0)

        client.keyboard_type("ALINK MAIN\r")
        deadline = time.monotonic() + 90.0
        screen = ""
        while time.monotonic() < deadline:
            screen, _d018, _dd00 = vp.read_active_screen_text(client)
            if "ALINK OK" in screen:
                break
            if any(msg in screen for msg in ("TOO LARGE", "SAVE FAIL", "BAD AVO")):
                raise vp.ViceError(f"ALINK terminal failure with screen:\n{screen}")
            time.sleep(0.2)
        else:
            raise vp.ViceError(f"timed out waiting for ALINK OK; last screen was:\n{screen}")

        client.keyboard_type("AVMRUN BIN/MAIN.AVMTXT\r")
        deadline = time.monotonic() + 90.0
        while time.monotonic() < deadline:
            screen, _d018, _dd00 = vp.read_active_screen_text(client)
            if all(
                fragment in screen
                for fragment in (
                    "RUN ALINK.PRG",
                    "ALINK OK",
                    "RUN AVMRUN.PRG",
                    "ARGS BIN/MAIN.AVMTXT",
                    "HELLOTOOL7",
                    "42",
                    f"B:DNP/{project_name}>",
                )
            ):
                return
            if any(msg in screen for msg in ("BAD AVM", "UNSUPPORTED AVM", "LOAD FAIL", "NO FILE", "TOO LARGE")):
                raise vp.ViceError(f"AVMRUN terminal failure with screen:\n{screen}")
            time.sleep(0.2)
        raise vp.ViceError(f"timed out waiting for ALINK -> AVMRUN proof; last screen was:\n{screen}")
    finally:
        try:
            client.quit_emulator()
        finally:
            client.close()
        vp.terminate_process_tree(process)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ALINK -> AVMRUN proof through the direct typed release-image path")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--attempt-delay", type=float, default=4.0)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()
    work_root = fs_root.parent / f"{fs_root.name}-alink-avmrun"

    for attempt in range(1, args.attempts + 1):
        connect_delay = CONNECT_DELAYS[(attempt - 1) % len(CONNECT_DELAYS)]
        try:
            shutil.rmtree(work_root, ignore_errors=True)
            shutil.copytree(fs_root, work_root)
            project_root = rap.prepare_workspace(work_root, project_name)
            install_avmrun(work_root, project_root)
            vp.cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, args.attempt_delay)))
            run_once(image, work_root, project_name, connect_delay)
            rap.verify_host_output(project_root)
            return 0
        except vp.ViceError as exc:
            if attempt == args.attempts:
                print(exc, file=sys.stderr)
                return 1
            time.sleep(args.attempt_delay)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
