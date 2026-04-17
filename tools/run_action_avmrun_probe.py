#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import vice_prg_probe as vp

WORKSPACE_CONNECT_DELAYS = (10.0,) + tuple(delay for delay in vp.default_connect_delays() if delay != 10.0)
PATH_DEBUG_ADDRS = {
    "TOOL_ABI_CURRENT_PATH": 0xCD00,
    "TOOL_ABI_OPEN_PATH": 0xCD40,
}


def screen_text(client: vp.BinaryMonitorClient) -> str:
    text, _d018, _dd00 = vp.read_active_screen_text(client)
    return text


def screen_text_for_fragment(client: vp.BinaryMonitorClient, fragment: str) -> str:
    text, _d018, _dd00 = vp.read_screen_text_for_fragment(client, fragment)
    return text


def prime_workspace_drive9(client: vp.BinaryMonitorClient) -> dict[str, dict[str, int]]:
    before = {
        "IECDevice9": client.resource_get_int("IECDevice9"),
        "VirtualDevice9": client.resource_get_int("VirtualDevice9"),
        "FileSystemDevice9": client.resource_get_int("FileSystemDevice9"),
    }
    client.resource_set_int("IECDevice9", 1)
    client.resource_set_int("VirtualDevice9", 1)
    client.resource_set_int("FileSystemDevice9", 1)
    after = {
        "IECDevice9": client.resource_get_int("IECDevice9"),
        "VirtualDevice9": client.resource_get_int("VirtualDevice9"),
        "FileSystemDevice9": client.resource_get_int("FileSystemDevice9"),
    }
    return {"before": before, "after": after}


def last_nonempty_line(screen: str) -> str:
    for line in reversed(screen.splitlines()):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def nudge_to_prompt(
    client: vp.BinaryMonitorClient,
    process,
    expected_fragment: str = "A:D64/>",
    attempts: int = 3,
    timeout: float = 8.0,
) -> str:
    last_error: vp.ViceError | None = None
    try:
        return vp.wait_for_screen_and_state(
            client,
            process,
            expected_fragment,
            marker_addr=None,
            marker_value=None,
            extra_checks=[],
            timeout=timeout,
        )
    except vp.ViceError as exc:
        last_error = exc

    for _ in range(attempts):
        client.keyboard_feed("\r")
        try:
            return vp.wait_for_screen_and_state(
                client,
                process,
                expected_fragment,
                marker_addr=None,
                marker_value=None,
                extra_checks=[],
                timeout=timeout,
            )
        except vp.ViceError as exc:
            last_error = exc

    assert last_error is not None
    raise last_error


def maybe_retry_command_enter(
    client: vp.BinaryMonitorClient,
    *,
    last_screen: str,
    retry_echo: str | None,
    retry_count: int,
) -> int:
    if retry_count >= 4 or not retry_echo or not vp.screen_contains(last_screen, retry_echo):
        return retry_count
    send_return(client, 5.0)
    return retry_count + 1


def wait_for_screen_fragment(
    client: vp.BinaryMonitorClient,
    fragment: str,
    timeout: float,
    *,
    retry_echo: str | None = None,
    poll_interval: float = 0.2,
) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    retry_count = 0
    while time.monotonic() < deadline:
        last_screen = screen_text_for_fragment(client, fragment)
        if vp.screen_contains(last_screen, fragment):
            return last_screen
        retry_count = maybe_retry_command_enter(
            client,
            last_screen=last_screen,
            retry_echo=retry_echo,
            retry_count=retry_count,
        )
        time.sleep(poll_interval)
    raise vp.ViceError(f"expected screen fragment {fragment!r} was not present in final screen:\n{last_screen}")


def wait_for_screen_fragments(
    client: vp.BinaryMonitorClient,
    fragments: list[str],
    timeout: float,
    *,
    retry_echo: str | None = None,
    poll_interval: float = 0.2,
) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    retry_count = 0
    while time.monotonic() < deadline:
        last_screen = screen_text(client)
        if not all(vp.screen_contains(last_screen, fragment) for fragment in fragments):
            for fragment in fragments:
                if not vp.screen_contains(last_screen, fragment):
                    candidate = screen_text_for_fragment(client, fragment)
                    if vp.screen_contains(candidate, fragment):
                        last_screen = candidate
                        break
        if all(vp.screen_contains(last_screen, fragment) for fragment in fragments):
            return last_screen
        retry_count = maybe_retry_command_enter(
            client,
            last_screen=last_screen,
            retry_echo=retry_echo,
            retry_count=retry_count,
        )
        time.sleep(poll_interval)
    missing = [fragment for fragment in fragments if not vp.screen_contains(last_screen, fragment)]
    raise vp.ViceError(f"expected screen fragments {missing!r} were not present in final screen:\n{last_screen}")


