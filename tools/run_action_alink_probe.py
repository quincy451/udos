#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

import run_action_probe_fs as pfs
import vice_prg_probe as vp


ROOT = Path(__file__).resolve().parent
ACTION_ALINK_BUILD = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "ALINK.PRG"
CONNECT_DELAYS = (10.0, 14.0)


write_ascii = pfs.write_ascii
ensure_catalog_entries = pfs.ensure_catalog_entries
case_insensitive_child = pfs.case_insensitive_child
detect_lowercase_workspace = pfs.detect_lowercase_workspace
host_name = pfs.host_name


def log_progress(verbose: bool, payload: dict[str, object]) -> None:
    if verbose:
        print(payload, flush=True)


def main_object_text() -> str:
    return (
        'OBJ1\n'
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
        'OBJ1\n'
        'x h 0 7\n'
        'x z 7 1\n'
        'b u0c1r\n'
        'b r\n'
        'u u\n'
        'n h\n'
    )


def tool_object_text() -> str:
    return (
        'OBJ1\n'
        'x t 0 16\n'
        'b s0i0u0r\n'
        's TOOL\n'
        'i 7\n'
        'u u\n'
        'n t\n'
    )


def util_object_text() -> str:
    return (
        'OBJ1\n'
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


def verify_bad_name_rejected(project_root: Path) -> None:
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    bin_dir = project_root / host_name("BIN", lowercase_workspace)
    prg_path = bin_dir / host_name("MAIN.PRG", lowercase_workspace)
    bad_path = bin_dir / host_name("MAIN.BAD", lowercase_workspace)
    if prg_path.exists():
        raise RuntimeError(f"did not expect direct PRG artifact {prg_path} to exist")
    if bad_path.exists():
        raise RuntimeError(f"did not expect invalid-name artifact {bad_path} to exist")


def run_once(image: Path, work_root: Path, project_name: str, connect_delay: float) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "run_action_command_probe.py"),
        "--disk",
        str(image),
        "--fs-root",
        str(work_root),
        "--command",
        "ALINK MAIN.BAD",
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
        "ARGS MAIN.BAD",
        "--contains",
        "BAD NAME",
        "--not-contains",
        "SAVE FAIL",
        "--not-contains",
        "BAD OBJECT",
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
    parser = argparse.ArgumentParser(description="Run a focused ALINK proof through the UDOS VICE probe harness")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--attempt-delay", type=float, default=2.0)
    parser.add_argument("--verbose", action="store_true", help="print progress payloads")
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()

    work_root = fs_root.parent / f"{fs_root.name}-alink"

    for attempt in range(1, args.attempts + 1):
        connect_delay = CONNECT_DELAYS[(attempt - 1) % len(CONNECT_DELAYS)]
        log_progress(
            args.verbose,
            {
                "attempt": attempt,
                "attempts": args.attempts,
                "connect_delay": connect_delay,
            },
        )
        try:
            shutil.rmtree(work_root, ignore_errors=True)
            shutil.copytree(fs_root, work_root)
            project_root = prepare_workspace(work_root, project_name)
            vp.cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, args.attempt_delay)))
            run_once(image, work_root, project_name, connect_delay)
            verify_bad_name_rejected(project_root)
            return 0
        except vp.ViceError as exc:
            if attempt == args.attempts:
                print(exc, file=sys.stderr)
                return 1
            time.sleep(args.attempt_delay)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
