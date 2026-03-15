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


def wait_for_screen_fragments(client: vp.BinaryMonitorClient, fragments: list[str], timeout: float) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    while time.monotonic() < deadline:
        last_screen = screen_text(client)
        if all(fragment in last_screen for fragment in fragments):
            return last_screen
        time.sleep(0.2)
    missing = [fragment for fragment in fragments if fragment not in last_screen]
    raise vp.ViceError(f"expected screen fragments {missing!r} were not present in final screen:\n{last_screen}")


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


def wait_for_prompt_count_and_fragments(
    client: vp.BinaryMonitorClient, prompt: str, minimum: int, fragments: list[str], timeout: float
) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    while time.monotonic() < deadline:
        last_screen = screen_text(client)
        if last_screen.count(prompt) >= minimum and all(fragment in last_screen for fragment in fragments):
            return last_screen
        time.sleep(0.2)
    missing = [fragment for fragment in fragments if fragment not in last_screen]
    raise vp.ViceError(
        f"expected prompt {prompt!r} at least {minimum} times and fragments {missing!r}:\n{last_screen}"
    )


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


def type_command(client: vp.BinaryMonitorClient, command: str, timeout: float) -> None:
    client.keyboard_type(command)
    wait_for_keyboard_idle(client, timeout)
    time.sleep(0.2)
    client.keyboard_type("\r")
    wait_for_keyboard_idle(client, timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a focused Action workspace command probe in VICE")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--command", default="AVMRUN UDOSHELLO.AVM")
    parser.add_argument("--mount-path", default="/IMAGES/ACTION.DNP")
    parser.add_argument("--mount-result", default="B:ACTION DNP")
    parser.add_argument("--b-prompt", default="B:DNP/>")
    parser.add_argument("--run-marker", default="RUN AVMRUN.PRG")
    parser.add_argument("--done-fragment", default="UDOS AVM OK")
    parser.add_argument("--prompt-count", type=int, default=2)
    parser.add_argument("--initial-settle", type=float, default=1.5)
    parser.add_argument("--command-settle", type=float, default=1.0)
    parser.add_argument("--attempts", type=int, default=4)
    parser.add_argument("--attempt-delay", type=float, default=2.0)
    parser.add_argument("--pre-command", action="append", default=[])
    parser.add_argument("--post-command")
    parser.add_argument("--post-done-fragment")
    parser.add_argument("--contains", action="append", default=[])
    parser.add_argument("--not-contains", action="append", default=[])
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    last_error: Exception | None = None
    last_screen = ""

    for attempt in range(1, args.attempts + 1):
        port = vp.reserve_tcp_port()
        process = vp.launch_vice(
            image,
            port,
            extra_args=[
                "-iecdevice9",
                "-device9",
                "1",
                "-fs9",
                str(fs_root),
                "-fslongnames",
            ],
        )
        client = vp.BinaryMonitorClient("127.0.0.1", port, timeout=5.0)

        try:
            client.connect(time.monotonic() + 20.0)
            client.ping()
            client.resume()

            wait_for_screen_fragment(client, "A:D64/>", 60.0)
            time.sleep(args.initial_settle)
            type_command(client, f"MOUNT B: {args.mount_path}", 30.0)
            time.sleep(1.0)
            wait_for_mount_completion(client, 30.0)
            type_command(client, "B:", 30.0)
            screen = wait_for_screen_fragment(client, args.b_prompt, 30.0)
            prompt_count = screen.count(args.b_prompt)
            time.sleep(args.command_settle)
            for pre_command in args.pre_command:
                type_command(client, pre_command, 30.0)
                prompt_count += 1
                wait_for_prompt_count(client, args.b_prompt, prompt_count, 30.0)
                time.sleep(args.command_settle)
            type_command(client, args.command, 30.0)
            if args.run_marker:
                wait_for_screen_fragment(client, args.run_marker, 30.0)
            prompt_count += 1
            fragments: list[str] = []
            if args.done_fragment:
                fragments.append(args.done_fragment)
            screen = wait_for_prompt_count_and_fragments(client, args.b_prompt, prompt_count, fragments, 30.0)
            if args.post_command:
                time.sleep(args.command_settle)
                type_command(client, args.post_command, 30.0)
                if args.post_done_fragment and args.post_done_fragment.endswith(">"):
                    screen = wait_for_screen_fragment(client, args.post_done_fragment, 30.0)
                else:
                    prompt_count += 1
                    post_fragments: list[str] = []
                    if args.post_done_fragment:
                        post_fragments.append(args.post_done_fragment)
                    screen = wait_for_prompt_count_and_fragments(
                        client, args.b_prompt, prompt_count, post_fragments, 30.0
                    )
            for fragment in args.contains:
                if fragment not in screen:
                    raise vp.ViceError(
                        f"expected screen fragment {fragment!r} was not present in final screen:\n{screen}"
                    )
            for fragment in args.not_contains:
                if fragment in screen:
                    raise vp.ViceError(
                        f"unexpected screen fragment {fragment!r} was present in final screen:\n{screen}"
                    )
            print(screen)
            return 0
        except Exception as exc:
            last_error = exc
            try:
                last_screen = screen_text(client)
            except Exception:
                last_screen = ""
            if attempt < args.attempts:
                time.sleep(args.attempt_delay)
            else:
                if last_screen:
                    print(last_screen)
                print(exc, file=sys.stderr)
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

    return 1 if last_error is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())
