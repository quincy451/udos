#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from pathlib import Path

import run_action_avmrun_probe as avp
import vice_prg_probe as vp


ROOT = Path(__file__).resolve().parents[1]
ACTION = ROOT.parent / "actionc64u"
BUILD_DIR = ACTION / "build" / "udos_tools"

AVM_VERSION_V2 = 2
AVM_FLAG_ACHERON = 1
AVM_FLAG_NATIVE_HELPERS = 2

OPCODE_SETP16 = 0x61
OPCODE_CALLN = 0x49

INTRINSIC_LINKED_DBF_CREATE = 0xFB01
INTRINSIC_LINKED_DBF_CURRRECNO = 0xFB02
INTRINSIC_LINKED_DBF_TOTALRECS = 0xFB03
INTRINSIC_LINKED_DBF_CLOSE = 0xFB04
INTRINSIC_LINKED_DBF_OPEN = 0xFB05
INTRINSIC_EXIT = 0xFF20

AVM_HEADER_SIZE_V2 = 12
FILE_BUFFER_ADDR = 0x4800
REQUEST_SIZE = 14
FILENAME_BYTES = b"TEST.DBF\x00"
EXPECTED_DBF_BYTES_MINIMAL = bytes(
    (
        ord("D"),
        ord("B"),
        ord("F"),
        ord("1"),
        0x03,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
    )
)
EXPECTED_DBF_BYTES_RECORDS = bytes(
    (
        ord("D"), ord("B"), ord("F"), ord("1"),
        0x03, 0x00,
        0x02, 0x00,
        0x02, 0x00,
        0x34, 0x12, 0x00, 0x00, 0x78, 0x56,
        0x00, 0x00, 0xBC, 0x9A, 0x00, 0x00,
    )
)


def build_artifacts() -> tuple[Path, bytes]:
    # This probe validates the shipped AVMRUN DBF fast path, so it intentionally
    # builds the production runner rather than helper assets only.
    subprocess.run(["bash", "tools/build_avmrun_udos.sh"], cwd=ACTION, check=True, stdout=subprocess.DEVNULL)
    avmrun = BUILD_DIR / "AVMRUN.PRG"
    helper = BUILD_DIR / "RT_DBF1_HELPER.BIN"
    if not avmrun.is_file():
        raise FileNotFoundError(avmrun)
    if not helper.is_file():
        raise FileNotFoundError(helper)
    helper_blob = helper.read_bytes()
    if helper_blob[:4] != b"AVNH" or helper_blob[5] != 5:
        raise RuntimeError("unexpected DBF helper header")
    return avmrun, helper_blob


def make_request(
    *,
    handle: int = 0,
    field_count: int = 3,
    curr: int = 0,
    field_index: int = 0,
    value: int = 0,
) -> bytearray:
    return bytearray(
        (
            0x00,
            handle & 0xFF,
            field_count & 0xFF,
            (field_count >> 8) & 0xFF,
            0x00,
            0x00,
            curr & 0xFF,
            (curr >> 8) & 0xFF,
            0x00,
            0x00,
            field_index & 0xFF,
            (field_index >> 8) & 0xFF,
            value & 0xFF,
            (value >> 8) & 0xFF,
        )
    )


def build_minimal_fastdbf_avm(helper_blob: bytes) -> bytes:
    request_blocks = [
        make_request(handle=0),
        make_request(handle=1),
        make_request(handle=0),
        make_request(handle=1),
        make_request(handle=1),
    ]
    operations = [
        INTRINSIC_LINKED_DBF_CREATE,
        INTRINSIC_LINKED_DBF_CLOSE,
        INTRINSIC_LINKED_DBF_OPEN,
        INTRINSIC_LINKED_DBF_CURRRECNO,
        INTRINSIC_LINKED_DBF_TOTALRECS,
    ]
    exec_len = len(operations) * 6 + 3
    requests_base = FILE_BUFFER_ADDR + AVM_HEADER_SIZE_V2 + exec_len
    path_abs = requests_base + len(request_blocks) * REQUEST_SIZE
    for block in request_blocks:
        block[8] = path_abs & 0xFF
        block[9] = (path_abs >> 8) & 0xFF

    request_offsets = [exec_len + i * REQUEST_SIZE for i in range(len(request_blocks))]
    exec_code = bytearray()
    for request_offset, intrinsic in zip(request_offsets, operations):
        exec_code.extend(
            (
                OPCODE_SETP16,
                request_offset & 0xFF,
                request_offset >> 8,
                OPCODE_CALLN,
                intrinsic & 0xFF,
                intrinsic >> 8,
            )
        )
    exec_code.extend((OPCODE_CALLN, INTRINSIC_EXIT & 0xFF, INTRINSIC_EXIT >> 8))

    payload = bytes(exec_code + b"".join(bytes(block) for block in request_blocks) + FILENAME_BYTES)
    trailer = bytearray(b"AVH1")
    trailer.append(1)
    trailer.append(5)
    trailer.extend((len(helper_blob) & 0xFF, (len(helper_blob) >> 8) & 0xFF))
    trailer.extend(helper_blob)

    header = bytearray(b"AVM1")
    header.append(AVM_VERSION_V2)
    header.extend((len(payload) & 0xFF, (len(payload) >> 8) & 0xFF))
    header.extend((0x00, 0x00))
    header.append(AVM_FLAG_ACHERON | AVM_FLAG_NATIVE_HELPERS)
    header.extend((exec_len & 0xFF, (exec_len >> 8) & 0xFF))
    return bytes(header + payload + trailer)


