#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import vice_prg_probe as vp


def screen_text(client: vp.BinaryMonitorClient) -> str:
    return vp.screen_ram_to_text(client.memory_get(0x0400, 0x07E7))


def wait_for_screen_fragment(client: vp.BinaryMonitorClient, fragment: str, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    while time.monotonic() < deadline:
        last_screen = screen_text(client)
        if fragment in last_screen:
            return last_screen
        time.sleep(0.2)
    raise vp.ViceError(f"expected screen fragment {fragment!r} was not present in final screen:\n{last_screen}")


def wait_for_mount_completion(client: vp.BinaryMonitorClient, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    while time.monotonic() < deadline:
        last_screen = screen_text(client)
        if "B:ACTION DNP" in last_screen:
            return last_screen
        if last_screen.count("A:D64/>") >= 2:
            return last_screen
        time.sleep(0.2)
    raise vp.ViceError(f"mount did not complete in time:\n{last_screen}")


def wait_for_keyboard_idle(client: vp.BinaryMonitorClient, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if client.memory_get(vp.KEYBUF_COUNT, vp.KEYBUF_COUNT)[0] == 0:
            return
        time.sleep(0.05)
    raise vp.ViceError("timed out waiting for C64 keyboard buffer to drain after command")


def wait_for_tree_prompt(client: vp.BinaryMonitorClient, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    while time.monotonic() < deadline:
        last_screen = screen_text(client)
        if "B:DNP/>" in last_screen:
            return last_screen
        time.sleep(0.2)
    raise vp.ViceError(f"timed out waiting for B:DNP/>:\n{last_screen}")


def wait_for_prompt_count(client: vp.BinaryMonitorClient, prompt: str, minimum: int, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    while time.monotonic() < deadline:
        last_screen = screen_text(client)
        if last_screen.count(prompt) >= minimum:
            return last_screen
        time.sleep(0.2)
    raise vp.ViceError(
        f"expected prompt {prompt!r} at least {minimum} times, got {last_screen.count(prompt)}:\n{last_screen}"
    )


def wait_for_fragments(client: vp.BinaryMonitorClient, fragments: list[str], timeout: float) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    while time.monotonic() < deadline:
        last_screen = screen_text(client)
        if all(fragment in last_screen for fragment in fragments):
            return last_screen
        time.sleep(0.2)
    missing = [fragment for fragment in fragments if fragment not in last_screen]
    raise vp.ViceError(f"missing screen fragments {missing!r}:\n{last_screen}")


def type_command(client: vp.BinaryMonitorClient, command: str, timeout: float) -> None:
    clear_keyboard_buffer(client)
    client.keyboard_type(command + "\r")
    wait_for_keyboard_idle(client, timeout)


def clear_keyboard_buffer(client: vp.BinaryMonitorClient) -> None:
    client.memory_set(vp.KEYBUF_DATA, bytes(10))
    client.memory_set(vp.KEYBUF_COUNT, b"\x00")


def parse_file_text_check(spec: str) -> tuple[Path, str]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError("expected RELPATH=TEXT")
    relpath, text = spec.split("=", 1)
    return Path(relpath), text


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a resident VICE tree mutation probe and verify host persistence")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--mount-path", default="/IMAGES/ACTION.DNP")
    parser.add_argument("--pre-command", action="append", default=[])
    parser.add_argument("--contains", action="append", default=[])
    parser.add_argument("--expect-file", action="append", default=[])
    parser.add_argument("--absent-file", action="append", default=[])
    parser.add_argument("--expect-file-text", action="append", default=[], type=parse_file_text_check)
    parser.add_argument("--attempts", type=int, default=4)
    parser.add_argument("--attempt-delay", type=float, default=2.0)
    parser.add_argument("--initial-settle", type=float, default=4.0)
    parser.add_argument("--command-settle", type=float, default=8.0)
    parser.add_argument("--verbose", action="store_true", help="print the final successful screen")
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    last_error: Exception | None = None

    for attempt in range(1, args.attempts + 1):
        port = vp.reserve_tcp_port()
        process = vp.launch_vice(
            image,
            port,
            extra_args=[
                "-iecdevice9",
                "-fs9",
                str(fs_root),
                "-fslongnames",
            ],
        )
        client = vp.BinaryMonitorClient("127.0.0.1", port, timeout=5.0)
        step = "connect"
        last_screen = ""

        try:
            step = "connect"
            client.connect(time.monotonic() + 20.0)
            step = "ping"
            client.ping()
            step = "resume"
            client.resume()
            step = "boot_prompt"
            wait_for_screen_fragment(client, "A:D64/>", 60.0)
            step = "initial_settle"
            time.sleep(args.initial_settle)
            step = "clear_keyboard"
            clear_keyboard_buffer(client)
            step = "mount"
            type_command(client, f"MOUNT B: {args.mount_path}", 30.0)
            time.sleep(1.0)
            step = "mount_wait"
            wait_for_mount_completion(client, 30.0)
            step = "drive_b"
            type_command(client, "B:", 30.0)
            step = "tree_prompt"
            screen = wait_for_tree_prompt(client, 30.0)
            prompt_count = screen.count("B:DNP/>")
            for pre_command in args.pre_command:
                step = f"pre:{pre_command}"
                type_command(client, pre_command, 30.0)
                time.sleep(args.command_settle)
                prompt_count += 1
                wait_for_prompt_count(client, "B:DNP/>", prompt_count, 20.0)
            step = f"command:{args.command}"
            type_command(client, args.command, 30.0)
            time.sleep(args.command_settle)
            step = "final_screen"
            fragments = list(args.contains)
            prompt_count += 1
            fragments.append("B:DNP/>")
            final_screen = wait_for_prompt_count(client, "B:DNP/>", prompt_count, 20.0)
            if not all(fragment in final_screen for fragment in fragments):
                final_screen = wait_for_fragments(client, fragments, 20.0)
            if args.verbose:
                print(final_screen)
            break
        except Exception as exc:
            last_error = exc
            if attempt >= args.attempts:
                try:
                    last_screen = screen_text(client)
                except Exception:
                    last_screen = ""
                if last_screen:
                    print(last_screen)
                print(f"probe step: {step}", file=sys.stderr)
                print(exc, file=sys.stderr)
                return 1
            time.sleep(args.attempt_delay)
        finally:
            try:
                client.quit_emulator()
            except Exception:
                pass
            client.close()
            process.terminate()
            try:
                process.wait(timeout=5.0)
            except Exception:
                process.kill()
    else:
        if last_error is not None:
            print(last_error, file=sys.stderr)
        return 1

    for relpath in args.expect_file:
        path = fs_root / relpath
        if not path.is_file():
            raise SystemExit(f"expected host file {path} to exist")

    for relpath in args.absent_file:
        path = fs_root / relpath
        if path.exists():
            raise SystemExit(f"expected host path {path} to be absent")

    for relpath, text in args.expect_file_text:
        path = fs_root / relpath
        if not path.is_file():
            raise SystemExit(f"expected host file {path} to exist for text check")
        actual = path.read_text(errors="ignore")
        if text not in actual:
            raise SystemExit(f"expected host file {path} to contain {text!r}, got {actual!r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
