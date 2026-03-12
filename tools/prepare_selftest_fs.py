#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def ensure_manifest_entry(path: Path, entry: str) -> None:
    lines = path.read_text(encoding="ascii").splitlines()
    if entry not in lines:
        lines.append(entry)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a clean VICE fsdevice tree for UDOS self-test runs")
    parser.add_argument("--base", required=True, help="source fsdevice root")
    parser.add_argument("--output", required=True, help="destination fsdevice root")
    args = parser.parse_args()

    base = Path(args.base)
    output = Path(args.output)
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(base, output)

    src_dir = output / "IMAGES" / "WORK.DNP" / "SRC"
    work_dir = output / "IMAGES" / "WORK.DNP" / "WORK"
    src_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    (src_dir / "RESULT.TXT").write_text("UDOS SELFTEST RESULT\n", encoding="ascii")
    ensure_manifest_entry(src_dir / "UDOSDIR.TXT", "F RESULT.TXT")
    (work_dir / "UDOSDIR.TXT").write_text("", encoding="ascii")
    for stale in ("SUCCESS.TXT", "FAIL.TXT", "BOOT2.PRG", "BOOT3.PRG"):
        candidate = work_dir / stale
        if candidate.exists():
            candidate.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