def build_record_fastdbf_avm(helper_blob: bytes) -> bytes:
    intrinsic_linked_dbf_appendblank = 0xFB06
    intrinsic_linked_dbf_go = 0xFB07
    intrinsic_linked_dbf_readfield = 0xFB08
    intrinsic_linked_dbf_writefield = 0xFB09

    request_blocks = [
        make_request(handle=0),                                # create
        make_request(handle=1),                                # append 1
        make_request(handle=1, field_index=0, value=0x1234),   # write rec1 field0
        make_request(handle=1, field_index=2, value=0x5678),   # write rec1 field2
        make_request(handle=1),                                # append 2
        make_request(handle=1, field_index=1, value=0x9ABC),   # write rec2 field1
        make_request(handle=1),                                # close
        make_request(handle=0),                                # open
        make_request(handle=1, curr=1),                        # go rec1
        make_request(handle=1, field_index=0),                 # read rec1 field0
        make_request(handle=1, field_index=2),                 # read rec1 field2
        make_request(handle=1, curr=2),                        # go rec2
        make_request(handle=1, field_index=1),                 # read rec2 field1
        make_request(handle=1),                                # meta curr/total
    ]
    operations = [
        INTRINSIC_LINKED_DBF_CREATE,
        intrinsic_linked_dbf_appendblank,
        intrinsic_linked_dbf_writefield,
        intrinsic_linked_dbf_writefield,
        intrinsic_linked_dbf_appendblank,
        intrinsic_linked_dbf_writefield,
        INTRINSIC_LINKED_DBF_CLOSE,
        INTRINSIC_LINKED_DBF_OPEN,
        intrinsic_linked_dbf_go,
        intrinsic_linked_dbf_readfield,
        intrinsic_linked_dbf_readfield,
        intrinsic_linked_dbf_go,
        intrinsic_linked_dbf_readfield,
        INTRINSIC_LINKED_DBF_CURRRECNO,
        INTRINSIC_LINKED_DBF_TOTALRECS,
    ]
    request_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 13]
    exec_len = len(operations) * 6 + 3
    requests_base = FILE_BUFFER_ADDR + AVM_HEADER_SIZE_V2 + exec_len
    path_abs = requests_base + len(request_blocks) * REQUEST_SIZE
    for block in request_blocks:
        block[8] = path_abs & 0xFF
        block[9] = (path_abs >> 8) & 0xFF

    request_offsets = [exec_len + i * REQUEST_SIZE for i in range(len(request_blocks))]
    exec_code = bytearray()
    for req_index, intrinsic in zip(request_indices, operations):
        request_offset = request_offsets[req_index]
        exec_code.extend(
            (
                OPCODE_SETP16,
                request_offset & 0xFF,
                request_offset >> 8,
                OPCODE_CALLN,
                intrinsic & 0xFF,
                intrinsic >> 8,
            )
        )
    exec_code.extend((OPCODE_CALLN, INTRINSIC_EXIT & 0xFF, INTRINSIC_EXIT >> 8))
    payload = bytes(exec_code + b"".join(bytes(block) for block in request_blocks) + FILENAME_BYTES)
    trailer = bytearray(b"AVH1")
    trailer.append(1)
    trailer.append(5)
    trailer.extend((len(helper_blob) & 0xFF, (len(helper_blob) >> 8) & 0xFF))
    trailer.extend(helper_blob)

    header = bytearray(b"AVM1")
    header.append(AVM_VERSION_V2)
    header.extend((len(payload) & 0xFF, (len(payload) >> 8) & 0xFF))
    header.extend((0x00, 0x00))
    header.append(AVM_FLAG_ACHERON | AVM_FLAG_NATIVE_HELPERS)
    header.extend((exec_len & 0xFF, (exec_len >> 8) & 0xFF))
    return bytes(header + payload + trailer)


def ensure_catalog_entries(path: Path, entries: list[str]) -> None:
    lines: list[str] = []
    if path.is_file():
        lines = [line.strip() for line in path.read_text(encoding="ascii", errors="ignore").splitlines() if line.strip()]
    for entry in entries:
        if entry not in lines:
            lines.append(entry)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="ascii")


