#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import run_action_actc_probe as rcp
import run_action_alink_probe as rap
import run_action_avmrun_probe as avp
import vice_prg_probe as vp

ROOT = Path(__file__).resolve().parent
ACTION_ALINK_BUILD = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "ALINK.PRG"
ACTION_AVMRUN_BUILD = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "AVMRUN.PRG"
AVM_PACK = ROOT.parent.parent / "actionc64u" / "tools" / "avm_pack.py"
CONNECT_DELAYS = rap.CONNECT_DELAYS
ALINK_RESIDENT_DEBUG = (
    ("RETURN0", 0x03E8),
    ("RETURN1", 0x03E9),
    ("RETURN2", 0x03EA),
    ("RETURN3", 0x03EB),
    ("ALINK_TRACE", 0x03FC),
    ("DBG_FD", 0x03FD),
    ("DBG_FE", 0x03FE),
    ("DBG_FF", 0x03FF),
    ("WRITEBACK_STAGE", 0x03F4),
    ("SAVE_STAGE", 0xC59E),
    ("SAVE_OPEN0", 0xC59F),
    ("SAVE_OPEN1", 0xC5A0),
    ("SAVE_OPEN2", 0xC5A1),
    ("SAVE_OPEN3", 0xC5A2),
)
ALINK_SAVE_PATH_ADDR = 0xC5A3
ALINK_SAVE_PATH_LEN = 96
PROMPT_TIMEOUT = 90.0
SETTLE_SECONDS = 5.0


def source_text() -> str:
    return (
        'MODULE MAIN\r'
        'PROC MAIN()\r'
        'PrintE("HELLO")\r'
        'W()\r'
        'PrintI((100 + 20) + 4)\r'
        'PrintIE((60 - 3) > (50 + 7))\r'
        'RETURN\r'
    )


def work_object_text() -> str:
    return (
        'AVO1\n'
        'x w 0 13\n'
        'b s0i0r\n'
        's TOOL\n'
        'i 7\n'
        'n w\n'
    )


def expected_main_object_fragments() -> list[str]:
    return [
        'AVO1',
        'x main 0 30',
        'b e0u0p0p1ayp2p3gzr',
        'u w',
        's HELLO',
        'i 120',
        'i 4',
        'i 57\ni 57',
        'k 7',
        'n main',
    ]


def expected_avm_source() -> str:
    return (
        'entry 0\n'
        'code $2d\n'
        'setp16 main_str0\n'
        'calln printe\n'
        'call w\n'
        'push16 120\n'
        'push16 4\n'
        'add\n'
        'calln printi\n'
        'push16 57\n'
        'push16 57\n'
        'gt\n'
        'calln printie\n'
        'calln exit\n'
        'w:\n'
        'setp16 w_str0\n'
        'calln print\n'
        'push16 7\n'
        'calln printie\n'
        'ret\n'
        'main_str0:\n'
        'stringz HELLO\n'
        'w_str0:\n'
        'stringz TOOL\n'
    )


def install_program(fs_root: Path, project_root: Path, build_path: Path, name: str) -> None:
    if not build_path.is_file():
        raise RuntimeError(f'missing built program: {build_path}')
    root_target = fs_root / 'IMAGES' / 'ACTION.DNP' / name
    shutil.copy2(build_path, root_target)
    shutil.copy2(root_target, project_root / name)
    rap.ensure_catalog_entries(
        fs_root / 'IMAGES' / 'ACTION.DNP' / 'UDOSDIR.TXT',
        [f'D {project_root.name.upper()}', f'F {name}'],
    )
    rap.ensure_catalog_entries(project_root / 'UDOSDIR.TXT', [f'F {name}'])


