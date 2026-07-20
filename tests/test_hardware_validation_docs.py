from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent


class HardwareValidationDocsTests(unittest.TestCase):
    def test_hardware_runbook_covers_uci_paths_without_claiming_validation(self) -> None:
        runbook = (ROOT / "HARDWARE_VALIDATION.md").read_text(encoding="utf-8")
        lowered = runbook.lower()
        normalized = " ".join(lowered.split())

        self.assertIn("no target hardware validation has been completed", lowered)
        self.assertIn("do not mark", lowered)
        self.assertIn("command_matrix.md", lowered)
        self.assertIn("vice does not provide the ultimate uci block", lowered)
        self.assertIn("repeated `read_data` into reu", normalized)
        self.assertIn("hardware tool abi mutation", lowered)

        for token in (
            "MOUNT_DISK",
            "CHANGE_DIR",
            "GET_PATH",
            "OPEN_DIR",
            "READ_DIR",
            "OPEN_FILE",
            "READ_DATA",
            "CLOSE_FILE",
            "FILE_SEEK",
            "WRITE_DATA",
            "CREATE_DIR",
            "DELETE_FILE",
            "RENAME_FILE",
            "COPY_FILE",
            "FILE_STAT",
        ):
            self.assertIn(token, runbook)

        for command in ("MOUNT", "VOL", "DIR", "CD", "TYPE", "COPY", "REN", "DEL", "MD", "RD"):
            self.assertIn(command, runbook)

        for image_type in ("D64", "D71", "D81", "DNP"):
            self.assertIn(image_type, runbook)

        for section in (
            "## Smoke Sequence",
            "## Tree Mutation Sequence",
            "## External Tool Load Sequence",
            "## External Tool Save Sequence",
            "## External Tool Stream Write Sequence",
            "## External Tool REU Stage Sequence",
            "## External Tool Rename Sequence",
            "## Directory Mutation Sequence",
            "## Wildcard Sequence",
            "## Program Launch Sequence",
            "## Command Overlay Sequence",
            "## Flat Image Sequence",
            "## Batch Sequence",
            "## Updating Project Status",
        ):
            self.assertIn(section, runbook)

        for command in ("TREE", "XCOPY", "DELTREE"):
            self.assertIn(command, runbook)
        self.assertIn("ACTMOVE", runbook)
        self.assertIn("ACTFILE", runbook)
        self.assertIn("ACTWRITE", runbook)
        self.assertIn("ACTSAVE", runbook)
        self.assertIn("ACTC", runbook)
        self.assertIn("svc_file_load_sc0", runbook)
        self.assertIn("svc_file_save_sc0", runbook)
        self.assertIn("svc_file_write_begin_sc0", runbook)
        self.assertIn("svc_file_write_chunk_sc0", runbook)
        self.assertIn("svc_file_write_close_sc0", runbook)
        self.assertIn("svc_file_stage_reu_sc0", runbook)

    def test_status_docs_point_to_hardware_runbook(self) -> None:
        for relative in ("BUILDING.md", "COMMAND_MATRIX.md", "TODO_UDOS.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("HARDWARE_VALIDATION.md", text)


if __name__ == "__main__":
    unittest.main()