def prepare_fs(fs_root: Path, avmrun_prg: Path, helper_blob: bytes, mode: str) -> None:
    src = ROOT / "build" / "udos-release-fs"
    if fs_root.exists():
        shutil.rmtree(fs_root)
    shutil.copytree(src, fs_root)

    img = fs_root / "IMAGES" / "ACTION.DNP"
    shutil.copy2(avmrun_prg, img / "AVMRUN.PRG")
    if mode == "minimal":
        avm_bytes = build_minimal_fastdbf_avm(helper_blob)
    elif mode == "records":
        avm_bytes = build_record_fastdbf_avm(helper_blob)
    else:
        raise ValueError(f"unsupported probe mode: {mode}")
    (img / "FASTDBF.AVM").write_bytes(avm_bytes)

    for removable in ("RT_DBF1_HELPER.BIN", "AVMRUN_OVL3.BIN"):
        target = img / removable
        if target.exists():
            target.unlink()

    ensure_catalog_entries(img / "UDOSDIR.TXT", ["F AVMRUN.PRG", "F FASTDBF.AVM"])


def run_probe(
    *,
    disk: Path,
    fs_root: Path,
    attempts: int,
    attempt_delay: float,
) -> str:
    last_error: Exception | None = None
    last_screen = ""
    connect_delays = avp.WORKSPACE_CONNECT_DELAYS
    for attempt in range(1, attempts + 1):
        vp.cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, attempt_delay)))
        port = vp.reserve_tcp_port()
        process = vp.launch_vice(
            disk,
            port,
            extra_args=["-iecdevice9", "-fs9", str(fs_root), "-fslongnames"],
        )
        client = vp.BinaryMonitorClient("127.0.0.1", port, timeout=5.0)
        try:
            connect_delay = connect_delays[(attempt - 1) % len(connect_delays)]
            if connect_delay > 0.0:
                time.sleep(connect_delay)
            client.connect(time.monotonic() + 20.0)
            client.ping()
            client.resume()

            avp.wait_for_screen_fragment(client, "A:D64/>", 60.0, poll_interval=0.2)
            time.sleep(3.0)

            avp.type_command(client, "MOUNT B: /IMAGES/ACTION.DNP", 30.0)
            time.sleep(2.5)

            avp.type_command(client, "B:", 30.0)
            screen = avp.wait_for_screen_fragment(client, "B:DNP/>", 30.0, retry_echo="B:", poll_interval=0.2)
            prompt_count = vp.screen_count(screen, "B:DNP/>")

            avp.type_command(client, "AVMRUN FASTDBF.AVM", 30.0)
            time.sleep(1.0)
            avp.wait_for_screen_fragment(client, "RUN AVMRUN.PRG", 30.0, retry_echo="AVMRUN FASTDBF.AVM", poll_interval=0.2)
            screen = avp.wait_for_prompt_count(client, "B:DNP/>", prompt_count + 1, 30.0, poll_interval=0.2)

            for fragment in ("NEEDS AVMRUN COMPAT", "BAD AVM", "UNSUPPORTED AVM", "HARNESS NO ACHERON"):
                if vp.screen_contains(screen, fragment):
                    raise vp.ViceError(f"unexpected screen fragment {fragment!r} was present:\n{screen}")

            return screen
        except Exception as exc:
            last_error = exc
            try:
                last_screen = avp.screen_text(client)
            except Exception:
                last_screen = ""
        finally:
            try:
                client.quit_emulator()
            except Exception:
                pass
            client.close()
            vp.terminate_process_tree(process)

        if attempt < attempts:
            time.sleep(attempt_delay)

    message = str(last_error) if last_error is not None else "DBF fast-path probe failed"
    if last_screen:
        message += f"\nlast screen:\n{last_screen}"
    raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify AVMRUN linked DBF fast path in VICE")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--mode", choices=("minimal", "records"), default="minimal")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--attempt-delay", type=float, default=4.0)
    args = parser.parse_args()

    disk = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    avmrun_prg, helper_blob = build_artifacts()
    prepare_fs(fs_root, avmrun_prg, helper_blob, args.mode)
    screen = run_probe(
        disk=disk,
        fs_root=fs_root,
        attempts=args.attempts,
        attempt_delay=args.attempt_delay,
    )

    img = fs_root / "IMAGES" / "ACTION.DNP"
    dbf_path = img / "TEST.DBF"
    if not dbf_path.is_file():
        raise RuntimeError(f"expected {dbf_path} to exist after production DBF run")
    dbf_bytes = dbf_path.read_bytes()
    expected_dbf_bytes = EXPECTED_DBF_BYTES_MINIMAL if args.mode == "minimal" else EXPECTED_DBF_BYTES_RECORDS
    if dbf_bytes != expected_dbf_bytes:
        raise RuntimeError(f"unexpected TEST.DBF bytes: expected {expected_dbf_bytes!r}, got {dbf_bytes!r}")
    if (img / "RT_DBF1_HELPER.BIN").exists():
        raise RuntimeError("unexpected loose RT_DBF1_HELPER.BIN was restored during DBF fast-path proof")
    if (img / "AVMRUN_OVL3.BIN").exists():
        raise RuntimeError("unexpected AVMRUN_OVL3.BIN was restored during DBF fast-path proof")

    print(screen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
