from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MilestoneHandoffDocsTests(unittest.TestCase):
    def test_handoff_matches_current_project_boundary(self) -> None:
        handoff = (ROOT / "MILESTONE_HANDOFF.md").read_text(encoding="utf-8")
        lowered = handoff.lower()
        normalized_lower = " ".join(lowered.split())

        self.assertIn("ACTC.PRG -> OBJ/<MODULE>.OBJ -> ALINK.PRG -> BIN/<MODULE>.PRG", handoff)
        self.assertIn("there is no separate runtime runner", normalized_lower)
        self.assertIn("owns all bytes", handoff)
        self.assertNotIn("a" + "vmrun", lowered)

        for doc in (
            "FILESYSTEM_BEHAVIOR.md",
            "OPERATOR_GUIDE.md",
            "COMMAND_MATRIX.md",
            "HARDWARE_VALIDATION.md",
        ):
            self.assertIn(doc, handoff)

        for image_type in ("D64", "D71", "D81", "DNP"):
            self.assertIn(image_type, handoff)

        self.assertIn("one-level resident scaffold", normalized_lower)
        self.assertIn("root child", normalized_lower)
        self.assertIn("full recursive", normalized_lower)
        self.assertIn("TREE.OVL", handoff)
        self.assertIn("XCOPY.OVL", handoff)
        self.assertIn("DELTREE.OVL", handoff)
        self.assertIn("UDOV", handoff)
        self.assertIn("validates", normalized_lower)

        for command in ("TREE", "XCOPY", "DELTREE"):
            self.assertIn(command, handoff)
        self.assertIn("bounded recursive", normalized_lower)
        self.assertIn("post-order", normalized_lower)
        self.assertIn("current directory", normalized_lower)
        self.assertIn(
            "hardware/uci overlay staging is implemented but not hardware-validated",
            normalized_lower,
        )
        self.assertIn(
            "hardware tool abi mutations for nested enumeration",
            normalized_lower,
        )
        self.assertIn("implemented but not hardware-validated", normalized_lower)

        self.assertIn("VICE does not provide the", handoff)
        self.assertIn("No real C64 Ultimate hardware validation has been completed", handoff)
        self.assertIn("Hardware/UCI", handoff)

        for gate in (
            "make test",
            "vice-action-actc",
            "vice-action-alink",
            "vice-action-actc-alink-launch",
            "vice-action-alink-prg-matrix",
            "vice-action-actc-alink-launch-object-emission-matrix",
            "vice-action-actc-alink-launch-runtime-matrices",
        ):
            self.assertIn(gate, handoff)

        self.assertIn("1377 shapes", handoff)
        self.assertIn("196 shapes", handoff)
        self.assertIn("311 complex compiled-runtime cases", handoff)
        self.assertIn("real_two_function_nested_postfix.act", handoff)
        self.assertIn("real_function_nested_local_call_postfix.act", handoff)
        self.assertIn("real_function_user_call_arguments_postfix.act", handoff)
        self.assertIn("real_function_if_else_postfix.act", handoff)
        self.assertIn("real_function_sequential_if_else_postfix.act", handoff)
        self.assertIn("real_function_nested_if_else_postfix.act", handoff)
        self.assertIn("real_function_four_sequential_if_postfix.act", handoff)
        self.assertIn("real_function_four_deep_if_postfix.act", handoff)
        self.assertIn("ACTC_OVLO.BIN", handoff)
        self.assertIn("real_function_early_return_if_postfix.act", handoff)
        self.assertIn("real_function_early_return_four_deep_postfix.act", handoff)
        self.assertIn("ACTC_OVLP.BIN", handoff)
        self.assertIn("real_function_loops_postfix.act", handoff)
        self.assertIn("ACTC_OVLQ.BIN", handoff)
        self.assertIn("real_function_loop_exit_postfix.act", handoff)
        self.assertIn("ACTC_OVLR.BIN", handoff)
        self.assertIn("7,342 bytes with 850 bytes free", handoff)
        self.assertIn("real_function_for_postfix.act", handoff)
        self.assertIn("ACTC_OVLS.BIN", handoff)
        self.assertIn("7,836 bytes with 356 bytes free", handoff)
        self.assertIn("real_function_dynamic_for_postfix.act", handoff)
        self.assertIn("ACTC_OVLT.BIN", handoff)
        self.assertIn("ACTC_OVLU.BIN", handoff)
        self.assertIn("math1_angle_conversions_postfix.act", handoff)
        self.assertIn("real_function_literal_clamp_comma_locals_postfix.act", handoff)
        self.assertIn("8,155 bytes with 37 bytes free", handoff)
        self.assertIn("RT_F_SIGN.OBJ", handoff)
        self.assertIn("RT_F_MIN.OBJ", handoff)
        self.assertIn("RT_F_MAX.OBJ", handoff)
        self.assertIn("RT_F_CLAMP.OBJ", handoff)
        self.assertIn("RT_F_TRUNC.OBJ", handoff)
        self.assertIn("RT_F_FLOOR.OBJ", handoff)
        self.assertIn("RT_F_CEIL.OBJ", handoff)
        self.assertIn("RT_F_ROUND.OBJ", handoff)
        self.assertIn("RT_F_FRAC.OBJ", handoff)
        self.assertIn("RT_F_MOD.OBJ", handoff)
        self.assertIn("RT_F_HYPOT.OBJ", handoff)
        self.assertIn("RT_F_POW.OBJ", handoff)
        self.assertIn("RT_F_EXP.OBJ", handoff)
        self.assertIn("RT_F_LN.OBJ", handoff)
        self.assertIn("RT_F_LOG2.OBJ", handoff)
        self.assertIn("RT_F_LOG10.OBJ", handoff)
        self.assertIn("RT_F_DEG_TO_RAD.OBJ", handoff)
        self.assertIn("RT_F_RAD_TO_DEG.OBJ", handoff)
        self.assertIn("8,069 bytes with 123 bytes free", handoff)
        self.assertIn("7,065 bytes with 1,127 bytes free", handoff)
        self.assertIn("6,137 bytes with 2,055 bytes free", handoff)
        self.assertIn("7,006 bytes with 1,186 bytes free", handoff)
        self.assertIn("7,128 bytes with 1,064 bytes free", handoff)
        self.assertIn("7,485 bytes with 707 bytes free", handoff)
        self.assertIn("remaining 15", handoff)
        self.assertIn("RT_F_SIN.OBJ", handoff)
        self.assertIn("RT_F_COS.OBJ", handoff)
        self.assertIn("RT_F_TAN.OBJ", handoff)
        self.assertIn("RT_F_ATAN.OBJ", handoff)
        self.assertIn("RT_F_ATAN2.OBJ", handoff)
        self.assertIn("RT_F_ASIN.OBJ", handoff)
        self.assertIn("RT_F_WRAP_PI.OBJ", handoff)
        self.assertIn("8,065-byte image leaves 639", handoff)
        self.assertIn("7,110-byte image leaves 1,594", handoff)
        self.assertIn("ACTC_OVLH.BIN", handoff)
        self.assertIn("8,535-byte image leaves 169", handoff)
        self.assertIn("ACTC_OVLJ.BIN", handoff)
        self.assertIn("ACTC_OVLK.BIN", handoff)
        self.assertIn("7,554-byte image leaves 1,150", handoff)
        self.assertIn("ASMBLOCK", handoff)
        self.assertIn("zero\nblocks free", handoff)
        self.assertIn("13,806 bytes", handoff)
        self.assertIn("102\nseeded runtime fixtures", handoff)
        self.assertNotIn("remaining fixed REAL WHILE", handoff)

    def test_status_docs_point_to_milestone_handoff(self) -> None:
        for relative in ("README.md", "TODO_UDOS.md", "HARDWARE_VALIDATION.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("MILESTONE_HANDOFF.md", text)


if __name__ == "__main__":
    unittest.main()
