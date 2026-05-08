#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTION = ROOT.parent / "actionc64u"
RUNNER = ROOT / "tools" / "run_action_avmrun_probe.py"
BUILD_DIR = ACTION / "build" / "udos_tools"
AVM_VERSION_V2 = 2
AVM_FLAG_ACHERON = 1
AVM_FLAG_NATIVE_HELPERS = 2
OPCODE_GROW = 0x2F
OPCODE_CLRP = 0x5C
OPCODE_SETP8 = 0x5D
OPCODE_MOVEP = 0x5F
OPCODE_SETP16 = 0x61
OPCODE_CALLN = 0x49
INTRINSIC_LINKED_PRINTREAL = 0xFE32
INTRINSIC_EXIT = 0xFF20
AVM_HEADER_SIZE_V2 = 12
AVM_LOAD_BASE = 0x3600
AVM_PAYLOAD_BASE = AVM_LOAD_BASE + AVM_HEADER_SIZE_V2
REAL7_HIGH_WORD = 0x40E0
REAL7_HIGH_WORD_REL = (REAL7_HIGH_WORD - AVM_PAYLOAD_BASE) & 0xFFFF


def build_artifacts() -> tuple[Path, bytes]:
    # This probe is intentionally a production AVMRUN fast-path proof, not an
    # asset-only staging path.
    subprocess.run(["bash", "tools/build_avmrun_udos.sh"], cwd=ACTION, check=True, stdout=subprocess.DEVNULL)
    avmrun = BUILD_DIR / "AVMRUN.PRG"
    helper = BUILD_DIR / "RT_PRINT_F_HELPER.BIN"
    if not avmrun.is_file():
        raise FileNotFoundError(avmrun)
    if not helper.is_file():
        raise FileNotFoundError(helper)
    return avmrun, helper.read_bytes()


def build_fastreal_avm(helper_blob: bytes) -> bytes:
    exec_code = bytearray()
    # Build the three-cell PrintRE frame in visible registers r1-r3:
    # r1 = flags/newline, r2 = REAL high word, r3 = REAL low word.
    # grow 4 makes the existing current register become logical r4 scratch.
    exec_code.extend((OPCODE_GROW, 0xF8))       # grow 4
    exec_code.extend((OPCODE_CLRP,))            # r4 scratch = low word 0
    exec_code.extend((OPCODE_MOVEP, 0x06))      # r3 = low word 0
    exec_code.extend((OPCODE_MOVEP, 0x08))      # back to r4 scratch
    # setp16 is payload-relative in the AVMRUN native patcher. Seed it with
    # the load-base-adjusted offset so rebasing lands on the exact REAL high word.
    exec_code.extend((OPCODE_SETP16, REAL7_HIGH_WORD_REL & 0xFF, REAL7_HIGH_WORD_REL >> 8))
    exec_code.extend((OPCODE_MOVEP, 0x04))      # r2 = high word
    exec_code.extend((OPCODE_MOVEP, 0x08))      # back to r4 scratch
    exec_code.extend((OPCODE_SETP8, 0x01))      # r4 scratch = PrintRE newline flag
    exec_code.extend((OPCODE_MOVEP, 0x02))      # r1 = flags, current rP = r1
    exec_code.extend((OPCODE_CALLN, INTRINSIC_LINKED_PRINTREAL & 0xFF, INTRINSIC_LINKED_PRINTREAL >> 8))
    exec_code.extend((OPCODE_CALLN, INTRINSIC_EXIT & 0xFF, INTRINSIC_EXIT >> 8))
    payload = bytes(exec_code)

    trailer = bytearray(b"AVH1")
    trailer.append(1)
    trailer.append(1)
    trailer.extend((len(helper_blob) & 0xFF, (len(helper_blob) >> 8) & 0xFF))
    trailer.extend(helper_blob)

    header = bytearray(b"AVM1")
    header.append(AVM_VERSION_V2)
    header.extend((len(payload) & 0xFF, (len(payload) >> 8) & 0xFF))
    header.extend((0x00, 0x00))
    header.append(AVM_FLAG_ACHERON | AVM_FLAG_NATIVE_HELPERS)
    header.extend((len(exec_code) & 0xFF, (len(exec_code) >> 8) & 0xFF))
    return bytes(header + payload + trailer)


def ensure_catalog_entries(path: Path, entries: list[str]) -> None:
    lines: list[str] = []
    if path.is_file():
        lines = [line.strip() for line in path.read_text(encoding="ascii", errors="ignore").splitlines() if line.strip()]
    for entry in entries:
        if entry not in lines:
            lines.append(entry)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="ascii")


def prepare_fs(fs_root: Path, avmrun_prg: Path, helper_blob: bytes) -> None:
    src = ROOT / "build" / "udos-release-fs"
    if fs_root.exists():
        shutil.rmtree(fs_root)
    shutil.copytree(src, fs_root)

    img = fs_root / "IMAGES" / "ACTION.DNP"
    shutil.copy2(avmrun_prg, img / "AVMRUN.PRG")
    (img / "FASTREAL.AVM").write_bytes(build_fastreal_avm(helper_blob))

    for removable in (
        "RT_PRINT_F_HELPER.BIN",
        "AVMRUN_OVL1.BIN",
        "AVMRUN_OVL2.BIN",
        "AVMRUN_OVL3.BIN",
    ):
        target = img / removable
        if target.exists():
            target.unlink()

    ensure_catalog_entries(img / "UDOSDIR.TXT", ["F AVMRUN.PRG", "F FASTREAL.AVM"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify AVMRUN linked REAL-print native fast path in VICE")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--attempt-delay", type=float, default=4.0)
    args = parser.parse_args()

    disk = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    avmrun_prg, helper_blob = build_artifacts()
    prepare_fs(fs_root, avmrun_prg, helper_blob)

    cmd = [
        "python3",
        str(RUNNER),
        "--disk",
        str(disk),
        "--fs-root",
        str(fs_root),
        "--command",
        "AVMRUN FASTREAL.AVM",
        "--run-marker",
        "RUN AVMRUN.PRG",
        "--done-fragment",
        "7",
        "--prompt-count",
        "2",
        "--contains",
        "7",
        "--not-contains",
        "UNSUPPORTED AVM",
        "--not-contains",
        "BAD AVM",
        "--not-contains",
        "HARNESS NO ACHERON",
        "--attempts",
        str(args.attempts),
        "--attempt-delay",
        str(args.attempt_delay),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
