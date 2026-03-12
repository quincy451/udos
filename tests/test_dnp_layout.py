from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


TRACK_SIZE = 256 * 256
ROOT_HEADER = (1, 35)
ROOT_DIR = (1, 36)
SRC_HEADER = (1, 64)
SRC_DIR = (1, 65)
HELLO_DATA = (2, 0)
BOOT_DATA = (2, 1)


class DnpLayoutTests(unittest.TestCase):
    def _build_probe(self) -> Path:
        tmpdir = Path(tempfile.mkdtemp(prefix="udos-dnp-layout-"))
        image = tmpdir / "probe.dnp"
        data = bytearray(TRACK_SIZE * 4)
        self._write_partition_block(data, b"WORK")
        self._write_directory_header(data, ROOT_HEADER, b"WORK", ROOT_DIR, (0, 0), (0, 0), 0)
        self._write_directory_header(data, SRC_HEADER, b"SRC", SRC_DIR, ROOT_HEADER, ROOT_DIR, 2)
        self._write_dir_entry(
            data,
            ROOT_DIR,
            2,
            0x86,
            SRC_HEADER,
            b"SRC",
            size_sectors=2,
        )
        self._write_dir_entry(
            data,
            ROOT_DIR,
            0x22,
            0x82,
            HELLO_DATA,
            b"HELLO.PRG",
            size_sectors=1,
        )
        self._write_dir_entry(
            data,
            SRC_DIR,
            2,
            0x82,
            BOOT_DATA,
            b"BOOT.ASM",
            size_sectors=1,
        )
        self._write_file_sector(data, HELLO_DATA, b"HELLO FROM DNP\n")
        self._write_file_sector(data, BOOT_DATA, b"; BOOT.ASM DNP SOURCE\n")
        self._mark_used(data, (1, 0))
        self._mark_used(data, (1, 1))
        for sector in range(2, 34):
            self._mark_used(data, (1, sector))
        self._mark_used(data, ROOT_HEADER)
        self._mark_used(data, ROOT_DIR)
        self._mark_used(data, SRC_HEADER)
        self._mark_used(data, SRC_DIR)
        self._mark_used(data, HELLO_DATA)
        self._mark_used(data, BOOT_DATA)
        image.write_bytes(data)
        return image

    def _offset(self, track: int, sector: int) -> int:
        return ((track - 1) << 16) + (sector << 8)

    def _write_sector(self, data: bytearray, ts: tuple[int, int], payload: bytes) -> None:
        offset = self._offset(*ts)
        data[offset : offset + 256] = payload.ljust(256, b"\x00")

    def _petscii_name(self, name: bytes) -> bytes:
        encoded = bytearray()
        for value in name:
            if 0x61 <= value <= 0x7A:
                value -= 0x20
            if value == 0x20:
                encoded.append(0x20)
            else:
                encoded.append(value | 0x80)
        return bytes(encoded[:16]).ljust(16, b"\xA0")

    def _write_partition_block(self, data: bytearray, label: bytes) -> None:
        block = bytearray(256)
        block[0:2] = bytes(ROOT_DIR)
        block[2] = ord("H")
        block[4:20] = self._petscii_name(label)
        block[20:22] = bytes(ROOT_HEADER)
        block[22:24] = b"\x00\x00"
        block[24:26] = b"\x00\x00"
        block[26] = 0
        self._write_sector(data, (1, 1), bytes(block))

    def _write_directory_header(
        self,
        data: bytearray,
        header_ts: tuple[int, int],
        label: bytes,
        dir_ts: tuple[int, int],
        parent_header_ts: tuple[int, int],
        parent_dir_entry_ts: tuple[int, int],
        parent_dir_index: int,
    ) -> None:
        block = bytearray(256)
        block[0:2] = bytes(dir_ts)
        block[2] = ord("H")
        block[4:20] = self._petscii_name(label)
        block[20:22] = bytes(header_ts)
        block[22:24] = bytes(parent_header_ts)
        block[24:26] = bytes(parent_dir_entry_ts)
        block[26] = parent_dir_index
        self._write_sector(data, header_ts, bytes(block))

    def _write_dir_entry(
        self,
        data: bytearray,
        dir_ts: tuple[int, int],
        entry_offset: int,
        file_type: int,
        start_ts: tuple[int, int],
        name: bytes,
        *,
        size_sectors: int,
    ) -> None:
        offset = self._offset(*dir_ts)
        sector = bytearray(data[offset : offset + 256])
        sector[0:2] = b"\x00\xff"
        sector[entry_offset] = file_type
        sector[entry_offset + 1 : entry_offset + 3] = bytes(start_ts)
        sector[entry_offset + 3 : entry_offset + 19] = self._petscii_name(name)
        sector[entry_offset + 0x1E] = size_sectors & 0xFF
        sector[entry_offset + 0x1F] = (size_sectors >> 8) & 0xFF
        self._write_sector(data, dir_ts, bytes(sector))

    def _write_file_sector(self, data: bytearray, ts: tuple[int, int], payload: bytes) -> None:
        if len(payload) > 254:
            raise ValueError("payload too large for single-sector probe")
        block = bytearray(256)
        block[0] = 0
        block[1] = len(payload) + 1
        block[2 : 2 + len(payload)] = payload
        self._write_sector(data, ts, bytes(block))

    def _mark_used(self, data: bytearray, ts: tuple[int, int]) -> None:
        track, sector = ts
        bam_offset = self._offset(1, 2) + 0x20 + ((track - 1) * 0x20)
        byte_index = sector >> 3
        bit_mask = 1 << (sector & 7)
        data[bam_offset + byte_index] &= 0xFF ^ bit_mask

    def _decode_name(self, raw: bytes) -> bytes:
        out = bytearray()
        for value in raw:
            value &= 0x7F
            if value in (0x00, 0xA0):
                break
            out.append(value)
        return bytes(out).rstrip(b"\x20")

    def _find_dir_entry(self, data: bytes, dir_ts: tuple[int, int], name: bytes) -> tuple[int, tuple[int, int]]:
        track, sector = dir_ts
        while track:
            offset = self._offset(track, sector)
            block = data[offset : offset + 256]
            for entry_offset in range(2, 0x100, 0x20):
                if block[entry_offset] == 0:
                    continue
                entry_name = self._decode_name(block[entry_offset + 3 : entry_offset + 19])
                if entry_name == name:
                    return block[entry_offset], (block[entry_offset + 1], block[entry_offset + 2])
            track = block[0]
            sector = block[1]
            if track == 0:
                break
        raise AssertionError(f"missing directory entry {name!r}")

    def _read_file_chain(self, data: bytes, start_ts: tuple[int, int]) -> bytes:
        track, sector = start_ts
        out = bytearray()
        while track:
            offset = self._offset(track, sector)
            block = data[offset : offset + 256]
            next_track = block[0]
            next_sector = block[1]
            if next_track == 0:
                out.extend(block[2 : 2 + max(next_sector - 1, 0)])
                break
            out.extend(block[2:256])
            track, sector = next_track, next_sector
        return bytes(out)

    def test_partition_block_and_root_header_pointers(self) -> None:
        image = self._build_probe()
        data = image.read_bytes()
        self.assertEqual(data[self._offset(1, 1) : self._offset(1, 1) + 2], bytes(ROOT_DIR))
        self.assertEqual(data[self._offset(1, 1) + 20 : self._offset(1, 1) + 22], bytes(ROOT_HEADER))
        self.assertEqual(data[self._offset(*ROOT_HEADER) : self._offset(*ROOT_HEADER) + 2], bytes(ROOT_DIR))

    def test_root_directory_lists_subdirectory_and_program(self) -> None:
        image = self._build_probe()
        data = image.read_bytes()
        entry_type, start = self._find_dir_entry(data, ROOT_DIR, b"SRC")
        self.assertEqual(entry_type, 0x86)
        self.assertEqual(start, SRC_HEADER)
        entry_type, start = self._find_dir_entry(data, ROOT_DIR, b"HELLO.PRG")
        self.assertEqual(entry_type, 0x82)
        self.assertEqual(start, HELLO_DATA)

    def test_subdirectory_lists_nested_file(self) -> None:
        image = self._build_probe()
        data = image.read_bytes()
        entry_type, start = self._find_dir_entry(data, SRC_DIR, b"BOOT.ASM")
        self.assertEqual(entry_type, 0x82)
        self.assertEqual(start, BOOT_DATA)

    def test_file_chain_reads_expected_payloads(self) -> None:
        image = self._build_probe()
        data = image.read_bytes()
        self.assertEqual(self._read_file_chain(data, HELLO_DATA), b"HELLO FROM DNP\n")
        self.assertEqual(self._read_file_chain(data, BOOT_DATA), b"; BOOT.ASM DNP SOURCE\n")


if __name__ == "__main__":
    unittest.main()
