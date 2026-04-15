#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import run_action_actmon_probe as actmon


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a focused ACTMON CHECK proof through the generic Action VICE runner")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--attempt-delay", type=float, default=2.0)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    source_fs_root = Path(args.fs_root).resolve()
    fs_root = Path(tempfile.gettempdir()) / f"{source_fs_root.name}-actmon-check"
    project_name = args.project.upper()

    actmon.cleanup_stale_vice()

    modules = [
        ("MAIN", actmon.default_stub_body("MAIN")),
        ("HELPER", actmon.default_stub_body("HELPER")),
    ]

    baseline_root = Path(tempfile.gettempdir()) / f"{source_fs_root.name}-actmon-check-baseline"
    actmon.copytree_lowercase(source_fs_root, baseline_root)

    try:
        screen, _project_root = actmon.run_phase(
            image=image,
            baseline_root=baseline_root,
            fs_root=fs_root,
            project_name=project_name,
            modules=modules,
            command="ACTMON.PRG CHECK",
            run_marker="",
            fragments=[
                "PROJECT YES",
                "SRC YES",
                "BIN YES",
                "OBJ YES",
                "MODULES 2",
                "MISSING 0",
                "ACTMON OK",
            ],
            attempts=args.attempts,
            attempt_delay=args.attempt_delay,
        )
    except actmon.ProbeError as exc:
        print(exc, file=sys.stderr)
        return 1

    if screen:
        print(screen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
