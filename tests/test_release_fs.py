from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestReleaseFs(unittest.TestCase):
    def test_prepare_release_fs_includes_action_workspace_when_exporter_exists(self) -> None:
        root = Path(__file__).resolve().parents[1]
        tool = root / "tools" / "prepare_release_fs.py"
        base = root / "tests" / "vicefs"

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "release-fs"
            result = subprocess.run(
                [sys.executable, str(tool), "--base", str(base), "--output", str(output)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            self.assertTrue((output / "IMAGES" / "WORK.DNP").is_dir())
            action_root = output / "IMAGES" / "ACTION.DNP"
            self.assertTrue(action_root.is_dir())
            self.assertTrue((action_root / "ACTINFO.PRG").is_file())
            self.assertTrue((action_root / "DOC" / "OPERATOR.TXT").is_file())
            self.assertTrue((action_root / "SRC" / "HELLO.ACT").is_file())
            self.assertTrue((action_root / "LIB" / "LIBMODS.DAT").is_file())
            old_binary_pattern = "*." + ("A" + "VM")
            self.assertFalse(list(action_root.rglob(old_binary_pattern)))
            self.assertFalse(list(action_root.rglob("*.AVT")))
            old_vm_prefix = "A" + "VM"
            old_runner = old_vm_prefix + "RUN"
            for name in (
                old_vm_prefix + "INFO.PRG",
                old_runner + ".PRG",
                old_runner + "C.PRG",
                "ACTDBG.PRG",
                "ACTDBG_OVL1.BIN",
                "ACTDBG_OVL2.BIN",
            ):
                self.assertFalse((action_root / name).exists(), name)
            self.assertFalse(list(action_root.glob("RT_*_HELPER.BIN")))
            self.assertFalse(list(action_root.glob(old_runner + "_OVL*.BIN")))


if __name__ == "__main__":
    unittest.main()
