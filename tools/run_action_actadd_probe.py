#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import vice_prg_probe as vp


def screen_text(client: vp.BinaryMonitorClient) -> str:
    return vp.screen_ram_to_text(client.memory_get(0x0400, 0x07E7))


def wait_for_screen_fragments(
    client: vp.BinaryMonitorClient,
    process,
    fragments: list[str],
    timeout: float,
) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise vp.ViceError(
                f"x64sc exited early while waiting for ACTADD probe\nstdout:\n{stdout}\nstderr:\n{stderr}"
            )
        last_screen = screen_text(client)
        if all(fragment in last_screen for fragment in fragments):
            return last_screen
        time.sleep(0.2)
    missing = [fragment for fragment in fragments if fragment not in last_screen]
    raise vp.ViceError(
        f"expected screen fragments {missing!r} were not present in final screen:\n{last_screen}"
    )


def wait_keyboard_idle(client: vp.BinaryMonitorClient, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if client.memory_get(vp.KEYBUF_COUNT, vp.KEYBUF_COUNT)[0] == 0:
            return
        time.sleep(0.05)
    raise vp.ViceError("timed out waiting for C64 keyboard buffer to drain")


def type_command(client: vp.BinaryMonitorClient, command: str, timeout: float) -> None:
    wait_keyboard_idle(client, timeout)
    client.keyboard_type(command)
    wait_keyboard_idle(client, timeout)
    time.sleep(0.2)
    client.keyboard_type("\r")
    wait_keyboard_idle(client, timeout)


def wait_mount(client: vp.BinaryMonitorClient, process, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise vp.ViceError(
                f"x64sc exited early while waiting for ACTADD mount\nstdout:\n{stdout}\nstderr:\n{stderr}"
            )
        wait_keyboard_idle(client, 5.0)
        last_screen = screen_text(client)
        if "B:ACTION DNP" in last_screen or last_screen.count("A:D64/>") >= 2:
            return last_screen
        time.sleep(0.2)
    raise vp.ViceError(f"ACTADD mount did not complete in time:\n{last_screen}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a focused ACTADD probe in VICE")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--module", default="HELPER")
    parser.add_argument("--mount-path", default="/IMAGES/ACTION.DNP")
    parser.add_argument("--expect", choices=["create", "exists"], required=True)
    parser.add_argument("--attempts", type=int, default=4)
    parser.add_argument("--attempt-delay", type=float, default=2.0)
    parser.add_argument("--keybuf-delay", type=int, default=8)
    parser.add_argument("--initial-settle", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_prompt = f"B:DNP/{args.project.upper()}>"
    module_name = args.module.upper()
    if args.expect == "create":
        expected_fragments = [
            "RUN ACTADD.PRG",
            "ACTADD OK",
            f"PROC {module_name}()",
            "ENDPROC",
            project_prompt,
        ]
    else:
        expected_fragments = [
            "RUN ACTADD.PRG",
            "EXISTS",
            project_prompt,
        ]

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
            wait_for_screen_fragments(client, process, ["A:D64/>"], args.timeout)
            time.sleep(args.initial_settle)
            type_command(client, f"MOUNT B: {args.mount_path}", args.timeout)
            wait_mount(client, process, args.timeout)
            type_command(client, "B:", args.timeout)
            wait_for_screen_fragments(client, process, ["B:DNP/>"], args.timeout)
            type_command(client, f"CD {args.project}", args.timeout)
            wait_for_screen_fragments(client, process, [project_prompt], args.timeout)
            type_command(client, f"ACTADD.PRG {args.module}", args.timeout)
            if args.expect == "create":
                wait_for_screen_fragments(
                    client,
                    process,
                    ["RUN ACTADD.PRG", "ACTADD OK", project_prompt],
                    args.timeout,
                )
                type_command(client, f"TYPE SRC/{args.module}.ACT", args.timeout)
            screen = wait_for_screen_fragments(client, process, expected_fragments, args.timeout)
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
            try:
                process.wait(timeout=10.0)
            except Exception:
                process.kill()

    if last_error is not None:
        raise SystemExit(1)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
