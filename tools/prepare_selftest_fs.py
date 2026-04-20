#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def ensure_manifest_entry(path: Path, entry: str) -> None:
    lines = path.read_text(encoding="ascii").splitlines()
    if entry not in lines:
        lines.append(entry)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def copytree_lowercase(source: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(source):
        root_path = Path(root)
        rel = root_path.relative_to(source)
        if rel.parts:
            dest_root = dest.joinpath(*[part.lower() for part in rel.parts])
        else:
            dest_root = dest
        dest_root.mkdir(parents=True, exist_ok=True)
        for dirname in dirs:
            (dest_root / dirname.lower()).mkdir(parents=True, exist_ok=True)
        for filename in files:
            shutil.copy2(root_path / filename, dest_root / filename.lower())


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a clean VICE fsdevice tree for UDOS self-test runs")
    parser.add_argument("--base", required=True, help="source fsdevice root")
    parser.add_argument("--output", required=True, help="destination fsdevice root")
    args = parser.parse_args()

    base = Path(args.base)
    output = Path(args.output)
    if output.exists():
        shutil.rmtree(output)
    copytree_lowercase(base, output)

    src_dir = output / "images" / "work.dnp" / "src"
    work_dir = output / "images" / "work.dnp" / "work"
    src_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    (src_dir / "RESULT.TXT").write_text("UDOS SELFTEST RESULT\n", encoding="ascii")
    ensure_manifest_entry(src_dir / "UDOSDIR.TXT", "F RESULT.TXT")
    (work_dir / "UDOSDIR.TXT").write_text("", encoding="ascii")
    for stale in ("SUCCESS.TXT", "FAIL.TXT", "BOOT2.PRG", "BOOT3.PRG", "HELLO2.PRG", "HELLO3.PRG"):
        candidate = work_dir / stale
        if candidate.exists():
            candidate.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
