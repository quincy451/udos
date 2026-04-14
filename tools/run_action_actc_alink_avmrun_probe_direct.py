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
import vice_prg_probe as vp

ROOT = Path(__file__).resolve().parent
ACTION_ALINK_BUILD = ROOT.parent.parent / 'actionc64u' / 'build' / 'udos_tools' / 'ALINK.PRG'
ACTION_AVMRUN_BUILD = ROOT.parent.parent / 'actionc64u' / 'build' / 'udos_tools' / 'AVMRUN.PRG'
AVM_PACK = ROOT.parent.parent / 'actionc64u' / 'tools' / 'avm_pack.py'
ACTC_CONNECT_DELAY = rcp.CONNECT_DELAYS[0]
ALINK_AVMRUN_CONNECT_DELAY = rap.CONNECT_DELAYS[0]
AVMRUN_CONNECT_DELAY = rap.CONNECT_DELAYS[0]
STAGE_ATTEMPTS = 3
STAGE_ATTEMPT_DELAY = 2.0
ACTC_PHASE_TIMEOUT = 180.0
ALINK_PHASE_TIMEOUT = 180.0
AVMRUN_PHASE_TIMEOUT = 180.0


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
        'code $35\n'
        'setp16 main_str0\n'
        'calln printe\n'
        'call w\n'
        'push16 50\n'
        'push16 7\n'
        'add\n'
        'push16 3\n'
        'sub\n'
        'calln printi\n'
        'push16 60\n'
        'push16 3\n'
        'sub\n'
        'push16 2\n'
        'add\n'
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
    lowercase_workspace = rcp.detect_lowercase_workspace(fs_root)
    images_root = rcp.case_insensitive_child(fs_root, rcp.host_name('IMAGES', lowercase_workspace))
    action_root = rcp.case_insensitive_child(images_root, rcp.host_name('ACTION.DNP', lowercase_workspace))
    root_target = action_root / rcp.host_name(name, lowercase_workspace)
    shutil.copy2(build_path, root_target)
    shutil.copy2(root_target, project_root / rcp.host_name(name, lowercase_workspace))
    rap.ensure_catalog_entries(
        action_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace),
        [f'D {project_root.name.upper()}', f'F {name}'],
    )
    rap.ensure_catalog_entries(project_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace), [f'F {name}'])


def prepare_link_workspace(fs_root: Path, project_root: Path) -> None:
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    obj_root = project_root / rcp.host_name('OBJ', lowercase_workspace)
    rap.write_ascii(obj_root / rcp.host_name('W.AVO', lowercase_workspace), work_object_text())
    rap.ensure_catalog_entries(obj_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace), ['F W.AVO'])
    install_program(fs_root, project_root, ACTION_ALINK_BUILD, 'ALINK.PRG')
    install_program(fs_root, project_root, ACTION_AVMRUN_BUILD, 'AVMRUN.PRG')


def verify_host_output(project_root: Path) -> None:
    rcp.verify_host_output(project_root)
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    avm_path = project_root / rcp.host_name('BIN', lowercase_workspace) / rcp.host_name('MAIN.AVM', lowercase_workspace)
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


