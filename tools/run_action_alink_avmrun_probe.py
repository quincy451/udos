#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
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


def resolve_avm_output_command(project_root: Path) -> tuple[str, str]:
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    bin_dir = project_root / rap.host_name("BIN", lowercase_workspace)
    actual_avm = rap.case_insensitive_child(bin_dir, "MAIN.AVM")
    if not actual_avm.is_file():
        raise vp.ViceError(f"expected linked AVM output under {bin_dir}")
    rap.ensure_catalog_entries(bin_dir / rap.host_name("UDOSDIR.TXT", lowercase_workspace), [f"F {actual_avm.name}"])
    return f"{bin_dir.name}/{actual_avm.name}", actual_avm.name


def run_avmrun_once(image: Path, work_root: Path, project_name: str, connect_delay: float, avm_relpath: str, avm_name: str) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "run_action_avmrun_probe.py"),
        "--disk",
        str(image),
        "--fs-root",
        str(work_root),
        "--command",
        f"AVMRUN {avm_relpath}",
        "--pre-command",
        f"CD {project_name}",
        "--pre-prompt",
        f"B:DNP/{project_name}",
        "--final-prompt",
        f"B:DNP/{project_name}>",
        "--run-marker",
        "RUN AVMRUN.PRG",
        "--done-fragment",
        "12342",
        "--contains",
        f"ARGS {avm_relpath.upper()}",
        "--contains",
        "HELLOWORLD",
        "--contains",
        "TOOL7",
        "--contains",
        "12342",
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
        raise vp.ViceError("AVMRUN phase timed out after 180s") from exc
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or "AVMRUN phase failed"
        if avm_name.upper() != avm_name:
            details = details.replace(avm_relpath.upper(), avm_relpath)
        raise vp.ViceError(details)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ALINK -> AVMRUN proof through the proven staged release-image flow")
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
            rap.run_once(image, work_root, project_name, connect_delay)
            rap.verify_host_output(project_root)
            avm_relpath, avm_name = resolve_avm_output_command(project_root)
            run_avmrun_once(image, work_root, project_name, connect_delay, avm_relpath, avm_name)
            return 0
        except vp.ViceError as exc:
            if attempt == args.attempts:
                print(exc, file=sys.stderr)
                return 1
            time.sleep(args.attempt_delay)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
