from __future__ import annotations

import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAS_VICE = shutil.which("x64sc") is not None
RESIDENT_CODE_START = 0x1810
PROGRAM_IMAGE_MAX = 240
REU_VICE_TREE_TOTAL = PROGRAM_IMAGE_MAX * 6 * 2
REU_LAUNCH_HIRAM_SIZE = 0x1000
TOOL_WRITEBACK_NAME_MAX = 32
TOOL_WRITEBACK_MAX_RECORDS = 48
TOOL_WRITEBACK_RECORD_SIZE = 5 + TOOL_WRITEBACK_NAME_MAX + 1 + 1 + TOOL_WRITEBACK_NAME_MAX
MAX_LINE_LEN = 31
TOOL_STREAM_SHADOW_SIZE = MAX_LINE_LEN + 1


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

    def test_proj3_vice_fixtures_register_the_directory_in_root_catalog(self) -> None:
        makefile = (ROOT / "Makefile").read_text()
        target_starts = list(
            re.finditer(r"^([A-Za-z0-9_.%-]+):(?:\s|$)", makefile, re.MULTILINE)
        )
        checked: list[str] = []
        for index, match in enumerate(target_starts):
            end = target_starts[index + 1].start() if index + 1 < len(target_starts) else len(makefile)
            block = makefile[match.start():end]
            if '--pre-command "CD PROJ3"' not in block:
                continue
            checked.append(match.group(1))
            self.assertIn("D PROJ3", block, match.group(1))
            self.assertIn("ACTION.DNP/UDOSDIR.TXT", block, match.group(1))
            self.assertNotIn("'D PROJ3\\n' >>", block, match.group(1))
        self.assertGreaterEqual(len(checked), 11)

    def test_release_requires_complete_actdbg_workspace_payload(self) -> None:
        makefile = (ROOT / "Makefile").read_text()
        release = makefile.split("release:", 1)[1].split("vice-release:", 1)[0]
        self.assertIn("ACTION.DNP/ACTDBG.PRG", release)
        self.assertIn("ACTION.DNP/ACTDBG_OVL1.BIN", release)
        self.assertIn("ACTION.DNP/ACTDBG_OVL2.BIN", release)
        self.assertIn("b'DGOV'", release)
        self.assertIn("ACTION.DNP/ACTEDIT_OVL1.BIN", release)
        self.assertIn("b'AEOV\\x02'", release)

    @unittest.skipUnless(HAS_VICE, "VICE not installed")
    def test_actedit_mutation_overlay_runs_in_vice(self) -> None:
        self.run_make("vice-action-actedit-overlay")

    def test_resident_builds(self) -> None:
        self.run_make("resident")
        self.assertTrue((ROOT / "build" / "udos-resident.prg").is_file())
        self.assertTrue((ROOT / "build" / "udos-resident.d64").is_file())

    def test_tool_callable_resident_code_stays_below_action_overlay(self) -> None:
        self.run_make("resident")
        labels = load_ld65_labels(ROOT / "build" / "udos-resident.labels")
        safe_end = labels["tool_abi_overlay_safe_end"]
        self.assertLessEqual(safe_end, 0xA000)
        self.assertLess(labels["vice_probe_name"], safe_end)
        self.assertGreaterEqual(labels["header_text"], safe_end)
        self.assertGreaterEqual(labels["error_response_table"], safe_end)
        self.assertGreaterEqual(labels["volume_system"], safe_end)
        self.assertGreaterEqual(labels["resp_dir_flat"], safe_end)
        self.assertGreaterEqual(
            labels["tool_stream_queue_writeback"],
            labels["tool_abi_swapped_low_additions_start"],
        )
        self.assertLess(
            labels["tool_stream_queue_writeback"],
            labels["tool_abi_preserved_start"],
        )
        self.assertGreaterEqual(
            labels["classify_vice_manifest_mutation"],
            safe_end,
        )

    def test_hardware_tree_launch_streams_command_overlays_to_reu(self) -> None:
        self.run_make("resident")
        labels = load_ld65_labels(ROOT / "build" / "udos-resident.labels")
        safe_end = labels["tool_abi_overlay_safe_end"]
        self.assertGreaterEqual(labels["prepare_external_program_launch_hw"], safe_end)
        self.assertGreaterEqual(labels["stage_launch_program_to_reu_hw_current"], safe_end)

        source = (ROOT / "src" / "asm" / "udos_resident.asm").read_text()
        for fragment in (
            "PROGRAM_LAUNCH_UCI_HOST = 3",
            "jsr stage_launch_program_to_reu_hw_current",
            "jsr uci_read_open_file_into_ptr_len",
            "jsr reu_transfer_chunk_loop_preserved",
            "jmp finish_staged_launch_program_from_reu",
        ):
            self.assertIn(fragment, source)

    def test_hardware_tree_tool_abi_mutations_use_uci_primitives(self) -> None:
        self.run_make("resident")
        labels = load_ld65_labels(ROOT / "build" / "udos-resident.labels")
        safe_end = labels["tool_abi_overlay_safe_end"]
        for label in (
            "open_file_read_hw_current",
            "query_program_file_hw",
            "uci_read_open_file_into_ptr_len",
            "open_dest_file_hw",
            "uci_write_open_file_from_ptr_len",
            "close_current_file_hw",
            "tool_abi_file_load_sc0",
            "tool_abi_file_save_sc0",
            "tool_abi_file_save_prepare_length",
            "tool_abi_file_write_hw_current",
            "tool_abi_file_write_begin_sc0_preserved",
            "tool_abi_file_write_chunk_sc0_preserved",
            "tool_abi_file_write_chunk_current_preserved",
            "tool_abi_file_write_close_sc0_preserved",
            "tool_abi_file_stage_reu_sc0_preserved",
            "tool_abi_file_stage_reu_hw_preserved",
            "tool_abi_begin_program_resolver_state",
            "tool_abi_restore_program_resolver_state",
            "create_dir_hw_current",
            "lookup_dir_target_current",
            "fill_tree_dir_cache_current",
            "remove_dir_current",
            "tool_abi_dir_begin_sc0",
            "tool_abi_dir_make_sc0",
            "tool_abi_dir_remove_sc0",
            "tool_abi_file_delete_sc0",
            "tool_abi_file_rename_sc0",
            "tool_abi_file_rename_restore_state",
            "tool_abi_file_copy_sc0",
        ):
            self.assertLess(labels[label], safe_end)

        source = (ROOT / "src" / "asm" / "udos_resident.asm").read_text()
        save_capture = source.split(
            "tool_abi_runtime_file_save_capture_args_template:", 1
        )[1].split("tool_abi_runtime_file_save_measure_template:", 1)[0]
        save_restore = source.split(
            "tool_abi_runtime_file_save_restore_args_template:", 1
        )[1].split("tool_abi_runtime_call_one_path_template:", 1)[0]
        hardware_load = source.split(
            "tool_abi_runtime_file_load_hw_template:", 1
        )[1].split("tool_abi_runtime_file_load_hw_template_end:", 1)[0]
        self.assertIn("lda $00,x", save_capture)
        self.assertIn("sta $00,x", save_restore)
        self.assertNotIn("stx PTR", save_capture)
        self.assertNotIn("stx PTR", save_restore)
        self.assertIn("lda $00,x", hardware_load)
        self.assertIn("sta $00,x", hardware_load)
        self.assertNotIn("stx PTR", hardware_load)

        swap_probe = (ROOT / "src" / "asm" / "udos_tool_swap_test.asm").read_text()
        self.assertIn("ALIAS_PARAMS = $F9", swap_probe)
        self.assertIn("ldx #ALIAS_PARAMS\n    jsr SVC_FILE_SAVE_SC0", swap_probe)
        self.assertIn("ldx #ALIAS_PARAMS\n    jsr SVC_FILE_COPY_SC0", swap_probe)
        self.assertIn("ldx #ALIAS_PARAMS\n    jsr SVC_FILE_RENAME_SC0", swap_probe)

        for fragment in (
            "DOS_CMD_CREATE_DIR = $16",
            "jsr build_uci_create_dir_command",
            "jsr fill_hw_dir_cache_current",
            "jsr create_dir_hw_current",
            "jsr remove_dir_current",
            "jsr delete_file_hw",
            "jsr copy_file_hw",
        ):
            self.assertIn(fragment, source)
        self.assertNotIn("tool_abi_resolve_copy_dest_shadow", source)

        rename_body = source.split("tool_abi_file_rename_sc0:", 1)[1].split(
            "tool_abi_file_copy_sc0:", 1
        )[0]
        for fragment in (
            "jsr transport_snapshot_is_uci",
            "jsr tool_abi_begin_program_resolver_state",
            "jsr tool_abi_restore_program_resolver_state",
            "jsr query_program_file_hw",
            "jsr rename_file_hw",
            "jsr copy_file_hw",
            "jsr delete_file_hw",
        ):
            self.assertIn(fragment, rename_body)
        self.assertNotIn("jsr uci_probe", rename_body)
        self.assertNotIn("tool_abi_file_rename_capture:", source)
        self.assertLess(
            rename_body.index("jsr resolve_copy_dest"),
            rename_body.index("jsr resolve_file_target"),
        )
        self.assertLess(
            rename_body.index("jsr copy_path_name_to_copy_dst_buffer"),
            rename_body.index("jsr query_file_response_vice_current"),
        )

        copy_body = source.split("tool_abi_file_copy_sc0:", 1)[1].split(
            "stash_tool_dir_writeback:", 1
        )[0]
        self.assertLess(
            copy_body.index("jsr resolve_copy_dest"),
            copy_body.index("jsr resolve_file_target"),
        )
        self.assertIn("lda #<TOOL_ABI_SWAP_PATH_B", copy_body)

        two_path_runtime = source.split(
            "tool_abi_runtime_call_two_paths_template:", 1
        )[1].split("tool_abi_runtime_file_write_begin_template:", 1)[0]
        before_source_capture = two_path_runtime.split(
            "jsr tool_abi_runtime_call_one_path", 1
        )[0]
        self.assertIn("jsr tool_abi_runtime_capture_path_b", before_source_capture)
        self.assertNotIn("sta 2,x", before_source_capture)

        exact_query = source.split("query_file_vice_host_exact_current:", 1)[1].split(
            "query_program_file_vice_host_current:", 1
        )[0]
        self.assertIn(
            "bcs query_file_vice_host_exact_current_restore_open", exact_query
        )
        self.assertNotIn("query_file_vice_host_exact_current_restore_fail", source)

        load_body = source.split("tool_abi_runtime_file_load_hw_template:", 1)[1].split(
            "tool_abi_runtime_file_load_hw_template_end:", 1
        )[0]
        for fragment in (
            "REU_TOOL_LOAD_BANK = $FD",
            "jsr tool_abi_file_stage_reu_capped_sc0_preserved",
            "lda TOOL_ABI_FILE_STATUS",
            "jsr tool_abi_reu_read_sc0_preserved",
            "sta TOOL_ABI_SWAP_INPUT_A",
        ):
            self.assertIn(fragment, source if fragment.startswith("REU_") else load_body)
        self.assertNotIn("jsr uci_probe", load_body)
        install_body = source.split("svc_install_tool_abi_runtime:", 1)[1].split(
            "svc_sync_tool_cmdline_shadow:", 1
        )[0]
        self.assertIn("jsr transport_snapshot_is_uci", install_body)
        self.assertIn("tool_abi_runtime_file_load_hw_template", install_body)
        self.assertIn("tool_abi_runtime_file_load_sc0", install_body)

        save_body = source.split("tool_abi_file_save_sc0:", 1)[1].split(
            "tool_abi_dir_make_sc0:", 1
        )[0]
        for fragment in (
            "jsr transport_snapshot_is_uci",
            "jsr tool_abi_begin_program_resolver_state",
            "jsr tool_abi_restore_program_resolver_state",
            "lda TOOL_ABI_FILE_LIMIT_LO",
            "lda TOOL_ABI_FILE_LIMIT_HI",
            "cpy #PROGRAM_IMAGE_MAX-1",
            "jsr open_dest_file_hw",
            "lda TOOL_ABI_FILE_DEST_LO\n    sta SCREEN_PTR",
            "lda TOOL_ABI_FILE_DEST_HI\n    sta SCREEN_PTR+1",
            "lda #MAX_RESPONSE_LEN",
            "sta TOOL_ABI_FILE_LEN_LO",
            "jsr uci_write_open_file_from_ptr_len",
            "adc TOOL_ABI_FILE_LEN_LO",
            "sbc TOOL_ABI_FILE_LEN_LO",
            "jsr close_current_file_hw",
        ):
            self.assertIn(fragment, save_body)
        self.assertIn(
            "tool_abi_file_save_fail_tree:\n    jmp tool_abi_file_save_fail_restore",
            save_body,
        )
        self.assertNotIn("jsr uci_probe", save_body)

        stream_body = source.split("tool_abi_file_write_begin_sc0_preserved:", 1)[1].split(
            "tool_abi_file_stage_reu_sc0_preserved:", 1
        )[0]
        for fragment in (
            "TOOL_ABI_STREAM_DRIVE = $CDCC",
            "TOOL_ABI_STREAM_OPEN = $CDCD",
            "jsr transport_snapshot_is_uci",
            "jsr tool_stream_shadow_clear",
            "jsr tool_abi_begin_program_resolver_state",
            "jsr tool_abi_restore_program_resolver_state",
            "cmp #ASCII_BANG",
            "lda LAUNCH_DRIVE_SNAPSHOT",
            "lda LAUNCH_DIR_SNAPSHOT",
            "jsr open_dest_file_hw",
            "sta TOOL_ABI_STREAM_DRIVE",
            "sta TOOL_ABI_STREAM_OPEN",
            "jmp tool_abi_runtime_file_write_chunk",
            "jmp tool_abi_runtime_file_write_close",
        ):
            self.assertIn(fragment, source if fragment.startswith("TOOL_ABI_") else stream_body)
        swapped_low = source.split("tool_abi_swapped_low_additions_start:", 1)[1].split(
            "tool_abi_swapped_low_additions_end:", 1
        )[0]
        self.assertIn("jsr close_current_file_hw", swapped_low)
        self.assertIn("tool_stream_queue_writeback:", swapped_low)
        queue_body = swapped_low.split("tool_stream_queue_writeback:", 1)[1]
        self.assertEqual(queue_body.count("jsr tool_stream_shadow_load_reu"), 2)
        write_path_body = source.split(
            "tool_abi_build_write_path_from_ptr_safe_preserved:", 1
        )[1].split("tool_abi_file_write_begin_sc0_preserved:", 1)[0]
        self.assertIn("lda #'@'", write_path_body)
        self.assertIn("lda #ASCII_COLON", write_path_body)
        self.assertNotIn("jsr uci_probe", stream_body)

        stage_body = source.split("tool_abi_file_stage_reu_sc0_preserved:", 1)[1].split(
            "vice_clear_status_preserved:", 1
        )[0]
        for fragment in (
            "jsr transport_snapshot_is_uci",
            "jsr tool_abi_begin_program_resolver_state",
            "jsr tool_abi_restore_program_resolver_state",
            "cmp #ASCII_BANG",
            "lda LAUNCH_DRIVE_SNAPSHOT",
            "lda LAUNCH_DIR_SNAPSHOT",
            "jsr query_program_file_hw",
            "TOOL_ABI_STAGE_CAP_MODE",
            "TOOL_FILE_STATUS_TOO_LARGE",
            "lda uci_data_buffer+3",
            "adc uci_data_buffer+2",
            "jsr open_file_read_hw_current",
            "jsr uci_read_open_file_into_ptr_len",
            "jsr reu_transfer_chunk_loop_preserved",
            "jsr close_current_file_hw",
            "cmp uci_data_buffer+2",
        ):
            self.assertIn(fragment, stage_body)
        vice_stage_body = stage_body.split(
            "tool_abi_file_stage_reu_vice_preserved:", 1
        )[1].split("tool_abi_file_stage_reu_hw_preserved:", 1)[0]
        self.assertLess(
            vice_stage_body.index("jsr tool_abi_open_program_read_path_preserved"),
            vice_stage_body.index("sta launch_reu_reu_lo"),
        )
        self.assertNotIn("jsr uci_probe", stage_body)

    def test_tool_backend_selection_survives_low_resident_clobber(self) -> None:
        self.run_make("resident")
        labels = load_ld65_labels(ROOT / "build" / "udos-resident.labels")
        self.assertGreaterEqual(
            labels["transport_snapshot_is_uci"],
            labels["tool_abi_preserved_start"],
        )
        self.assertLess(
            labels["transport_snapshot_is_uci"],
            labels["tool_abi_overlay_safe_end"],
        )

    def test_vice_manifest_enumeration_streams_the_complete_catalog(self) -> None:
        source = (ROOT / "src" / "asm" / "udos_resident.asm").read_text()
        body = source.split(
            "fill_vice_manifest_dir_cache_host_current:", 1
        )[1].split("finish_vice_manifest_stream_line:", 1)[0]

        for fragment in (
            "jsr CHRIN",
            "jsr READST",
            "and #$40",
            "jsr finish_vice_manifest_stream_line",
            "jsr vice_close_current_file",
        ):
            self.assertIn(fragment, body)
        self.assertNotIn("flat_sector_buffer", body)
        self.assertNotIn("vice_read_length", body)
        self.assertNotIn("parse_vice_manifest_buffer_entries", source)

    def test_vice_manifest_stream_reader_drops_blank_phantom_records(self) -> None:
        source = (ROOT / "src" / "asm" / "udos_resident.asm").read_text()
        body = source.split("read_vice_manifest_stream_line:", 1)[1].split(
            "vice_manifest_stream_line_matches_mutation:", 1
        )[0]

        for fragment in (
            "cpy #$01",
            "cmp #$0D",
            "cmp #$0A",
            "sty vice_read_length",
            "sta flat_dir_sector_buffer,y",
        ):
            self.assertIn(fragment, body)

    def test_vice_manifest_cache_prioritizes_late_directories(self) -> None:
        source = (ROOT / "src" / "asm" / "udos_resident.asm").read_text()
        store = source.split("store_vice_dir_entry_if_any:", 1)[1].split(
            "make_hw_dir_cache_room_for_dir:", 1
        )[0]
        admission = source.split("make_hw_dir_cache_room_for_dir:", 1)[1].split(
            "store_vice_dir_entry_name:", 1
        )[0]

        self.assertLess(
            store.index("jsr make_hw_dir_cache_room_for_dir"),
            store.index("jsr store_vice_dir_entry_name"),
        )
        for fragment in (
            "cmp #HW_DIR_CACHE_MAX",
            "lda vice_dir_flag",
            "beq make_hw_dir_cache_room_fail",
            "cmp #ASCII_SLASH",
            "jsr remove_hw_dir_cache_current_index",
        ):
            self.assertIn(fragment, admission)

    def test_vice_paths_and_transport_preserve_backend_contracts(self) -> None:
        source = (ROOT / "src" / "asm" / "udos_resident.asm").read_text()
        makefile = (ROOT / "Makefile").read_text()
        path_copy = source.split(
            "copy_screen_ptr_string_to_current_ptr_ascii:", 1
        )[1].split("get_dir_parent_for_a:", 1)[0]
        transport = source.split("svc_transport_get_mode:", 1)[1].split(
            "detect_transport_mode_a:", 1
        )[0]

        real_read = makefile.split("vice-real-read:", 1)[1].split(
            "vice-real-tree-write:", 1
        )[0]
        self.assertIn("--check-byte 0xCFF0=0x03", real_read)
        self.assertNotIn("--check-byte 0xCFF0=0x01", real_read)
        vice_probe = source.split("vice_probe_available:", 1)[1].split(
            "svc_drive_get_current:", 1
        )[0]
        dir_make = source.split("tool_abi_dir_make_sc0:", 1)[1].split(
            "tool_abi_dir_remove_sc0:", 1
        )[0]

        for fragment in (
            "jsr screen_code_to_ascii",
            "cmp #'a'",
            "cmp #'z'+1",
            "and #$DF",
        ):
            self.assertIn(fragment, path_copy)
        for fragment in (
            "txa\n    pha",
            "jsr detect_transport_mode_a",
            "pla\n    tax",
            "sta 0,x",
        ):
            self.assertIn(fragment, transport)
        self.assertIn("cmp #TRANSPORT_MODE_VICE_FS", vice_probe)
        self.assertIn("clc\n    rts", vice_probe)
        self.assertIn("lda tool_dir_status_from_path,y", dir_make)
        self.assertNotIn(
            "cmp #PATH_STATUS_OK\n    beq :+\n    jmp tool_abi_dir_make_fail",
            dir_make,
        )

    def test_tool_abi_runtime_swaps_overwritten_low_resident_code(self) -> None:
        self.run_make("resident")
        labels = load_ld65_labels(ROOT / "build" / "udos-resident.labels")
        runtime_source = labels["tool_abi_runtime_template"]
        runtime_size = labels["tool_abi_runtime_template_end"] - runtime_source
        self.assertGreaterEqual(runtime_source, labels["tool_abi_overlay_safe_end"])
        self.assertLessEqual(runtime_size, 0x40E)
        self.assertLessEqual(0xC8E7 + runtime_size, 0xCCF5)
        self.assertEqual(labels["tool_abi_preserved_start"], 0x9800)
        self.assertLessEqual(labels["tool_abi_overlay_safe_end"], 0xA000)

        def runtime_target(label: str) -> int:
            return 0xC8E7 + labels[label] - runtime_source

        resident = (ROOT / "build" / "udos-resident.prg").read_bytes()
        load_address = resident[0] | (resident[1] << 8)
        fixed_offset = 2 + labels["tool_abi_fixed_template"] - load_address

        def fixed_target(index: int) -> int:
            entry = resident[fixed_offset + (index * 3) : fixed_offset + ((index + 1) * 3)]
            self.assertEqual(entry[0], 0x4C)
            return entry[1] | (entry[2] << 8)

        expected_runtime_targets = {
            6: "tool_abi_runtime_file_load_sc0_template",
            7: "tool_abi_runtime_dir_begin_current_template",
            8: "tool_abi_runtime_dir_next_template",
            9: "tool_abi_runtime_file_save_sc0_template",
            10: "tool_abi_runtime_dir_make_sc0_template",
            11: "tool_abi_runtime_dir_remove_sc0_template",
            12: "tool_abi_runtime_file_delete_sc0_template",
            13: "tool_abi_runtime_file_rename_sc0_template",
            14: "tool_abi_runtime_file_copy_sc0_template",
            21: "tool_abi_runtime_dir_begin_sc0_template",
        }
        for index, label in expected_runtime_targets.items():
            self.assertEqual(fixed_target(index), runtime_target(label))
        self.assertEqual(
            fixed_target(22), labels["tool_abi_program_chain_sc0_preserved"]
        )

        source = (ROOT / "src" / "asm" / "udos_resident.asm").read_text()
        self.assertIn("REU_RESIDENT_PRIVATE_BANK = $FF", source)
        self.assertIn(
            "REU_RESIDENT_RESERVED_BYTES = REU_TOOL_STREAM_SHADOW_BASE + TOOL_STREAM_SHADOW_SIZE",
            source,
        )
        for fragment in (
            "TOOL_SVC_PROGRAM_CHAIN_SC0 = TOOL_ABI_BASE + 66",
            "PROGRAM_CHAIN_REQUEST_MASK = $80",
            "jsr tool_stream_shadow_capture_preserved",
            "jsr tool_stream_shadow_save_reu",
            "jsr tool_stream_shadow_load_reu",
            "svc svc_program_prepare_run\n    svc svc_program_finish_prepare",
        ):
            self.assertIn(fragment, source)
        self.assertNotIn("REU_TOOL_STREAM_CONTENT", source)
        self.assertNotIn("tool_stream_content_", source)
        for fragment in (
            "REU_TOOL_SWAP_BANK = $FE",
            "REU_TOOL_LOAD_BANK = $FD",
            "jsr svc_install_tool_abi_runtime",
            "tool_abi_runtime_file_load_hw_template",
            "jsr tool_abi_file_stage_reu_capped_sc0_preserved",
            "jsr tool_abi_reu_read_sc0_preserved",
            "lda #<(tool_abi_preserved_start-RESIDENT_CODE_START)",
            "jmp tool_abi_runtime_file_write_begin",
            "jmp tool_abi_runtime_file_write_chunk",
            "jmp tool_abi_runtime_file_write_close",
            "jmp tool_abi_runtime_file_stage_reu",
            "jsr tool_abi_runtime_save_tool_low",
            "jsr tool_abi_runtime_restore_resident_low",
            "jsr tool_abi_runtime_save_resident_low",
            "jsr tool_abi_runtime_restore_tool_low",
            "jsr tool_abi_runtime_console_putc",
            "jsr tool_abi_runtime_console_mod40",
        ):
            self.assertIn(fragment, source)
        preserved = source.split("tool_abi_preserved_start:", 1)[1].split(
            "tool_abi_overlay_safe_end:", 1
        )[0]
        self.assertNotIn("jsr tool_abi_console_putc\n", preserved)
        self.assertNotIn("jsr tool_abi_console_mod40\n", preserved)
        self.assertNotIn("jsr uci_probe", preserved)

        self.assertEqual(source.count("jsr uci_probe"), 1)
        self.assertIn("jsr transport_snapshot_is_uci", source)
        self.assertIn("lda TRANSPORT_SNAPSHOT", source)

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_resident_runs_in_vice(self) -> None:
        self.run_make("vice-resident")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_implicit_launch_runs_in_vice(self) -> None:
        self.run_make("vice-launch")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_tool_chain_launch_runs_in_vice(self) -> None:
        self.run_make("vice-chain")

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
    def test_tool_abi_low_resident_swap_runs_in_vice(self) -> None:
        self.run_make("vice-tool-abi-swap")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_real_tree_reads_run_in_vice(self) -> None:
        self.run_make("vice-real-read")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_tree_command_runs_in_vice(self) -> None:
        self.run_make("vice-tree")

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
    def test_action_direct_tool_workflow_runs_in_vice(self) -> None:
        self.run_make("vice-action-tool-workflow")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_compile_failure_returns_to_editor_in_vice(self) -> None:
        self.run_make("vice-action-tool-error-workflow")

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
    def test_action_tree_overlay_runs_in_vice(self) -> None:
        self.run_make("vice-action-tree-overlay")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_invalid_action_tree_overlay_falls_back_in_vice(self) -> None:
        self.run_make("vice-action-tree-overlay-invalid")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_xcopy_overlay_runs_in_vice(self) -> None:
        self.run_make("vice-action-xcopy-overlay")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_invalid_action_xcopy_overlay_is_rejected_in_vice(self) -> None:
        self.run_make("vice-action-xcopy-overlay-invalid")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_xcopy_overlay_rejects_flat_images_in_vice(self) -> None:
        self.run_make("vice-action-xcopy-overlay-flat")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_deltree_overlay_runs_in_vice(self) -> None:
        self.run_make("vice-action-deltree-overlay")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_deltree_overlay_rewrites_large_parent_manifest_in_vice(self) -> None:
        self.run_make("vice-action-deltree-overlay-large-manifest")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_invalid_action_deltree_overlay_is_rejected_in_vice(self) -> None:
        self.run_make("vice-action-deltree-overlay-invalid")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_deltree_overlay_rejects_flat_images_in_vice(self) -> None:
        self.run_make("vice-action-deltree-overlay-flat")

    @unittest.skipUnless(HAS_VICE, "x64sc not installed")
    def test_action_deltree_overlay_protects_current_directory_in_vice(self) -> None:
        self.run_make("vice-action-deltree-overlay-busy")

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
        reu_used = (
            REU_VICE_TREE_TOTAL
            + resident_size
            + REU_LAUNCH_HIRAM_SIZE
            + (TOOL_WRITEBACK_RECORD_SIZE * TOOL_WRITEBACK_MAX_RECORDS)
            + TOOL_STREAM_SHADOW_SIZE
        )
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
