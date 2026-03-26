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
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()
    project_root = rap.prepare_workspace(fs_root, project_name)
    output_path = project_root / "bin" / "main.avm.txt"

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

    deadline = time.monotonic() + args.wait_seconds
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise vp.ViceError("x64sc exited before ALINK produced host output")
            if output_path.is_file():
                rap.verify_host_output(project_root)
                return 0
            time.sleep(0.5)
    finally:
        vp.terminate_process_tree(process)

    print(f"expected host file {output_path} to exist after {args.wait_seconds:.1f} seconds", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
