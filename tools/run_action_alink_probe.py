#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ACTION_ALINK_BUILD = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "ALINK.PRG"


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


def object_text() -> str:
    return (
        'AVO1\n'
        '{"entry_offset":0,"exports":[["main",0],["helper",0]],"calls":["helper"],"imports":["rt.format_int","rt.print_line","rt.print_str"],'
        '"module":"main","payload_hex":"6d61696e00","version":1}\n'
    )


def prepare_workspace(fs_root: Path, project_name: str) -> Path:
    project_root = fs_root / "IMAGES" / "ACTION.DNP" / project_name.upper()
    lower_project_root = project_root.parent / project_root.name.lower()
    shutil.rmtree(project_root, ignore_errors=True)
    shutil.rmtree(lower_project_root, ignore_errors=True)
    (project_root / "src").mkdir(parents=True, exist_ok=True)
    (project_root / "bin").mkdir(exist_ok=True)
    (project_root / "obj").mkdir(exist_ok=True)

    write_ascii(project_root / "readme.txt", "ACTION PROJECT READY\n")
    write_ascii(project_root / "ACTION.PROJ", "ACTION PROJECT\rMAIN.ACT\r")
    write_ascii(project_root / "UDOSDIR.TXT", "D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF README.TXT\n")
    write_ascii(project_root / "src" / "UDOSDIR.TXT", "F MAIN.ACT\n")
    write_ascii(project_root / "bin" / "UDOSDIR.TXT", "")
    write_ascii(project_root / "obj" / "UDOSDIR.TXT", "F MAIN.AVO\n")
    write_ascii(project_root / "src" / "main.act", 'MODULE MAIN\rPROC MAIN()\rPrint("HELLO")\rPrintIE(42)\rRETURN\r')
    write_ascii(project_root / "obj" / "main.avo", object_text())

    if ACTION_ALINK_BUILD.is_file():
        root_target = fs_root / "IMAGES" / "ACTION.DNP" / "ALINK.PRG"
        shutil.copy2(ACTION_ALINK_BUILD, root_target)
        shutil.copy2(root_target, project_root / "ALINK.PRG")
        ensure_catalog_entries(fs_root / "IMAGES" / "ACTION.DNP" / "UDOSDIR.TXT", [f"D {project_name.upper()}", "F ALINK.PRG"])
        ensure_catalog_entries(project_root / "UDOSDIR.TXT", ["F ALINK.PRG"])

    return project_root


def verify_host_output(project_root: Path) -> None:
    output_path = project_root / "bin" / "main.map"
    if not output_path.is_file():
        raise RuntimeError(f"expected host file {output_path} to exist")
    text = output_path.read_text(encoding="ascii", errors="ignore")
    required = [
        "ALINK1",
        "MODULE main",
        "OBJECT OBJ/MAIN.AVO",
        "EXPORT main",
        "EXPORT helper",
        "CALL main helper",
        "INCLUDE rt.format_int",
        "INCLUDE rt.print_line",
        "INCLUDE rt.print_str",
        "RESOLVE main rt.format_int",
        "RESOLVE main rt.print_line",
        "RESOLVE main rt.print_str",
    ]
    missing = [fragment for fragment in required if fragment not in text]
    if missing:
        raise RuntimeError(f"expected host map {output_path} to contain {missing!r}")


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
    shutil.rmtree(work_root, ignore_errors=True)
    shutil.copytree(fs_root, work_root)
    project_root = prepare_workspace(work_root, project_name)

    probe = Path(__file__).with_name("vice_prg_probe.py")
    command = [
        sys.executable,
        str(probe),
        "--disk",
        str(image),
        "--vice-arg=-iecdevice9",
        "--vice-arg=-device9",
        "--vice-arg=1",
        "--vice-arg=-fs9",
        f"--vice-arg={work_root}",
        "--vice-arg=-fslongnames",
        "--feed-after",
        "A:D64/>",
        "--feed-step",
        "MOUNT B: /IMAGES/ACTION.DNP\\r",
        "--feed-step",
        "B:\\r",
        "--feed-step",
        f"CD {project_name}\\r",
        "--feed-step",
        "ALINK MAIN\\r",
        "--feed-step-mode",
        "type",
        "--feed-step-settle",
        "2.0",
        "--expected",
        "ALINK OK",
        "--contains",
        "RUN ALINK.PRG",
        "--contains",
        "ARGS MAIN",
        "--contains",
        "ALINK OK",
        "--contains",
        f"B:DNP/{project_name}>",
        "--settle",
        "3.0",
        "--timeout",
        "90",
        "--attempts",
        "1",
    ]

    for attempt in range(1, args.attempts + 1):
        result = subprocess.run(command, cwd=ROOT.parent, check=False)
        if result.returncode == 0:
            verify_host_output(project_root)
            return 0
        if attempt < args.attempts:
            time.sleep(args.attempt_delay)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