def wait_for_prompt_count(
    client: vp.BinaryMonitorClient,
    prompt: str,
    minimum: int,
    timeout: float,
    *,
    retry_echo: str | None = None,
    poll_interval: float = 0.2,
) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    retry_count = 0
    while time.monotonic() < deadline:
        last_screen = screen_text_for_fragment(client, prompt)
        if vp.screen_count(last_screen, prompt) >= minimum:
            return last_screen
        retry_count = maybe_retry_command_enter(
            client,
            last_screen=last_screen,
            retry_echo=retry_echo,
            retry_count=retry_count,
        )
        time.sleep(poll_interval)
    raise vp.ViceError(
        f"expected prompt {prompt!r} at least {minimum} times, got {vp.screen_count(last_screen, prompt)}:\n{last_screen}"
    )


def wait_for_prompt_count_and_fragments(
    client: vp.BinaryMonitorClient,
    prompt: str,
    minimum: int,
    fragments: list[str],
    timeout: float,
    *,
    retry_echo: str | None = None,
    poll_interval: float = 0.2,
) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    retry_count = 0
    while time.monotonic() < deadline:
        last_screen = screen_text_for_fragment(client, prompt)
        if not all(vp.screen_contains(last_screen, fragment) for fragment in fragments):
            for fragment in fragments:
                if not vp.screen_contains(last_screen, fragment):
                    candidate = screen_text_for_fragment(client, fragment)
                    if vp.screen_contains(candidate, fragment):
                        last_screen = candidate
                        break
        if vp.screen_count(last_screen, prompt) >= minimum and all(
            vp.screen_contains(last_screen, fragment) for fragment in fragments
        ):
            return last_screen
        retry_count = maybe_retry_command_enter(
            client,
            last_screen=last_screen,
            retry_echo=retry_echo,
            retry_count=retry_count,
        )
        time.sleep(poll_interval)
    missing = [fragment for fragment in fragments if not vp.screen_contains(last_screen, fragment)]
    raise vp.ViceError(
        f"expected prompt {prompt!r} at least {minimum} times and fragments {missing!r}:\n{last_screen}"
    )


def wait_for_mount_completion(
    client: vp.BinaryMonitorClient,
    timeout: float,
    *,
    retry_echo: str | None = None,
    poll_interval: float = 0.2,
) -> str:
    deadline = time.monotonic() + timeout
    last_screen = ""
    retry_count = 0
    while time.monotonic() < deadline:
        last_screen = screen_text(client)
        if not vp.screen_contains(last_screen, "B:ACTION DNP"):
            candidate = screen_text_for_fragment(client, "B:ACTION DNP")
            if vp.screen_contains(candidate, "B:ACTION DNP"):
                last_screen = candidate
        if vp.screen_count(last_screen, "A:D64/>") < 2:
            candidate = screen_text_for_fragment(client, "A:D64/>")
            if vp.screen_contains(candidate, "A:D64/>"):
                last_screen = candidate
        if vp.screen_contains(last_screen, "B:ACTION DNP"):
            return last_screen
        if vp.screen_count(last_screen, "A:D64/>") >= 2 and vp.screen_contains(last_nonempty_line(last_screen), "A:D64/>"):
            return last_screen
        retry_count = maybe_retry_command_enter(
            client,
            last_screen=last_screen,
            retry_echo=retry_echo,
            retry_count=retry_count,
        )
        time.sleep(poll_interval)
    raise vp.ViceError(f"mount did not complete in time:\n{last_screen}")


