from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FilesystemBehaviorDocsTests(unittest.TestCase):
    def test_filesystem_behavior_guide_documents_current_contract(self) -> None:
        guide = (ROOT / "FILESYSTEM_BEHAVIOR.md").read_text(encoding="utf-8")
        lowered = guide.lower()
        normalized = " ".join(guide.split())
        normalized_lower = normalized.lower()

        for doc in (
            "OPERATOR_GUIDE.md",
            "FS_ABSTRACTION.md",
            "COMMAND_MATRIX.md",
            "HARDWARE_VALIDATION.md",
            "BUILDING.md",
        ):
            self.assertIn(doc, guide)

        for image_type in ("D64", "D71", "D81"):
            self.assertIn(image_type, guide)
        self.assertIn("DNP", guide)
        self.assertIn("flat images have one root namespace", lowered)
        self.assertIn("tree-capable images", lowered)

        for command in ("DIR", "TREE", "XCOPY", "DELTREE", "CD", "MD", "RD", "TYPE", "COPY", "REN", "DEL"):
            self.assertIn(f"`{command}`", guide)

        for wildcard in (
            "COPY *.* /WORK",
            "COPY *.PRG /WORK",
            "COPY NAME.* /WORK",
            "DEL *.*",
            "DEL *.PRG",
            "DEL NAME.*",
        ):
            self.assertIn(wildcard, guide)

        for failure in (
            "NO SUCH FILE",
            "NO SUCH DIR",
            "DIR NOT EMPTY",
            "PROGRAM NOT FOUND",
            "DRIVE NOT PRESENT",
        ):
            self.assertIn(failure, guide)

        for backend in ("Mock", "Flat", "VICE tree", "Hardware/UCI"):
            self.assertIn(backend, guide)
        self.assertIn("VICE does not provide the Ultimate UCI", guide)
        self.assertIn("there is no separate runtime runner", normalized_lower)
        self.assertIn("one-level resident scaffold", normalized_lower)
        self.assertIn("root child directories one level", normalized_lower)
        self.assertIn("full recursive tree traversal", normalized_lower)
        self.assertIn("TREE.OVL", guide)
        self.assertIn("XCOPY.OVL", guide)
        self.assertIn("DELTREE.OVL", guide)
        self.assertIn("validates", normalized_lower)
        self.assertIn("XCOPY <source-dir> <destination-dir>", guide)
        self.assertIn("DELTREE <directory>", guide)
        self.assertIn("post-order", normalized_lower)
        self.assertIn("current directory", normalized_lower)
        self.assertIn("not transactional", normalized_lower)
        self.assertIn("one logical line at a time", normalized_lower)
        self.assertIn("not limited to a 255-byte total catalog size", normalized_lower)
        self.assertIn("UDOSDIR.TMP", guide)
        self.assertIn("missing catalog is created directly", normalized_lower)
        self.assertIn(
            "hardware/uci overlay staging is implemented but not hardware-validated",
            normalized_lower,
        )
        self.assertIn(
            "hardware tool abi mutations for nested directory creation",
            normalized_lower,
        )
        self.assertIn("implemented but not hardware-validated", normalized_lower)

    def test_status_docs_point_to_filesystem_behavior_guide(self) -> None:
        for relative in ("README.md", "TODO_UDOS.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("FILESYSTEM_BEHAVIOR.md", text)


if __name__ == "__main__":
    unittest.main()
