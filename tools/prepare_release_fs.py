#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def rewrite_manifest(path: Path, drop: set[str]) -> None:
    if not path.exists():
        return
    kept: list[str] = []
    for line in path.read_text(encoding="ascii").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) != 2:
            kept.append(stripped)
            continue
        name = parts[1].upper()
        if name in drop:
            continue
        kept.append(stripped)
    path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a clean VICE fsdevice tree for UDOS release images")
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
    src_manifest = src_dir / "UDOSDIR.TXT"
    work_manifest = work_dir / "UDOSDIR.TXT"

    for name in ("ARGS.BAT", "BATCH.BAT", "STOP.BAT"):
        candidate = src_dir / name
        if candidate.exists():
            candidate.unlink()
    rewrite_manifest(src_manifest, {"ARGS.BAT", "BATCH.BAT", "STOP.BAT"})

    work_dir.mkdir(parents=True, exist_ok=True)
    if not work_manifest.exists():
        work_manifest.write_text("", encoding="ascii")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
