#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import run_action_alink_probe as rap
import vice_prg_probe as vp


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the focused ALINK proof through a resident autoexec image")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--wait-seconds", type=float, default=160.0)
    parser.add_argument("--connect-delay", type=float, default=40.0)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--attempt-delay", type=float, default=4.0)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()
    project_root = rap.prepare_workspace(fs_root, project_name)
    output_path = project_root / "bin" / "main.avmtxt"

    last_error: str | None = None
    for attempt in range(1, max(1, args.attempts) + 1):
        if output_path.exists():
            output_path.unlink()
        vp.cleanup_stale_vice(settle_seconds=2.0)
        port = vp.reserve_tcp_port()
        process = vp.launch_vice(
            image,
            port,
            extra_args=[
                "-iecdevice9",
                "-device9",
                "1",
                "-fs9",
                str(fs_root),
                "-fslongnames",
            ],
        )
        client = vp.BinaryMonitorClient("127.0.0.1", port, timeout=5.0)

        deadline = time.monotonic() + args.wait_seconds
        try:
            if args.connect_delay > 0.0:
                time.sleep(args.connect_delay)
            client.connect(time.monotonic() + 20.0)
            client.ping()
            client.resume()
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise vp.ViceError("x64sc exited before ALINK produced host output")
                if output_path.is_file():
                    rap.verify_host_output(project_root)
                    return 0
                time.sleep(0.5)
            last_error = f"expected host file {output_path} to exist after {args.wait_seconds:.1f} seconds"
        except Exception as exc:
            last_error = str(exc)
        finally:
            try:
                client.quit_emulator()
            finally:
                client.close()
            vp.terminate_process_tree(process)
        if attempt < max(1, args.attempts) and args.attempt_delay > 0.0:
            time.sleep(args.attempt_delay)

    print(last_error or f"expected host file {output_path} to exist after {args.wait_seconds:.1f} seconds", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
