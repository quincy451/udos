from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAS_VICE = shutil.which("x64sc") is not None
RESIDENT_CODE_START = 0x1810
REU_VICE_TREE_TOTAL = 255 * 6 * 2


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
    def test_batch_argument_expansion_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-batch-args"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_batch_stop_on_error_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-batch-stop"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_autoexec_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-autoexec"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_autoexec_selftest_images_run_in_vice(self) -> None:
        subprocess.run(["make", "vice-selftest"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_workspace_bridge_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-action-workspace"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actdir_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-action-actdir"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actflow_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-action-actflow"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actinfo_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-action-actinfo"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actcopy_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-action-actcopy"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actdel_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-action-actdel"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actmkdir_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-action-actmkdir"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actmove_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-action-actmove"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actrmdir_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-action-actrmdir"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actwrite_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-action-actwrite"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_avminfo_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-action-avminfo"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_avmrun_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-action-avmrun"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_avmrun_flow_runs_in_vice(self) -> None:
        subprocess.run(["make", "vice-action-avmrun-flow"], cwd=ROOT, check=True)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_mem_reports_linked_usage_in_vice(self) -> None:
        subprocess.run(["make", "resident"], cwd=ROOT, check=True)
        labels = load_ld65_labels(ROOT / "build" / "udos-resident.labels")
        used = 0
        free = 0xFFFF
        reu_used = labels["__ACHERON_LAST__"] + REU_VICE_TREE_TOTAL
        reu_free = 0x1000000 - reu_used
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "vice_prg_probe.py"),
                "--disk",
                str(ROOT / "build" / "udos-resident.d64"),
                "--feed-after",
                "A:D64/>",
                "--feed-text",
                "MEM\\r",
                "--vice-arg=-iecdevice9",
                "--vice-arg=-device9",
                "--vice-arg=1",
                f"--vice-arg=-fs9",
                f"--vice-arg={ROOT / 'tests' / 'vicefs'}",
                "--vice-arg=-fslongnames",
                "--expected",
                "RAM USED",
                "--contains",
                f"RAM USED {used}",
                "--contains",
                str(free),
                "--contains",
                f"REU USED {reu_used}",
                "--contains",
                str(reu_free),
                "--settle",
                "1.0",
                "--timeout",
                "60",
            ],
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
