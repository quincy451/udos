from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAS_VICE = shutil.which("x64sc") is not None
RESIDENT_CODE_START = 0x1810


def load_ld65_labels(path: Path) -> dict[str, int]:
    symbols: dict[str, int] = {}
    for line in path.read_text(errors="ignore").splitlines():
        parts = line.split()
        if len(parts) != 3 or parts[0] != "al":
            continue
        symbols[parts[2].lstrip(".")] = int(parts[1], 16)
    return symbols


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

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_implicit_launch_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-launch"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_wildcard_copy_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-copy"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_reserved_drive_tokens_run_in_vice(self) -> None:
        subprocess.run(["make", "vice-drive"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_real_tree_reads_run_in_vice(self) -> None:
        subprocess.run(["make", "vice-real-read"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_real_tree_write_lifecycle_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-real-tree-write"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_real_tree_host_rename_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-real-tree-rename"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_real_tree_wildcards_run_in_vice(self) -> None:
        subprocess.run(["make", "vice-real-tree-wild"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_real_tree_directory_create_remove_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-real-tree-dir"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_real_tree_rmdir_rejects_nonempty_dirs_in_vice(self) -> None:
        subprocess.run(["make", "vice-real-tree-rmdir"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_mem_reports_linked_usage_in_vice(self) -> None:
        subprocess.run(["make", "resident"], cwd=ROOT, check=True)
        labels = load_ld65_labels(ROOT / "build" / "udos-resident.labels")
        used = labels["__ACHERON_LAST__"] - RESIDENT_CODE_START
        free = 0xFFFF - used
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "vice_prg_probe.py"),
                "--disk",
                str(ROOT / "build" / "udosres.prg"),
                "--feed-after",
                "A:D64/>",
                "--feed-text",
                "MEM\\r",
                "--expected",
                "RAM USED",
                "--contains",
                f"RAM USED {used} FREE {free}",
                "--contains",
                "REU USED 0 FRE",
                "--contains",
                "E 16777216",
            ],
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
