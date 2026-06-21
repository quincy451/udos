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
REU_LAUNCH_HIRAM_SIZE = 0x0C00


def load_ld65_labels(path: Path) -> dict[str, int]:
    symbols: dict[str, int] = {}
    for line in path.read_text(errors="ignore").splitlines():
        parts = line.split()
        if len(parts) != 3 or parts[0] != "al":
            continue
        symbols[parts[2].lstrip(".")] = int(parts[1], 16)
    return symbols


class UdosBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not HAS_VICE:
            return
        subprocess.run(["make", "resident", "release"], cwd=ROOT, check=True)

    def run_make(self, target: str) -> None:
        cmd = ["make"]
        if target.startswith("vice-"):
            cmd.extend(["PROOF_DEPS=", "RESIDENT_DEPS=", "RELEASE_DEPS="])
        cmd.append(target)
        subprocess.run(cmd, cwd=ROOT, check=True)

    def test_resident_builds(self) -> None:
        self.run_make("resident")
        self.assertTrue((ROOT / "build" / "udos-resident.prg").is_file())
        self.assertTrue((ROOT / "build" / "udos-resident.d64").is_file())

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_resident_runs_in_vice(self) -> None:
        self.run_make("vice-resident")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_implicit_launch_runs_in_vice(self) -> None:
        self.run_make("vice-launch")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_wildcard_copy_runs_in_vice(self) -> None:
        self.run_make("vice-copy")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_reserved_drive_tokens_run_in_vice(self) -> None:
        self.run_make("vice-drive")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_reu_service_roundtrip_runs_in_vice(self) -> None:
        self.run_make("vice-reu-services")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_real_tree_reads_run_in_vice(self) -> None:
        self.run_make("vice-real-read")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_real_tree_write_lifecycle_runs_in_vice(self) -> None:
        self.run_make("vice-real-tree-write")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_real_tree_host_rename_runs_in_vice(self) -> None:
        self.run_make("vice-real-tree-rename")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_real_tree_wildcards_run_in_vice(self) -> None:
        self.run_make("vice-real-tree-wild")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_real_tree_directory_create_remove_runs_in_vice(self) -> None:
        self.run_make("vice-real-tree-dir")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_real_tree_rmdir_rejects_nonempty_dirs_in_vice(self) -> None:
        self.run_make("vice-real-tree-rmdir")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_batch_argument_expansion_runs_in_vice(self) -> None:
        self.run_make("vice-batch-args")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_batch_stop_on_error_runs_in_vice(self) -> None:
        self.run_make("vice-batch-stop")

    @unittest.skip("embedded resident AUTOEXEC.BAT is disabled because the resident image no longer fits it")
    def test_autoexec_runs_in_vice(self) -> None:
        self.run_make("vice-autoexec")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_autoexec_selftest_images_run_in_vice(self) -> None:
        self.run_make("vice-selftest")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_workspace_bridge_runs_in_vice(self) -> None:
        self.run_make("vice-action-workspace")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actadd_runs_in_vice(self) -> None:
        self.run_make("vice-action-actadd")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actadd_persists_in_vice(self) -> None:
        self.run_make("vice-action-actadd-persist")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_act2save_runs_in_vice(self) -> None:
        self.run_make("vice-action-act2save")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actc_runs_in_vice(self) -> None:
        self.run_make("vice-action-actc")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_alink_runs_in_vice(self) -> None:
        self.run_make("vice-action-alink")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actc_alink_launch_printmath_runs_in_vice(self) -> None:
        self.run_make("vice-action-actc-alink-launch-printmath")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actc_alink_launch_runs_in_vice(self) -> None:
        self.run_make("vice-action-actc-alink-launch")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actc_alink_launch_nested_else_chain_runs_in_vice(self) -> None:
        self.run_make("vice-action-actc-alink-launch-nested-else-chain")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actchk_runs_in_vice(self) -> None:
        self.run_make("vice-action-actchk")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actmon_check_runs_in_vice(self) -> None:
        self.run_make("vice-action-actmon-check")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actmon_runs_in_vice(self) -> None:
        self.run_make("vice-action-actmon")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actdir_runs_in_vice(self) -> None:
        self.run_make("vice-action-actdir")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actsrc_runs_in_vice(self) -> None:
        self.run_make("vice-action-actsrc")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actfile_runs_in_vice(self) -> None:
        self.run_make("vice-action-actfile")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actwork_runs_in_vice(self) -> None:
        self.run_make("vice-action-actwork")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actflow_runs_in_vice(self) -> None:
        self.run_make("vice-action-actflow")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actinfo_runs_in_vice(self) -> None:
        self.run_make("vice-action-actinfo")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actnew_runs_in_vice(self) -> None:
        self.run_make("vice-action-actnew")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actnew_prg_runs_in_vice(self) -> None:
        self.run_make("vice-action-actnew-prg")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actnew_prg_persists_in_vice(self) -> None:
        self.run_make("vice-action-actnew-prg-persist")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actcopy_runs_in_vice(self) -> None:
        self.run_make("vice-action-actcopy")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actdel_runs_in_vice(self) -> None:
        self.run_make("vice-action-actdel")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actmkdir_runs_in_vice(self) -> None:
        self.run_make("vice-action-actmkdir")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actmkdir_persists_in_vice(self) -> None:
        self.run_make("vice-action-actmkdir-persist")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actmove_runs_in_vice(self) -> None:
        self.run_make("vice-action-actmove")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actmove_persists_in_vice(self) -> None:
        self.run_make("vice-action-actmove-persist")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actrmdir_runs_in_vice(self) -> None:
        self.run_make("vice-action-actrmdir")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actrmdir_persists_in_vice(self) -> None:
        self.run_make("vice-action-actrmdir-persist")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_actwrite_runs_in_vice(self) -> None:
        self.run_make("vice-action-actwrite")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_mem_reports_linked_usage_in_vice(self) -> None:
        labels = load_ld65_labels(ROOT / "build" / "udos-resident.labels")
        used = 0
        free = 0xFFFF
        resident_size = labels["resident_image_end"] - RESIDENT_CODE_START
        reu_used = REU_VICE_TREE_TOTAL + resident_size + REU_LAUNCH_HIRAM_SIZE
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