def prepare_workspace(fs_root: Path, project_name: str) -> Path:
    project_root = fs_root / 'IMAGES' / 'ACTION.DNP' / project_name.upper()
    lower_project_root = project_root.parent / project_root.name.lower()
    shutil.rmtree(project_root, ignore_errors=True)
    shutil.rmtree(lower_project_root, ignore_errors=True)
    (project_root / 'src').mkdir(parents=True, exist_ok=True)
    (project_root / 'bin').mkdir(exist_ok=True)
    (project_root / 'obj').mkdir(exist_ok=True)

    rap.write_ascii(project_root / 'readme.txt', 'ACTION PROJECT READY\n')
    rap.write_ascii(project_root / 'ACTION.PROJ', 'ACTION PROJECT\rMAIN.ACT\r')
    rap.write_ascii(project_root / 'UDOSDIR.TXT', 'D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF README.TXT\n')
    rap.write_ascii(project_root / 'src' / 'UDOSDIR.TXT', 'F MAIN.ACT\n')
    rap.write_ascii(project_root / 'bin' / 'UDOSDIR.TXT', '')
    rap.write_ascii(project_root / 'obj' / 'UDOSDIR.TXT', 'F W.AVO\n')
    rap.write_ascii(project_root / 'src' / 'main.act', source_text())
    rap.write_ascii(project_root / 'obj' / 'w.avo', work_object_text())

    install_program(fs_root, project_root, rcp.ACTION_ACTC_BUILD, 'ACTC.PRG')
    install_program(fs_root, project_root, ACTION_ALINK_BUILD, 'ALINK.PRG')
    install_program(fs_root, project_root, ACTION_AVMRUN_BUILD, 'AVMRUN.PRG')
    return project_root


