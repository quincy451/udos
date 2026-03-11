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

    def _assert_asciiish_label(self, data: bytes, offset: int, expected: bytes) -> None:
        actual = bytes(b & 0x7F for b in data[offset : offset + len(expected)])
        self.assertEqual(actual, expected)

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


if __name__ == "__main__":
    unittest.main()
