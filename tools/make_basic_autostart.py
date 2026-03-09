#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

LOAD_ADDR = 0x1000
BASIC_ADDR = 0x0801


def parse_start_address(labels_path: Path) -> int:
    for line in labels_path.read_text().splitlines():
        line = line.strip()
        if line.endswith(" .start"):
            parts = line.split()
            if len(parts) >= 3:
                return int(parts[1], 16)
    raise SystemExit(f"could not find .start in labels file: {labels_path}")


def build_basic_stub(entry_addr: int) -> bytes:
    sys_text = str(entry_addr).encode("ascii")
    line = bytearray()
    body_len = 2 + 1 + 1 + len(sys_text) + 1
    next_line_addr = BASIC_ADDR + 4 + body_len
    line.extend(next_line_addr.to_bytes(2, "little"))
    line.extend((10).to_bytes(2, "little"))
    line.append(0x9E)
    line.append(0x20)
    line.extend(sys_text)
    line.append(0x00)
    line.extend((0x0000).to_bytes(2, "little"))
    return bytes(line)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Wrap a $1000 PRG in a BASIC SYS autostart loader")
    parser.add_argument("--input", required=True, help="input PRG with load address $1000")
    parser.add_argument("--labels", required=True, help="ld65 labels file containing .start")
    parser.add_argument("--output", required=True, help="output autostart PRG")
    args = parser.parse_args(argv)

    source = Path(args.input)
    labels = Path(args.labels)
    target = Path(args.output)
    data = source.read_bytes()
    if len(data) < 2:
        raise SystemExit("input PRG is too short")
    load_addr = int.from_bytes(data[:2], "little")
    if load_addr != LOAD_ADDR:
        raise SystemExit(f"expected load address ${LOAD_ADDR:04X}, got ${load_addr:04X}")

    entry_addr = parse_start_address(labels)
    basic = build_basic_stub(entry_addr)
    filler_len = LOAD_ADDR - (BASIC_ADDR + len(basic))
    if filler_len < 0:
        raise SystemExit("BASIC stub overlaps machine code start")

    wrapped = bytearray()
    wrapped.extend(BASIC_ADDR.to_bytes(2, "little"))
    wrapped.extend(basic)
    wrapped.extend(b"\x00" * filler_len)
    wrapped.extend(data[2:])
    target.write_bytes(wrapped)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
