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
ACTION_ALINK_BUILD = ROOT.parent.parent / 'actionc64u' / 'build' / 'udos_tools' / 'ALINK.PRG'
ACTION_AVMRUN_BUILD = ROOT.parent.parent / 'actionc64u' / 'build' / 'udos_tools' / 'AVMRUN.PRG'
AVM_PACK = ROOT.parent.parent / 'actionc64u' / 'tools' / 'avm_pack.py'
ACTC_CONNECT_DELAY = 32.0
ALINK_AVMRUN_CONNECT_DELAY = 44.0


def work_object_text() -> str:
    return (
        'AVO1\n'
        'x w 0 13\n'
        'b s0i0r\n'
        's TOOL\n'
        'i 7\n'
        'n w\n'
    )


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


def prepare_link_workspace(fs_root: Path, project_root: Path) -> None:
    rap.write_ascii(project_root / 'obj' / 'w.avo', work_object_text())
    rap.ensure_catalog_entries(project_root / 'obj' / 'UDOSDIR.TXT', ['F W.AVO'])
    install_program(fs_root, project_root, ACTION_ALINK_BUILD, 'ALINK.PRG')
    install_program(fs_root, project_root, ACTION_AVMRUN_BUILD, 'AVMRUN.PRG')


def verify_host_output(project_root: Path) -> None:
    rcp.verify_host_output(project_root)
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


