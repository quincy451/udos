from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAS_VICE = shutil.which("x64sc") is not None


class UdosBuildTests(unittest.TestCase):
    def test_proof_builds(self) -> None:
        subprocess.run(["make", "proof"], cwd=ROOT, check=True)
        self.assertTrue((ROOT / "build" / "udos-proof.prg").is_file())
        self.assertTrue((ROOT / "build" / "udos-proof.d64").is_file())

    def test_resident_builds(self) -> None:
        subprocess.run(["make", "resident"], cwd=ROOT, check=True)
        self.assertTrue((ROOT / "build" / "udos-resident.prg").is_file())
        self.assertTrue((ROOT / "build" / "udos-resident.d64").is_file())

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_proof_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-proof"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_resident_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-resident"], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
