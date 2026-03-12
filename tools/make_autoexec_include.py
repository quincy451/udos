#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def render_bytes(data: bytes) -> str:
    if not data:
        return "    .byte $00\n"
    parts = [f"${byte:02x}" for byte in data]
    lines: list[str] = []
    width = 16
    for index in range(0, len(parts), width):
        lines.append("    .byte " + ", ".join(parts[index : index + width]))
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a ca65 include file for UDOS AUTOEXEC.BAT content")
    parser.add_argument("--input", required=True, help="plain-text AUTOEXEC source file")
    parser.add_argument("--output", required=True, help="assembler include output path")
    args = parser.parse_args()

    source = Path(args.input)
    output = Path(args.output)

    text = source.read_text(encoding="ascii")
    lines = text.splitlines()
    payload = b"\r".join(line.encode("ascii") for line in lines) + b"\x00"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_bytes(payload), encoding="ascii")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
