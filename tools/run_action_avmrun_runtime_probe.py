#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTION = ROOT.parent / 'actionc64u'
RUNNER = ROOT / 'tools' / 'run_action_avmrun_probe.py'


def build_avmrun() -> Path:
    subprocess.run(['bash', 'tools/build_avmrun_udos.sh'], cwd=ACTION, check=True, stdout=subprocess.DEVNULL)
    prg = ACTION / 'build' / 'udos_tools' / 'AVMRUN.PRG'
    if not prg.is_file():
        raise FileNotFoundError(prg)
    return prg


def pack_text(text_path: Path, output_path: Path) -> None:
    subprocess.run(
        ['python3', str(ACTION / 'tools' / 'avm_pack.py'), '--text', '--flags', '1', str(text_path), '--output', str(output_path)],
        cwd=ACTION,
        check=True,
    )


def prepare_fs(fs_root: Path, avmrun_prg: Path) -> None:
    src = ROOT / 'build' / 'udos-release-fs'
    if fs_root.exists():
        shutil.rmtree(fs_root)
    shutil.copytree(src, fs_root)
    img = fs_root / 'IMAGES' / 'ACTION.DNP'
    samples = {
        'RUNTC.AVT': (
            'entry start\n'
            'code $0d\n'
            'start:\n'
            '  push16 100\n'
            '  push16 24\n'
            '  add\n'
            '  calln printie\n'
            '  calln exit\n'
        ),
        'RUNTG.AVT': (
            'entry start\n'
            'code $17\n'
            'start:\n'
            '  push16 60\n'
            '  push16 57\n'
            '  sub\n'
            '  calln printie\n'
            '  push16 60\n'
            '  push16 57\n'
            '  gt\n'
            '  calln printie\n'
            '  calln exit\n'
        ),
    }
    for name, text in samples.items():
        txt = img / name
        avm = img / name.replace('.AVT', '.AVM')
        txt.write_text(text, encoding='ascii')
        pack_text(txt, avm)
    shutil.copy2(avmrun_prg, img / 'AVMRUN.PRG')
    manifest = img / 'UDOSDIR.TXT'
    lines = [line.strip() for line in manifest.read_text(encoding='ascii', errors='ignore').splitlines() if line.strip()]
    for entry in ('F AVMRUN.PRG', 'F RUNTC.AVM', 'F RUNTC.AVT', 'F RUNTG.AVM', 'F RUNTG.AVT'):
        if entry not in lines:
            lines.append(entry)
    manifest.write_text('\n'.join(lines) + '\n', encoding='ascii')


def run_probe(disk: Path, fs_root: Path, command: str, *checks: str, attempts: int, attempt_delay: float) -> None:
    args = [
        'python3', str(RUNNER),
        '--disk', str(disk),
        '--fs-root', str(fs_root),
        '--command', command,
        '--b-prompt', 'B:DNP/',
        '--final-prompt', 'B:DNP/>',
        '--done-fragment', '',
        '--not-contains', 'UNSUPPORTED AVM',
        '--not-contains', 'BAD AVM',
        '--attempts', str(attempts),
        '--attempt-delay', str(attempt_delay),
        '--shell-timeout', '40',
        '--boot-timeout', '60',
    ]
    for check in checks:
        args.extend(['--contains', check])
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description='Verify AVMRUN runtime arithmetic/comparison samples in VICE')
    parser.add_argument('--disk', required=True)
    parser.add_argument('--fs-root', required=True)
    parser.add_argument('--attempts', type=int, default=3)
    parser.add_argument('--attempt-delay', type=float, default=4.0)
    args = parser.parse_args()

    disk = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    avmrun_prg = build_avmrun()
    prepare_fs(fs_root, avmrun_prg)
    run_probe(disk, fs_root, 'AVMRUN RUNTC.AVM', '124', attempts=args.attempts, attempt_delay=args.attempt_delay)
    run_probe(disk, fs_root, 'AVMRUN RUNTG.AVM', '3', '1', attempts=args.attempts, attempt_delay=args.attempt_delay)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
