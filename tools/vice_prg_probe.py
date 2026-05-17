#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import signal
import socket
import struct
import subprocess
import sys
import time

API_VERSION = 0x02
STX = 0x02
CMD_MEMORY_GET = 0x01
CMD_MEMORY_SET = 0x02
CMD_REGISTERS_GET = 0x31
CMD_REGISTERS_SET = 0x32
CMD_RESOURCE_GET = 0x51
CMD_RESOURCE_SET = 0x52
CMD_KEYBOARD_FEED = 0x72
CMD_PING = 0x81
CMD_REGISTERS_AVAILABLE = 0x83
CMD_EXIT = 0xAA
CMD_QUIT = 0xBB
RESP_RESUMED = 0x63
KEYBUF_COUNT = 0x00C6
KEYBUF_DATA = 0x0277
INPUT_MODE_SCRIPT = 0x01
SCRIPT_LINE_STRIDE = 32
SCRIPT_LINE_MAX = 12
UDOS_LAUNCH_DEBUG_BYTES = (
    ("TOOL_DEBUG0", 0x03D0),
    ("TOOL_DEBUG1", 0x03D1),
    ("TOOL_DEBUG2", 0x03D2),
    ("TOOL_DEBUG3", 0x03D3),
    ("TOOL_DEBUG4", 0x03D4),
    ("TOOL_DEBUG5", 0x03D5),
    ("TOOL_DEBUG6", 0x03D6),
    ("TOOL_DEBUG7", 0x03D7),
    ("TOOL_DEBUG8", 0x03D8),
    ("TOOL_DEBUG9", 0x03D9),
    ("TOOL_DEBUG10", 0x03DA),
    ("TOOL_DEBUG11", 0x03DB),
    ("TOOL_DEBUG12", 0x03DC),
    ("TOOL_DEBUG13", 0x03DD),
    ("TOOL_DEBUG14", 0x03DE),
    ("TOOL_DEBUG15", 0x03DF),
    ("LAUNCH_RESULT_FLAG", 0x03F0),
    ("LAUNCH_EXIT_STATUS", 0x03F1),
    ("LAUNCH_TRACE_STAGE", 0x03F2),
    ("LAUNCH_TRACE_CODE", 0x03F3),
    ("WRITEBACK_TRACE_STAGE", 0x03F4),
    ("WRITEBACK_TRACE_COUNT", 0x03F5),
    ("WRITEBACK_TRACE_KIND", 0x03F6),
    ("LAUNCH_PATH_TRACE0", 0x03F7),
    ("LAUNCH_PATH_TRACE1", 0x03F8),
    ("LAUNCH_PATH_TRACE2", 0x03F9),
    ("LAUNCH_PATH_TRACE3", 0x03FA),
    ("RETURN_QUEUE_TRACE0", 0x03E8),
    ("RETURN_QUEUE_TRACE1", 0x03E9),
    ("RETURN_QUEUE_TRACE2", 0x03EA),
    ("RETURN_QUEUE_TRACE3", 0x03EB),
    ("TOOL_QUEUE_TRACE0", 0x03FB),
    ("TOOL_QUEUE_TRACE1", 0x03FC),
    ("TOOL_QUEUE_TRACE2", 0x03FD),
    ("TOOL_QUEUE_TRACE3", 0x03FE),
    ("TOOL_QUEUE_TRACE4", 0x03FF),
    ("REU_REMAIN_HI_SNAPSHOT", 0xCFE2),
    ("REU_RTS_LO_SNAPSHOT", 0xCFE3),
    ("REU_RTS_HI_SNAPSHOT", 0xCFE4),
    ("REU_ENTRY_RTS_LO_SNAPSHOT", 0xCFE5),
    ("REU_ENTRY_RTS_HI_SNAPSHOT", 0xCFE6),
    ("PROGRAM_STATE_SNAPSHOT", 0xCFF6),
    ("PROGRAM_EXIT_SNAPSHOT", 0xCFF7),
    ("STAGE_SNAPSHOT", 0xCFFD),
    ("SAVE_STAGE", 0xC59E),
    ("SAVE_OPEN0", 0xC59F),
    ("SAVE_OPEN1", 0xC5A0),
    ("SAVE_OPEN2", 0xC5A1),
    ("SAVE_OPEN3", 0xC5A2),
    ("SAVE_DEBUG_OPEN_STATUS0", 0xC59F),
    ("SAVE_DEBUG_OPEN_STATUS1", 0xC5A0),
)
SCREEN_BASE_CANDIDATES = (
    0x9400,
    0x9000,
    0x8C00,
    0x8800,
    0x8400,
    0x8000,
    0x0800,
    0x0400,
)
_SCREEN_BASE_HINT: int | None = None
MAIN_MEMSPACE = 0x00
MAIN_BANK_CPU = 0x0000
MAIN_BANK_RAM = 0x0001
MAIN_BANK_ROM = 0x0002
MAIN_BANK_IO = 0x0003
MAIN_BANK_CART = 0x0004


class ViceError(RuntimeError):
    pass


