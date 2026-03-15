#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import sys
import time

API_VERSION = 0x02
STX = 0x02
CMD_MEMORY_GET = 0x01
CMD_MEMORY_SET = 0x02
CMD_KEYBOARD_FEED = 0x72
CMD_PING = 0x81
CMD_EXIT = 0xAA
CMD_QUIT = 0xBB
RESP_RESUMED = 0x63
KEYBUF_COUNT = 0x00C6
KEYBUF_DATA = 0x0277
INPUT_MODE_SCRIPT = 0x01
SCRIPT_LINE_STRIDE = 32
SCRIPT_LINE_MAX = 12


class ViceError(RuntimeError):
    pass


class BinaryMonitorClient:
    def __init__(self, host: str, port: int, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: socket.socket | None = None
        self.request_id = 1

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
            deadline = time.monotonic() + (self.timeout * 3.0)
            while time.monotonic() < deadline:
                pending = self.memory_get(KEYBUF_COUNT, KEYBUF_COUNT)[0]
                if pending == 0:
                    break
                time.sleep(0.02)
            else:
                raise ViceError("timed out waiting for C64 keyboard buffer to drain")
            self.memory_set(KEYBUF_DATA, bytes((byte,)))
            self.memory_set(KEYBUF_COUNT, b"\x01")


def reserve_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def screen_code_to_ascii(code: int) -> str:
    if code in {0x00, 0x20, 0xA0}:
        return " "
    if 1 <= code <= 26:
        return chr(ord("A") + code - 1)
    if 0x30 <= code <= 0x39:
        return chr(code)
    if 0x21 <= code <= 0x2F or 0x3A <= code <= 0x3F:
        return chr(code)
    if 0x40 <= code <= 0x5A:
        return chr(code)
    return "?"


def screen_ram_to_text(data: bytes) -> str:
    chars = [screen_code_to_ascii(byte) for byte in data[:1000]]
    rows = ["".join(chars[row * 40 : (row + 1) * 40]).rstrip() for row in range(25)]
    return "\n".join(rows).strip()


def locate_x64sc() -> Path:
    candidate = shutil.which("x64sc")
    if not candidate:
        raise ViceError("x64sc not found on PATH")
    return Path(candidate).resolve()


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
) -> subprocess.Popen[str]:
    cmd = [
        str(locate_x64sc()),
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
    if keybuf is not None:
        cmd.extend(["-keybuf", decode_escapes(keybuf)])
    if keybuf_delay is not None:
        cmd.extend(["-keybuf-delay", str(keybuf_delay)])
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


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
    deadline = time.monotonic() + timeout
    last_screen = ""
    saw_fragment = False
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise ViceError(f"x64sc exited early while waiting for screen text\nstdout:\n{stdout}\nstderr:\n{stderr}")
        last_screen = screen_ram_to_text(client.memory_get(0x0400, 0x07E7))
        if fragment in last_screen:
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
        if args.feed_text is not None:
            client.keyboard_type(args.feed_text)
        if args.feed_step:
            for chunk in args.feed_step:
                if args.feed_step_mode == "type":
                    client.keyboard_type(chunk)
                else:
                    client.keyboard_feed(chunk)
                if args.feed_step_settle > 0.0:
                    time.sleep(args.feed_step_settle)
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
            if fragment not in screen:
                raise ViceError(f"expected screen fragment {fragment!r} was not present in final screen:\n{screen}")
        for fragment in args.absent:
            if fragment in screen:
                raise ViceError(f"screen fragment {fragment!r} should not be present in final screen:\n{screen}")
        return screen
    finally:
        try:
            client.quit_emulator()
        finally:
            client.close()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


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
    parser.add_argument("--feed-step-mode", choices=["feed", "type"], default="feed", help="transport to use for each --feed-step chunk")
    parser.add_argument("--feed-step-settle", type=float, default=1.0, help="seconds to wait after each --feed-step chunk")
    parser.add_argument("--labels", help="optional ld65 labels file for scripted resident input injection")
    parser.add_argument("--script-line", action="append", default=[], help="scripted input line to inject through UDOS script mode")
    parser.add_argument("--vice-arg", action="append", default=[], help="extra raw argument to pass through to x64sc")
    parser.add_argument("--settle", type=float, default=0.0, help="seconds to wait after the expected fragment before capturing the final screen")
    parser.add_argument("--timeout", type=float, default=60.0, help="seconds to wait for the banner")
    parser.add_argument("--attempts", type=int, default=1, help="number of times to retry the VICE probe before failing")
    parser.add_argument("--attempt-delay", type=float, default=1.0, help="seconds to wait between failed attempts")
    parser.add_argument("--output", help="optional file path to write the final captured screen")
    args = parser.parse_args(argv)

    attempts = max(1, args.attempts)
    last_error: ViceError | None = None
    for attempt in range(1, attempts + 1):
        try:
            screen = run_probe(args)
            if args.output:
                Path(args.output).write_text(screen + "\n")
            print(screen)
            return 0
        except ViceError as exc:
            last_error = exc
            if attempt == attempts:
                print(exc, file=sys.stderr)
                return 1
            time.sleep(max(0.0, args.attempt_delay))
    assert last_error is not None
    print(last_error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
