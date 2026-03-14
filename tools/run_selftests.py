#!/usr/bin/env python3
from __future__ import annotations

import difflib
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELFTEST_ROOT = ROOT / "tests" / "selftest"
VICE_FS_ROOT = ROOT / "tests" / "vicefs"
PYTHON = sys.executable

CASES = [
    ("read", "READ OK", 60),
    ("copy", "COPY OK", 60),
    ("rename", "RENAME OK", 120),
    ("delete", "DELETE OK", 60),
    ("dir", "DIR OK", 60),
]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    for name, expected_fragment, timeout in CASES:
        build_dir = ROOT / "build" / f"selftest-{name}"
        fs_dir = ROOT / "build" / f"selftest-{name}-fs"
        artifact = ROOT / "build" / f"udos-selftest-{name}.d64"
        actual = ROOT / "build" / f"udos-selftest-{name}.actual.txt"
        expected = SELFTEST_ROOT / f"expected_{name}.txt"
        autoexec = SELFTEST_ROOT / f"autoexec_{name}.txt"

        run([PYTHON, str(ROOT / "tools" / "prepare_selftest_fs.py"), "--base", str(VICE_FS_ROOT), "--output", str(fs_dir)])
        run(["make", f"BUILD_DIR={build_dir.relative_to(ROOT)}", f"AUTOEXEC_SRC={autoexec.relative_to(ROOT)}", "resident"])
        shutil.copy2(build_dir / "udos-resident.d64", artifact)
        time.sleep(2.0)

        run(
            [
                PYTHON,
                str(ROOT / "tools" / "vice_prg_probe.py"),
                "--disk",
                str(artifact),
                "--vice-arg=-iecdevice8",
                "--vice-arg=-device8",
                "--vice-arg=1",
                f"--vice-arg=-fs8",
                f"--vice-arg={build_dir}",
                "--vice-arg=-iecdevice9",
                "--vice-arg=-device9",
                "--vice-arg=1",
                f"--vice-arg=-fs9",
                f"--vice-arg={fs_dir}",
                "--vice-arg=-fslongnames",
                "--expected",
                expected_fragment,
                "--settle",
                "2.0",
                "--attempts",
                "2",
                "--timeout",
                str(timeout),
                "--output",
                str(actual),
            ]
        )

        actual_text = actual.read_text()
        expected_text = expected.read_text()
        if actual_text != expected_text:
            diff = "".join(
                difflib.unified_diff(
                    expected_text.splitlines(keepends=True),
                    actual_text.splitlines(keepends=True),
                    fromfile=str(expected),
                    tofile=str(actual),
                )
            )
            sys.stderr.write(diff)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
