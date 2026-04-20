#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELFTEST_ATTEMPTS = os.environ.get("SELFTEST_ATTEMPTS", "4")

CASES = ["read", "copy", "rename", "delete", "dir"]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    for name in CASES:
        run(["make", f"SELFTEST_ATTEMPTS={SELFTEST_ATTEMPTS}", f"vice-selftest-{name}"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