def run_actc_phase(image: Path, work_root: Path, project_name: str, project_root: Path) -> None:
    cmd = [
        sys.executable,
        str(ROOT / 'run_action_avmrun_probe.py'),
        '--disk',
        str(image),
        '--fs-root',
        str(work_root),
        '--command',
        'ACTC MAIN',
        '--pre-command',
        f'CD {project_name}',
        '--pre-prompt',
        f'B:DNP/{project_name}',
        '--final-prompt',
        f'B:DNP/{project_name}>',
        '--run-marker',
        'RUN ACTC.PRG',
        '--done-fragment',
        '',
        '--contains',
        'ARGS MAIN',
        '--not-contains',
        'BAD LITERAL',
        '--not-contains',
        'BAD PROC',
        '--not-contains',
        'NOT IN PROJECT',
        '--not-contains',
        'NO FILE',
        '--not-contains',
        'SAVE FAIL',
        '--attempts',
        '1',
        '--connect-delay',
        str(ACTC_CONNECT_DELAY),
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=ACTC_PHASE_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise vp.ViceError(f'ACTC phase timed out after {ACTC_PHASE_TIMEOUT:.0f}s') from exc
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or 'ACTC phase failed'
        raise vp.ViceError(details)

    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    avo_path = project_root / rcp.host_name('OBJ', lowercase_workspace) / rcp.host_name('MAIN.AVO', lowercase_workspace)
    if not avo_path.is_file():
        raise vp.ViceError(f'ACTC phase completed without expected host output {avo_path}')


def run_alink_phase(image: Path, work_root: Path, project_name: str, project_root: Path) -> None:
    cmd = [
        sys.executable,
        str(ROOT / 'run_action_avmrun_probe.py'),
        '--disk',
        str(image),
        '--fs-root',
        str(work_root),
        '--command',
        'ALINK MAIN',
        '--pre-command',
        f'CD {project_name}',
        '--pre-prompt',
        f'B:DNP/{project_name}',
        '--final-prompt',
        f'B:DNP/{project_name}>',
        '--run-marker',
        'RUN ALINK.PRG',
        '--done-fragment',
        '',
        '--contains',
        'ARGS MAIN',
        '--not-contains',
        'SAVE FAIL',
        '--not-contains',
        'BAD AVO',
        '--not-contains',
        'TOO LARGE',
        '--attempts',
        '1',
        '--connect-delay',
        str(ALINK_AVMRUN_CONNECT_DELAY),
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=ALINK_PHASE_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise vp.ViceError(f'ALINK phase timed out after {ALINK_PHASE_TIMEOUT:.0f}s') from exc
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or 'ALINK phase failed'
        raise vp.ViceError(details)


def run_avmrun_phase(image: Path, work_root: Path, project_name: str) -> None:
    cmd = [
        sys.executable,
        str(ROOT / 'run_action_avmrun_probe.py'),
        '--disk',
        str(image),
        '--fs-root',
        str(work_root),
        '--command',
        'AVMRUN BIN/MAIN.AVM',
        '--pre-command',
        f'CD {project_name}',
        '--pre-prompt',
        f'B:DNP/{project_name}',
        '--final-prompt',
        f'B:DNP/{project_name}>',
        '--run-marker',
        'RUN AVMRUN.PRG',
        '--done-fragment',
        '5459',
        '--contains',
        'HELLO',
        '--contains',
        'TOOL7',
        '--contains',
        'ARGS BIN/MAIN.AVM',
        '--attempts',
        '1',
        '--connect-delay',
        str(AVMRUN_CONNECT_DELAY),
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=AVMRUN_PHASE_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise vp.ViceError(f'AVMRUN phase timed out after {AVMRUN_PHASE_TIMEOUT:.0f}s') from exc
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or 'AVMRUN phase failed'
        raise vp.ViceError(details)


def run_once(image: Path, fs_root: Path, project_name: str, work_root: Path) -> None:
    shutil.rmtree(work_root, ignore_errors=True)
    shutil.copytree(fs_root, work_root, copy_function=shutil.copy)
    project_root = rcp.prepare_workspace(work_root, project_name)

    last_exc: Exception | None = None
    for attempt in range(1, STAGE_ATTEMPTS + 1):
        try:
            vp.cleanup_stale_vice(settle_seconds=4.0)
            run_actc_phase(image, work_root, project_name, project_root)
            last_exc = None
            break
        except vp.ViceError as exc:
            last_exc = exc
            if attempt == STAGE_ATTEMPTS:
                raise
            time.sleep(STAGE_ATTEMPT_DELAY)
    if last_exc is not None:
        raise last_exc
    rcp.verify_host_output(project_root)

    prepare_link_workspace(work_root, project_root)

    last_exc: Exception | None = None
    for attempt in range(1, STAGE_ATTEMPTS + 1):
        try:
            vp.cleanup_stale_vice(settle_seconds=4.0)
            run_alink_phase(image, work_root, project_name, project_root)
            last_exc = None
            break
        except vp.ViceError as exc:
            last_exc = exc
            if attempt == STAGE_ATTEMPTS:
                raise
            time.sleep(STAGE_ATTEMPT_DELAY)
    if last_exc is not None:
        raise last_exc
    verify_host_output(project_root)

    last_exc = None
    for attempt in range(1, STAGE_ATTEMPTS + 1):
        try:
            vp.cleanup_stale_vice(settle_seconds=4.0)
            run_avmrun_phase(image, work_root, project_name)
            last_exc = None
            break
        except vp.ViceError as exc:
            last_exc = exc
            if attempt == STAGE_ATTEMPTS:
                raise
            time.sleep(STAGE_ATTEMPT_DELAY)
    if last_exc is not None:
        raise last_exc


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
