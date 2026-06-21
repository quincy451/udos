from __future__ import annotations

import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