def wait_for_keyboard_idle(client: vp.BinaryMonitorClient, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if client.memory_get(vp.KEYBUF_COUNT, vp.KEYBUF_COUNT)[0] == 0:
            return
        time.sleep(0.05)
    raise vp.ViceError("timed out waiting for C64 keyboard buffer to drain after command")


def clear_keyboard_buffer(client: vp.BinaryMonitorClient) -> None:
    client.memory_set(vp.KEYBUF_DATA, bytes(10))
    client.memory_set(vp.KEYBUF_COUNT, b"\x00")


def send_text(client: vp.BinaryMonitorClient, text: str, timeout: float) -> None:
    clear_keyboard_buffer(client)
    try:
        client.keyboard_type(text)
        try:
            wait_for_keyboard_idle(client, timeout)
        except vp.ViceError:
            # The final return can linger in the C64 key buffer even after the shell
            # is ready to consume it; later screen waits already handle that case.
            pass
    except vp.ViceError:
        clear_keyboard_buffer(client)
        client.keyboard_feed(text)
    time.sleep(0.1)


def send_return(client: vp.BinaryMonitorClient, timeout: float) -> None:
    send_text(client, "\r", timeout)


def type_command(client: vp.BinaryMonitorClient, command: str, timeout: float) -> None:
    send_text(client, command + "\r", timeout)


def read_c_string(client: vp.BinaryMonitorClient, addr: int, max_len: int = 128) -> str:
    data = client.memory_get(addr, addr + max_len - 1)
    end = data.find(b"\x00")
    if end >= 0:
        data = data[:end]
    return data.decode("ascii", errors="replace")


def read_screen_string(client: vp.BinaryMonitorClient, addr: int, max_len: int = 64) -> str:
    data = client.memory_get(addr, addr + max_len - 1)
    chars: list[str] = []
    for byte in data:
        if byte == 0:
            break
        chars.append(vp.screen_code_to_ascii(byte))
    return "".join(chars)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a focused Action workspace command probe in VICE")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--command", default="AVMRUN UDOSHELLO.AVM")
    parser.add_argument("--mount-path", default="/IMAGES/ACTION.DNP")
    parser.add_argument("--mount-result", default="B:ACTION DNP")
    parser.add_argument("--b-prompt", default="B:DNP/>")
    parser.add_argument("--final-prompt")
    parser.add_argument("--run-marker", default="RUN AVMRUN.PRG")
    parser.add_argument("--done-fragment", default="UDOS AVM OK")
    parser.add_argument("--prompt-count", type=int, default=2)
    parser.add_argument("--skip-command-prompt", action="store_true")
    parser.add_argument("--initial-settle", type=float, default=3.0)
    parser.add_argument("--command-settle", type=float, default=1.0)
    parser.add_argument("--connect-delay", type=float)
    parser.add_argument("--boot-timeout", type=float, default=60.0)
    parser.add_argument("--boot-settle", type=float, default=0.0)
    parser.add_argument("--poll-interval", type=float, default=0.2)
    parser.add_argument("--shell-timeout", type=float, default=30.0)
    parser.add_argument("--attempts", type=int, default=4)
    parser.add_argument("--attempt-delay", type=float)
    parser.add_argument("--pre-command", action="append", default=[])
    parser.add_argument("--pre-prompt", action="append", default=[])
    parser.add_argument("--pre-fragment", action="append", default=[])
    parser.add_argument("--post-command")
    parser.add_argument("--post-done-fragment")
    parser.add_argument("--contains", action="append", default=[])
    parser.add_argument("--not-contains", action="append", default=[])
    parser.add_argument("--labels")
    args = parser.parse_args()

    if args.skip_command_prompt and args.post_command:
        parser.error("--skip-command-prompt cannot be used with --post-command")

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    labels = vp.load_ld65_labels(Path(args.labels).resolve()) if args.labels else None
    last_error: Exception | None = None
    last_screen = ""
    attempt_notes: list[str] = []
    connect_delays = (args.connect_delay,) if args.connect_delay is not None else WORKSPACE_CONNECT_DELAYS
    attempt_delay = args.attempt_delay if args.attempt_delay is not None else vp.default_attempt_delay()

    for attempt in range(1, args.attempts + 1):
        vp.cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, attempt_delay)))
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

        try:
            connect_delay = connect_delays[(attempt - 1) % len(connect_delays)]
            if connect_delay > 0.0:
                time.sleep(connect_delay)
            client.connect(time.monotonic() + 20.0)
            client.ping()
            client.resume()
            if args.boot_settle > 0.0:
                time.sleep(args.boot_settle)

            wait_for_screen_fragment(client, "A:D64/>", args.boot_timeout, poll_interval=args.poll_interval)
            time.sleep(args.initial_settle)
            mount_command = f"MOUNT B: {args.mount_path}"
            type_command(client, mount_command, args.shell_timeout)
            time.sleep(1.0)
            try:
                wait_for_mount_completion(
                    client,
                    args.shell_timeout,
                    retry_echo=mount_command,
                    poll_interval=args.poll_interval,
                )
            except vp.ViceError:
                type_command(client, mount_command, args.shell_timeout)
                time.sleep(1.0)
                wait_for_mount_completion(
                    client,
                    args.shell_timeout,
                    retry_echo=mount_command,
                    poll_interval=args.poll_interval,
                )
            type_command(client, "B:", args.shell_timeout)
            screen = wait_for_screen_fragment(
                client,
                args.b_prompt,
                args.shell_timeout,
                retry_echo="B:",
                poll_interval=args.poll_interval,
            )
            final_prompt = args.final_prompt or args.b_prompt
            prompt_count = vp.screen_count(screen, final_prompt)
            time.sleep(args.command_settle)
            for index, pre_command in enumerate(args.pre_command):
                type_command(client, pre_command, args.shell_timeout)
                pre_fragments: list[str] = []
                if index < len(args.pre_prompt) and args.pre_prompt[index]:
                    pre_fragments.append(args.pre_prompt[index])
                if index < len(args.pre_fragment) and args.pre_fragment[index]:
                    pre_fragments.append(args.pre_fragment[index])
                if pre_fragments:
                    screen = wait_for_screen_fragments(
                        client,
                        pre_fragments,
                        args.shell_timeout,
                        retry_echo=pre_command,
                        poll_interval=args.poll_interval,
                    )
                    prompt_count = max(prompt_count, vp.screen_count(screen, final_prompt))
                else:
                    prompt_count += 1
                    screen = wait_for_prompt_count(
                        client,
                        args.b_prompt,
                        prompt_count,
                        args.shell_timeout,
                        retry_echo=pre_command,
                        poll_interval=args.poll_interval,
                    )
                    prompt_count = max(prompt_count, vp.screen_count(screen, final_prompt))
                time.sleep(args.command_settle)
            type_command(client, args.command, args.shell_timeout)
            time.sleep(args.command_settle)
            if args.run_marker:
                wait_for_screen_fragment(
                    client,
                    args.run_marker,
                    args.shell_timeout,
                    retry_echo=args.command,
                    poll_interval=args.poll_interval,
                )
            if args.skip_command_prompt:
                fragments: list[str] = []
                if args.done_fragment:
                    fragments.append(args.done_fragment)
                if fragments:
                    screen = wait_for_screen_fragments(
                        client,
                        fragments,
                        args.shell_timeout,
                        retry_echo=args.command if not args.run_marker else None,
                        poll_interval=args.poll_interval,
                    )
                else:
                    time.sleep(args.shell_timeout)
                    screen = screen_text(client)
            else:
                prompt_count += 1
                fragments: list[str] = []
                if args.done_fragment:
                    fragments.append(args.done_fragment)
                screen = wait_for_prompt_count_and_fragments(
                    client,
                    final_prompt,
                    prompt_count,
                    fragments,
                    args.shell_timeout,
                    retry_echo=args.command if not args.run_marker else None,
                    poll_interval=args.poll_interval,
                )
            if args.post_command:
                time.sleep(args.command_settle)
                type_command(client, args.post_command, args.shell_timeout)
                if args.post_done_fragment and args.post_done_fragment.endswith(">"):
                    screen = wait_for_screen_fragment(
                        client,
                        args.post_done_fragment,
                        args.shell_timeout,
                        retry_echo=args.post_command,
                        poll_interval=args.poll_interval,
                    )
                    prompt_count = max(prompt_count, vp.screen_count(screen, final_prompt))
                else:
                    prompt_count += 1
                    post_fragments: list[str] = []
                    if args.post_done_fragment:
                        post_fragments.append(args.post_done_fragment)
                    screen = wait_for_prompt_count_and_fragments(
                        client,
                        final_prompt,
                        prompt_count,
                        post_fragments,
                        args.shell_timeout,
                        retry_echo=args.post_command,
                        poll_interval=args.poll_interval,
                    )
            for fragment in args.contains:
                if not vp.screen_contains(screen, fragment):
                    raise vp.ViceError(
                        f"expected screen fragment {fragment!r} was not present in final screen:\n{screen}"
                    )
            for fragment in args.not_contains:
                if vp.screen_contains(screen, fragment):
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
            try:
                launch_trace = vp.format_udos_launch_trace(client)
            except Exception:
                launch_trace = ""
            path_trace = ""
            if labels:
                path_parts: list[str] = []
                for label_name in ("TOOL_ABI_OPEN_PATH", "dest_fullpath_buffer", "source_fullpath_buffer", "TOOL_ABI_CURRENT_PATH"):
                    addr = labels.get(label_name) or labels.get(f".{label_name}") or PATH_DEBUG_ADDRS.get(label_name)
                    if addr is None:
                        continue
                    try:
                        value = read_c_string(client, addr)
                    except Exception:
                        continue
                    path_parts.append(f"{label_name}={value!r}")
                for label_name in ("temp_drive", "temp_dir_id", "source_drive", "source_dir_id", "dest_drive", "dest_dir_id"):
                    addr = labels.get(label_name) or labels.get(f".{label_name}")
                    if addr is None:
                        continue
                    try:
                        value = client.memory_get(addr, addr)[0]
                    except Exception:
                        continue
                    path_parts.append(f"{label_name}=0x{value:02X}")
                path_name_addr = labels.get("path_name_buffer") or labels.get(".path_name_buffer")
                if path_name_addr is not None:
                    try:
                        value = read_screen_string(client, path_name_addr)
                    except Exception:
                        value = ""
                    path_parts.append(f"path_name_buffer={value!r}")
                arg_buffer_addr = labels.get("arg_buffer") or labels.get(".arg_buffer")
                if arg_buffer_addr is not None:
                    try:
                        value = read_screen_string(client, arg_buffer_addr)
                    except Exception:
                        value = ""
                    path_parts.append(f"arg_buffer={value!r}")
                arg_length_addr = labels.get("arg_length") or labels.get(".arg_length")
                if arg_length_addr is not None:
                    try:
                        value = client.memory_get(arg_length_addr, arg_length_addr)[0]
                    except Exception:
                        value = 0
                    path_parts.append(f"arg_length=0x{value:02X}")
                uci_cmd_addr = labels.get("uci_cmd_buffer") or labels.get(".uci_cmd_buffer")
                if uci_cmd_addr is not None:
                    try:
                        value = read_c_string(client, uci_cmd_addr)
                    except Exception:
                        value = ""
                    path_parts.append(f"uci_cmd_buffer={value!r}")
                vice_dir_state_addr = labels.get("vice_dir_state_b") or labels.get(".vice_dir_state_b")
                vice_dir_parent_addr = labels.get("vice_dir_parent_b") or labels.get(".vice_dir_parent_b")
                vice_dir_names_addr = labels.get("vice_dir_names_b") or labels.get(".vice_dir_names_b")
                if (
                    vice_dir_state_addr is not None
                    and vice_dir_parent_addr is not None
                    and vice_dir_names_addr is not None
                ):
                    for index in range(6):
                        try:
                            state = client.memory_get(
                                vice_dir_state_addr + index, vice_dir_state_addr + index
                            )[0]
                            parent = client.memory_get(
                                vice_dir_parent_addr + index, vice_dir_parent_addr + index
                            )[0]
                            name = read_c_string(client, vice_dir_names_addr + (index * 21))
                        except Exception:
                            continue
                        path_parts.append(
                            f"vice_dir_b[{index}]=state:0x{state:02X},parent:0x{parent:02X},name:{name!r}"
                        )
                path_trace = " ".join(path_parts)
            note_parts = [f"attempt {attempt}: {exc}"]
            if launch_trace:
                note_parts.append(launch_trace)
            if path_trace:
                note_parts.append(path_trace)
            if last_screen:
                note_parts.append(f"screen:\n{last_screen}")
            attempt_notes.append("\n".join(note_parts))
            if attempt < args.attempts:
                time.sleep(attempt_delay)
            else:
                if last_screen:
                    print(last_screen)
                if attempt_notes:
                    print("\n\n".join(attempt_notes), file=sys.stderr)
                if launch_trace:
                    print(launch_trace, file=sys.stderr)
                if path_trace:
                    print(path_trace, file=sys.stderr)
                print(exc, file=sys.stderr)
        finally:
            try:
                client.quit_emulator()
            except Exception:
                pass
            client.close()
            vp.terminate_process_tree(process)

    return 1 if last_error is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())
