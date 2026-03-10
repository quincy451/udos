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
CMD_PING = 0x81
CMD_EXIT = 0xAA
CMD_QUIT = 0xBB
RESP_RESUMED = 0x63


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


def decode_keybuf(text: str) -> str:
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
        "+sound",
        "-sounddev",
        "dummy",
    ]
    if keybuf is not None:
        cmd.extend(["-keybuf", decode_keybuf(keybuf)])
    if keybuf_delay is not None:
        cmd.extend(["-keybuf-delay", str(keybuf_delay)])
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def wait_for_screen_and_state(
    client: BinaryMonitorClient,
    process: subprocess.Popen[str],
    fragment: str,
    *,
    marker_addr: int,
    marker_value: int,
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
            marker = client.memory_get(marker_addr, marker_addr)[0]
            if marker == marker_value:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Autostart a PRG or disk image in VICE and verify the expected runtime state")
    parser.add_argument("--disk", required=True, help="path to a PRG or disk image to autostart")
    parser.add_argument("--expected", required=True, help="screen fragment to wait for")
    parser.add_argument("--marker-address", default="0xCFFF", help="hex or decimal address for the ready marker")
    parser.add_argument("--marker-value", default="0x42", help="expected ready marker byte")
    parser.add_argument("--check-byte", action="append", default=[], help="extra checks in addr=value form, hex or decimal")
    parser.add_argument("--keybuf", help="optional VICE -keybuf string to inject during autostart")
    parser.add_argument("--keybuf-delay", type=int, help="optional VICE -keybuf-delay value")
    parser.add_argument("--timeout", type=float, default=25.0, help="seconds to wait for the banner")
    args = parser.parse_args(argv)

    image = Path(args.disk).resolve()
    if not image.is_file():
        raise SystemExit(f"disk image not found: {image}")

    port = reserve_tcp_port()
    process = launch_vice(image, port, keybuf=args.keybuf, keybuf_delay=args.keybuf_delay)
    client = BinaryMonitorClient("127.0.0.1", port, timeout=5.0)
    try:
        client.connect(time.monotonic() + 20.0)
        client.ping()
        client.resume()
        marker_addr = int(args.marker_address, 0)
        marker_value = int(args.marker_value, 0)
        extra_checks: list[tuple[int, int]] = []
        for item in args.check_byte:
            addr_text, value_text = item.split("=", 1)
            addr = int(addr_text, 0)
            value = int(value_text, 0)
            extra_checks.append((addr, value))
        screen = wait_for_screen_and_state(
            client,
            process,
            args.expected,
            marker_addr=marker_addr,
            marker_value=marker_value,
            extra_checks=extra_checks,
            timeout=args.timeout,
        )
        print(screen)
        return 0
    except ViceError as exc:
        print(exc, file=sys.stderr)
        return 1
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


if __name__ == "__main__":
    raise SystemExit(main())
