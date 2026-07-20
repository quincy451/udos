from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_action_probe_fs as pfs
import run_action_actc_probe as actc_probe
import run_action_actmon_probe as actmon_probe


class TestToolPaths(unittest.TestCase):
    def test_tool_scripts_do_not_hardcode_wsl_workspace(self) -> None:
        root = Path(__file__).resolve().parents[1]
        findings: list[str] = []
        for path in sorted((root / "tools").glob("*.py")):
            text = path.read_text(encoding="utf-8", errors="replace")
            if "/mnt/c/test/action" in text:
                findings.append(path.relative_to(root).as_posix())

        self.assertFalse(
            findings,
            "Tool scripts must derive workspace paths from __file__, not /mnt/c/test/action: "
            + ", ".join(findings),
        )

    def test_case_path_sync_uses_the_authoritative_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            authoritative = root / "SRC" / "SWAPTEST.PRG"
            stale = root / "src" / "swaptest.prg"
            authoritative.parent.mkdir(parents=True)
            stale.parent.mkdir(parents=True)
            authoritative.write_bytes(b"new")
            stale.write_bytes(b"stale")

            pfs.sync_case_path_variants(root, authoritative)

            for directory in ("SRC", "src"):
                for filename in ("SWAPTEST.PRG", "swaptest.prg"):
                    self.assertEqual(
                        (root / directory / filename).read_bytes(),
                        b"new",
                    )

    def test_actmon_fixture_uses_lowercase_mutable_files_with_uppercase_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "PROJ3"
            actmon_probe.write_project_state(
                project_root,
                [("MAIN", "PROC MAIN()\rENDPROC\r")],
                lowercase_workspace=False,
            )

            self.assertTrue((project_root / "src").is_dir())
            self.assertFalse((project_root / "src").is_symlink())
            self.assertEqual((project_root / "SRC").readlink(), Path("src"))
            self.assertEqual((project_root / "ACTION.PROJ").readlink(), Path("action.proj"))
            self.assertEqual((project_root / "src" / "MAIN.ACT").readlink(), Path("main.act"))
            self.assertFalse((project_root / "src" / "main.act").is_symlink())
            self.assertEqual((project_root / "udosdir.txt").readlink(), Path("UDOSDIR.TXT"))

    def test_actc_fixture_uses_one_mutable_tree_for_case_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fs_root = Path(tmpdir)
            action_root = fs_root / "images" / "action.dnp"
            action_root.mkdir(parents=True)

            project_root = actc_probe.prepare_workspace(fs_root, "PROJ3")

            self.assertTrue((project_root / "src").is_dir())
            self.assertFalse((project_root / "src").is_symlink())
            self.assertEqual((project_root / "SRC").readlink(), Path("src"))
            self.assertEqual((project_root / "OBJ").readlink(), Path("obj"))
            self.assertEqual((project_root / "ACTION.PROJ").readlink(), Path("action.proj"))
            self.assertEqual((project_root / "src" / "MAIN.ACT").readlink(), Path("main.act"))
            self.assertEqual((project_root / "obj" / "udosdir.txt").readlink(), Path("UDOSDIR.TXT"))
            self.assertTrue(
                (project_root / "OBJ" / "UDOSDIR.TXT").samefile(
                    project_root / "obj" / "udosdir.txt"
                )
            )

            catalog_path = project_root / "obj" / "UDOSDIR.TXT"
            catalog_path.write_text("\nF MAIN.OBJ\n", encoding="ascii")
            with self.assertRaisesRegex(RuntimeError, "expected object catalog"):
                actc_probe.verify_output_catalog(project_root)
            catalog_path.write_text("F MAIN.OBJ\n", encoding="ascii")
            actc_probe.verify_output_catalog(project_root)


if __name__ == "__main__":
    unittest.main()
