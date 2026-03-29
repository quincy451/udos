#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
import tempfile
from pathlib import Path

import vice_prg_probe as vp


ROOT = Path(__file__).resolve().parent
ACTION_ALINK_BUILD = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "ALINK.PRG"
AVM_PACK = ROOT.parent.parent / "actionc64u" / "tools" / "avm_pack.py"
CONNECT_DELAYS = (44.0, 40.0, 36.0, 32.0, 28.0, 24.0)


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


def main_object_text() -> str:
    return (
        'AVO1\n'
        'x main 0 19\n'
        'b s0u0u1i0r\n'
        'u h\n'
        'u t\n'
        's HELLO\n'
        'i 42\n'
        'k 7\n'
        'n main\n'
    )


def helper_object_text() -> str:
    return (
        'AVO1\n'
        'x h 0 7\n'
        'x z 7 1\n'
        'b u0c1r\n'
        'b r\n'
        'u u\n'
        'n h\n'
    )


def tool_object_text() -> str:
    return (
        'AVO1\n'
        'x t 0 16\n'
        'b s0i0u0r\n'
        's TOOL\n'
        'i 7\n'
        'u u\n'
        'n t\n'
    )


def util_object_text() -> str:
    return (
        'AVO1\n'
        'x u 0 4\n'
        'x v 4 1\n'
        'b c1r\n'
        'b r\n'
        'n u\n'
    )


def expected_avm_text() -> str:
    return (
        "entry main\n"
        "main:\n"
        "setp16 main_str0\n"
        "calln print\n"
        "call h\n"
        "call t\n"
        "push16 42\n"
        "calln printie\n"
        "ret\n"
        "h:\n"
        "call u\n"
        "call z\n"
        "ret\n"
        "z:\n"
        "ret\n"
        "t:\n"
        "setp16 t_str0\n"
        "calln print\n"
        "push16 7\n"
        "calln printie\n"
        "call u\n"
        "ret\n"
        "t_str0:\n"
        "stringz TOOL\n"
        "u:\n"
        "call v\n"
        "ret\n"
        "v:\n"
        "ret\n"
        "main_str0:\n"
        "stringz HELLO\n"
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
    write_ascii(project_root / "obj" / "UDOSDIR.TXT", "F H.AVO\nF MAIN.AVO\nF T.AVO\nF U.AVO\n")
    write_ascii(project_root / "src" / "main.act", 'MODULE MAIN\rPROC MAIN()\rPrint("HELLO")\rPrintIE(42)\rRETURN\r')
    write_ascii(project_root / "obj" / "main.avo", main_object_text())
    write_ascii(project_root / "obj" / "h.avo", helper_object_text())
    write_ascii(project_root / "obj" / "t.avo", tool_object_text())
    write_ascii(project_root / "obj" / "u.avo", util_object_text())

    if ACTION_ALINK_BUILD.is_file():
        root_target = fs_root / "IMAGES" / "ACTION.DNP" / "ALINK.PRG"
        shutil.copy2(ACTION_ALINK_BUILD, root_target)
        shutil.copy2(root_target, project_root / "ALINK.PRG")
        ensure_catalog_entries(fs_root / "IMAGES" / "ACTION.DNP" / "UDOSDIR.TXT", [f"D {project_name.upper()}", "F ALINK.PRG"])
        ensure_catalog_entries(project_root / "UDOSDIR.TXT", ["F ALINK.PRG"])

    return project_root


def verify_host_output(project_root: Path) -> None:
    avm_text_path = project_root / "bin" / "main.avmtxt"
    if not avm_text_path.is_file():
        raise RuntimeError(f"expected host file {avm_text_path} to exist")
    avm_text = avm_text_path.read_text(encoding="ascii", errors="ignore")
    required_avm_text = [
        "entry main",
        "main:",
        "setp16 main_str0",
        "calln print",
        "call h",
        "call t",
        "push16 42",
        "calln printie",
        "h:",
        "call u",
        "call z",
        "z:",
        "t:",
        "setp16 t_str0",
        "calln print",
        "push16 7",
        "calln printie",
        "call u",
        "u:",
        "call v",
        "v:",
        "t_str0:",
        "stringz TOOL",
        "stringz HELLO",
        "ret",
    ]
    missing_avm_text = [fragment for fragment in required_avm_text if fragment not in avm_text]
    if missing_avm_text:
        raise RuntimeError(f"expected host AVM text {avm_text_path} to contain {missing_avm_text!r}")
    with tempfile.TemporaryDirectory() as tmpdir:
        packed_path = Path(tmpdir) / "main.avm"
        expected_text_path = Path(tmpdir) / "expected.avm.txt"
        expected_packed_path = Path(tmpdir) / "expected.avm"
        expected_text_path.write_text(expected_avm_text(), encoding="ascii")
        for src, dst in ((avm_text_path, packed_path), (expected_text_path, expected_packed_path)):
            subprocess.run(
                [
                    sys.executable,
                    str(AVM_PACK),
                    "--text",
                    "--flags",
                    "1",
                    str(src),
                    "-o",
                    str(dst),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        packed = packed_path.read_bytes()
        expected = expected_packed_path.read_bytes()
    if packed != expected:
        raise RuntimeError(f"expected packed AVM bytes {expected!r}, got {packed!r}")


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

        client.keyboard_type("MOUNT B: /IMAGES/ACTION.DNP\r")
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

        client.keyboard_type("B:\r")
        vp.wait_for_screen_and_state(
            client,
            process,
            "B:DNP/",
            marker_addr=None,
            marker_value=None,
            extra_checks=[],
            timeout=90.0,
        )
        time.sleep(5.0)

        client.keyboard_type(f"CD {project_name}\r")
        vp.wait_for_screen_and_state(
            client,
            process,
            f"B:DNP/{project_name}",
            marker_addr=None,
            marker_value=None,
            extra_checks=[],
            timeout=90.0,
        )
        time.sleep(5.0)

        client.keyboard_type("ALINK MAIN\r")
        screen = vp.wait_for_screen_and_state(
            client,
            process,
            "ALINK OK",
            marker_addr=None,
            marker_value=None,
            extra_checks=[],
            timeout=90.0,
        )

        for fragment in ("RUN ALINK.PRG", "ARGS MAIN", "ALINK OK", f"B:DNP/{project_name}>"):
            if fragment not in screen:
                raise vp.ViceError(f"expected screen fragment {fragment!r} was not present in final screen:\n{screen}")
    finally:
        try:
            client.quit_emulator()
        finally:
            client.close()
        vp.terminate_process_tree(process)


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

    for attempt in range(1, args.attempts + 1):
        connect_delay = CONNECT_DELAYS[(attempt - 1) % len(CONNECT_DELAYS)]
        try:
            shutil.rmtree(work_root, ignore_errors=True)
            shutil.copytree(fs_root, work_root)
            project_root = prepare_workspace(work_root, project_name)
            vp.cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, args.attempt_delay)))
            run_once(image, work_root, project_name, connect_delay)
            verify_host_output(project_root)
            return 0
        except vp.ViceError as exc:
            if attempt == args.attempts:
                print(exc, file=sys.stderr)
                return 1
            time.sleep(args.attempt_delay)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
