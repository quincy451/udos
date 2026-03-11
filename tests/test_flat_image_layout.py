from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


class FlatImageLayoutTests(unittest.TestCase):
    def _build_probe(self, image_type: str, label: str) -> Path:
        tmpdir = Path(tempfile.mkdtemp(prefix="udos-flat-layout-"))
        sample = tmpdir / "sample.txt"
        sample.write_text("hello\n", encoding="ascii")
        image = tmpdir / f"probe.{image_type}"
        subprocess.run(
            ["c1541", "-format", f"{label},01", image_type, str(image), "-write", str(sample), "HELLO"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return image

    def _build_d71_side2_probe(self) -> Path:
        tmpdir = Path(tempfile.mkdtemp(prefix="udos-flat-layout-d71-side2-"))
        filler = tmpdir / "fill.bin"
        filler.write_bytes(b"A" * 180000)
        sample = tmpdir / "sample.txt"
        sample.write_text("hello\n", encoding="ascii")
        image = tmpdir / "probe.d71"
        subprocess.run(
            [
                "c1541",
                "-format",
                "D71SIDE2,01",
                "d71",
                str(image),
                "-write",
                str(filler),
                "FILLER",
                "-write",
                str(sample),
                "HELLO",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return image

    def _assert_asciiish_label(self, data: bytes, offset: int, expected: bytes) -> None:
        actual = bytes(b & 0x7F for b in data[offset : offset + len(expected)])
        self.assertEqual(actual, expected)

    def _track_sectors(self, image_type: str, track: int) -> int:
        if image_type == "d81":
            return 40
        if image_type == "d71" and track > 35:
            track -= 35
        if track < 18:
            return 21
        if track < 25:
            return 19
        if track < 31:
            return 18
        return 17

    def _image_offset(self, image_type: str, track: int, sector: int) -> int:
        total = 0
        for prior in range(1, track):
            total += self._track_sectors(image_type, prior)
        total += sector
        return total * 256

    def _decode_name(self, raw: bytes) -> bytes:
        out = bytearray()
        for value in raw:
            value &= 0x7F
            if value in (0x00, 0x20):
                break
            if value == 0x20:
                break
            out.append(value)
        return bytes(out).rstrip(b"\x20")

    def _find_root_entry(self, data: bytes, image_type: str, name: bytes) -> tuple[int, int]:
        track, sector = (40, 3) if image_type == "d81" else (18, 1)
        while track:
            offset = self._image_offset(image_type, track, sector)
            sector_data = data[offset : offset + 256]
            for entry_offset in range(2, 0xE3, 0x20):
                if sector_data[entry_offset] == 0:
                    continue
                entry_name = self._decode_name(sector_data[entry_offset + 3 : entry_offset + 19])
                if entry_name == name:
                    return sector_data[entry_offset + 1], sector_data[entry_offset + 2]
            track = sector_data[0]
            sector = sector_data[1]
        raise AssertionError(f"missing entry {name!r}")

    def _find_root_entry_offset(self, data: bytes, image_type: str, name: bytes) -> int:
        track, sector = (40, 3) if image_type == "d81" else (18, 1)
        while track:
            offset = self._image_offset(image_type, track, sector)
            sector_data = data[offset : offset + 256]
            for entry_offset in range(2, 0xE3, 0x20):
                if sector_data[entry_offset] == 0:
                    continue
                entry_name = self._decode_name(sector_data[entry_offset + 3 : entry_offset + 19])
                if entry_name == name:
                    return offset + entry_offset
            track = sector_data[0]
            sector = sector_data[1]
        raise AssertionError(f"missing entry offset for {name!r}")

    def _read_file_chain(self, data: bytes, image_type: str, track: int, sector: int) -> bytes:
        out = bytearray()
        while track:
            offset = self._image_offset(image_type, track, sector)
            sector_data = data[offset : offset + 256]
            next_track = sector_data[0]
            next_sector = sector_data[1]
            if next_track == 0:
                used = max(next_sector - 1, 0)
                out.extend(sector_data[2 : 2 + used])
                break
            out.extend(sector_data[2:256])
            track, sector = next_track, next_sector
        return bytes(out)

    def test_d64_label_and_directory_offsets(self) -> None:
        image = self._build_probe("d64", "D64TEST")
        data = image.read_bytes()
        self._assert_asciiish_label(data, 0x16590, b"D64TEST")
        self.assertEqual(bytes(b & 0x7F for b in data[0x16605:0x1660A]), b"HELLO")

    def test_d71_label_and_directory_offsets(self) -> None:
        image = self._build_probe("d71", "D71TEST")
        data = image.read_bytes()
        self._assert_asciiish_label(data, 0x16590, b"D71TEST")
        self.assertEqual(bytes(b & 0x7F for b in data[0x16605:0x1660A]), b"HELLO")

    def test_d81_label_and_directory_offsets(self) -> None:
        image = self._build_probe("d81", "D81TEST")
        data = image.read_bytes()
        self._assert_asciiish_label(data, 0x61804, b"D81TEST")
        self.assertEqual(bytes(b & 0x7F for b in data[0x61B05:0x61B0A]), b"HELLO")

    def test_d64_file_chain_reads_sample(self) -> None:
        image = self._build_probe("d64", "D64TEST")
        data = image.read_bytes()
        track, sector = self._find_root_entry(data, "d64", b"HELLO")
        self.assertEqual(self._read_file_chain(data, "d64", track, sector), b"hello\n")

    def test_d71_file_chain_reads_sample(self) -> None:
        image = self._build_probe("d71", "D71TEST")
        data = image.read_bytes()
        track, sector = self._find_root_entry(data, "d71", b"HELLO")
        self.assertEqual(self._read_file_chain(data, "d71", track, sector), b"hello\n")

    def test_d81_file_chain_reads_sample(self) -> None:
        image = self._build_probe("d81", "D81TEST")
        data = image.read_bytes()
        track, sector = self._find_root_entry(data, "d81", b"HELLO")
        self.assertEqual(self._read_file_chain(data, "d81", track, sector), b"hello\n")

    def test_d71_second_side_offset_boundary(self) -> None:
        self.assertEqual(self._image_offset("d71", 36, 0), 683 * 256)

    def test_d64_delete_updates_bam_and_directory_entry(self) -> None:
        image = self._build_probe("d64", "D64TEST")
        before = image.read_bytes()
        subprocess.run(["c1541", str(image), "-delete", "HELLO"], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        after = image.read_bytes()
        self.assertEqual(before[0x16544] + 1, after[0x16544])
        self.assertEqual(before[0x16545] | 0x01, after[0x16545])
        self.assertEqual(after[0x16602], 0x00)

    def test_d81_delete_updates_bam_and_directory_entry(self) -> None:
        image = self._build_probe("d81", "D81TEST")
        before = image.read_bytes()
        subprocess.run(["c1541", str(image), "-delete", "HELLO"], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        after = image.read_bytes()
        self.assertEqual(before[0x619F4] + 1, after[0x619F4])
        self.assertEqual(before[0x619F5] | 0x01, after[0x619F5])
        self.assertEqual(after[0x61B02], 0x00)

    def test_d71_side2_delete_updates_side2_bam_and_directory_entry(self) -> None:
        image = self._build_d71_side2_probe()
        before = image.read_bytes()
        track, sector = self._find_root_entry(before, "d71", b"HELLO")
        self.assertGreaterEqual(track, 36)
        self.assertEqual(sector, 0)
        subprocess.run(["c1541", str(image), "-delete", "HELLO"], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        after = image.read_bytes()
        self.assertEqual(before[0x165DF] + 1, after[0x165DF])
        self.assertEqual(before[0x41006] | 0x01, after[0x41006])
        self.assertEqual(after[0x16622], 0x00)

    def test_d64_rename_updates_directory_name_only(self) -> None:
        image = self._build_probe("d64", "D64TEST")
        before = image.read_bytes()
        subprocess.run(["c1541", str(image), "-rename", "HELLO", "BOOT3.PRG"], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        after = image.read_bytes()
        self.assertEqual(after[0x16605:0x16615], bytes([0xC2, 0xCF, 0xCF, 0xD4, 0x33, 0x2E, 0xD0, 0xD2, 0xC7, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0]))
        self.assertEqual(before[0x16600:0x16605], after[0x16600:0x16605])
        self.assertEqual(before[0x16615:0x16620], after[0x16615:0x16620])

    def test_d81_rename_updates_directory_name_only(self) -> None:
        image = self._build_probe("d81", "D81TEST")
        before = image.read_bytes()
        subprocess.run(["c1541", str(image), "-rename", "HELLO", "BOOT3.PRG"], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        after = image.read_bytes()
        self.assertEqual(after[0x61B05:0x61B15], bytes([0xC2, 0xCF, 0xCF, 0xD4, 0x33, 0x2E, 0xD0, 0xD2, 0xC7, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0]))
        self.assertEqual(before[0x61B00:0x61B05], after[0x61B00:0x61B05])
        self.assertEqual(before[0x61B15:0x61B20], after[0x61B15:0x61B20])

    def test_d71_side2_rename_updates_directory_name_only(self) -> None:
        image = self._build_d71_side2_probe()
        before = image.read_bytes()
        entry_offset = self._find_root_entry_offset(before, "d71", b"HELLO")
        subprocess.run(["c1541", str(image), "-rename", "HELLO", "BOOT3.PRG"], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        after = image.read_bytes()
        self.assertEqual(after[entry_offset + 3 : entry_offset + 19], bytes([0xC2, 0xCF, 0xCF, 0xD4, 0x33, 0x2E, 0xD0, 0xD2, 0xC7, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0]))
        self.assertEqual(before[entry_offset : entry_offset + 3], after[entry_offset : entry_offset + 3])
        self.assertEqual(before[entry_offset + 19 : entry_offset + 32], after[entry_offset + 19 : entry_offset + 32])

    def test_d64_copy_creates_new_entry_and_payload(self) -> None:
        image = self._build_probe("d64", "D64COPY")
        before = image.read_bytes()
        subprocess.run(["c1541", str(image), "-copy", "HELLO", "BOOT3.PRG"], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        after = image.read_bytes()
        track, sector = self._find_root_entry(after, "d64", b"BOOT3.PRG")
        entry_offset = self._find_root_entry_offset(after, "d64", b"BOOT3.PRG")
        self.assertEqual(self._read_file_chain(after, "d64", track, sector), b"hello\n")
        self.assertEqual(before[0x16544] - 1, after[0x16544])
        self.assertEqual(after[entry_offset + 3 : entry_offset + 19], bytes([0xC2, 0xCF, 0xCF, 0xD4, 0x33, 0x2E, 0xD0, 0xD2, 0xC7, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0]))
        self.assertEqual(after[entry_offset + 28 : entry_offset + 30], b"\x01\x00")

    def test_d71_copy_creates_new_entry_and_payload(self) -> None:
        image = self._build_probe("d71", "D71COPY")
        subprocess.run(["c1541", str(image), "-copy", "HELLO", "BOOT3.PRG"], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        after = image.read_bytes()
        track, sector = self._find_root_entry(after, "d71", b"BOOT3.PRG")
        entry_offset = self._find_root_entry_offset(after, "d71", b"BOOT3.PRG")
        self.assertEqual(self._read_file_chain(after, "d71", track, sector), b"hello\n")
        self.assertEqual(after[entry_offset + 3 : entry_offset + 19], bytes([0xC2, 0xCF, 0xCF, 0xD4, 0x33, 0x2E, 0xD0, 0xD2, 0xC7, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0]))
        self.assertEqual(after[entry_offset + 28 : entry_offset + 30], b"\x01\x00")

    def test_d81_copy_creates_new_entry_and_payload(self) -> None:
        image = self._build_probe("d81", "D81COPY")
        before = image.read_bytes()
        subprocess.run(["c1541", str(image), "-copy", "HELLO", "BOOT3.PRG"], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        after = image.read_bytes()
        track, sector = self._find_root_entry(after, "d81", b"BOOT3.PRG")
        entry_offset = self._find_root_entry_offset(after, "d81", b"BOOT3.PRG")
        self.assertEqual(self._read_file_chain(after, "d81", track, sector), b"hello\n")
        self.assertEqual(before[0x619F4] - 1, after[0x619F4])
        self.assertEqual(after[entry_offset + 3 : entry_offset + 19], bytes([0xC2, 0xCF, 0xCF, 0xD4, 0x33, 0x2E, 0xD0, 0xD2, 0xC7, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0]))
        self.assertEqual(after[entry_offset + 28 : entry_offset + 30], b"\x01\x00")


if __name__ == "__main__":
    unittest.main()