def verify_host_output(project_root: Path) -> None:
    object_path = project_root / 'obj' / 'main.avo'
    if not object_path.is_file():
        raise RuntimeError(f'expected host file {object_path} to exist')
    object_text = object_path.read_text(encoding='ascii', errors='ignore')
    missing = [fragment for fragment in expected_main_object_fragments() if fragment not in object_text]
    if missing:
        raise RuntimeError(f'expected host object {object_path} to contain {missing!r}')

    avm_path = project_root / 'bin' / 'main.avm'
    if not avm_path.is_file():
        raise RuntimeError(f'expected host file {avm_path} to exist')
    with tempfile.TemporaryDirectory() as tmpdir:
        expected_text_path = Path(tmpdir) / 'expected.avm.txt'
        expected_packed_path = Path(tmpdir) / 'expected.avm'
        expected_text_path.write_text(expected_avm_source(), encoding='ascii')
        subprocess.run(
            [
                sys.executable,
                str(AVM_PACK),
                '--text',
                '--flags',
                '1',
                str(expected_text_path),
                '-o',
                str(expected_packed_path),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        packed = avm_path.read_bytes()
        expected = expected_packed_path.read_bytes()
    if packed != expected:
        raise RuntimeError(f'expected packed AVM bytes {expected!r}, got {packed!r}')


def read_alink_trace(client: vp.BinaryMonitorClient) -> str:
    try:
        debug = vp.format_debug_snapshot(vp.read_debug_bytes(client, ALINK_RESIDENT_DEBUG))
        raw = client.memory_get(ALINK_SAVE_PATH_ADDR, ALINK_SAVE_PATH_ADDR + ALINK_SAVE_PATH_LEN - 1)
        path_bytes = bytes(raw).split(b'\x00', 1)[0]
        path = path_bytes.decode('ascii', errors='replace')
        return f'{debug} SAVE_PATH={path!r}'
    except Exception:
        return 'ALINK_TRACE=<unavailable>'


def run_once(image: Path, work_root: Path, project_name: str, connect_delay: float) -> None:
    project_root = work_root / 'IMAGES' / 'ACTION.DNP' / project_name.upper()
    port = vp.reserve_tcp_port()
    process = vp.launch_vice(
        image,
        port,
        extra_args=[
            '-iecdevice9',
            '-device9',
            '1',
            '-fs9',
            str(work_root),
            '-fslongnames',
        ],
    )
    client = vp.BinaryMonitorClient('127.0.0.1', port, timeout=5.0)
    try:
        if connect_delay > 0.0:
            time.sleep(connect_delay)
        client.connect(time.monotonic() + 20.0)
        client.ping()
        client.resume()

        vp.wait_for_screen_and_state(client, process, 'A:D64/>', marker_addr=None, marker_value=None, extra_checks=[], timeout=PROMPT_TIMEOUT)
        time.sleep(SETTLE_SECONDS)

        mount_command = 'MOUNT B: /IMAGES/ACTION.DNP'
        client.keyboard_feed(mount_command + '\r')
        time.sleep(1.0)
        avp.wait_for_mount_completion(client, PROMPT_TIMEOUT, retry_echo=mount_command)
        time.sleep(SETTLE_SECONDS)

        avp.type_command(client, 'B:', PROMPT_TIMEOUT)
        vp.wait_for_screen_and_state(client, process, 'B:DNP/', marker_addr=None, marker_value=None, extra_checks=[], timeout=PROMPT_TIMEOUT)
        time.sleep(SETTLE_SECONDS)

        cd_command = f'CD {project_name}'
        avp.type_command(client, cd_command, PROMPT_TIMEOUT)
        vp.wait_for_screen_and_state(client, process, f'B:DNP/{project_name}', marker_addr=None, marker_value=None, extra_checks=[], timeout=PROMPT_TIMEOUT)
        time.sleep(SETTLE_SECONDS)

        client.keyboard_type('ACTC MAIN\r')
        deadline = time.monotonic() + PROMPT_TIMEOUT
        screen = ''
        while time.monotonic() < deadline:
            screen, _d018, _dd00 = vp.read_active_screen_text(client)
            if 'ACTC OK' in screen:
                break
            if any(msg in screen for msg in ('BAD LITERAL', 'BAD PROC', 'NOT IN PROJECT', 'NO FILE', 'SAVE FAIL')):
                raise vp.ViceError(f'ACTC terminal failure with screen:\n{screen}')
            time.sleep(0.2)
        else:
            raise vp.ViceError(f'timed out waiting for ACTC OK; last screen was:\n{screen}')

        client.keyboard_type('ALINK MAIN\r')
        deadline = time.monotonic() + PROMPT_TIMEOUT
        saw_alink_run = False
        while time.monotonic() < deadline:
            screen, _d018, _dd00 = vp.read_active_screen_text(client)
            if 'RUN ALINK.PRG' in screen:
                saw_alink_run = True
            if 'ALINK OK' in screen:
                break
            if saw_alink_run and f'B:DNP/{project_name}>' in screen and (project_root / 'bin' / 'main.avm').is_file():
                break
            if any(msg in screen for msg in ('TOO LARGE', 'SAVE FAIL', 'BAD AVO')):
                raise vp.ViceError(f'ALINK terminal failure ({read_alink_trace(client)}) with screen:\n{screen}')
            time.sleep(0.2)
        else:
            raise vp.ViceError(f'timed out waiting for ALINK completion ({read_alink_trace(client)}); last screen was:\n{screen}')

        client.keyboard_type('AVMRUN BIN/MAIN.AVM\r')
        deadline = time.monotonic() + PROMPT_TIMEOUT
        while time.monotonic() < deadline:
            screen, _d018, _dd00 = vp.read_active_screen_text(client)
            if all(
                fragment in screen
                for fragment in (
                    'RUN ACTC.PRG',
                    'ACTC OK',
                    'RUN ALINK.PRG',
                    'RUN AVMRUN.PRG',
                    'ARGS BIN/MAIN.AVM',
                    'HELLO',
                    'TOOL7',
                    '1240',
                    f'B:DNP/{project_name}>',
                )
            ):
                return
            if any(msg in screen for msg in ('BAD AVM', 'UNSUPPORTED AVM', 'LOAD FAIL', 'NO FILE', 'TOO LARGE')):
                raise vp.ViceError(f'AVMRUN terminal failure with screen:\n{screen}')
            time.sleep(0.2)
        raise vp.ViceError(f'timed out waiting for ACTC -> ALINK -> AVMRUN proof; last screen was:\n{screen}')
    finally:
        try:
            client.quit_emulator()
        finally:
            client.close()
        vp.terminate_process_tree(process)


def main() -> int:
    parser = argparse.ArgumentParser(description='Run the ACTC -> ALINK -> AVMRUN pipeline through the direct typed release-image path')
    parser.add_argument('--disk', required=True)
    parser.add_argument('--fs-root', required=True)
    parser.add_argument('--project', default='PROJ3')
    parser.add_argument('--attempts', type=int, default=3)
    parser.add_argument('--attempt-delay', type=float, default=4.0)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()
    work_root = fs_root.parent / f'{fs_root.name}-actc-alink-avmrun-direct'

    for attempt in range(1, args.attempts + 1):
        connect_delay = CONNECT_DELAYS[(attempt - 1) % len(CONNECT_DELAYS)]
        try:
            shutil.rmtree(work_root, ignore_errors=True)
            shutil.copytree(fs_root, work_root, copy_function=shutil.copy)
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


if __name__ == '__main__':
    raise SystemExit(main())