def wait_for_shell_prompt(client: vp.BinaryMonitorClient, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_screen = ''
    retries = 0
    while time.monotonic() < deadline:
        last_screen, _d018, _dd00 = vp.read_active_screen_text(client)
        if 'A:D64/>' in last_screen:
            return
        if 'UDOS FOR COMMODORE 64' in last_screen and retries < 6:
            client.memory_set(vp.KEYBUF_COUNT, b'\x00')
            client.memory_set(vp.KEYBUF_DATA, bytes(10))
            try:
                client.keyboard_type('\r')
            except Exception:
                client.keyboard_feed('\r')
            retries += 1
            time.sleep(1.0)
            continue
        time.sleep(0.2)
    raise vp.ViceError(f"timed out waiting for screen text 'A:D64/>'; last screen was:\n{last_screen}")


def run_actc_phase(image: Path, work_root: Path, project_name: str, project_root: Path) -> None:
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
        if ACTC_CONNECT_DELAY > 0.0:
            time.sleep(ACTC_CONNECT_DELAY)
        client.connect(time.monotonic() + 20.0)
        client.ping()
        client.resume()

        wait_for_shell_prompt(client, 90.0)
        time.sleep(5.0)

        mount_command = 'MOUNT B: /IMAGES/ACTION.DNP'
        client.keyboard_feed(mount_command + '\r')
        time.sleep(1.0)
        avp.wait_for_mount_completion(client, 90.0, retry_echo=mount_command)
        time.sleep(5.0)

        client.keyboard_type('B:\r')
        vp.wait_for_screen_and_state(
            client,
            process,
            'B:DNP/',
            marker_addr=None,
            marker_value=None,
            extra_checks=[],
            timeout=90.0,
        )
        time.sleep(5.0)

        client.keyboard_type(f'CD {project_name}\r')
        vp.wait_for_screen_and_state(
            client,
            process,
            f'B:DNP/{project_name}',
            marker_addr=None,
            marker_value=None,
            extra_checks=[],
            timeout=90.0,
        )
        time.sleep(5.0)

        client.keyboard_type('ACTC MAIN\r')
        deadline = time.monotonic() + 90.0
        screen = ''
        saw_run = False
        retry_count = 0
        while time.monotonic() < deadline:
            screen, _d018, _dd00 = vp.read_active_screen_text(client)
            if 'RUN ACTC.PRG' in screen:
                saw_run = True
            if 'ACTC OK' in screen:
                return
            if saw_run and (project_root / 'obj' / 'main.avo').is_file():
                return
            if any(msg in screen for msg in ('SAVE FAIL', 'BAD LITERAL', 'BAD PROC', 'NOT IN PROJECT', 'NO FILE')):
                raise vp.ViceError(f"ACTC terminal failure ({rcp.read_actc_trace(client)}) with screen:\n{screen}")
            retry_count = avp.maybe_retry_command_enter(
                client,
                last_screen=screen,
                retry_echo='ACTC MAIN',
                retry_count=retry_count,
            )
            time.sleep(0.2)
        raise vp.ViceError(f"timed out waiting for ACTC OK ({rcp.read_actc_trace(client)}); last screen was:\n{screen}")
    finally:
        try:
            client.quit_emulator()
        finally:
            client.close()
        vp.terminate_process_tree(process)


def run_alink_avmrun_phase(image: Path, work_root: Path, project_name: str, project_root: Path) -> None:
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
        if ALINK_AVMRUN_CONNECT_DELAY > 0.0:
            time.sleep(ALINK_AVMRUN_CONNECT_DELAY)
        client.connect(time.monotonic() + 20.0)
        client.ping()
        client.resume()

        vp.wait_for_screen_and_state(
            client,
            process,
            'A:D64/>',
            marker_addr=None,
            marker_value=None,
            extra_checks=[],
            timeout=90.0,
        )
        time.sleep(5.0)

        client.keyboard_type('MOUNT B: /IMAGES/ACTION.DNP\r')
        vp.wait_for_screen_and_state(
            client,
            process,
            'A:D64/>',
            marker_addr=None,
            marker_value=None,
            extra_checks=[],
            timeout=90.0,
        )
        time.sleep(5.0)

        client.keyboard_type('B:\r')
        vp.wait_for_screen_and_state(
            client,
            process,
            'B:DNP/',
            marker_addr=None,
            marker_value=None,
            extra_checks=[],
            timeout=90.0,
        )
        time.sleep(5.0)

        client.keyboard_type(f'CD {project_name}\r')
        vp.wait_for_screen_and_state(
            client,
            process,
            f'B:DNP/{project_name}',
            marker_addr=None,
            marker_value=None,
            extra_checks=[],
            timeout=90.0,
        )
        time.sleep(5.0)

        client.keyboard_type('ALINK MAIN\r')
        deadline = time.monotonic() + 90.0
        screen = ''
        saw_alink_run = False
        retry_count = 0
        while time.monotonic() < deadline:
            screen, _d018, _dd00 = vp.read_active_screen_text(client)
            if 'RUN ALINK.PRG' in screen:
                saw_alink_run = True
            if 'ALINK OK' in screen:
                break
            if saw_alink_run and (project_root / 'bin' / 'main.avm').is_file():
                break
            if any(msg in screen for msg in ('TOO LARGE', 'SAVE FAIL', 'BAD AVO')):
                raise vp.ViceError(f'ALINK terminal failure with screen:\n{screen}')
            retry_count = avp.maybe_retry_command_enter(
                client,
                last_screen=screen,
                retry_echo='ALINK MAIN',
                retry_count=retry_count,
            )
            time.sleep(0.2)
        else:
            raise vp.ViceError(f'timed out waiting for ALINK OK; last screen was:\n{screen}')

        client.keyboard_type('AVMRUN BIN/MAIN.AVM\r')
        deadline = time.monotonic() + 90.0
        retry_count = 0
        while time.monotonic() < deadline:
            screen, _d018, _dd00 = vp.read_active_screen_text(client)
            if all(
                fragment in screen
                for fragment in (
                    'RUN AVMRUN.PRG',
                    'ARGS BIN/MAIN.AVM',
                    'TOOL7',
                    '1240',
                    f'B:DNP/{project_name}>',
                )
            ):
                return
            if any(msg in screen for msg in ('BAD AVM', 'UNSUPPORTED AVM', 'LOAD FAIL', 'NO FILE', 'TOO LARGE')):
                raise vp.ViceError(f'AVMRUN terminal failure with screen:\n{screen}')
            retry_count = avp.maybe_retry_command_enter(
                client,
                last_screen=screen,
                retry_echo='AVMRUN BIN/MAIN.AVM',
                retry_count=retry_count,
            )
            time.sleep(0.2)
        raise vp.ViceError(f'timed out waiting for ALINK -> AVMRUN proof; last screen was:\n{screen}')
    finally:
        try:
            client.quit_emulator()
        finally:
            client.close()
        vp.terminate_process_tree(process)


def run_once(image: Path, fs_root: Path, project_name: str, work_root: Path) -> None:
    shutil.rmtree(work_root, ignore_errors=True)
    shutil.copytree(fs_root, work_root, copy_function=shutil.copy)
    project_root = rcp.prepare_workspace(work_root, project_name)

    vp.cleanup_stale_vice(settle_seconds=4.0)
    run_actc_phase(image, work_root, project_name, project_root)
    rcp.verify_host_output(project_root)

    prepare_link_workspace(work_root, project_root)

    vp.cleanup_stale_vice(settle_seconds=4.0)
    run_alink_avmrun_phase(image, work_root, project_name, project_root)
    verify_host_output(project_root)


def main() -> int:
    parser = argparse.ArgumentParser(description='Run the ACTC -> ALINK -> AVMRUN pipeline by chaining the proven phase probes')
    parser.add_argument('--disk', required=True)
    parser.add_argument('--fs-root', required=True)
    parser.add_argument('--project', default='PROJ3')
    parser.add_argument('--attempts', type=int, default=2)
    parser.add_argument('--attempt-delay', type=float, default=4.0)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()
    work_root = fs_root.parent / f'{fs_root.name}-actc-alink-avmrun-direct'

    for attempt in range(1, args.attempts + 1):
        try:
            run_once(image, fs_root, project_name, work_root)
            return 0
        except (vp.ViceError, RuntimeError) as exc:
            if attempt == args.attempts:
                print(exc, file=sys.stderr)
                return 1
            time.sleep(args.attempt_delay)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