class BinaryMonitorClient:
    def __init__(self, host: str, port: int, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: socket.socket | None = None
        self.request_id = 1
        self._register_info_cache: dict[int, dict[int, tuple[str, int]]] = {}

    def connect(self, deadline: float) -> None:
        last_error: OSError | None = None
        while time.monotonic() < deadline:
            try:
                sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
                sock.settimeout(self.timeout)
                self.sock = sock
                return
            except OSError as exc:
                last_error = exc
                time.sleep(0.2)
        raise ViceError(f"unable to connect to VICE binary monitor: {last_error}")

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def _recv_exact(self, length: int) -> bytes:
        if self.sock is None:
            raise ViceError("monitor socket is not connected")
        buf = bytearray()
        while len(buf) < length:
            part = self.sock.recv(length - len(buf))
            if not part:
                raise ViceError("VICE monitor connection closed")
            buf.extend(part)
        return bytes(buf)

    def _read_response(self) -> tuple[int, int, int, bytes]:
        header = self._recv_exact(12)
        if header[0] != STX:
            raise ViceError(f"unexpected response prefix 0x{header[0]:02x}")
        version = header[1]
        if version != API_VERSION:
            raise ViceError(f"unexpected monitor API version {version}")
        body_len = struct.unpack_from("<I", header, 2)[0]
        response_type = header[6]
        error_code = header[7]
        request_id = struct.unpack_from("<I", header, 8)[0]
        body = self._recv_exact(body_len) if body_len else b""
        return response_type, error_code, request_id, body

    def _send_command(self, command_type: int, body: bytes = b"") -> int:
        if self.sock is None:
            raise ViceError("monitor socket is not connected")
        request_id = self.request_id
        self.request_id += 1
        packet = bytearray()
        packet.append(STX)
        packet.append(API_VERSION)
        packet.extend(struct.pack("<I", len(body)))
        packet.extend(struct.pack("<I", request_id))
        packet.append(command_type)
        packet.extend(body)
        self.sock.sendall(packet)
        return request_id

    def command(self, command_type: int, body: bytes = b"") -> bytes:
        request_id = self._send_command(command_type, body)
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            response_type, error_code, response_request_id, payload = self._read_response()
            if response_request_id != request_id:
                continue
            if error_code != 0:
                raise ViceError(f"VICE monitor command 0x{command_type:02x} failed with error 0x{error_code:02x}")
            if response_type != command_type:
                raise ViceError(f"VICE monitor command 0x{command_type:02x} got response 0x{response_type:02x}")
            return payload
        raise ViceError(f"timed out waiting for response to command 0x{command_type:02x}")

    def command_expect(self, command_type: int, expected_response_type: int, body: bytes = b"") -> bytes:
        request_id = self._send_command(command_type, body)
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            response_type, error_code, response_request_id, payload = self._read_response()
            if response_request_id != request_id:
                continue
            if error_code != 0:
                raise ViceError(f"VICE monitor command 0x{command_type:02x} failed with error 0x{error_code:02x}")
            if response_type != expected_response_type:
                raise ViceError(
                    f"VICE monitor command 0x{command_type:02x} got response 0x{response_type:02x}; "
                    f"expected 0x{expected_response_type:02x}"
                )
            return payload
        raise ViceError(f"timed out waiting for response to command 0x{command_type:02x}")

    def ping(self) -> None:
        self.command(CMD_PING)

    def keyboard_feed(self, text: str) -> None:
        encoded = decode_escapes(text).encode("ascii", errors="strict")
        if len(encoded) > 0xFF:
            raise ViceError("keyboard feed text is too long for a single packet")
        self.command(CMD_KEYBOARD_FEED, bytes((len(encoded),)) + encoded)
        self.resume()

    def resume(self) -> None:
        self.command(CMD_EXIT)
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            response_type, error_code, _request_id, _payload = self._read_response()
            if error_code != 0:
                raise ViceError(f"VICE resume failed with error 0x{error_code:02x}")
            if response_type == RESP_RESUMED:
                return
        raise ViceError("timed out waiting for VICE resume event")

    def quit_emulator(self) -> None:
        try:
            self.command(CMD_QUIT)
        except Exception:
            pass

    def memory_get(self, start: int, end: int, *, memspace: int = 0, bank: int = 0) -> bytes:
        body = bytes((0,)) + struct.pack("<HHBH", start, end, memspace, bank)
        response = self.command(CMD_MEMORY_GET, body)
        if len(response) < 2:
            raise ViceError("memory-get response too short")
        segment_len = struct.unpack_from("<H", response, 0)[0]
        data = response[2:]
        if segment_len != len(data):
            raise ViceError(f"memory-get length mismatch: header={segment_len} actual={len(data)}")
        self.resume()
        return data

    def memory_set(self, start: int, data: bytes, *, memspace: int = 0, bank: int = 0) -> None:
        if not data:
            return
        end = start + len(data) - 1
        body = bytes((0,)) + struct.pack("<HHBH", start, end, memspace, bank) + data
        self.command(CMD_MEMORY_SET, body)
        self.resume()

    def keyboard_type(self, text: str) -> None:
        encoded = decode_escapes(text).encode("ascii", errors="strict")
        for byte in encoded:
            deadline = time.monotonic() + 0.3
            while time.monotonic() < deadline:
                pending = self.memory_get(KEYBUF_COUNT, KEYBUF_COUNT)[0]
                if pending == 0:
                    break
                time.sleep(0.02)
            else:
                # Probe runs can leave a stale pending key count even after the
                # emulated shell has already moved on. Clear it and continue.
                self.memory_set(KEYBUF_COUNT, b"\x00")
            self.memory_set(KEYBUF_DATA, bytes((byte,)))
            self.memory_set(KEYBUF_COUNT, b"\x01")

    def resource_get(self, name: str) -> tuple[int, bytes]:
        encoded = name.encode("ascii", errors="strict")
        if not encoded or len(encoded) > 0xFF:
            raise ViceError("resource name length must be 1..255 bytes")
        response = self.command(CMD_RESOURCE_GET, bytes((len(encoded),)) + encoded)
        if len(response) < 2:
            raise ViceError("resource-get response too short")
        value_type = response[0]
        value_len = response[1]
        value = response[2:]
        if value_len != len(value):
            raise ViceError(f"resource-get length mismatch: header={value_len} actual={len(value)}")
        return value_type, value

    def resource_get_int(self, name: str) -> int:
        value_type, value = self.resource_get(name)
        if value_type != 1:
            raise ViceError(f"resource '{name}' is not an integer resource")
        if len(value) != 4:
            raise ViceError(f"resource '{name}' returned {len(value)} bytes, expected 4")
        return struct.unpack_from("<I", value, 0)[0]

    def resource_set_int(self, name: str, value: int) -> None:
        encoded = name.encode("ascii", errors="strict")
        if not encoded or len(encoded) > 0xFF:
            raise ViceError("resource name length must be 1..255 bytes")
        if value < 0 or value > 0xFFFFFFFF:
            raise ViceError("integer resource value must fit in uint32")
        body = bytearray()
        body.append(1)
        body.append(len(encoded))
        body.extend(encoded)
        body.append(4)
        body.extend(struct.pack("<I", value))
        self.command(CMD_RESOURCE_SET, bytes(body))

    def resource_get_string(self, name: str) -> str:
        value_type, value = self.resource_get(name)
        if value_type != 0:
            raise ViceError(f"resource '{name}' is not a string resource")
        return value.decode("utf-8", errors="replace")

    def resource_set_string(self, name: str, value: str) -> None:
        encoded_name = name.encode("ascii", errors="strict")
        encoded_value = value.encode("utf-8", errors="strict")
        if not encoded_name or len(encoded_name) > 0xFF:
            raise ViceError("resource name length must be 1..255 bytes")
        if not encoded_value or len(encoded_value) > 0xFF:
            raise ViceError("string resource value length must be 1..255 bytes")
        body = bytearray()
        body.append(0)
        body.append(len(encoded_name))
        body.extend(encoded_name)
        body.append(len(encoded_value))
        body.extend(encoded_value)
        self.command(CMD_RESOURCE_SET, bytes(body))

    def registers_available(self, *, memspace: int = 0) -> list[dict[str, int | str]]:
        response = self.command(CMD_REGISTERS_AVAILABLE, bytes((memspace,)))
        if len(response) < 2:
            raise ViceError("registers-available response too short")
        count = struct.unpack_from("<H", response, 0)[0]
        cursor = 2
        registers: list[dict[str, int | str]] = []
        register_info: dict[int, tuple[str, int]] = {}
        for _ in range(count):
            if cursor >= len(response):
                raise ViceError("registers-available response truncated before item header")
            item_size = response[cursor]
            cursor += 1
            if item_size < 4 or cursor + item_size > len(response):
                raise ViceError("registers-available response has invalid item size")
            reg_id = response[cursor]
            reg_bits = response[cursor + 1]
            name_len = response[cursor + 2]
            if name_len + 3 != item_size:
                raise ViceError("registers-available response has invalid name length")
            name_start = cursor + 3
            name_end = name_start + name_len
            name = response[name_start:name_end].decode("ascii", errors="replace")
            entry = {"id": reg_id, "bits": reg_bits, "name": name}
            registers.append(entry)
            register_info[reg_id] = (name, reg_bits)
            cursor += item_size
        if cursor != len(response):
            raise ViceError("registers-available response has trailing bytes")
        self._register_info_cache[memspace] = register_info
        self.resume()
        return registers

    def registers_get(self, *, memspace: int = 0) -> dict[str, int]:
        register_info = self._register_info_cache.get(memspace)
        if register_info is None:
            self.registers_available(memspace=memspace)
            register_info = self._register_info_cache.get(memspace, {})
        response = self.command(CMD_REGISTERS_GET, bytes((memspace,)))
        if len(response) < 2:
            raise ViceError("registers-get response too short")
        count = struct.unpack_from("<H", response, 0)[0]
        cursor = 2
        registers: dict[str, int] = {}
        for _ in range(count):
            if cursor >= len(response):
                raise ViceError("registers-get response truncated before item header")
            item_size = response[cursor]
            cursor += 1
            if item_size < 3 or cursor + item_size > len(response):
                raise ViceError("registers-get response has invalid item size")
            reg_id = response[cursor]
            reg_val = struct.unpack_from("<H", response, cursor + 1)[0]
            reg_name = register_info.get(reg_id, (f"REG_{reg_id}", 16))[0]
            registers[reg_name] = reg_val
            cursor += item_size
        if cursor != len(response):
            raise ViceError("registers-get response has trailing bytes")
        self.resume()
        return registers

    def registers_set(self, updates: dict[str, int], *, memspace: int = 0) -> None:
        if not updates:
            return
        register_info = self._register_info_cache.get(memspace)
        if register_info is None:
            self.registers_available(memspace=memspace)
            register_info = self._register_info_cache.get(memspace, {})
        name_to_id = {name: reg_id for reg_id, (name, _bits) in register_info.items()}
        body = bytearray((memspace,))
        body.extend(struct.pack("<H", len(updates)))
        for name, value in updates.items():
            reg_id = name_to_id.get(name)
            if reg_id is None:
                raise ViceError(f"unknown register '{name}' for memspace {memspace}")
            body.append(3)
            body.append(reg_id)
            body.extend(struct.pack("<H", value & 0xFFFF))
        response = self.command_expect(CMD_REGISTERS_SET, CMD_REGISTERS_GET, bytes(body))
        if len(response) < 2:
            raise ViceError("registers-set response too short")
        self.resume()


def reserve_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def petscii_to_ascii(code: int) -> str:
    if code == 0x0D:
        return "\n"
    if code == 0x0A:
        return "\r"
    if code <= 0x1F:
        return "."
    if code in {0xA0, 0xE0}:
        return " "
    if 0xC1 <= code <= 0xDA:
        return chr(ord("A") + code - 0xC1)
    if 0x41 <= code <= 0x5A:
        return chr(ord("a") + code - 0x41)
    if 0x20 <= code <= 0x7E:
        return chr(code)
    return "."


def screen_code_to_ascii(code: int) -> str:
    code &= 0x7F
    if code <= 0x1F:
        code += 0x40
    elif 0x40 <= code <= 0x5F:
        code += 0x20
    return petscii_to_ascii(code)


def screen_ram_to_text(data: bytes) -> str:
    chars = [screen_code_to_ascii(byte) for byte in data[:1000]]
    rows = ["".join(chars[row * 40 : (row + 1) * 40]).rstrip() for row in range(25)]
    return "\n".join(rows).strip()


def normalize_screen_text(text: str) -> str:
    return text.casefold()


def screen_contains(screen: str, fragment: str) -> bool:
    return normalize_screen_text(fragment) in normalize_screen_text(screen)


def screen_count(screen: str, fragment: str) -> int:
    return normalize_screen_text(screen).count(normalize_screen_text(fragment))


def active_screen_base(d018: int, dd00: int) -> int:
    if d018 == 0xFF and dd00 == 0xFF:
        return 0x0400
    vic_bank = ((dd00 ^ 0x03) & 0x03) * 0x4000
    screen_offset = ((d018 >> 4) & 0x0F) * 0x0400
    return vic_bank + screen_offset


def screen_text_score(text: str) -> int:
    useful = sum(1 for ch in text if ch.isalnum() or ch in " :/>,.-()")
    score = useful - (text.count("?") * 4)
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if lines:
        unique_lines = len(set(lines))
        if len(lines) >= 8 and unique_lines <= 2:
            score -= 400
    if "UDOS FOR COMMODORE 64" in text:
        score += 200
    return score


def best_screen_text_from_candidates(client: BinaryMonitorClient, *bases: int) -> tuple[str, int | None]:
    best_text = ""
    best_base: int | None = None
    best_score = -10_000
    seen: set[int] = set()
    for base in bases:
        if base in seen:
            continue
        seen.add(base)
        text = screen_ram_to_text(client.memory_get(base, base + 999, memspace=MAIN_MEMSPACE, bank=MAIN_BANK_RAM))
        if not text:
            continue
        score = screen_text_score(text)
        if score > best_score:
            best_text = text
            best_base = base
            best_score = score
    return best_text, best_base


def screen_base_candidates(screen_base: int | None = None) -> tuple[int, ...]:
    bases: list[int] = []
    if screen_base is not None:
        bases.append(screen_base)
    if _SCREEN_BASE_HINT is not None:
        bases.append(_SCREEN_BASE_HINT)
    bases.extend(SCREEN_BASE_CANDIDATES)
    return tuple(bases)


def screen_text_containing_fragment(
    client: BinaryMonitorClient,
    fragment: str,
    *bases: int,
) -> tuple[str, int | None]:
    seen: set[int] = set()
    for base in bases:
        if base in seen:
            continue
        seen.add(base)
        text = screen_ram_to_text(client.memory_get(base, base + 999, memspace=MAIN_MEMSPACE, bank=MAIN_BANK_RAM))
        if screen_contains(text, fragment):
            return text, base
    return "", None


def read_active_screen_text(client: BinaryMonitorClient) -> tuple[str, int, int]:
    global _SCREEN_BASE_HINT
    d018 = client.memory_get(0xD018, 0xD018, memspace=MAIN_MEMSPACE, bank=MAIN_BANK_IO)[0]
    dd00 = client.memory_get(0xDD00, 0xDD00, memspace=MAIN_MEMSPACE, bank=MAIN_BANK_IO)[0]
    screen_base = active_screen_base(d018, dd00)
    active_text = screen_ram_to_text(
        client.memory_get(screen_base, screen_base + 999, memspace=MAIN_MEMSPACE, bank=MAIN_BANK_RAM)
    )
    _SCREEN_BASE_HINT = screen_base
    return active_text, d018, dd00


def read_screen_text_for_fragment(client: BinaryMonitorClient, fragment: str) -> tuple[str, int, int]:
    global _SCREEN_BASE_HINT
    active_text, d018, dd00 = read_active_screen_text(client)
    if screen_contains(active_text, fragment):
        return active_text, d018, dd00
    fallback_text, fallback_base = screen_text_containing_fragment(
        client,
        fragment,
        *screen_base_candidates(active_screen_base(d018, dd00)),
    )
    if fallback_text:
        if fallback_base is not None:
            _SCREEN_BASE_HINT = fallback_base
        return fallback_text, d018, dd00
    return active_text, d018, dd00


def read_debug_bytes(
    client: BinaryMonitorClient,
    entries: tuple[tuple[str, int], ...] | list[tuple[str, int]],
) -> list[tuple[str, int, int]]:
    snapshot: list[tuple[str, int, int]] = []
    for label, addr in entries:
        value = client.memory_get(addr, addr)[0]
        snapshot.append((label, addr, value))
    return snapshot


def format_debug_snapshot(snapshot: list[tuple[str, int, int]]) -> str:
    parts = [f"{label}=0x{value:02X}@0x{addr:04X}" for label, addr, value in snapshot]
    return "VICE debug bytes: " + " ".join(parts)


def format_udos_launch_trace(client: BinaryMonitorClient) -> str:
    return format_debug_snapshot(read_debug_bytes(client, UDOS_LAUNCH_DEBUG_BYTES))


def locate_x64sc() -> Path:
    override = os.environ.get("VICE_X64SC")
    if override:
        candidate = Path(override).expanduser()
        if candidate.is_file():
            return candidate.resolve()
        raise ViceError(f"VICE_X64SC does not point to a file: {candidate}")
    windows_candidates = (
        Path(r"C:\c64\vice\GTK3VICE-3.10-win64\bin\x64sc.exe"),
        Path("/mnt/c/c64/vice/GTK3VICE-3.10-win64/bin/x64sc.exe"),
    )
    if os.name != "nt":
        for name in ("x64sc", "x64"):
            candidate = shutil.which(name)
            if candidate:
                return prefer_known_good_linux_vice(Path(candidate).resolve())
    for candidate in windows_candidates:
        if candidate.is_file():
            return candidate.resolve()
    candidate = shutil.which("x64sc")
    if candidate:
        return prefer_known_good_linux_vice(Path(candidate).resolve())
    raise ViceError("x64sc not found on PATH")


def locate_xvfb_run() -> Path | None:
    candidate = shutil.which("xvfb-run")
    if not candidate:
        return None
    return Path(candidate).resolve()


def display_is_usable() -> bool:
    display = os.environ.get("DISPLAY")
    if not display:
        return False
    try:
        result = subprocess.run(
            ["xdpyinfo"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5.0,
            check=False,
        )
    except Exception:
        return False
    return result.returncode == 0


def using_headless_xvfb(executable: Path) -> bool:
    if executable.suffix.lower() == ".exe":
        return False
    if display_is_usable():
        return False
    return locate_xvfb_run() is not None


def default_connect_delays() -> tuple[float, ...]:
    try:
        executable = locate_x64sc()
    except ViceError:
        return (0.0,)
    if executable.suffix.lower() == ".exe":
        return (8.0, 10.0, 12.0, 15.0)
    if using_headless_xvfb(executable):
        return (20.0, 24.0, 28.0, 32.0)
    return (11.0, 9.0, 13.0, 10.0, 14.0, 12.0)


def default_connect_delay() -> float:
    return default_connect_delays()[0]


def default_attempt_delay() -> float:
    try:
        executable = locate_x64sc()
    except ViceError:
        return 1.0
    if executable.suffix.lower() == ".exe":
        return 5.0
    if using_headless_xvfb(executable):
        return 4.0
    return 2.0


_VICE_OPTION_STYLE_CACHE: dict[str, tuple[bool, bool, bool]] = {}
_VICE_VERSION_CACHE: dict[str, str] = {}


def vice_version(path: Path) -> str:
    cache_key = str(path)
    cached = _VICE_VERSION_CACHE.get(cache_key)
    if cached is not None:
        return cached
    try:
        result = subprocess.run(
            [str(path), "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5.0,
            check=False,
        )
        line = result.stdout.splitlines()[0].strip() if result.stdout else ""
    except Exception:
        line = ""
    _VICE_VERSION_CACHE[cache_key] = line
    return line


def prefer_known_good_linux_vice(candidate: Path) -> Path:
    if os.name == "nt":
        return candidate
    distro_candidate = Path("/usr/bin/x64sc")
    if candidate == distro_candidate or not distro_candidate.is_file():
        return candidate
    if vice_version(candidate).startswith("x64sc (VICE 3.10)") and vice_version(distro_candidate).startswith(
        "x64sc (VICE 3.7.1)"
    ):
        return distro_candidate.resolve()
    return candidate


def _vice_binary_contains(path: Path, needle: bytes) -> bool:
    overlap = max(0, len(needle) - 1)
    tail = b""
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                return False
            window = tail + chunk
            if needle in window:
                return True
            tail = window[-overlap:] if overlap else b""


def normalize_vice_args_for_executable(executable: Path, extra_args: list[str]) -> list[str]:
    if not extra_args:
        return []
    cache_key = str(executable)
    cached = _VICE_OPTION_STYLE_CACHE.get(cache_key)
    if cached is None:
        cached = (
            _vice_binary_contains(executable, b"-busdevice9"),
            _vice_binary_contains(executable, b"-devicebackend9"),
            _vice_binary_contains(executable, b"-trapdevice9"),
        )
        _VICE_OPTION_STYLE_CACHE[cache_key] = cached
    use_busdevice, use_devicebackend, use_trapdevice = cached
    normalized: list[str] = []
    for arg in extra_args:
        if use_busdevice and (arg.startswith("-iecdevice") or arg.startswith("+iecdevice")):
            arg = arg[0] + "busdevice" + arg[len(arg[0] + "iecdevice") :]
        elif use_devicebackend and (arg.startswith("-device") or arg.startswith("+device")):
            arg = arg[0] + "devicebackend" + arg[len(arg[0] + "device") :]
        elif use_trapdevice and (arg.startswith("-virtualdev") or arg.startswith("+virtualdev")):
            arg = arg[0] + "trapdevice" + arg[len(arg[0] + "virtualdev") :]
        normalized.append(arg)
    return normalized


def enable_virtual_devices_for_filesystem_args(extra_args: list[str]) -> list[str]:
    if not extra_args:
        return []
    enabled_args = list(extra_args)
    for device in range(8, 12):
        fs_arg = f"-fs{device}"
        legacy_device_arg = f"-device{device}"
        modern_device_arg = f"-devicebackend{device}"
        legacy_virtual_arg = f"-virtualdev{device}"
        modern_virtual_arg = f"-trapdevice{device}"
        has_fs_root = fs_arg in extra_args
        has_filesystem_backend = False
        for index, arg in enumerate(extra_args[:-1]):
            if arg not in {legacy_device_arg, modern_device_arg}:
                continue
            if extra_args[index + 1] == "1":
                has_filesystem_backend = True
                break
        if not has_fs_root and not has_filesystem_backend:
            continue
        if any(
            arg in {legacy_virtual_arg, f"+virtualdev{device}", modern_virtual_arg, f"+trapdevice{device}"}
            for arg in extra_args
        ):
            continue
        enabled_args.append(legacy_virtual_arg)
    return enabled_args


def load_ld65_labels(path: Path) -> dict[str, int]:
    symbols: dict[str, int] = {}
    for line in path.read_text(errors="ignore").splitlines():
        parts = line.split()
        if len(parts) != 3 or parts[0] != "al":
            continue
        try:
            addr = int(parts[1], 16)
        except ValueError:
            continue
        name = parts[2]
        symbols[name] = addr
        if name.startswith("."):
            symbols[name[1:]] = addr
    return symbols


def decode_escapes(text: str) -> str:
    return (
        text.replace("\\r", "\r")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
    )


def launch_vice(
    image: Path,
    port: int,
    *,
    keybuf: str | None = None,
    keybuf_delay: int | None = None,
    extra_args: list[str] | None = None,
    capture_output: bool = False,
) -> subprocess.Popen[str]:
    global _SCREEN_BASE_HINT
    _SCREEN_BASE_HINT = None
    executable = locate_x64sc()
    vice_cmd = [
        str(executable),
        "-default",
        "-binarymonitor",
        "-binarymonitoraddress",
        f"ip4://127.0.0.1:{port}",
        "-autostart",
        str(image),
        "-warp",
        "-reu",
        "-reusize",
        "16384",
        "+sound",
        "-sounddev",
        "dummy",
    ]
    if executable.suffix.lower() != ".exe":
        vice_cmd.insert(2, "-console")
    if keybuf is not None:
        vice_cmd.extend(["-keybuf", decode_escapes(keybuf)])
    if keybuf_delay is not None:
        vice_cmd.extend(["-keybuf-delay", str(keybuf_delay)])
    if extra_args:
        extra_args = enable_virtual_devices_for_filesystem_args(extra_args)
        vice_cmd.extend(normalize_vice_args_for_executable(executable, extra_args))

    cmd = vice_cmd
    if executable.suffix.lower() != ".exe" and not display_is_usable():
        xvfb_run = locate_xvfb_run()
        if xvfb_run is not None:
            cmd = [
                str(xvfb_run),
                "-a",
                "-s",
                "-screen 0 1024x768x24",
                *vice_cmd,
            ]
    popen_kwargs: dict[str, object] = {
        "stdout": subprocess.PIPE if capture_output else subprocess.DEVNULL,
        "stderr": subprocess.PIPE if capture_output else subprocess.DEVNULL,
        "text": True,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True
    return subprocess.Popen(cmd, **popen_kwargs)


def terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        process.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        return
    process.terminate()
    try:
        process.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        process.wait(timeout=5)


def cleanup_stale_vice(*, settle_seconds: float | None = None) -> None:
    if os.name == "nt":
        for process_name in ("x64.exe", "x64sc.exe"):
            subprocess.run(
                ["taskkill", "/IM", process_name, "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
    else:
        for process_name in ("x64", "x64sc", "xvfb-run", "Xvfb"):
            subprocess.run(
                ["pkill", "-x", process_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
    if settle_seconds is None:
        settle_seconds = 1.0 if os.name != "nt" else 5.0
    if settle_seconds > 0.0:
        time.sleep(settle_seconds)


def wait_for_screen_and_state(
    client: BinaryMonitorClient,
    process: subprocess.Popen[str],
    fragment: str,
    *,
    marker_addr: int | None,
    marker_value: int | None,
    extra_checks: list[tuple[int, int]],
    timeout: float,
) -> str:
    global _SCREEN_BASE_HINT
    deadline = time.monotonic() + timeout
    last_screen = ""
    saw_fragment = False
    dead_start_polls = 0
    blank_start_polls = 0
    startup_reconnects = 0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise ViceError(f"x64sc exited early while waiting for screen text\nstdout:\n{stdout}\nstderr:\n{stderr}")
        last_screen, d018, dd00 = read_screen_text_for_fragment(client, fragment)
        if not last_screen:
            blank_start_polls += 1
        else:
            blank_start_polls = 0
        if not last_screen and d018 == 0xFF and dd00 == 0xFF:
            dead_start_polls += 1
        else:
            dead_start_polls = 0
        if dead_start_polls >= 150 or blank_start_polls >= 150:
            if startup_reconnects < 1:
                startup_reconnects += 1
                try:
                    client.close()
                except Exception:
                    pass
                time.sleep(1.0)
                reconnect_deadline = min(deadline, time.monotonic() + 20.0)
                client.connect(reconnect_deadline)
                client.ping()
                client.resume()
                dead_start_polls = 0
                blank_start_polls = 0
                time.sleep(1.0)
                continue
            time.sleep(0.2)
            continue
        if screen_contains(last_screen, fragment):
            saw_fragment = True
        if saw_fragment:
            marker_ok = True
            if marker_addr is not None and marker_value is not None:
                marker = client.memory_get(marker_addr, marker_addr)[0]
                marker_ok = marker == marker_value
            if marker_ok:
                checks_ok = True
                for addr, value in extra_checks:
                    actual = client.memory_get(addr, addr)[0]
                    if actual != value:
                        checks_ok = False
                        break
                if checks_ok:
                    return last_screen
        time.sleep(0.2)
    raise ViceError(f"timed out waiting for screen text {fragment!r}; last screen was:\n{last_screen}")


def run_probe(args: argparse.Namespace) -> str:
    image = Path(args.disk).resolve()
    if not image.is_file():
        raise SystemExit(f"disk image not found: {image}")

    port = reserve_tcp_port()
    process = launch_vice(
        image,
        port,
        keybuf=args.keybuf,
        keybuf_delay=args.keybuf_delay,
        extra_args=args.vice_arg,
    )
    client = BinaryMonitorClient("127.0.0.1", port, timeout=5.0)
    try:
        connect_delay = args.connect_delay if args.connect_delay is not None else default_connect_delay()
        if connect_delay > 0.0:
            time.sleep(connect_delay)
        client.connect(time.monotonic() + 20.0)
        client.ping()
        client.resume()
        marker_addr = int(args.marker_address, 0) if args.marker_address is not None else None
        marker_value = int(args.marker_value, 0) if args.marker_value is not None else None
        extra_checks: list[tuple[int, int]] = []
        for item in args.check_byte:
            addr_text, value_text = item.split("=", 1)
            addr = int(addr_text, 0)
            value = int(value_text, 0)
            extra_checks.append((addr, value))
        if args.script_line:
            if args.labels is None:
                raise ViceError("--script-line requires --labels")
            if args.feed_after is None:
                raise ViceError("--script-line requires --feed-after so the live prompt can be reached first")
            labels = load_ld65_labels(Path(args.labels).resolve())
            required = ["input_mode", "script_index", "script_line_count", "script_line_data"]
            missing = [name for name in required if name not in labels]
            if missing:
                raise ViceError(f"labels file missing symbols: {', '.join(missing)}")
            wait_for_screen_and_state(
                client,
                process,
                args.feed_after,
                marker_addr=None,
                marker_value=None,
                extra_checks=[],
                timeout=args.timeout,
            )
            if len(args.script_line) > SCRIPT_LINE_MAX:
                raise ViceError(f"at most {SCRIPT_LINE_MAX} --script-line values are supported")
            blob = bytearray(SCRIPT_LINE_STRIDE * SCRIPT_LINE_MAX)
            for index, line in enumerate(args.script_line):
                encoded = line.encode("ascii", errors="strict")
                if len(encoded) > SCRIPT_LINE_STRIDE - 1:
                    raise ViceError(f"script line {index + 1} is too long")
                start = index * SCRIPT_LINE_STRIDE
                blob[start : start + len(encoded)] = encoded
            client.memory_set(labels["script_line_data"], bytes(blob))
            client.memory_set(labels["script_index"], b"\x00")
            client.memory_set(labels["script_line_count"], bytes((len(args.script_line),)))
            client.memory_set(labels["input_mode"], bytes((INPUT_MODE_SCRIPT,)))
        if args.feed_text is not None or args.feed_step:
            if args.feed_after:
                wait_for_screen_and_state(
                    client,
                    process,
                    args.feed_after,
                    marker_addr=None,
                    marker_value=None,
                    extra_checks=[],
                    timeout=args.timeout,
                )
                if args.feed_after_settle > 0.0:
                    time.sleep(args.feed_after_settle)
        if args.feed_text is not None:
            client.keyboard_type(args.feed_text)
        if args.feed_step:
            step_after = list(args.feed_step_after)
            step_modes = list(args.feed_step_mode_seq)
            while len(step_after) < len(args.feed_step):
                step_after.append("")
            while len(step_modes) < len(args.feed_step):
                step_modes.append(args.feed_step_mode)
            for index, chunk in enumerate(args.feed_step):
                if step_modes[index] == "type":
                    client.keyboard_type(chunk)
                else:
                    client.keyboard_feed(chunk)
                if args.feed_step_settle > 0.0:
                    time.sleep(args.feed_step_settle)
                fragment = step_after[index]
                if fragment:
                    wait_for_screen_and_state(
                        client,
                        process,
                        fragment,
                        marker_addr=None,
                        marker_value=None,
                        extra_checks=[],
                        timeout=args.timeout,
                    )
                    if args.feed_step_after_settle > 0.0:
                        time.sleep(args.feed_step_after_settle)
        screen = wait_for_screen_and_state(
            client,
            process,
            args.expected,
            marker_addr=marker_addr,
            marker_value=marker_value,
            extra_checks=extra_checks,
            timeout=args.timeout,
        )
        if args.settle > 0.0:
            time.sleep(args.settle)
            screen = screen_ram_to_text(client.memory_get(0x0400, 0x07E7))
        for fragment in args.contains:
            if not screen_contains(screen, fragment):
                raise ViceError(f"expected screen fragment {fragment!r} was not present in final screen:\n{screen}")
        for fragment in args.absent:
            if screen_contains(screen, fragment):
                raise ViceError(f"screen fragment {fragment!r} should not be present in final screen:\n{screen}")
        return screen
    finally:
        try:
            client.quit_emulator()
        finally:
            client.close()
        terminate_process_tree(process)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Autostart a PRG or disk image in VICE and verify the expected runtime state")
    parser.add_argument("--disk", required=True, help="path to a PRG or disk image to autostart")
    parser.add_argument("--expected", required=True, help="screen fragment to wait for")
    parser.add_argument("--marker-address", help="optional hex or decimal address for a marker byte")
    parser.add_argument("--marker-value", help="optional expected marker byte value")
    parser.add_argument("--check-byte", action="append", default=[], help="extra checks in addr=value form, hex or decimal")
    parser.add_argument("--contains", action="append", default=[], help="extra screen fragments that must be present in the final screen")
    parser.add_argument("--absent", action="append", default=[], help="screen fragments that must not be present in the final screen")
    parser.add_argument("--keybuf", help="optional VICE -keybuf string to inject during autostart")
    parser.add_argument("--keybuf-delay", type=int, help="optional VICE -keybuf-delay value")
    parser.add_argument("--feed-after", help="optional screen fragment to wait for before binary-monitor keyboard feed")
    parser.add_argument("--feed-text", help="optional text to feed through the VICE binary monitor after startup")
    parser.add_argument("--feed-step", action="append", default=[], help="stepwise text chunk to feed through the VICE binary monitor")
    parser.add_argument("--feed-step-after", action="append", default=[], help="optional screen fragment to wait for after the corresponding --feed-step")
    parser.add_argument("--feed-step-after-settle", type=float, default=0.0, help="seconds to wait after a --feed-step-after match before sending the next step")
    parser.add_argument("--feed-step-mode", choices=["feed", "type"], default="feed", help="transport to use for each --feed-step chunk")
    parser.add_argument("--feed-step-mode-seq", action="append", choices=["feed", "type"], default=[], help="optional transport override for the corresponding --feed-step")
    parser.add_argument("--feed-after-settle", type=float, default=0.0, help="seconds to wait after --feed-after matches before sending feed text")
    parser.add_argument("--feed-step-settle", type=float, default=1.0, help="seconds to wait after each --feed-step chunk")
    parser.add_argument("--connect-delay", type=float, help="optional seconds to wait before attaching the binary monitor")
    parser.add_argument("--labels", help="optional ld65 labels file for scripted resident input injection")
    parser.add_argument("--script-line", action="append", default=[], help="scripted input line to inject through UDOS script mode")
    parser.add_argument("--vice-arg", action="append", default=[], help="extra raw argument to pass through to x64sc")
    parser.add_argument("--settle", type=float, default=0.0, help="seconds to wait after the expected fragment before capturing the final screen")
    parser.add_argument("--timeout", type=float, default=60.0, help="seconds to wait for the banner")
    parser.add_argument("--attempts", type=int, default=1, help="number of times to retry the VICE probe before failing")
    parser.add_argument("--attempt-delay", type=float, help="seconds to wait between failed attempts")
    parser.add_argument("--output", help="optional file path to write the final captured screen")
    args = parser.parse_args(argv)

    attempts = max(1, args.attempts)
    connect_delays = (args.connect_delay,) if args.connect_delay is not None else default_connect_delays()
    attempt_delay = args.attempt_delay if args.attempt_delay is not None else default_attempt_delay()
    last_error: ViceError | None = None
    for attempt in range(1, attempts + 1):
        try:
            cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, attempt_delay)))
            attempt_args = argparse.Namespace(**vars(args))
            attempt_args.connect_delay = connect_delays[(attempt - 1) % len(connect_delays)]
            screen = run_probe(attempt_args)
            if args.output:
                Path(args.output).write_text(screen + "\n")
            print(screen)
            return 0
        except ViceError as exc:
            last_error = exc
            if attempt == attempts:
                print(exc, file=sys.stderr)
                return 1
            time.sleep(max(0.0, attempt_delay))
    assert last_error is not None
    print(last_error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
