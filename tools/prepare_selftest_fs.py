#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

import run_action_probe_fs as pfs


def ensure_manifest_entry(path: Path, entry: str) -> None:
    lines = path.read_text(encoding="ascii").splitlines()
    if entry not in lines:
        lines.append(entry)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def map_directory_parts(parts: tuple[str, ...]) -> tuple[str, ...]:
    return parts


def copytree_vice_host_case(source: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(source):
        root_path = Path(root)
        rel = root_path.relative_to(source)
        if rel.parts:
            dest_root = dest.joinpath(*map_directory_parts(rel.parts))
        else:
            dest_root = dest
        dest_root.mkdir(parents=True, exist_ok=True)
        for dirname in dirs:
            (dest_root / dirname).mkdir(parents=True, exist_ok=True)
        for filename in files:
            dest_name = "UDOSDIR.TXT" if filename.upper() == "UDOSDIR.TXT" else filename.lower()
            shutil.copy2(root_path / filename, dest_root / dest_name)


def mirror_manifest_case(root: Path) -> None:
    for manifest in root.rglob("UDOSDIR.TXT"):
        shutil.copy2(manifest, manifest.with_name("udosdir.txt"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a clean VICE fsdevice tree for UDOS self-test runs")
    parser.add_argument("--base", required=True, help="source fsdevice root")
    parser.add_argument("--output", required=True, help="destination fsdevice root")
    args = parser.parse_args()

    base = Path(args.base)
    output = Path(args.output)
    if output.exists():
        shutil.rmtree(output)
    copytree_vice_host_case(base, output)
    mirror_manifest_case(output)

    src_dir = output / "IMAGES" / "WORK.DNP" / "SRC"
    work_dir = output / "IMAGES" / "WORK.DNP" / "WORK"
    src_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    (src_dir / "result.txt").write_text("UDOS SELFTEST RESULT\n", encoding="ascii")
    ensure_manifest_entry(src_dir / "UDOSDIR.TXT", "F RESULT.TXT")
    (work_dir / "UDOSDIR.TXT").write_text("", encoding="ascii")
    mirror_manifest_case(output)
    for stale in ("SUCCESS.TXT", "FAIL.TXT", "BOOT2.PRG", "BOOT3.PRG", "HELLO2.PRG", "HELLO3.PRG"):
        candidate = work_dir / stale.lower()
        if candidate.exists():
            candidate.unlink()
    pfs.add_case_aliases(output / "IMAGES" / "WORK.DNP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
