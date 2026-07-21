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
            self.assertTrue((action_root / "ACTSAVE.PRG").is_file())
            self.assertTrue((action_root / "ACTC.PRG").is_file())
            self.assertTrue((action_root / "ACTEDIT.PRG").is_file())
            self.assertEqual(
                (action_root / "ACTEDIT_OVL1.BIN").read_bytes()[:5], b"AEOV\x02"
            )
            self.assertTrue((action_root / "ACTDBG.PRG").is_file())
            self.assertEqual(
                (action_root / "ACTDBG_OVL1.BIN").read_bytes()[:4], b"DGOV"
            )
            self.assertEqual(
                (action_root / "ACTDBG_OVL2.BIN").read_bytes()[:4], b"DGOV"
            )
            tree_overlay = (action_root / "TREE.OVL").read_bytes()
            self.assertEqual(tree_overlay[:6], b"\x00\x09UDOV")
            self.assertEqual(tree_overlay[6:10], bytes((1, 6, 20, 0)))
            self.assertEqual(int.from_bytes(tree_overlay[10:12], "little"), 0x0900)
            self.assertEqual(int.from_bytes(tree_overlay[14:16], "little"), len(tree_overlay) - 2)
            xcopy_overlay = (action_root / "XCOPY.OVL").read_bytes()
            self.assertEqual(xcopy_overlay[:6], b"\x00\x09UDOV")
            self.assertEqual(xcopy_overlay[6:10], bytes((1, 6, 21, 0)))
            self.assertEqual(int.from_bytes(xcopy_overlay[10:12], "little"), 0x0900)
            self.assertGreaterEqual(int.from_bytes(xcopy_overlay[12:14], "little"), 0x090E)
            self.assertEqual(int.from_bytes(xcopy_overlay[14:16], "little"), len(xcopy_overlay) - 2)
            deltree_overlay = (action_root / "DELTREE.OVL").read_bytes()
            self.assertEqual(deltree_overlay[:6], b"\x00\x09UDOV")
            self.assertEqual(deltree_overlay[6:10], bytes((1, 6, 22, 0)))
            self.assertEqual(int.from_bytes(deltree_overlay[10:12], "little"), 0x0900)
            self.assertGreaterEqual(int.from_bytes(deltree_overlay[12:14], "little"), 0x090E)
            self.assertEqual(
                int.from_bytes(deltree_overlay[14:16], "little"),
                len(deltree_overlay) - 2,
            )
            for overlay_selector in "0123456789ABCDEFGHIJK":
                overlay = action_root / f"ACTC_OVL{overlay_selector}.BIN"
                self.assertTrue(overlay.is_file(), str(overlay))
                self.assertEqual(overlay.read_bytes()[:4], b"ACOV", str(overlay))
            self.assertTrue((action_root / "DOC" / "OPERATOR.TXT").is_file())
            self.assertTrue((action_root / "DOC" / "INPUT1.TXT").is_file())
            self.assertTrue((action_root / "DOC" / "DBF1.TXT").is_file())
            self.assertTrue((action_root / "DOC" / "DEBUGGER.TXT").is_file())
            self.assertTrue((action_root / "SRC" / "DBF1_DEMO.ACT").is_file())
            self.assertTrue((action_root / "SRC" / "GFX1_DEMO.ACT").is_file())
            self.assertTrue((action_root / "SRC" / "HELLO.ACT").is_file())
            self.assertTrue((action_root / "SRC" / "INPUT1_DEMO.ACT").is_file())
            self.assertTrue((action_root / "SRC" / "MATH1_DEMO.ACT").is_file())
            self.assertTrue((action_root / "SRC" / "SIDSPR1_DEMO.ACT").is_file())
            self.assertTrue((action_root / "LIB" / "LIBMODS.DAT").is_file())
            actionc64u_root = root.parent / "actionc64u"
            expected_runtime_objs = {
                path.name.upper()
                for source_dir in [
                    actionc64u_root / "src" / "runtime" / "modules",
                    actionc64u_root / "src" / "runtime" / "udos_modules",
                ]
                for path in source_dir.glob("*.obj")
            }
            exported_runtime_objs = {path.name.upper() for path in (action_root / "LIB").glob("RT_*.OBJ")}
            missing_runtime_objs = sorted(expected_runtime_objs - exported_runtime_objs)
            self.assertFalse(
                missing_runtime_objs,
                "Runtime OBJ modules missing from release ACTION.DNP/LIB: " + ", ".join(missing_runtime_objs),
            )
            self.assertTrue((action_root / "LIB" / "GFX1.ACT").is_file())
            self.assertTrue((action_root / "LIB" / "RT_GFX_SCREEN_CELL.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_GFX_COLOR_CELL.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_GFX_MBITMAP_OFF.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "INPUT1.ACT").is_file())
            self.assertTrue((action_root / "LIB" / "RT_JOY.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_JP.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_JS.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_MP.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_MSEEN.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_MX.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_MY.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_MB.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_MS.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "DBF1.ACT").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_CREATE.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_OPEN.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_STATE.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_CLOSE.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_GO.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_FIELDCOUNT.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_FIELDLEN.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_READBYTE.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_READFIELDBYTE.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_WRITEFIELDBYTE.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_WRITEBYTE.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_APPEND.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_PACK.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_SAVE.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_DELETE.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_UNDELETE.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_TOTALRECS.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_DBF_CURRRECNO.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "MATH1.ACT").is_file())
            self.assertTrue((action_root / "LIB" / "RT_F_ABS.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_F_SQRT.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_F_FRAC.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_F_SPECIAL.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "SIDSPR1.ACT").is_file())
            self.assertTrue((action_root / "LIB" / "RT_SID_FREQ.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_SID_STATE.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_SPRITE_ON.OBJ").is_file())
            self.assertTrue((action_root / "LIB" / "RT_SPRITE_PTR.OBJ").is_file())
            gfx1_contents = (action_root / "LIB" / "GFX1.ACT").read_text(encoding="ascii")
            self.assertIn("PROC ScreenCell(BYTE x,BYTE y,BYTE ch)", gfx1_contents)
            self.assertIn("PROC ColorCell(BYTE x,BYTE y,BYTE color)", gfx1_contents)
            self.assertIn("PROC MBitmapOff()", gfx1_contents)
            input1_contents = (action_root / "LIB" / "INPUT1.ACT").read_text(encoding="ascii")
            self.assertIn("BYTE FUNC Joy(BYTE port)", input1_contents)
            self.assertIn("BYTE FUNC JoySeen(BYTE port)", input1_contents)
            self.assertIn("BYTE FUNC MousePoll(BYTE port)", input1_contents)
            self.assertIn("BYTE FUNC MouseSeen()", input1_contents)
            self.assertIn("BYTE FUNC MouseX()", input1_contents)
            self.assertIn("BYTE FUNC MouseY()", input1_contents)
            self.assertIn("BYTE FUNC MouseBtn()", input1_contents)
            dbf1_contents = (action_root / "LIB" / "DBF1.ACT").read_text(encoding="ascii")
            self.assertIn("BYTE FUNC DbfCreate(CARD filename)", dbf1_contents)
            self.assertIn("BYTE FUNC DbfOpen(CARD filename)", dbf1_contents)
            self.assertIn("PROC DbfClose(BYTE handle)", dbf1_contents)
            self.assertIn("BYTE FUNC DbfGo(BYTE handle,BYTE recno)", dbf1_contents)
            self.assertIn("BYTE FUNC DbfFieldCount(BYTE handle)", dbf1_contents)
            self.assertIn("BYTE FUNC DbfFieldLen(BYTE handle,BYTE field)", dbf1_contents)
            self.assertIn("BYTE FUNC DbfReadByte(BYTE handle,BYTE offset)", dbf1_contents)
            self.assertIn(
                "BYTE FUNC DbfReadFieldByte(BYTE handle,BYTE field,BYTE offset)",
                dbf1_contents,
            )
            self.assertIn(
                "BYTE FUNC DbfWriteFieldByte(BYTE handle,BYTE field,BYTE offset,BYTE value)",
                dbf1_contents,
            )
            self.assertIn("BYTE FUNC DbfWriteByte(BYTE handle,BYTE offset,BYTE value)", dbf1_contents)
            self.assertIn("BYTE FUNC DbfAppend(BYTE handle)", dbf1_contents)
            self.assertIn("BYTE FUNC DbfSave(BYTE handle)", dbf1_contents)
            self.assertIn("BYTE FUNC DbfDelete(BYTE handle)", dbf1_contents)
            self.assertIn("BYTE FUNC DbfUndelete(BYTE handle)", dbf1_contents)
            self.assertIn("BYTE FUNC DbfTotalRecs(BYTE handle)", dbf1_contents)
            self.assertIn("BYTE FUNC DbfCurrRecNo(BYTE handle)", dbf1_contents)
            math1_contents = (action_root / "LIB" / "MATH1.ACT").read_text(encoding="ascii")
            self.assertIn("PROC PrintRE(REAL value)", math1_contents)
            self.assertIn("REAL FUNC FAbs(REAL value)", math1_contents)
            self.assertIn("REAL FUNC FSqrt(REAL value)", math1_contents)
            self.assertIn("REAL FUNC FTrunc(REAL value)", math1_contents)
            self.assertIn("REAL FUNC FFloor(REAL value)", math1_contents)
            self.assertIn("REAL FUNC FCeil(REAL value)", math1_contents)
            self.assertIn("REAL FUNC FRound(REAL value)", math1_contents)
            self.assertIn("REAL FUNC FFrac(REAL value)", math1_contents)
            self.assertIn("REAL FUNC FMod(REAL value,divisor)", math1_contents)
            self.assertIn("REAL CONST MATH_PI=3.14159265358979323846", math1_contents)
            self.assertIn("REAL CONST MATH_SQRT2=1.41421356237309504880", math1_contents)
            self.assertNotIn("MODULE MATH1", math1_contents)
            self.assertIn("REAL arithmetic/comparison operators", math1_contents)
            sidspr1_contents = (action_root / "LIB" / "SIDSPR1.ACT").read_text(encoding="ascii")
            self.assertIn("PROC SpriteData(BYTE n,CARD addr)", sidspr1_contents)
            self.assertIn("PROC SidFreq(BYTE v,CARD freq)", sidspr1_contents)
            input1_doc = (action_root / "DOC" / "INPUT1.TXT").read_text(encoding="ascii")
            self.assertIn("Joystick helpers:", input1_doc)
            self.assertIn("Mouse helpers:", input1_doc)
            dbf1_doc = (action_root / "DOC" / "DBF1.TXT").read_text(encoding="ascii")
            self.assertIn("DBF1 Database Library", dbf1_doc)
            self.assertIn("DbfCreate(filename) stages a new empty zero-field DBF image", dbf1_doc)
            self.assertIn("DbfOpen(filename) stages an existing DBF file", dbf1_doc)
            self.assertIn("DbfReadFieldByte(handle, field, offset)", dbf1_doc)
            self.assertIn("DbfWriteFieldByte(handle, field, offset, value)", dbf1_doc)
            self.assertIn("DbfWriteByte(handle, offset, value)", dbf1_doc)
            self.assertIn("DbfAppend(handle) appends one blank current record", dbf1_doc)
            self.assertIn("DbfPack(handle) removes deleted records", dbf1_doc)
            self.assertIn("DbfSave(handle) writes the staged DBF image", dbf1_doc)
            self.assertIn("DbfDelete(handle) sets the current record", dbf1_doc)
            self.assertIn("DbfUndelete(handle) clears the current record", dbf1_doc)
            self.assertIn("RT_DBF_CREATE.OBJ", dbf1_doc)
            self.assertIn("RT_DBF_OPEN.OBJ", dbf1_doc)
            self.assertIn("RT_DBF_READFIELDBYTE.OBJ", dbf1_doc)
            self.assertIn("RT_DBF_WRITEFIELDBYTE.OBJ", dbf1_doc)
            self.assertIn("RT_DBF_WRITEBYTE.OBJ", dbf1_doc)
            self.assertIn("RT_DBF_APPEND.OBJ", dbf1_doc)
            self.assertIn("RT_DBF_PACK.OBJ", dbf1_doc)
            self.assertIn("RT_DBF_SAVE.OBJ", dbf1_doc)
            self.assertIn("RT_DBF_DELETE.OBJ", dbf1_doc)
            self.assertIn("RT_DBF_UNDELETE.OBJ", dbf1_doc)
            old_binary_pattern = "*." + ("A" + "VM")
            self.assertFalse(list(action_root.rglob(old_binary_pattern)))
            self.assertFalse(list(action_root.rglob("*.AVT")))
            old_vm_prefix = "A" + "VM"
            old_runner = old_vm_prefix + "RUN"
            self.assertTrue((action_root / "ACTDBG.PRG").is_file())
            self.assertEqual((action_root / "ACTDBG_OVL1.BIN").read_bytes()[:4], b"DGOV")
            self.assertEqual((action_root / "ACTDBG_OVL2.BIN").read_bytes()[:4], b"DGOV")
            self.assertTrue((action_root / "ACTEDIT.PRG").is_file())
            self.assertEqual((action_root / "ACTEDIT_OVL1.BIN").read_bytes()[:5], b"AEOV\x02")
            for name in (
                old_vm_prefix + "INFO.PRG",
                old_runner + ".PRG",
                old_runner + "C.PRG",
            ):
                self.assertFalse((action_root / name).exists(), name)
            self.assertFalse(list(action_root.glob("RT_*_HELPER.BIN")))
            self.assertFalse(list(action_root.glob(old_runner + "_OVL*.BIN")))


if __name__ == "__main__":
    unittest.main()
