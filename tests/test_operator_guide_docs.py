from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OperatorGuideDocsTests(unittest.TestCase):
    def test_operator_guide_documents_current_command_surface(self) -> None:
        guide = (ROOT / "OPERATOR_GUIDE.md").read_text(encoding="utf-8")
        lowered = guide.lower()
        normalized = " ".join(lowered.split())

        self.assertIn("there is no separate runtime", lowered)
        self.assertIn("actc.prg -> obj/<module>.obj -> alink.prg -> bin/<module>.prg", lowered)
        self.assertIn("HARDWARE_VALIDATION.md", guide)
        self.assertIn("VICE does not provide the Ultimate UCI", guide)

        for command in (
            "HELP",
            "VER",
            "MEM",
            "VOL",
            "MOUNT",
            "DIR",
            "TREE",
            "XCOPY",
            "DELTREE",
            "CD",
            "MD",
            "RD",
            "TYPE",
            "COPY",
            "REN",
            "DEL",
        ):
            self.assertIn(f"### {command}", guide)

        for image_type in ("D64", "D71", "D81", "DNP"):
            self.assertIn(image_type, guide)

        for wildcard in ("COPY *.* /WORK", "COPY *.PRG /WORK", "DEL *.*", "DEL *.PRG"):
            self.assertIn(wildcard, guide)

        self.assertIn("one-level resident scaffold", normalized)
        self.assertIn("root child directories one level", normalized)
        self.assertIn("full recursive", normalized)
        self.assertIn("TREE.OVL", guide)
        self.assertIn("XCOPY.OVL", guide)
        self.assertIn("DELTREE.OVL", guide)
        self.assertIn("UDOV", guide)
        self.assertIn("validates", normalized)
        self.assertIn("XCOPY <source-dir> <destination-dir>".lower(), lowered)
        self.assertIn("48-mutation", normalized)
        self.assertIn("not transactional", normalized)

        self.assertIn("deltree <directory>", lowered)
        self.assertIn("post-order", normalized)
        self.assertIn("current directory", normalized)
        self.assertIn(
            "hardware/uci overlay staging is implemented but not hardware-validated",
            normalized,
        )

    def test_status_docs_point_to_operator_guide(self) -> None:
        for relative in ("README.md", "TODO_UDOS.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("OPERATOR_GUIDE.md", text)


if __name__ == "__main__":
    unittest.main()
