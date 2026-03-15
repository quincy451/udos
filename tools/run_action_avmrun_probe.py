#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import vice_prg_probe as vp


def wait_for_screen_fragment(client: vp.BinaryMonitorClient, fragment: str, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    while time.monotonic() < deadline:
        last_screen = vp.screen_ram_to_text(client.memory_get(0x0400, 0x07E7))
        if fragment in last_screen:
            return last_screen
        time.sleep(0.2)
    raise vp.ViceError(f"expected screen fragment {fragment!r} was not present in final screen:\n{last_screen}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the focused AVMRUN Action workspace probe in VICE")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
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
        client.keyboard_type("MOUNT B: /IMAGES/ACTION.DNP\r")
        time.sleep(2.0)
        client.keyboard_type("B:\r")
        time.sleep(2.0)
        client.keyboard_type("AVMRUN UDOSHELLO.AVM\r")
        time.sleep(1.0)

        screen = wait_for_screen_fragment(client, "UDOS AVM OK", 30.0)
        if "RUN AVMRUN.PRG" not in screen:
            raise vp.ViceError(f"expected screen fragment 'RUN AVMRUN.PRG' was not present in final screen:\n{screen}")
        print(screen)
        return 0
    except Exception as exc:
        try:
            screen = vp.screen_ram_to_text(client.memory_get(0x0400, 0x07E7))
            print(screen)
        except Exception:
            pass
        print(exc, file=sys.stderr)
        return 1
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


if __name__ == "__main__":
    raise SystemExit(main())
