BUILD_DIR := build
ASM_DIR := src/asm
PYTHON := python3
CA65 := ca65
LD65 := ld65
C1541 := c1541
VICE_FS_ROOT := tests/vicefs
VICE_LAUNCH_FS := build/vice-launch-fs
VICE_TREE_FS := build/vice-tree-fs
VICE_TREE_COPY_FS := build/vice-tree-copy-fs
VICE_TREE_WILD_FS := build/vice-tree-wild-fs
AUTOEXEC_SRC ?= $(ASM_DIR)/autoexec_default.txt
AUTOEXEC_INC := $(BUILD_DIR)/autoexec_script.inc
RESIDENT_DEFINES ?=
SELFTEST_ROOT := tests/selftest
SELFTEST_ATTEMPTS := 4
SELFTEST_READ_BUILD := build/selftest-read
SELFTEST_COPY_BUILD := build/selftest-copy
SELFTEST_RENAME_BUILD := build/selftest-rename
SELFTEST_DELETE_BUILD := build/selftest-delete
SELFTEST_DIR_BUILD := build/selftest-dir
SELFTEST_BATCH_BUILD := build/selftest-batch
SELFTEST_STOP_BUILD := build/selftest-stop
SELFTEST_LAUNCH_BUILD := build/selftest-launch
SELFTEST_READ_FS := build/selftest-read-fs
SELFTEST_COPY_FS := build/selftest-copy-fs
SELFTEST_RENAME_FS := build/selftest-rename-fs
SELFTEST_DELETE_FS := build/selftest-delete-fs
SELFTEST_DIR_FS := build/selftest-dir-fs
SELFTEST_BATCH_FS := build/selftest-batch-fs
SELFTEST_STOP_FS := build/selftest-stop-fs
SELFTEST_LAUNCH_FS := build/selftest-launch-fs
SELFTEST_READ_ARTIFACT := build/udos-selftest-read.d64
SELFTEST_COPY_ARTIFACT := build/udos-selftest-copy.d64
SELFTEST_RENAME_ARTIFACT := build/udos-selftest-rename.d64
SELFTEST_DELETE_ARTIFACT := build/udos-selftest-delete.d64
SELFTEST_DIR_ARTIFACT := build/udos-selftest-dir.d64
SELFTEST_BATCH_ARTIFACT := build/udos-selftest-batch.d64
SELFTEST_STOP_ARTIFACT := build/udos-selftest-stop.d64
SELFTEST_LAUNCH_ARTIFACT := build/udos-selftest-launch.d64
SELFTEST_READ_ACTUAL := build/udos-selftest-read.actual.txt
SELFTEST_COPY_ACTUAL := build/udos-selftest-copy.actual.txt
SELFTEST_RENAME_ACTUAL := build/udos-selftest-rename.actual.txt
SELFTEST_DELETE_ACTUAL := build/udos-selftest-delete.actual.txt
SELFTEST_DIR_ACTUAL := build/udos-selftest-dir.actual.txt
SELFTEST_BATCH_ACTUAL := build/udos-selftest-batch.actual.txt
SELFTEST_STOP_ACTUAL := build/udos-selftest-stop.actual.txt
SELFTEST_LAUNCH_ACTUAL := build/udos-selftest-launch.actual.txt
SELFTEST_READ_EXPECTED := $(SELFTEST_ROOT)/expected_read.txt
SELFTEST_COPY_EXPECTED := $(SELFTEST_ROOT)/expected_copy.txt
SELFTEST_RENAME_EXPECTED := $(SELFTEST_ROOT)/expected_rename.txt
SELFTEST_DELETE_EXPECTED := $(SELFTEST_ROOT)/expected_delete.txt
SELFTEST_DIR_EXPECTED := $(SELFTEST_ROOT)/expected_dir.txt
SELFTEST_BATCH_EXPECTED := $(SELFTEST_ROOT)/expected_batch.txt
SELFTEST_STOP_EXPECTED := $(SELFTEST_ROOT)/expected_stop.txt
SELFTEST_LAUNCH_EXPECTED := $(SELFTEST_ROOT)/expected_launch.txt
ACTIONTEST_ROOT := tests/action
ACTION_WORKSPACE_BUILD := build/action-workspace
ACTION_ACTDIR_BUILD := build/action-actdir
ACTION_ACTADD_BUILD := build/action-actadd
ACTION_ACTC_BUILD := build/action-actc
ACTION_ALINK_BUILD := build/action-alink
ACTION_ALINK_PRG_BUILD := build/action-alink-prg
ACTION_ACTC_ALINK_LAUNCH_BUILD := build/action-actc-alink-launch
ACTION_ACTFILE_BUILD := build/action-actfile
ACTION_ACTSRC_BUILD := build/action-actsrc
ACTION_ACTWORK_BUILD := build/action-actwork
ACTION_ACTNEW_BUILD := build/action-actnew
ACTION_ACTNEW_PRG_PERSIST_BUILD := build/actnew-prg-persist
ACTION_ACTINFO_BUILD := build/action-actinfo
ACTION_ACTWRITE_BUILD := build/action-actwrite
ACTION_WORKSPACE_FS := build/action-workspace-fs
ACTION_ACTSRC_FS := build/action-actsrc-fs
ACTION_ACTFILE_FS := build/action-actfile-fs
ACTION_ACTADD_FS := build/action-actadd-fs
ACTION_ACT2SAVE_FS := build/action-act2save-fs
ACTION_ACTC_FS := build/action-actc-fs
ACTION_ALINK_FS := build/action-alink-fs
ACTION_ALINK_PRG_FS := build/action-alink-prg-fs
ACTION_ACTC_ALINK_LAUNCH_FS := build/action-actc-alink-launch-fs
ACTION_ACTC_ALINK_LAUNCH_SHAPE ?= if_else_local_call_chain_nested_do_if_else
ACTION_ACTC_ALINK_PROBE_TIMEOUT ?= 720s
ACTION_ACTC_ALINK_PROBE_ATTEMPTS ?= 5
ACTION_ACTC_ALINK_INPUT_PROBE_ATTEMPTS ?= 5
ACTION_ALINK_PRG_OBJECT_CODE_PROBE_ATTEMPTS ?= 5
ACTION_ALINK_PRG_OBJECT_CODE_PROBE_TIMEOUT ?= 300s
ACTION_ALINK_PRG_OBJECT_CODE_SHELL_TIMEOUT ?= 180
ACTION_ACTC_ALINK_OBJECT_EMISSION_SHAPES := \
	single_call \
	fanout \
	local_chain_mixed_call \
	local_external_chain_mixed_call \
	local_external_helper_only_call \
	local_external_deep_helper_only_call \
	local_external_helper_mixed_repeat_call \
	local_external_project_library_helper_closure \
	local_external_project_imports_actc_secondary_export \
	local_external_project_imports_actc_secondary_export_local_chain \
	local_external_library_imports_actc_secondary_export \
	local_external_library_imports_actc_secondary_export_local_chain \
	local_external_direct_and_library_imports_actc_tail \
	local_external_library_project_imports_actc_secondary_export \
	local_external_library_project_imports_actc_secondary_export_local_chain \
	local_external_mixed_shared_library_dependency_dedup \
	local_external_dual_secondary_exports_shared_library_dedup \
	local_external_dual_secondary_exports_shared_project_dedup \
	local_external_dual_secondary_exports_shared_actc_local_dedup \
	local_external_project_library_transitive_shared_tail \
	local_external_project_library_transitive_project_tail \
	local_external_project_library_transitive_tail_imports_actc_local_chain \
	external_project_library_project_library_chain \
	external_call \
	local_external_call \
	local_external_pair_call \
	local_external_call_twice \
	local_external_mixed_repeat_call \
	external_pair_call \
	external_triple_call \
	external_lettered_import_call \
	external_dependency_windowed_lettered_import_call \
	local_external_project_dependency_windowed_lettered_import_call \
	local_external_project_dependency_windowed_lettered_mixed_helper_call \
	external_mixed_repeat_call \
	external_call_twice
ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES := \
	object_code_external_pair \
	object_code_external_triple_root_imports \
	object_code_external_offset_transitive_call \
	object_code_transitive_call \
	object_code_project_transitive_call \
	object_code_project_offset_library_dependency \
	object_code_project_precedes_library \
	object_code_project_second_export_import \
	object_code_project_second_export_named_symbol_import \
	object_code_project_second_export_imports_project_dependency \
	object_code_project_second_export_lettered_import_project_helper \
	object_code_project_second_export_lettered_import_library_helper \
	object_code_project_second_export_lowercase_z_import_library_helper \
	object_code_project_second_export_lowercase_z_import_project_helper \
	object_code_project_second_export_dependency_dual_lettered_import_mixed_helpers \
	object_code_project_second_export_transitive_project_dependency \
	object_code_project_second_export_project_dependency_imports_library_tail \
	object_code_project_second_export_transitive_library_dependency \
	object_code_mixed_second_export_transitive_project_dependency \
	object_code_mixed_project_library_closure \
	object_code_mixed_dual_transitive_project_library_closure \
	object_code_library_imports_project_dependency \
	object_code_library_second_export_imports_project_dependency \
	object_code_library_second_export_named_symbol_import \
	object_code_library_second_export_dependency_dual_lettered_import_mixed_helpers \
	object_code_library_second_export_lettered_import_project_helper \
	object_code_library_second_export_lettered_import_library_helper \
	object_code_library_second_export_lowercase_z_import_project_helper \
	object_code_library_second_export_lowercase_z_import_library_helper \
	object_code_library_second_export_imports_library_dependency \
	object_code_library_second_export_transitive_library_dependency \
	object_code_library_second_export_transitive_project_dependency \
	object_code_library_second_export_project_dependency_imports_library_tail \
	object_code_mixed_second_export_shared_library_dependency_dedup \
	object_code_mixed_second_export_shared_project_dependency_dedup \
	object_code_library_offset_project_dependency \
	object_code_library_imports_root_local_export \
	object_code_library_imports_offset_root_local_export \
	object_code_library_second_export_imports_root_local_export \
	object_code_library_second_export_dependency_imports_root_local_export \
	object_code_library_second_export_dependency_imports_offset_root_local_export \
	object_code_project_imports_offset_root_local_export \
	object_code_transitive_imports_offset_root_local_export \
	object_code_mixed_transitive_imports_offset_root_local_export \
	object_code_library_project_transitive_imports_offset_root_local_export \
	object_code_project_transitive_imports_offset_root_local_export \
	object_code_library_dual_import_project_library_dependencies \
	object_code_project_dual_import_project_library_dependencies \
	object_code_root_library_share_project_dependency_dedup \
	object_code_root_library_share_library_dependency_dedup \
	object_code_root_project_share_project_dependency_dedup \
	object_code_root_project_share_library_dependency_dedup \
	object_code_project_library_project_library_chain \
	object_code_mixed_shared_dependency_dedup \
	object_code_root_project_library_share_library_dependency_dedup \
	object_code_root_project_library_share_project_dependency_dedup \
	object_code_mixed_shared_library_dependency_dedup \
	object_code_external_lettered_import_pruned \
	object_code_project_lettered_import_pruned \
	object_code_lettered_import_call \
	object_code_project_lettered_import_call \
	object_code_project_dependency_lettered_import_project_helper \
	object_code_library_dependency_lettered_import_project_helper \
	object_code_library_dependency_lettered_import_library_helper \
	object_code_lowercase_z_import_call \
	object_code_project_lowercase_z_import_call \
	object_code_dependency_lowercase_z_import_pruned \
	object_code_project_dependency_lowercase_z_import_pruned \
	object_code_project_dependency_lowercase_z_import_project_helper \
	object_code_library_dependency_lowercase_z_import_project_helper \
	object_code_dependency_reloc_scan_windowed_imports \
	object_code_external_cycle \
	object_code_external_back_edge_cycle \
	object_code_mixed_project_library_back_edge_cycle \
	object_code_mixed_project_offset_back_edge_cycle \
	object_code_external_triangle \
	object_code_external_diamond \
	object_code_external_square
ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES := \
	object_code_return \
	object_code_split_machine_records \
	object_code_split_dependency_machine_records \
	object_code_named_symbol_relocations \
	object_code_named_symbol_relocation_import_closure \
	object_code_named_symbol_dependency_import_closure \
	object_code_named_symbol_dependency_local_export \
	object_code_local_call \
	object_code_external_call \
	object_code_offset_external_call \
	object_code_root_unused_import_ignored \
	object_code_root_unused_export_import_ignored \
	object_code_root_second_export_selected \
	object_code_root_second_export_import \
	object_code_root_second_export_named_symbol_import \
	object_code_root_second_export_imports_root_local_export \
	object_code_root_second_export_imports_offset_root_local_export \
	object_code_root_second_export_offset_local_and_library_project_tail \
	object_code_large_root_page_crossing \
	object_code_large_root_multi_reloc_page_crossing \
	object_code_reloc_scan_windowed_imports \
	object_code_large_dependency_page_crossing \
	object_code_project_large_dependency_page_crossing \
	object_code_project_large_dependency_library_tail_page_crossing \
	object_code_external_unused_import_ignored \
	object_code_external_second_export \
	object_code_external_second_export_import \
	object_code_root_second_export_transitive_library_dependency \
	object_code_root_second_export_transitive_project_dependency \
	object_code_root_second_export_project_second_export_library_tail \
	object_code_root_second_export_library_second_export_project_second_export_tail \
	object_code_root_second_export_mixed_project_library_dependency \
	object_code_root_second_export_mixed_library_project_dependency \
	object_code_root_second_export_dual_import_project_library_dependencies \
	object_code_root_second_export_dual_import_library_project_dependencies \
	object_code_root_second_export_dual_import_shared_library_dependency_dedup \
	object_code_root_second_export_dual_import_shared_project_dependency_dedup \
	object_code_root_second_export_root_project_share_project_dependency_dedup \
	object_code_root_second_export_root_library_share_project_dependency_dedup \
	object_code_root_second_export_root_project_share_library_dependency_dedup \
	object_code_root_second_export_root_library_share_library_dependency_dedup \
	object_code_root_second_export_root_project_library_share_library_dependency_dedup \
	object_code_root_second_export_root_project_library_share_project_dependency_dedup \
	object_code_root_second_export_dependency_dual_lettered_import_mixed_helpers \
	object_code_root_second_export_dependency_lowercase_z_import_project_helper \
	object_code_root_second_export_dependency_lowercase_z_import_library_helper \
	object_code_root_second_export_library_dependency_lowercase_z_import_project_helper \
	object_code_root_second_export_library_dependency_lowercase_z_import_library_helper \
	object_code_root_second_export_dependency_imports_root_local_export \
	object_code_root_second_export_dependency_imports_offset_root_local_export \
	object_code_external_call_twice \
	object_code_external_print_line \
	object_code_external_store_call \
	object_code_external_load_store_call \
	object_code_external_string_int_call \
	object_code_transitive_external_print_line \
	object_code_transitive_external_store_call \
	object_code_transitive_external_load_store_call \
	object_code_transitive_external_string_int_call
ACTION_ALINK_PRG_OBJECT_CODE_REJECTION_CASES := \
	object_code_unresolved_import_rejects \
	object_code_duplicate_export_rejects \
	object_code_missing_machine_record_rejects \
	object_code_zero_size_export_rejects \
	object_code_export_offset_past_machine_rejects \
	object_code_export_size_overruns_machine_rejects \
	object_code_reloc_unknown_import_index_rejects \
	object_code_dependency_unknown_lowercase_import_index_rejects \
	object_code_project_unknown_lowercase_import_index_blocks_library_fallback \
	object_code_project_second_export_named_symbol_local_export \
	object_code_reloc_malformed_offset_rejects \
	object_code_library_missing_machine_record_rejects \
	object_code_library_duplicate_export_rejects \
	object_code_library_zero_size_export_rejects \
	object_code_library_export_offset_past_machine_rejects \
	object_code_library_export_size_overruns_machine_rejects \
	object_code_library_reloc_malformed_offset_rejects \
	object_code_library_wrong_export_rejects \
	object_code_project_bad_dependency_blocks_library_fallback \
	object_code_project_zero_size_export_blocks_library_fallback \
	object_code_project_export_offset_past_machine_blocks_library_fallback \
	object_code_project_export_size_overruns_machine_blocks_library_fallback \
	object_code_project_duplicate_export_blocks_library_fallback \
	object_code_project_reloc_malformed_offset_blocks_library_fallback \
	object_code_project_wrong_export_blocks_library_fallback
ACTION_ACTC_ALINK_RUNTIME_SHAPES := \
	actc_runtime_cell_helpers_linked \
	actc_runtime_helper_free_unused_helper_libraries_pruned \
	actc_runtime_selective_hardware_helpers_linked \
	actc_runtime_reordered_hardware_helpers_linked \
	actc_runtime_mixed_hardware_helpers_linked \
	actc_runtime_variable_mixed_gfx_sprite_helpers_linked \
	actc_runtime_no_arg_hardware_helpers_linked \
	actc_runtime_stateful_byte_hardware_helpers_linked \
	actc_runtime_word_copy_fill_helpers_linked \
	actc_runtime_sid_osc3_readback_store_linked \
	actc_runtime_sid_osc3_byte_readback_store_linked \
	actc_runtime_sid_env3_readback_store_linked \
	actc_runtime_multi_readback_store_linked \
	actc_runtime_readback_store_copy_linked \
	actc_runtime_byte_readback_store_copy_linked \
	actc_runtime_sprite_hit_readback_store_linked \
	actc_runtime_sprite_hit_bg_readback_store_linked \
	actc_runtime_remaining_hardware_helpers_linked
ACTION_ACTC_ALINK_CARD_VARIABLE_RUNTIME_SHAPES := \
	actc_runtime_card_variable_gfx_screen_base_helper_linked \
	actc_runtime_card_variable_gfx_bitmap_base_helper_linked \
	actc_runtime_card_variable_gfx_screen_copy_helper_linked \
	actc_runtime_card_variable_gfx_color_copy_helper_linked \
	actc_runtime_card_variable_gfx_bitmap_copy_helper_linked \
	actc_runtime_card_variable_sprite_pos_helper_linked \
	actc_runtime_card_variable_sprite_data_helper_linked
ACTION_ACTC_ALINK_MATH_RUNTIME_SHAPES := \
	actc_runtime_math1_export_sample_linked \
	actc_runtime_math1_fabs_split_linked \
	actc_runtime_math1_fsqrt_split_linked \
	actc_runtime_math1_printre_split_linked \
	actc_runtime_math1_printr_split_linked \
	actc_runtime_math1_real_int_split_linked \
	actc_runtime_math1_real_to_int_split_linked \
	actc_runtime_math1_real_add_split_linked \
	actc_runtime_math1_real_sub_split_linked \
	actc_runtime_math1_real_mul_split_linked \
	actc_runtime_math1_real_div_split_linked \
	actc_runtime_math1_real_cmp_split_linked \
	real_printre_fabs \
	real_printre_fsqrt
ACTION_ACTC_ALINK_GFX_RUNTIME_SHAPES := \
	actc_runtime_gfx1_export_sample_linked \
	actc_runtime_gfx1_bgcolor_split_linked \
	actc_runtime_gfx1_bordercolor_split_linked \
	actc_runtime_gfx1_vic_bank_split_linked \
	actc_runtime_gfx1_screen_base_split_linked \
	actc_runtime_gfx1_bitmap_base_split_linked \
	actc_runtime_gfx1_screen_cell_split_linked \
	actc_runtime_gfx1_color_cell_split_linked \
	actc_runtime_gfx1_screen_copy_split_linked \
	actc_runtime_gfx1_color_copy_split_linked \
	actc_runtime_gfx1_bitmap_fill_split_linked \
	actc_runtime_gfx1_bitmap_copy_split_linked \
	actc_runtime_gfx1_bitmap_on_split_linked \
	actc_runtime_gfx1_bitmap_off_split_linked \
	actc_runtime_gfx1_mbitmap_on_split_linked \
	actc_runtime_gfx1_mbitmap_off_split_linked \
	actc_runtime_gfx_bgcolor_helper_linked \
	actc_runtime_gfx_bordercolor_helper_linked \
	actc_runtime_gfx_vic_bank_helper_linked \
	actc_runtime_gfx_screen_base_helper_linked \
	actc_runtime_gfx_bitmap_base_helper_linked \
	actc_runtime_gfx_screen_cell_helper_linked \
	actc_runtime_gfx_color_cell_helper_linked \
	actc_runtime_gfx_screen_copy_helper_linked \
	actc_runtime_gfx_color_copy_helper_linked \
	actc_runtime_gfx_bitmap_fill_helper_linked \
	actc_runtime_gfx_bitmap_copy_helper_linked \
	actc_runtime_gfx_bitmap_on_helper_linked \
	actc_runtime_gfx_bitmap_off_helper_linked \
	actc_runtime_gfx_mbitmap_on_helper_linked \
	actc_runtime_gfx_mbitmap_off_helper_linked
ACTION_ACTC_ALINK_VARIABLE_GFX_RUNTIME_SHAPES := \
	actc_runtime_variable_gfx_bgcolor_helper_linked \
	actc_runtime_variable_gfx_bordercolor_helper_linked \
	actc_runtime_variable_gfx_reassigned_color_helpers_linked \
	actc_runtime_variable_gfx_vic_bank_helper_linked \
	actc_runtime_variable_gfx_screen_cell_helper_linked \
	actc_runtime_variable_gfx_color_cell_helper_linked \
	actc_runtime_variable_gfx_bitmap_fill_helper_linked
ACTION_ACTC_ALINK_SID_RUNTIME_SHAPES := \
	actc_runtime_sidspr1_sid_vol_split_linked \
	actc_runtime_sidspr1_sid_freq_split_linked \
	actc_runtime_sidspr1_sid_pulse_split_linked \
	actc_runtime_sidspr1_sid_ad_split_linked \
	actc_runtime_sidspr1_sid_sr_split_linked \
	actc_runtime_sidspr1_sid_route_split_linked \
	actc_runtime_sidspr1_sid_res_split_linked \
	actc_runtime_sidspr1_sid_cutoff_split_linked \
	actc_runtime_sidspr1_sid_mode_split_linked \
	actc_runtime_sidspr1_sid_wave_split_linked \
	actc_runtime_sidspr1_sid_on_split_linked \
	actc_runtime_sidspr1_sid_off_split_linked \
	actc_runtime_sidspr1_sid_rst_split_linked \
	actc_runtime_sidspr1_sid_osc3_split_linked \
	actc_runtime_sidspr1_sid_env3_split_linked \
	actc_runtime_sid_vol_helper_linked \
	actc_runtime_sid_mode_helper_linked \
	actc_runtime_sid_freq_helper_linked \
	actc_runtime_sid_pulse_helper_linked \
	actc_runtime_sid_wave_helper_linked \
	actc_runtime_sid_ad_helper_linked \
	actc_runtime_sid_sr_helper_linked \
	actc_runtime_sid_on_helper_linked \
	actc_runtime_sid_off_helper_linked \
	actc_runtime_sid_rst_helper_linked \
	actc_runtime_sid_route_helper_linked \
	actc_runtime_sid_res_helper_linked \
	actc_runtime_sid_cutoff_helper_linked \
	actc_runtime_sid_osc3_helper_linked \
	actc_runtime_sid_env3_helper_linked
ACTION_ACTC_ALINK_VARIABLE_SID_RUNTIME_SHAPES := \
	actc_runtime_variable_sid_vol_helper_linked \
	actc_runtime_variable_sid_reassigned_level_helpers_linked \
	actc_runtime_variable_sid_mode_helper_linked \
	actc_runtime_variable_sid_freq_helper_linked \
	actc_runtime_variable_sid_pulse_helper_linked \
	actc_runtime_variable_sid_wave_helper_linked \
	actc_runtime_variable_sid_ad_helper_linked \
	actc_runtime_variable_sid_sr_helper_linked \
	actc_runtime_variable_sid_on_helper_linked \
	actc_runtime_variable_sid_off_helper_linked \
	actc_runtime_variable_sid_route_helper_linked \
	actc_runtime_variable_sid_res_helper_linked \
	actc_runtime_variable_sid_cutoff_helper_linked
ACTION_ACTC_ALINK_SPRITE_RUNTIME_SHAPES := \
	actc_runtime_sidspr1_sprite_color_split_linked \
	actc_runtime_sidspr1_sprite_data_split_linked \
	actc_runtime_sidspr1_sprite_ptr_split_linked \
	actc_runtime_sidspr1_sprite_pos_split_linked \
	actc_runtime_sidspr1_sprite_on_split_linked \
	actc_runtime_sidspr1_sprite_off_split_linked \
	actc_runtime_sidspr1_sprite_hit_split_linked \
	actc_runtime_sidspr1_sprite_hit_bg_split_linked \
	actc_runtime_sidspr1_sprite_mc_split_linked \
	actc_runtime_sidspr1_sprite_xexp_split_linked \
	actc_runtime_sidspr1_sprite_yexp_split_linked \
	actc_runtime_sidspr1_sprite_prio_split_linked \
	actc_runtime_sidspr1_sprite_set_mc_split_linked \
	actc_runtime_sprite_color_helper_linked \
	actc_runtime_sprite_data_helper_linked \
	actc_runtime_sprite_ptr_helper_linked \
	actc_runtime_sprite_pos_helper_linked \
	actc_runtime_sprite_pos_low_x_helper_linked \
	actc_runtime_sprite_on_helper_linked \
	actc_runtime_sprite_off_helper_linked \
	actc_runtime_sprite_hit_helper_linked \
	actc_runtime_sprite_hit_bg_helper_linked \
	actc_runtime_sprite_mc_helper_linked \
	actc_runtime_sprite_mc_clear_helper_linked \
	actc_runtime_sprite_xexp_helper_linked \
	actc_runtime_sprite_xexp_clear_helper_linked \
	actc_runtime_sprite_yexp_helper_linked \
	actc_runtime_sprite_yexp_clear_helper_linked \
	actc_runtime_sprite_prio_helper_linked \
	actc_runtime_sprite_prio_clear_helper_linked \
	actc_runtime_sprite_set_mc_helper_linked
ACTION_ACTC_ALINK_VARIABLE_SPRITE_RUNTIME_SHAPES := \
	actc_runtime_variable_sprite_color_helper_linked \
	actc_runtime_variable_sprite_reassigned_color_helpers_linked \
	actc_runtime_variable_sprite_ptr_helper_linked \
	actc_runtime_variable_sprite_on_helper_linked \
	actc_runtime_variable_sprite_off_helper_linked \
	actc_runtime_variable_sprite_mc_helper_linked \
	actc_runtime_variable_sprite_mc_clear_helper_linked \
	actc_runtime_variable_sprite_xexp_helper_linked \
	actc_runtime_variable_sprite_xexp_clear_helper_linked \
	actc_runtime_variable_sprite_yexp_helper_linked \
	actc_runtime_variable_sprite_yexp_clear_helper_linked \
	actc_runtime_variable_sprite_prio_helper_linked \
	actc_runtime_variable_sprite_prio_clear_helper_linked \
	actc_runtime_variable_sprite_set_mc_helper_linked
ACTION_ACTC_ALINK_INPUT_RUNTIME_SHAPES := \
	actc_runtime_input_joystick_helpers_linked \
	actc_runtime_input_joystick_condition_gfx_helper_linked \
	actc_runtime_input_joystick_not_equal_condition_gfx_helper_linked \
	actc_runtime_input_joystick_state_store_linked \
	actc_runtime_input_joystick_two_button_mask_linked \
	actc_runtime_input_joystick_button_state_helpers_linked \
	actc_runtime_input_mouse_helpers_linked \
	actc_runtime_input_mouse_state_store_linked \
	actc_runtime_input_mouse_two_button_mask_linked \
	actc_runtime_input_mouse_button_state_helpers_linked \
	actc_runtime_input_mouse_button_condition_gfx_helper_linked \
	actc_runtime_input_mouse_button_not_equal_condition_gfx_helper_linked \
	actc_runtime_input_joystick_button_condition_gfx_helper_linked \
	actc_runtime_input_mouse_button2_condition_gfx_helper_linked \
	actc_runtime_input_variable_port_store_linked \
	actc_runtime_input_dual_port_presence_store_linked \
	actc_runtime_input_gfx_mixed_helpers_linked \
	actc_runtime_input_mouse_result_gfx_arg_linked \
	actc_runtime_input_mouse_result_sid_arg_linked \
	actc_runtime_input_mouse_result_sprite_second_arg_linked \
	actc_runtime_input_mouse_x_result_sprite_pos_second_arg_linked \
	actc_runtime_input_mouse_y_result_sprite_pos_third_arg_linked \
	actc_runtime_input_mouse_button_result_sid_arg_linked \
	actc_runtime_input_joystick_result_sid_arg_linked \
	actc_runtime_input_joystick_result_sid_word_arg_linked \
	actc_runtime_input_joystick_result_sid_first_arg_linked \
	actc_runtime_input_joystick_result_sid_freq_second_arg_linked \
	actc_runtime_input_joystick_result_sid_pulse_second_arg_linked \
	actc_runtime_input_joystick_result_sprite_second_arg_linked \
	actc_runtime_input_joystick_result_sprite_first_arg_linked \
	actc_runtime_input_joystick_result_sprite_data_first_arg_linked \
	actc_runtime_input_joystick_result_sprite_data_second_arg_linked \
	actc_runtime_input_joystick_result_sprite_ptr_first_arg_linked \
	actc_runtime_input_joystick_result_sprite_ptr_second_arg_linked \
	actc_runtime_input_joystick_result_sprite_mc_first_arg_linked \
	actc_runtime_input_joystick_result_sprite_mc_second_arg_linked \
	actc_runtime_input_joystick_result_sprite_xexp_first_arg_linked \
	actc_runtime_input_joystick_result_sprite_xexp_second_arg_linked \
	actc_runtime_input_joystick_result_sprite_yexp_first_arg_linked \
	actc_runtime_input_joystick_result_sprite_yexp_second_arg_linked \
	actc_runtime_input_joystick_result_sprite_prio_first_arg_linked \
	actc_runtime_input_joystick_result_sprite_prio_second_arg_linked \
	actc_runtime_input_joystick_result_sprite_set_mc_first_arg_linked \
	actc_runtime_input_joystick_result_sprite_set_mc_second_arg_linked \
	actc_runtime_input_joystick_result_sprite_pos_first_arg_linked \
	actc_runtime_input_joystick_result_sprite_pos_second_arg_linked \
	actc_runtime_input_joystick_result_sprite_pos_third_arg_linked \
	actc_runtime_input_joystick_result_sid_second_arg_linked \
	actc_runtime_input_joystick_result_sid_wave_first_arg_linked \
	actc_runtime_input_joystick_result_sid_ad_first_arg_linked \
	actc_runtime_input_joystick_result_sid_ad_second_arg_linked \
	actc_runtime_input_joystick_result_sid_sr_first_arg_linked \
	actc_runtime_input_joystick_result_sid_sr_second_arg_linked \
	actc_runtime_input_joystick_result_gfx_first_arg_linked \
	actc_runtime_input_joystick_result_gfx_second_arg_linked \
	actc_runtime_input_joystick_result_gfx_third_arg_linked \
	actc_runtime_input_sid_mixed_helpers_linked \
	actc_runtime_input_sprite_mixed_helpers_linked \
	actc_runtime_input_math_mixed_helpers_linked \
	actc_runtime_input_mouse_math_mixed_helpers_linked \
	actc_runtime_input_joystick_math_store_helpers_linked \
	actc_runtime_input_mouse_math_store_helpers_linked \
	actc_runtime_input1_export_sample_linked \
	actc_runtime_input1_joy_split_linked \
	actc_runtime_input1_joy_seen_split_linked \
	actc_runtime_input1_joy_button_split_linked \
	actc_runtime_input1_mouse_poll_split_linked \
	actc_runtime_input1_mouse_seen_split_linked \
	actc_runtime_input1_mouse_x_split_linked \
	actc_runtime_input1_mouse_y_split_linked \
	actc_runtime_input1_mouse_button_split_linked \
	actc_runtime_input1_mouse_button_state_split_linked
ACTION_ACTC_ALINK_DBF_RUNTIME_SHAPES := \
	actc_runtime_dbf1_export_sample_linked \
	actc_runtime_dbf1_create_split_linked \
	actc_runtime_dbf1_open_split_linked \
	actc_runtime_dbf1_open_missing_file_linked \
	actc_runtime_dbf1_close_split_linked \
	actc_runtime_dbf1_close_state_reset_linked \
	actc_runtime_dbf1_go_split_linked \
	actc_runtime_dbf1_invalid_record_field_linked \
	actc_runtime_dbf1_field_count_split_linked \
	actc_runtime_dbf1_field_len_split_linked \
	actc_runtime_dbf1_read_byte_split_linked \
	actc_runtime_dbf1_large_file_read_byte_linked \
	actc_runtime_dbf1_read_field_byte_split_linked \
	actc_runtime_dbf1_write_field_byte_split_linked \
	actc_runtime_dbf1_write_byte_split_linked \
	actc_runtime_dbf1_save_split_linked \
	actc_runtime_dbf1_large_file_save_linked \
	actc_runtime_dbf1_save_invalid_handle_linked \
	actc_runtime_dbf1_read_byte_invalid_offset_linked \
	actc_runtime_dbf1_read_byte_invalid_handle_linked \
	actc_runtime_dbf1_delete_undelete_split_linked \
	actc_runtime_dbf1_append_split_linked \
	actc_runtime_dbf1_pack_split_linked \
	actc_runtime_dbf1_deleted_split_linked \
	actc_runtime_dbf1_header_record_len_split_linked \
	actc_runtime_dbf1_read_byte_result_sprite_arg_linked \
	actc_runtime_dbf1_read_byte_joystick_offset_linked \
	actc_runtime_dbf1_total_recs_split_linked \
	actc_runtime_dbf1_curr_rec_no_split_linked \
	actc_runtime_dbf1_total_recs_result_sid_arg_linked
ACTION_ACTC_ALINK_MISC_RUNTIME_SHAPES := \
	actc_runtime_repeated_bgcolor_helper_dedup \
	actc_runtime_sidspr1_export_sample_linked \
	actc_runtime_sidspr1_sid_wave_mask_linked \
	actc_runtime_sidspr1_sid_mode_mask_linked \
	actc_runtime_sidspr1_sprite_prio_back_linked \
	actc_runtime_named_hardware_constants_linked \
	actc_runtime_named_constant_mixed_runtime_expr_linked
ACTION_ACTCHK_FS := build/action-actchk-fs
ACTION_ACTMON_FS := build/action-actmon-fs
ACTION_ACTWORK_FS := build/action-actwork-fs
ACTION_ACTWRITE_FS := build/action-actwrite-fs
ACTION_ACTADD_PERSIST_FS := build/actadd-persist-fs
ACTION_ACTNEW_PRG_FS := build/action-actnew-prg-fs
ACTION_ACTNEW_PRG_PERSIST_FS := build/actnew-prg-persist-fs
ACTION_ACTFLOW_FS := build/action-actflow-fs
ACTION_ACTDEL_FS := build/action-actdel-fs
ACTION_ACTMKDIR_FS := build/action-actmkdir-fs
ACTION_ACTMKDIR_PERSIST_FS := build/action-actmkdir-persist-fs
ACTION_ACTMOVE_FS := build/action-actmove-fs
ACTION_ACTMOVE_PERSIST_FS := build/action-actmove-persist-fs
ACTION_ACTRMDIR_PERSIST_FS := build/action-actrmdir-persist-fs
ACTION_COPY_ROOT_FS := build/action-copy-root-fs
ACTION_ACTCOPY_FS := build/action-actcopy-fs
ACTION_WORKSPACE_ARTIFACT := build/udos-action-workspace.d64
ACTION_ACTDIR_ARTIFACT := build/udos-action-actdir.d64
ACTION_ACTADD_ARTIFACT := build/udos-action-actadd.d64
ACTION_ACTC_ARTIFACT := build/udos-action-actc.d64
ACTION_ALINK_ARTIFACT := build/udos-action-alink.d64
ACTION_ACTFILE_ARTIFACT := build/udos-action-actfile.d64
ACTION_ACTSRC_ARTIFACT := build/udos-action-actsrc.d64
ACTION_ACTWORK_ARTIFACT := build/udos-action-actwork.d64
ACTION_ACTNEW_ARTIFACT := build/udos-action-actnew.d64
ACTION_ACTINFO_ARTIFACT := build/udos-action-actinfo.d64
ACTION_ACTWRITE_ARTIFACT := build/udos-action-actwrite.d64

RESIDENT_OBJ := $(BUILD_DIR)/udos_resident.o
RESIDENT_PRG := $(BUILD_DIR)/udos-resident.prg
RESIDENT_RAW := $(BUILD_DIR)/UDOSCORE.PRG
RESIDENT_BOOT_OBJ := $(BUILD_DIR)/udos_boot.o
RESIDENT_BOOT_PRG := $(BUILD_DIR)/udos-boot.prg
RESIDENT_BOOT_LOAD_PRG := $(BUILD_DIR)/udos-boot-load.prg
RESIDENT_BOOT_LABELS := $(BUILD_DIR)/udos-boot.labels
RESIDENT_BOOT_MAP := $(BUILD_DIR)/udos-boot.map
RESIDENT_AUTO_PRG := $(BUILD_DIR)/udosres.prg
RESIDENT_DISK := $(BUILD_DIR)/udos-resident.d64
RESIDENT_LABELS := $(BUILD_DIR)/udos-resident.labels
RESIDENT_MAP := $(BUILD_DIR)/udos-resident.map
RETURN_TEST_OBJ := $(BUILD_DIR)/udos_return_test.o
RETURN_TEST_BIN := $(BUILD_DIR)/udos_return_test.bin
RETURN_TEST_PRG := $(BUILD_DIR)/rettest.prg
CLOBBER_TEST_OBJ := $(BUILD_DIR)/udos_clobber_test.o
CLOBBER_TEST_BIN := $(BUILD_DIR)/udos_clobber_test.bin
CLOBBER_TEST_PRG := $(BUILD_DIR)/clobber.prg
REU_SERVICE_TEST_OBJ := $(BUILD_DIR)/udos_reu_service_test.o
REU_SERVICE_TEST_BIN := $(BUILD_DIR)/udos_reu_service_test.bin
REU_SERVICE_TEST_PRG := $(BUILD_DIR)/reutest.prg
VICE_REU_SERVICE_FS := build/vice-reu-service-fs
RELEASE_BUILD := build/release
RELEASE_DISK := build/udos-release.d64
RELEASE_FS := build/udos-release-fs
ACTIONC64U_DIR ?= $(abspath $(CURDIR)/../actionc64u)
ACTC_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
ACTC_HARNESS_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actc_harness_udos.sh
ACTADD_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actadd_udos.sh
ACT2SAVE_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_act2save_udos.sh
ALINK_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
ACTMON_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actmon_udos.sh
ACTCHK_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actchk_udos.sh
ACTCOPY_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actcopy_udos.sh
ACTDEL_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actdel_udos.sh
ACTEDIT_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actedit_udos.sh
ACTDIR_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actdir_udos.sh
ACTFILE_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actfile_udos.sh
ACTINFO_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actinfo_udos.sh
ACTMKDIR_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actmkdir_udos.sh
ACTMOVE_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actren_udos.sh
ACTNEW_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actnew_udos.sh
ACTRMDIR_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actrmdir_udos.sh
ACTSRC_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actsrc_udos.sh
ACTWRITE_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actwrite_udos.sh
ACTWORK_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actwork_udos.sh
ACTC_OVERLAY_BUILD := $(ACTIONC64U_DIR)/tools/build_actc_overlay_noop.sh
ACTC_OVERLAY_SOURCE_BUILD := $(ACTIONC64U_DIR)/tools/build_actc_overlay_source_header.sh
ACTC_OVERLAY_DECL_BUILD := $(ACTIONC64U_DIR)/tools/build_actc_overlay_decl_counts.sh
ACTC_OVERLAY_LAYOUT_BUILD := $(ACTIONC64U_DIR)/tools/build_actc_overlay_payload_layout.sh
ACTC_OVERLAY_IMPORT_BUILD := $(ACTIONC64U_DIR)/tools/build_actc_overlay_runtime_imports.sh
ACTC_OVERLAY_EMIT_BUILD := $(ACTIONC64U_DIR)/tools/build_actc_overlay_emit_object.sh
ACTC_OVERLAY_BODY_BUILD := $(ACTIONC64U_DIR)/tools/build_actc_overlay_body_collect.sh
ACTC_OVERLAY_PREALLOC_BUILD := $(ACTIONC64U_DIR)/tools/build_actc_overlay_body_preallocate.sh
ACTC_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTC.PRG
ACTC_OVERLAY_BIN := $(ACTIONC64U_DIR)/build/udos_tools/ACTC_OVL0.BIN
ACTC_OVERLAY_SOURCE_BIN := $(ACTIONC64U_DIR)/build/udos_tools/ACTC_OVL1.BIN
ACTC_OVERLAY_DECL_BIN := $(ACTIONC64U_DIR)/build/udos_tools/ACTC_OVL2.BIN
ACTC_OVERLAY_LAYOUT_BIN := $(ACTIONC64U_DIR)/build/udos_tools/ACTC_OVL3.BIN
ACTC_OVERLAY_IMPORT_BIN := $(ACTIONC64U_DIR)/build/udos_tools/ACTC_OVL4.BIN
ACTC_OVERLAY_EMIT_BIN := $(ACTIONC64U_DIR)/build/udos_tools/ACTC_OVL5.BIN
ACTC_OVERLAY_BODY_BIN := $(ACTIONC64U_DIR)/build/udos_tools/ACTC_OVL6.BIN
ACTC_OVERLAY_PREALLOC_BIN := $(ACTIONC64U_DIR)/build/udos_tools/ACTC_OVL7.BIN
ACTADD_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTADD.PRG
ACT2SAVE_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACT2SAVE.PRG
ALINK_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ALINK.PRG
ACTMON_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTMON.PRG
ACTCHK_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTCHK.PRG
ACTCOPY_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTCOPY.PRG
ACTDEL_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTDEL.PRG
ACTEDIT_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTEDIT.PRG
ACTDIR_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTDIR.PRG
ACTFILE_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTFILE.PRG
ACTINFO_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTINFO.PRG
ACTMKDIR_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTMKDIR.PRG
ACTMOVE_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTMOVE.PRG
ACTNEW_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTNEW.PRG
ACTRMDIR_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTRMDIR.PRG
ACTSRC_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTSRC.PRG
ACTWRITE_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTWRITE.PRG
ACTWORK_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTWORK.PRG

PROOF_DEPS ?=
RESIDENT_DEPS ?= resident
RELEASE_DEPS ?= release

.PHONY: all clean force resident release vice-release vice-action-workspace vice-action-actadd vice-action-actadd-persist vice-action-act2save vice-action-actc vice-action-alink vice-action-alink-prg vice-action-alink-prg-matrix vice-action-alink-prg-fanout vice-action-alink-prg-word-store vice-action-alink-prg-word-load-store vice-action-alink-prg-real-printre-int vice-action-alink-prg-real-printre-byte vice-action-alink-prg-real-printre-fraction vice-action-alink-prg-if-else vice-action-alink-prg-nested-if vice-action-alink-prg-real-do-until vice-action-alink-prg-real-while vice-action-alink-prg-do-until-eq vice-action-alink-prg-do-until-lt vice-action-alink-prg-if-local-call-do-until-eq vice-action-alink-prg-if-else-local-call-do-until-eq vice-action-alink-prg-nested-if-local-call vice-action-alink-prg-nested-else-local-call vice-action-alink-prg-nested-do-local-call vice-action-alink-prg-nested-do-if-else-local-call vice-action-alink-prg-if-local-call-nested-do-if-else vice-action-alink-prg-if-else-local-call-nested-do-if-else vice-action-alink-prg-nested-else-local-call-nested-do-if-else vice-action-alink-prg-if-else-local-call-chain-nested-do-if-else vice-action-alink-prg-nested-else-local-call-chain-nested-do-if-else vice-action-alink-launch-word-store vice-action-alink-launch-word-load-store vice-action-actc-alink-launch vice-action-actc-alink-launch-object-emission-matrix vice-action-actc-alink-launch-printmath vice-action-actc-alink-launch-if-else-chain vice-action-actc-alink-launch-nested-else-chain vice-action-actchk vice-action-actmon-check vice-action-actmon vice-action-actcopy vice-action-copy-root vice-action-actdir vice-action-actfile vice-action-actflow vice-action-actinfo vice-action-actnew vice-action-actnew-prg vice-action-actnew-prg-persist vice-action-actdel vice-action-actmkdir vice-action-actmkdir-persist vice-action-actmove vice-action-actmove-persist vice-action-actrmdir vice-action-actrmdir-persist vice-action-actsrc vice-action-actwork vice-action-actwrite vice-resident vice-launch vice-clobber vice-copy vice-drive vice-real-read vice-real-tree-write vice-real-tree-rename vice-real-tree-wild vice-real-tree-wild-copy vice-real-tree-wild-delete vice-real-tree-dir vice-real-tree-rmdir vice-batch-args vice-batch-stop vice-autoexec vice-selftest-read vice-selftest-copy vice-selftest-rename vice-selftest-delete vice-selftest-dir vice-selftest-batch vice-selftest-stop vice-selftest-launch vice-selftest test
.PHONY: vice-reu-services

all: resident

clean:
	rm -rf $(BUILD_DIR)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

force:

$(AUTOEXEC_INC): $(AUTOEXEC_SRC) | $(BUILD_DIR)
	$(PYTHON) tools/make_autoexec_include.py --input $< --output $@

$(RESIDENT_OBJ): force $(ASM_DIR)/udos_resident.asm $(AUTOEXEC_INC) | $(BUILD_DIR)
	$(CA65) -g $(RESIDENT_DEFINES) -o $@ $(ASM_DIR)/udos_resident.asm -I $(BUILD_DIR) -I $(ASM_DIR)

$(RESIDENT_BOOT_OBJ): force $(ASM_DIR)/udos_boot.asm | $(BUILD_DIR)
	$(CA65) -g -o $@ $(ASM_DIR)/udos_boot.asm

$(RETURN_TEST_OBJ): force $(ASM_DIR)/udos_return_test.asm | $(BUILD_DIR)
	$(CA65) -g -o $@ $(ASM_DIR)/udos_return_test.asm

$(RETURN_TEST_BIN): $(RETURN_TEST_OBJ)
	$(LD65) -C $(ASM_DIR)/udos_prog.cfg -o $@ $(RETURN_TEST_OBJ)

$(RETURN_TEST_PRG): $(RETURN_TEST_BIN)
	$(PYTHON) -c "from pathlib import Path; data=Path('$(RETURN_TEST_BIN)').read_bytes(); Path('$(RETURN_TEST_PRG)').write_bytes(bytes((0x00,0x09))+data)"

$(CLOBBER_TEST_OBJ): force $(ASM_DIR)/udos_clobber_test.asm | $(BUILD_DIR)
	$(CA65) -g -o $@ $(ASM_DIR)/udos_clobber_test.asm

$(CLOBBER_TEST_BIN): $(CLOBBER_TEST_OBJ)
	$(LD65) -C $(ASM_DIR)/udos_prog.cfg -o $@ $(CLOBBER_TEST_OBJ)

$(CLOBBER_TEST_PRG): $(CLOBBER_TEST_BIN)
	$(PYTHON) -c "from pathlib import Path; data=Path('$(CLOBBER_TEST_BIN)').read_bytes(); Path('$(CLOBBER_TEST_PRG)').write_bytes(bytes((0x00,0x09))+data)"

$(REU_SERVICE_TEST_OBJ): force $(ASM_DIR)/udos_reu_service_test.asm | $(BUILD_DIR)
	$(CA65) -g -o $@ $(ASM_DIR)/udos_reu_service_test.asm

$(REU_SERVICE_TEST_BIN): $(REU_SERVICE_TEST_OBJ)
	$(LD65) -C $(ASM_DIR)/udos_prog.cfg -o $@ $(REU_SERVICE_TEST_OBJ)

$(REU_SERVICE_TEST_PRG): $(REU_SERVICE_TEST_BIN)
	$(PYTHON) -c "from pathlib import Path; data=Path('$(REU_SERVICE_TEST_BIN)').read_bytes(); Path('$(REU_SERVICE_TEST_PRG)').write_bytes(bytes((0x00,0x09))+data)"

resident: $(RESIDENT_OBJ) $(RESIDENT_BOOT_OBJ)
	$(LD65) -Ln $(RESIDENT_LABELS) -C $(ASM_DIR)/udos_c64.cfg -m $(RESIDENT_MAP) -o $(RESIDENT_PRG) $(RESIDENT_OBJ)
	cp $(RESIDENT_PRG) $(RESIDENT_RAW)
	$(LD65) -Ln $(RESIDENT_BOOT_LABELS) -C $(ASM_DIR)/udos_boot.cfg -m $(RESIDENT_BOOT_MAP) -o $(RESIDENT_BOOT_PRG) $(RESIDENT_BOOT_OBJ)
	$(PYTHON) -c "from pathlib import Path; data=Path('$(RESIDENT_BOOT_PRG)').read_bytes(); Path('$(RESIDENT_BOOT_LOAD_PRG)').write_bytes(bytes((0x10,0x08))+data)"
	$(PYTHON) tools/make_basic_autostart.py --input $(RESIDENT_BOOT_LOAD_PRG) --labels $(RESIDENT_BOOT_LABELS) --output $(RESIDENT_AUTO_PRG) --expected-load-addr 0x0810
	$(C1541) -format "udos,01" d64 $(RESIDENT_DISK) -write $(RESIDENT_AUTO_PRG) udosboot -write $(RESIDENT_RAW) udoscore

release:
	$(MAKE) BUILD_DIR=$(RELEASE_BUILD) RESIDENT_DEFINES="-D UDOS_INCLUDE_AUTOEXEC=0" resident
	bash $(ACTC_UDOS_BUILD)
	bash $(ACTC_OVERLAY_BUILD)
	bash $(ACTC_OVERLAY_SOURCE_BUILD)
	bash $(ACTC_OVERLAY_DECL_BUILD)
	bash $(ACTC_OVERLAY_LAYOUT_BUILD)
	bash $(ACTC_OVERLAY_IMPORT_BUILD)
	bash $(ACTC_OVERLAY_EMIT_BUILD)
	bash $(ACTC_OVERLAY_BODY_BUILD)
	bash $(ACTC_OVERLAY_PREALLOC_BUILD)
	bash $(ACTADD_UDOS_BUILD)
	bash $(ACT2SAVE_UDOS_BUILD)
	bash $(ALINK_UDOS_BUILD)
	bash $(ACTMON_UDOS_BUILD)
	bash $(ACTCHK_UDOS_BUILD)
	bash $(ACTCOPY_UDOS_BUILD)
	bash $(ACTDEL_UDOS_BUILD)
	bash $(ACTEDIT_UDOS_BUILD)
	bash $(ACTDIR_UDOS_BUILD)
	bash $(ACTFILE_UDOS_BUILD)
	bash $(ACTINFO_UDOS_BUILD)
	bash $(ACTMKDIR_UDOS_BUILD)
	bash $(ACTMOVE_UDOS_BUILD)
	bash $(ACTNEW_UDOS_BUILD)
	bash $(ACTRMDIR_UDOS_BUILD)
	bash $(ACTSRC_UDOS_BUILD)
	bash $(ACTWRITE_UDOS_BUILD)
	bash $(ACTWORK_UDOS_BUILD)
	$(PYTHON) tools/prepare_release_fs.py --base $(VICE_FS_ROOT) --output $(RELEASE_FS)
	cp $(RELEASE_BUILD)/udos-resident.d64 $(RELEASE_DISK)
	-$(C1541) $(RELEASE_DISK) -delete ACTC.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTC_OVL0.BIN
	-$(C1541) $(RELEASE_DISK) -delete ACTC_OVL1.BIN
	-$(C1541) $(RELEASE_DISK) -delete ACTC_OVL2.BIN
	-$(C1541) $(RELEASE_DISK) -delete ACTC_OVL3.BIN
	-$(C1541) $(RELEASE_DISK) -delete ACTC_OVL4.BIN
	-$(C1541) $(RELEASE_DISK) -delete ACTC_OVL5.BIN
	-$(C1541) $(RELEASE_DISK) -delete ACTC_OVL6.BIN
	-$(C1541) $(RELEASE_DISK) -delete ACTC_OVL7.BIN
	-$(C1541) $(RELEASE_DISK) -delete ACTADD.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACT2SAVE.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTSAVE.PRG
	-$(C1541) $(RELEASE_DISK) -delete ALINK.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTMON.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTCHK.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTCOPY.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTDEL.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTEDIT.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTDIR.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTFILE.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTINFO.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTMKDIR.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTMOVE.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTNEW.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTRMDIR.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTSRC.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTWRITE.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTWORK.PRG
	$(C1541) $(RELEASE_DISK) -write $(ACTC_UDOS_PRG) ACTC.PRG -write $(ACTC_OVERLAY_BIN) ACTC_OVL0.BIN -write $(ACTC_OVERLAY_SOURCE_BIN) ACTC_OVL1.BIN -write $(ACTC_OVERLAY_DECL_BIN) ACTC_OVL2.BIN -write $(ACTC_OVERLAY_LAYOUT_BIN) ACTC_OVL3.BIN -write $(ACTC_OVERLAY_IMPORT_BIN) ACTC_OVL4.BIN -write $(ACTC_OVERLAY_EMIT_BIN) ACTC_OVL5.BIN -write $(ACTC_OVERLAY_BODY_BIN) ACTC_OVL6.BIN -write $(ACTC_OVERLAY_PREALLOC_BIN) ACTC_OVL7.BIN -write $(ACTADD_UDOS_PRG) ACTADD.PRG -write $(ACT2SAVE_UDOS_PRG) ACT2SAVE.PRG -write $(ACT2SAVE_UDOS_PRG) ACTSAVE.PRG -write $(ALINK_UDOS_PRG) ALINK.PRG -write $(ACTMON_UDOS_PRG) ACTMON.PRG -write $(ACTCHK_UDOS_PRG) ACTCHK.PRG -write $(ACTCOPY_UDOS_PRG) ACTCOPY.PRG -write $(ACTDEL_UDOS_PRG) ACTDEL.PRG -write $(ACTEDIT_UDOS_PRG) ACTEDIT.PRG -write $(ACTDIR_UDOS_PRG) ACTDIR.PRG -write $(ACTFILE_UDOS_PRG) ACTFILE.PRG -write $(ACTINFO_UDOS_PRG) ACTINFO.PRG -write $(ACTMKDIR_UDOS_PRG) ACTMKDIR.PRG -write $(ACTMOVE_UDOS_PRG) ACTMOVE.PRG -write $(ACTNEW_UDOS_PRG) ACTNEW.PRG -write $(ACTRMDIR_UDOS_PRG) ACTRMDIR.PRG -write $(ACTSRC_UDOS_PRG) ACTSRC.PRG -write $(ACTWRITE_UDOS_PRG) ACTWRITE.PRG -write $(ACTWORK_UDOS_PRG) ACTWORK.PRG

vice-release: $(RELEASE_DEPS)
	$(PYTHON) tools/vice_prg_probe.py --disk $(RELEASE_DISK) \
		--expected "A:D64/>" --settle 1.0 --absent "AUTOEXEC OK"

vice-action-workspace: $(RELEASE_DEPS)
	rm -rf $(ACTION_WORKSPACE_FS)
	mkdir -p $(ACTION_WORKSPACE_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_WORKSPACE_FS)/
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_WORKSPACE_FS) \
		--pre-command "DIR" --pre-prompt "B:DNP/>" --pre-fragment "BIN/ DOC/ LIB/ SRC/" \
		--command "TYPE README.TXT" --run-marker "" --done-fragment "ACTIONC64U FOR UDOS" --skip-command-prompt \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/>" \
		--attempts 4 --attempt-delay 2.0 \
		--contains "ACTIONC64U FOR UDOS"

vice-action-actadd: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTADD_FS)
	mkdir -p $(ACTION_ACTADD_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTADD_FS)/
	rm -rf $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/src \
		$(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/bin \
		$(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	printf 'ACTION PROJECT READY\n' > $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/readme.txt
	printf 'ACTION PROJECT\rMAIN.ACT\r' > $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	printf 'D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF README.TXT\n' > $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/UDOSDIR.TXT
	printf 'F MAIN.ACT\n' > $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/src/UDOSDIR.TXT
	printf '' > $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/bin/UDOSDIR.TXT
	printf '' > $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/obj/UDOSDIR.TXT
	printf 'PROC MAIN()\rENDPROC\r' > $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/src/main.act
	ln -s PROJ3 $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/proj3
	ln -s ACTION.PROJ $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/action.proj
	ln -s UDOSDIR.TXT $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/udosdir.txt
	ln -s src $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/SRC
	ln -s bin $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/BIN
	ln -s obj $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/OBJ
	ln -s readme.txt $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/README.TXT
	ln -s UDOSDIR.TXT $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/src/udosdir.txt
	ln -s main.act $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/src/MAIN.ACT
	ln -s UDOSDIR.TXT $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/bin/udosdir.txt
	ln -s UDOSDIR.TXT $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/obj/udosdir.txt
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTADD_FS) \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--command "ACTADD HELPER" --run-marker "RUN ACTADD.PRG" --done-fragment "ACTADD OK" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTADD.PRG" --contains "ACTADD OK" --contains "B:DNP/PROJ3>"
	test -d $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/bin
	test -d $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	test -d $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/src
	test -f $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	grep -q "ACTION PROJECT" $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	grep -q "MAIN.ACT" $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	grep -q "HELPER.ACT" $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	grep -q "D SRC" $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/UDOSDIR.TXT
	grep -q "F HELPER.ACT" $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/SRC/UDOSDIR.TXT
	grep -q "PROC HELPER()" $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/SRC/HELPER.ACT
	grep -q "ENDPROC" $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/SRC/HELPER.ACT

vice-action-actdir: $(RELEASE_DEPS)
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--command "ACTDIR" --run-marker "RUN ACTDIR.PRG" --done-fragment "" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/>" \
		--attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTDIR.PRG" --contains "BIN/" --contains "DOC/" --contains "LIB/" --contains "SRC/"

vice-action-actsrc: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTSRC_FS)
	mkdir -p $(ACTION_ACTSRC_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTSRC_FS)/
	rm -rf $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/src \
		$(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/bin \
		$(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	printf 'ACTION PROJECT READY\n' > $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/readme.txt
	printf 'ACTION PROJECT\rMAIN.ACT\rHELPER.ACT\r' > $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	printf 'D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF README.TXT\n' > $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/UDOSDIR.TXT
	printf 'F MAIN.ACT\nF HELPER.ACT\n' > $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/src/UDOSDIR.TXT
	printf '' > $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/bin/UDOSDIR.TXT
	printf '' > $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/obj/UDOSDIR.TXT
	printf 'PROC MAIN()\rENDPROC\r' > $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/src/main.act
	printf 'PROC HELPER()\rENDPROC\r' > $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	ln -s PROJ3 $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/proj3
	ln -s ACTION.PROJ $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/action.proj
	ln -s UDOSDIR.TXT $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/udosdir.txt
	ln -s src $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/SRC
	ln -s bin $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/BIN
	ln -s obj $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/OBJ
	ln -s UDOSDIR.TXT $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/src/udosdir.txt
	ln -s main.act $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/src/MAIN.ACT
	ln -s helper.act $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/src/HELPER.ACT
	ln -s UDOSDIR.TXT $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/bin/udosdir.txt
	ln -s UDOSDIR.TXT $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/obj/udosdir.txt
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTSRC_FS) \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--command "ACTSRC.PRG" --run-marker "RUN ACTSRC.PRG" --done-fragment "" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTSRC.PRG" --contains "MAIN.ACT" --contains "HELPER.ACT" --contains "B:DNP/PROJ3>"

vice-action-actfile: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTFILE_FS)
	mkdir -p $(ACTION_ACTFILE_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTFILE_FS)/
	rm -rf $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/src \
		$(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/bin \
		$(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	printf 'ACTION PROJECT READY\n' > $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/readme.txt
	printf 'ACTION PROJECT\rMAIN.ACT\rHELPER.ACT\r' > $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	printf 'D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF README.TXT\n' > $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/UDOSDIR.TXT
	printf 'F MAIN.ACT\nF HELPER.ACT\n' > $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/src/UDOSDIR.TXT
	printf '' > $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/bin/UDOSDIR.TXT
	printf '' > $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/obj/UDOSDIR.TXT
	printf 'PROC MAIN()\rENDPROC\r' > $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/src/main.act
	printf 'PROC HELPER()\rENDPROC\r' > $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	ln -s PROJ3 $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/proj3
	ln -s ACTION.PROJ $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/action.proj
	ln -s UDOSDIR.TXT $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/udosdir.txt
	ln -s src $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/SRC
	ln -s bin $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/BIN
	ln -s obj $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/OBJ
	ln -s UDOSDIR.TXT $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/src/udosdir.txt
	ln -s main.act $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/src/MAIN.ACT
	ln -s helper.act $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/src/HELPER.ACT
	ln -s UDOSDIR.TXT $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/bin/udosdir.txt
	ln -s UDOSDIR.TXT $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/obj/udosdir.txt
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTFILE_FS) \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--command "ACTFILE MAIN" --run-marker "RUN ACTFILE.PRG" --done-fragment "" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTFILE.PRG" --contains "PROC MAIN()" --contains "ENDPROC" --contains "B:DNP/PROJ3>"

vice-action-actwork: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTWORK_FS)
	mkdir -p $(ACTION_ACTWORK_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTWORK_FS)/
	rm -rf $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/src \
		$(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/bin \
		$(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	printf 'ACTION PROJECT READY\n' > $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/readme.txt
	printf 'ACTION PROJECT\rMAIN.ACT\rHELPER.ACT\r' > $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	printf 'D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF README.TXT\n' > $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/UDOSDIR.TXT
	printf 'F MAIN.ACT\nF HELPER.ACT\n' > $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/src/UDOSDIR.TXT
	printf '' > $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/bin/UDOSDIR.TXT
	printf '' > $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/obj/UDOSDIR.TXT
	printf 'PROC MAIN()\rENDPROC\r' > $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/src/main.act
	printf 'PROC HELPER()\rENDPROC\r' > $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	ln -s PROJ3 $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/proj3
	ln -s ACTION.PROJ $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/action.proj
	ln -s UDOSDIR.TXT $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/udosdir.txt
	ln -s src $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/SRC
	ln -s bin $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/BIN
	ln -s obj $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/OBJ
	ln -s UDOSDIR.TXT $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/src/udosdir.txt
	ln -s main.act $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/src/MAIN.ACT
	ln -s helper.act $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/src/HELPER.ACT
	ln -s UDOSDIR.TXT $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/bin/udosdir.txt
	ln -s UDOSDIR.TXT $(ACTION_ACTWORK_FS)/IMAGES/ACTION.DNP/PROJ3/obj/udosdir.txt
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTWORK_FS) \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--command "ACTWORK" --run-marker "RUN ACTWORK.PRG" --done-fragment "" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTWORK.PRG" --contains "PROJECT YES" --contains "SRC YES" --contains "BIN YES" \
		--contains "OBJ YES" --contains "MODULES 2" --contains "B:DNP/PROJ3>"

vice-action-actnew: vice-action-actnew-prg

vice-action-actnew-prg: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTNEW_PRG_FS)
	mkdir -p $(ACTION_ACTNEW_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTNEW_PRG_FS)/
	rm -rf $(ACTION_ACTNEW_PRG_FS)/IMAGES/ACTION.DNP/DEMO $(ACTION_ACTNEW_PRG_FS)/IMAGES/ACTION.DNP/demo
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTNEW_PRG_FS) \
		--command "ACTNEW DEMO" --run-marker "RUN ACTNEW.PRG" --done-fragment "ACTNEW OK" \
		--connect-delay 20.0 --attempts 4 --attempt-delay 2.0 --shell-timeout 180 --skip-command-prompt --host-timeout 300 \
		--clean-host-path IMAGES/ACTION.DNP/DEMO --clean-host-path IMAGES/ACTION.DNP/demo \
		--host-exists IMAGES/ACTION.DNP/DEMO/BIN \
		--host-exists IMAGES/ACTION.DNP/DEMO/OBJ \
		--host-exists IMAGES/ACTION.DNP/DEMO/SRC \
		--host-exists IMAGES/ACTION.DNP/DEMO/ACTION.PROJ \
		--host-exists IMAGES/ACTION.DNP/DEMO/README.TXT \
		--host-exists IMAGES/ACTION.DNP/DEMO/SRC/MAIN.ACT \
		--host-exists IMAGES/ACTION.DNP/DEMO/UDOSDIR.TXT \
		--host-exists IMAGES/ACTION.DNP/DEMO/SRC/UDOSDIR.TXT \
		--host-contains "IMAGES/ACTION.DNP/DEMO/UDOSDIR.TXT=D SRC" \
		--host-contains "IMAGES/ACTION.DNP/DEMO/SRC/UDOSDIR.TXT=F MAIN.ACT" \
		--contains "RUN ACTNEW.PRG" --contains "ACTNEW OK"
	test -d $(ACTION_ACTNEW_PRG_FS)/IMAGES/ACTION.DNP/DEMO/BIN
	test -d $(ACTION_ACTNEW_PRG_FS)/IMAGES/ACTION.DNP/DEMO/OBJ
	test -d $(ACTION_ACTNEW_PRG_FS)/IMAGES/ACTION.DNP/DEMO/SRC
	test -f $(ACTION_ACTNEW_PRG_FS)/IMAGES/ACTION.DNP/DEMO/ACTION.PROJ
	grep -q "MAIN.ACT" $(ACTION_ACTNEW_PRG_FS)/IMAGES/ACTION.DNP/DEMO/ACTION.PROJ
	grep -q "ACTION PROJECT READY" $(ACTION_ACTNEW_PRG_FS)/IMAGES/ACTION.DNP/DEMO/README.TXT
	grep -q "PROC MAIN()" $(ACTION_ACTNEW_PRG_FS)/IMAGES/ACTION.DNP/DEMO/SRC/MAIN.ACT
	grep -q "D SRC" $(ACTION_ACTNEW_PRG_FS)/IMAGES/ACTION.DNP/DEMO/UDOSDIR.TXT
	grep -q "F MAIN.ACT" $(ACTION_ACTNEW_PRG_FS)/IMAGES/ACTION.DNP/DEMO/SRC/UDOSDIR.TXT

vice-action-actnew-prg-persist: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTNEW_PRG_PERSIST_FS)
	mkdir -p $(ACTION_ACTNEW_PRG_PERSIST_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTNEW_PRG_PERSIST_FS)/
	rm -rf $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJA $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/proja
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTNEW_PRG_PERSIST_FS) \
		--command "ACTNEW PROJA" --run-marker "RUN ACTNEW.PRG" --done-fragment "ACTNEW OK" \
		--connect-delay 20.0 --attempts 4 --attempt-delay 2.0 --shell-timeout 180 --skip-command-prompt --host-timeout 300 \
		--clean-host-path IMAGES/ACTION.DNP/PROJA --clean-host-path IMAGES/ACTION.DNP/proja \
		--host-exists IMAGES/ACTION.DNP/PROJA/BIN \
		--host-exists IMAGES/ACTION.DNP/PROJA/OBJ \
		--host-exists IMAGES/ACTION.DNP/PROJA/SRC \
		--host-exists IMAGES/ACTION.DNP/PROJA/ACTION.PROJ \
		--host-exists IMAGES/ACTION.DNP/PROJA/README.TXT \
		--host-exists IMAGES/ACTION.DNP/PROJA/SRC/MAIN.ACT \
		--host-exists IMAGES/ACTION.DNP/PROJA/UDOSDIR.TXT \
		--host-exists IMAGES/ACTION.DNP/PROJA/SRC/UDOSDIR.TXT \
		--host-contains "IMAGES/ACTION.DNP/PROJA/UDOSDIR.TXT=D SRC" \
		--host-contains "IMAGES/ACTION.DNP/PROJA/SRC/UDOSDIR.TXT=F MAIN.ACT" \
		--contains "RUN ACTNEW.PRG" --contains "ACTNEW OK"
	test -d $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJA/BIN
	test -d $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJA/OBJ
	test -d $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJA/SRC
	test -f $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJA/ACTION.PROJ
	grep -q "MAIN.ACT" $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJA/ACTION.PROJ
	grep -q "ACTION PROJECT READY" $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJA/README.TXT
	grep -q "PROC MAIN()" $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJA/SRC/MAIN.ACT
	grep -q "D SRC" $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJA/UDOSDIR.TXT
	grep -q "F MAIN.ACT" $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJA/SRC/UDOSDIR.TXT

vice-action-actadd-persist: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTADD_PERSIST_FS)
	mkdir -p $(ACTION_ACTADD_PERSIST_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTADD_PERSIST_FS)/
	rm -rf $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src \
		$(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/bin \
		$(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	printf 'ACTION PROJECT READY\n' > $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/readme.txt
	printf 'ACTION PROJECT\rMAIN.ACT\r' > $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	printf 'D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF README.TXT\n' > $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/UDOSDIR.TXT
	printf 'F MAIN.ACT\nF HELPER.ACT\n' > $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/UDOSDIR.TXT
	printf '' > $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/bin/UDOSDIR.TXT
	printf '' > $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/obj/UDOSDIR.TXT
	printf 'PROC MAIN()\rENDPROC\r' > $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/main.act
	printf 'PROC OLDHELPER()\rENDPROC\r' > $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	ln -s PROJ3 $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/proj3
	ln -s ACTION.PROJ $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/action.proj
	ln -s UDOSDIR.TXT $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/udosdir.txt
	ln -s src $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/SRC
	ln -s bin $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/BIN
	ln -s obj $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/OBJ
	ln -s UDOSDIR.TXT $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/udosdir.txt
	ln -s main.act $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/MAIN.ACT
	ln -s helper.act $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/HELPER.ACT
	ln -s UDOSDIR.TXT $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/bin/udosdir.txt
	ln -s UDOSDIR.TXT $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/obj/udosdir.txt
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTADD_PERSIST_FS) \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--command "ACTADD HELPER" --run-marker "RUN ACTADD.PRG" --done-fragment "EXISTS" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--prompt-count 2 --attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTADD.PRG" --contains "EXISTS" --contains "B:DNP/PROJ3>"
	test -d $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/bin
	test -d $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	test -d $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src
	test -f $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	grep -q "ACTION PROJECT" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	grep -q "MAIN.ACT" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	! grep -q "HELPER.ACT" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	grep -q "ACTION PROJECT READY" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/readme.txt
	grep -q "PROC MAIN()" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/main.act
	grep -q "PROC OLDHELPER()" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	! grep -q "PROC HELPER()" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	grep -q "ENDPROC" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act

vice-action-act2save: $(RELEASE_DEPS)
	sleep 2
	$(PYTHON) tools/run_action_act2save_seeded_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--attempts 4 --attempt-delay 2.0

vice-action-actc: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTC_FS)
	mkdir -p $(ACTION_ACTC_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_FS)/
	sleep 2
	$(PYTHON) tools/run_action_actc_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_FS) \
		--attempts 3 --attempt-delay 4.0

vice-action-alink: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_FS)
	mkdir -p $(ACTION_ALINK_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_FS)/
	$(PYTHON) tools/run_action_alink_seeded_runtime_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_FS) \
		--attempts 3 --attempt-delay 4.0

vice-action-alink-prg: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape word_store --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	PYTHONPATH=tools $(PYTHON) -c 'import run_action_alink_prg_probe as p; [print(name) for name in p.DIRECT_PRG_CASES]' | while IFS= read -r shape; do \
		echo "=== $$shape ==="; \
		$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) --shape "$$shape" --skip-launch --attempts 1 || exit $$?; \
	done

.PHONY: vice-action-alink-prg-object-code-graph-launch-matrix
vice-action-alink-prg-object-code-graph-launch-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
		for shape in $(ACTION_ALINK_PRG_OBJECT_CODE_GRAPH_SHAPES); do \
			echo "=== $$shape ==="; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			for attempt in $$(seq 1 $(ACTION_ALINK_PRG_OBJECT_CODE_PROBE_ATTEMPTS)); do \
				timeout $(ACTION_ALINK_PRG_OBJECT_CODE_PROBE_TIMEOUT) $(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) --shape "$$shape" --attempts 1 --attempt-delay 4.0 --shell-timeout $(ACTION_ALINK_PRG_OBJECT_CODE_SHELL_TIMEOUT) && break; \
				status=$$?; \
				echo "shape $$shape attempt $$attempt failed with status $$status"; \
				PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
				if [ $$attempt -eq $(ACTION_ALINK_PRG_OBJECT_CODE_PROBE_ATTEMPTS) ]; then exit $$status; fi; \
				sleep 4; \
			done; \
		done

.PHONY: vice-action-alink-prg-object-code-core-launch-matrix
vice-action-alink-prg-object-code-core-launch-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
		for shape in $(ACTION_ALINK_PRG_OBJECT_CODE_CORE_SHAPES); do \
			echo "=== $$shape ==="; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			for attempt in $$(seq 1 $(ACTION_ALINK_PRG_OBJECT_CODE_PROBE_ATTEMPTS)); do \
				timeout $(ACTION_ALINK_PRG_OBJECT_CODE_PROBE_TIMEOUT) $(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) --shape "$$shape" --attempts 1 --attempt-delay 4.0 --shell-timeout $(ACTION_ALINK_PRG_OBJECT_CODE_SHELL_TIMEOUT) && break; \
				status=$$?; \
				echo "shape $$shape attempt $$attempt failed with status $$status"; \
				PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
				if [ $$attempt -eq $(ACTION_ALINK_PRG_OBJECT_CODE_PROBE_ATTEMPTS) ]; then exit $$status; fi; \
				sleep 4; \
			done; \
		done

.PHONY: vice-action-alink-prg-object-code-rejection-matrix
vice-action-alink-prg-object-code-rejection-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	for shape in $(ACTION_ALINK_PRG_OBJECT_CODE_REJECTION_CASES); do \
		echo "=== $$shape ==="; \
		$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) --shape "$$shape" --skip-launch --attempts 1 || exit $$?; \
	done

.PHONY: vice-action-alink-prg-object-code-matrices
vice-action-alink-prg-object-code-matrices:
	$(MAKE) vice-action-alink-prg-object-code-graph-launch-matrix
	$(MAKE) vice-action-alink-prg-object-code-core-launch-matrix
	$(MAKE) vice-action-alink-prg-object-code-rejection-matrix

vice-action-alink-prg-selective-runtime-libs: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape actc_runtime_selective_hardware_helpers_linked --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-helper-sequence: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape actc_runtime_reordered_hardware_helpers_linked --attempts 3 --attempt-delay 4.0

.PHONY: vice-action-alink-prg-mixed-helper-sequence
vice-action-alink-prg-mixed-helper-sequence: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape actc_runtime_mixed_hardware_helpers_linked --attempts 3 --attempt-delay 4.0

.PHONY: vice-action-alink-prg-variable-mixed-helper-sequence
vice-action-alink-prg-variable-mixed-helper-sequence: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape actc_runtime_variable_mixed_gfx_sprite_helpers_linked --attempts 3 --attempt-delay 4.0

.PHONY: vice-action-alink-prg-no-arg-helper-sequence
vice-action-alink-prg-no-arg-helper-sequence: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape actc_runtime_no_arg_hardware_helpers_linked --attempts 3 --attempt-delay 4.0

.PHONY: vice-action-alink-prg-stateful-byte-helper-sequence
vice-action-alink-prg-stateful-byte-helper-sequence: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape actc_runtime_stateful_byte_hardware_helpers_linked --attempts 3 --attempt-delay 4.0

.PHONY: vice-action-alink-prg-word-copy-fill-helper-sequence
vice-action-alink-prg-word-copy-fill-helper-sequence: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape actc_runtime_word_copy_fill_helpers_linked --attempts 3 --attempt-delay 4.0

.PHONY: vice-action-alink-prg-cell-helper-sequence
vice-action-alink-prg-cell-helper-sequence: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape actc_runtime_cell_helpers_linked --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-fanout: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape fanout --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-word-store: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape word_store --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-word-load-store: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape word_load_store --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-printre-int: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape real_printre_int --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-printre-byte: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape real_printre_byte --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-printre-fraction: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape real_printre_fraction --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-printre-add: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape real_printre_add --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-printre-sub: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape real_printre_sub --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-printre-mul: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape real_printre_mul --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-if-gt: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape real_if_gt --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-if-gt-false: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape real_if_gt_false --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-if-lt: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape real_if_lt --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-if-ge: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape real_if_ge --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-if-le: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape real_if_le --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-if-eq: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape real_if_eq --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-if-ne: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape real_if_ne --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-real-if-false: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	for shape in real_if_gt_false real_if_lt_false real_if_ge_false real_if_le_false real_if_eq_false real_if_ne_false; do \
		$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
			--shape "$$shape" --attempts 3 --attempt-delay 4.0 || exit $$?; \
	done

vice-action-alink-prg-real-if-else: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	for shape in real_if_else_true real_if_else_false \
		real_if_lt_else_true real_if_lt_else_false \
		real_if_ge_else_true real_if_ge_else_false \
		real_if_le_else_true real_if_le_else_false \
		real_if_eq_else_true real_if_eq_else_false \
		real_if_ne_else_true real_if_ne_else_false; do \
		$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
			--shape "$$shape" --attempts 3 --attempt-delay 4.0 || exit $$?; \
	done

vice-action-alink-prg-real-nested-if: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	for shape in real_nested_if_gt real_nested_if_gt_false \
		real_nested_if_lt real_nested_if_lt_false \
		real_nested_if_ge real_nested_if_ge_false \
		real_nested_if_le real_nested_if_le_false \
		real_nested_if_eq real_nested_if_eq_false \
		real_nested_if_ne real_nested_if_ne_false; do \
		$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
			--shape "$$shape" --attempts 3 --attempt-delay 4.0 || exit $$?; \
	done

vice-action-alink-prg-real-do-until: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	for shape in real_do_until_eq real_do_until_gt real_do_until_lt real_do_until_ge real_do_until_le real_do_until_ne \
		real_do_until_gt_real_add_loop real_do_until_ge_real_add_loop \
		real_do_until_lt_real_add_loop real_do_until_le_real_add_loop \
		real_do_until_gt_real_sub_loop real_do_until_ge_real_sub_loop \
		real_do_until_lt_real_sub_loop real_do_until_le_real_sub_loop; do \
		$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
			--shape "$$shape" --attempts 3 --attempt-delay 4.0 || exit $$?; \
	done

vice-action-alink-prg-real-while: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	for shape in real_while_gt_once real_while_ge_once real_while_lt_once real_while_le_once \
		real_while_gt_update_nonzero_once real_while_ge_update_nonzero_once \
		real_while_lt_update_nonzero_once real_while_le_update_nonzero_once \
		real_while_gt_real_sub_loop real_while_ge_real_sub_loop \
		real_while_lt_real_add_loop real_while_le_real_add_loop \
		real_while_gt_real_add_skip real_while_ge_real_add_skip \
		real_while_lt_real_sub_skip real_while_le_real_sub_skip; do \
		$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
			--shape "$$shape" --attempts 3 --attempt-delay 4.0 || exit $$?; \
	done

vice-action-alink-prg-if-else: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape if_else --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-nested-if: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape nested_if --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-nested-else: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape nested_else --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-nested-do-until-eq: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape nested_do_until_eq --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-do-if-until-eq: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape do_if_until_eq --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-do-if-else-until-eq: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape do_if_else_until_eq --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-if-do-until-eq: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape if_do_until_eq --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-if-else-do-until-eq: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape if_else_do_until_eq --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-if-local-call-do-until-eq: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape if_local_call_do_until_eq --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-if-else-local-call-do-until-eq: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape if_else_local_call_do_until_eq --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-nested-if-local-call: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape nested_if_local_call --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-nested-else-local-call: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape nested_else_local_call --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-nested-do-local-call: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape nested_do_local_call --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-nested-do-if-else-local-call: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape nested_do_if_else_local_call --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-if-local-call-nested-do-if-else: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape if_local_call_nested_do_if_else --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-if-else-local-call-nested-do-if-else: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape if_else_local_call_nested_do_if_else --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-nested-else-local-call-nested-do-if-else: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape nested_else_local_call_nested_do_if_else --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-if-else-local-call-chain-nested-do-if-else: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape if_else_local_call_chain_nested_do_if_else --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-nested-else-local-call-chain-nested-do-if-else: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape nested_else_local_call_chain_nested_do_if_else --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-if-ne: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape if_ne --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-if-ge: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape if_ge --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-do-until-eq: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape do_until_eq --attempts 3 --attempt-delay 4.0

vice-action-alink-prg-do-until-lt: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTC_HARNESS_UDOS_BUILD)
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape do_until_lt --attempts 3 --attempt-delay 4.0

vice-action-alink-launch-word-store: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape word_store --attempts 3 --attempt-delay 4.0

vice-action-alink-launch-word-load-store: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_PRG_FS)
	mkdir -p $(ACTION_ALINK_PRG_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_PRG_FS)/
	$(PYTHON) tools/run_action_alink_prg_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_PRG_FS) \
		--shape word_load_store_seeded --attempts 3 --attempt-delay 4.0

vice-action-actc-alink-launch-printmath: $(RELEASE_DEPS)
	$(MAKE) vice-action-actc-alink-launch ACTION_ACTC_ALINK_LAUNCH_SHAPE=printmath

vice-action-actc-alink-launch: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	$(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) \
		$(if $(ACTION_ACTC_ALINK_LAUNCH_SHAPE),--shape $(ACTION_ACTC_ALINK_LAUNCH_SHAPE),)

vice-action-actc-alink-launch-object-emission-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	for shape in $(ACTION_ACTC_ALINK_OBJECT_EMISSION_SHAPES); do \
		echo "=== $$shape ==="; \
		timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) --shape "$$shape" --attempts $(ACTION_ACTC_ALINK_PROBE_ATTEMPTS) --attempt-delay 4.0 || { \
			status=$$?; \
			echo "runtime shape $$shape failed with status $$status"; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			exit $$status; \
		}; \
	done

vice-action-actc-alink-launch-if-else-chain: $(RELEASE_DEPS)
	$(MAKE) vice-action-actc-alink-launch ACTION_ACTC_ALINK_LAUNCH_SHAPE=if_else_local_call_chain_nested_do_if_else

vice-action-actc-alink-launch-nested-else-chain: $(RELEASE_DEPS)
	$(MAKE) vice-action-actc-alink-launch ACTION_ACTC_ALINK_LAUNCH_SHAPE=nested_else_local_call_chain_nested_do_if_else

.PHONY: vice-action-actc-alink-launch-selective-runtime-libs
vice-action-actc-alink-launch-selective-runtime-libs:
	$(MAKE) vice-action-actc-alink-launch ACTION_ACTC_ALINK_LAUNCH_SHAPE=actc_runtime_selective_hardware_helpers_linked

.PHONY: vice-action-actc-alink-launch-runtime-matrices
vice-action-actc-alink-launch-runtime-matrices:
	$(MAKE) vice-action-actc-alink-launch-runtime-matrix
	$(MAKE) vice-action-actc-alink-launch-card-variable-runtime-matrix
	$(MAKE) vice-action-actc-alink-launch-math-runtime-matrix
	$(MAKE) vice-action-actc-alink-launch-gfx-runtime-matrix
	$(MAKE) vice-action-actc-alink-launch-variable-gfx-runtime-matrix
	$(MAKE) vice-action-actc-alink-launch-sid-runtime-matrix
	$(MAKE) vice-action-actc-alink-launch-variable-sid-runtime-matrix
	$(MAKE) vice-action-actc-alink-launch-sprite-runtime-matrix
	$(MAKE) vice-action-actc-alink-launch-variable-sprite-runtime-matrix
	$(MAKE) vice-action-actc-alink-launch-input-runtime-matrix
	$(MAKE) vice-action-actc-alink-launch-dbf-runtime-matrix
	$(MAKE) vice-action-actc-alink-launch-misc-runtime-matrix
	$(MAKE) vice-action-actc-alink-launch-helper-demos

.PHONY: vice-action-actc-alink-launch-runtime-matrix
vice-action-actc-alink-launch-runtime-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	for shape in $(ACTION_ACTC_ALINK_RUNTIME_SHAPES); do \
		echo "=== $$shape ==="; \
		timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) --shape "$$shape" --attempts $(ACTION_ACTC_ALINK_PROBE_ATTEMPTS) --attempt-delay 4.0 || { \
			status=$$?; \
			echo "runtime shape $$shape failed with status $$status"; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			exit $$status; \
		}; \
	done

.PHONY: vice-action-actc-alink-launch-card-variable-runtime-matrix
vice-action-actc-alink-launch-card-variable-runtime-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	for shape in $(ACTION_ACTC_ALINK_CARD_VARIABLE_RUNTIME_SHAPES); do \
		echo "=== $$shape ==="; \
		timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) --shape "$$shape" --attempts $(ACTION_ACTC_ALINK_PROBE_ATTEMPTS) --attempt-delay 4.0 || { \
			status=$$?; \
			echo "runtime shape $$shape failed with status $$status"; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			exit $$status; \
		}; \
	done

.PHONY: vice-action-actc-alink-launch-math-runtime-matrix
vice-action-actc-alink-launch-math-runtime-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	for shape in $(ACTION_ACTC_ALINK_MATH_RUNTIME_SHAPES); do \
		echo "=== $$shape ==="; \
		timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) --shape "$$shape" --attempts $(ACTION_ACTC_ALINK_PROBE_ATTEMPTS) --attempt-delay 4.0 || { \
			status=$$?; \
			echo "runtime shape $$shape failed with status $$status"; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			exit $$status; \
		}; \
	done

.PHONY: vice-action-actc-alink-launch-gfx-runtime-matrix
vice-action-actc-alink-launch-gfx-runtime-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	for shape in $(ACTION_ACTC_ALINK_GFX_RUNTIME_SHAPES); do \
		echo "=== $$shape ==="; \
		timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) --shape "$$shape" --attempts $(ACTION_ACTC_ALINK_PROBE_ATTEMPTS) --attempt-delay 4.0 || { \
			status=$$?; \
			echo "runtime shape $$shape failed with status $$status"; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			exit $$status; \
		}; \
	done

.PHONY: vice-action-actc-alink-launch-variable-gfx-runtime-matrix
vice-action-actc-alink-launch-variable-gfx-runtime-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	for shape in $(ACTION_ACTC_ALINK_VARIABLE_GFX_RUNTIME_SHAPES); do \
		echo "=== $$shape ==="; \
		timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) --shape "$$shape" --attempts $(ACTION_ACTC_ALINK_PROBE_ATTEMPTS) --attempt-delay 4.0 || { \
			status=$$?; \
			echo "runtime shape $$shape failed with status $$status"; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			exit $$status; \
		}; \
	done

.PHONY: vice-action-actc-alink-launch-sid-runtime-matrix
vice-action-actc-alink-launch-sid-runtime-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	for shape in $(ACTION_ACTC_ALINK_SID_RUNTIME_SHAPES); do \
		echo "=== $$shape ==="; \
		timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) --shape "$$shape" --attempts $(ACTION_ACTC_ALINK_PROBE_ATTEMPTS) --attempt-delay 4.0 || { \
			status=$$?; \
			echo "runtime shape $$shape failed with status $$status"; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			exit $$status; \
		}; \
	done

.PHONY: vice-action-actc-alink-launch-variable-sid-runtime-matrix
vice-action-actc-alink-launch-variable-sid-runtime-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	for shape in $(ACTION_ACTC_ALINK_VARIABLE_SID_RUNTIME_SHAPES); do \
		echo "=== $$shape ==="; \
		timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) --shape "$$shape" --attempts $(ACTION_ACTC_ALINK_PROBE_ATTEMPTS) --attempt-delay 4.0 || { \
			status=$$?; \
			echo "runtime shape $$shape failed with status $$status"; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			exit $$status; \
		}; \
	done

.PHONY: vice-action-actc-alink-launch-sprite-runtime-matrix
vice-action-actc-alink-launch-sprite-runtime-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	for shape in $(ACTION_ACTC_ALINK_SPRITE_RUNTIME_SHAPES); do \
		echo "=== $$shape ==="; \
		timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) --shape "$$shape" --attempts $(ACTION_ACTC_ALINK_PROBE_ATTEMPTS) --attempt-delay 4.0 || { \
			status=$$?; \
			echo "runtime shape $$shape failed with status $$status"; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			exit $$status; \
		}; \
	done

.PHONY: vice-action-actc-alink-launch-variable-sprite-runtime-matrix
vice-action-actc-alink-launch-variable-sprite-runtime-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	for shape in $(ACTION_ACTC_ALINK_VARIABLE_SPRITE_RUNTIME_SHAPES); do \
		echo "=== $$shape ==="; \
		timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) --shape "$$shape" --attempts $(ACTION_ACTC_ALINK_PROBE_ATTEMPTS) --attempt-delay 4.0 || { \
			status=$$?; \
			echo "runtime shape $$shape failed with status $$status"; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			exit $$status; \
		}; \
	done

.PHONY: vice-action-actc-alink-launch-input-runtime-matrix
vice-action-actc-alink-launch-input-runtime-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	for shape in $(ACTION_ACTC_ALINK_INPUT_RUNTIME_SHAPES); do \
		echo "=== $$shape ==="; \
		timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) --shape "$$shape" --attempts $(ACTION_ACTC_ALINK_INPUT_PROBE_ATTEMPTS) --attempt-delay 4.0 || { \
			status=$$?; \
			echo "runtime shape $$shape failed with status $$status"; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			exit $$status; \
		}; \
	done

.PHONY: vice-action-actc-alink-launch-dbf-runtime-matrix
vice-action-actc-alink-launch-dbf-runtime-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	for shape in $(ACTION_ACTC_ALINK_DBF_RUNTIME_SHAPES); do \
		echo "=== $$shape ==="; \
		timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) --shape "$$shape" --attempts $(ACTION_ACTC_ALINK_PROBE_ATTEMPTS) --attempt-delay 4.0 || { \
			status=$$?; \
			echo "runtime shape $$shape failed with status $$status"; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			exit $$status; \
		}; \
	done

.PHONY: vice-action-actc-alink-launch-input1-demo
vice-action-actc-alink-launch-input1-demo: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	$(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) \
		--shape actc_runtime_input1_export_sample_linked --source-from /IMAGES/ACTION.DNP/SRC/INPUT1_DEMO.ACT

.PHONY: vice-action-actc-alink-launch-dbf1-demo
vice-action-actc-alink-launch-dbf1-demo: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	$(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) \
		--shape actc_runtime_dbf1_export_sample_linked --source-from /IMAGES/ACTION.DNP/SRC/DBF1_DEMO.ACT

.PHONY: vice-action-actc-alink-launch-gfx1-demo
vice-action-actc-alink-launch-gfx1-demo: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	$(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) \
		--shape actc_runtime_gfx1_export_sample_linked --source-from /IMAGES/ACTION.DNP/SRC/GFX1_DEMO.ACT

.PHONY: vice-action-actc-alink-launch-math1-demo
vice-action-actc-alink-launch-math1-demo: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	$(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) \
		--shape actc_runtime_math1_export_sample_linked --source-from /IMAGES/ACTION.DNP/SRC/MATH1_DEMO.ACT

.PHONY: vice-action-actc-alink-launch-sidspr1-demo
vice-action-actc-alink-launch-sidspr1-demo: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	$(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) \
		--shape actc_runtime_sidspr1_export_sample_linked --source-from /IMAGES/ACTION.DNP/SRC/SIDSPR1_DEMO.ACT

.PHONY: vice-action-actc-alink-launch-helper-demos
vice-action-actc-alink-launch-helper-demos:
	$(MAKE) vice-action-actc-alink-launch-input1-demo
	$(MAKE) vice-action-actc-alink-launch-dbf1-demo
	$(MAKE) vice-action-actc-alink-launch-gfx1-demo
	$(MAKE) vice-action-actc-alink-launch-math1-demo
	$(MAKE) vice-action-actc-alink-launch-sidspr1-demo

.PHONY: vice-action-actc-alink-launch-misc-runtime-matrix
vice-action-actc-alink-launch-misc-runtime-matrix: $(RELEASE_DEPS)
	bash $(ACTIONC64U_DIR)/tools/build_tool_abi_harness.sh
	bash $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
	bash $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_LAUNCH_FS)
	mkdir -p $(ACTION_ACTC_ALINK_LAUNCH_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_LAUNCH_FS)/
	for shape in $(ACTION_ACTC_ALINK_MISC_RUNTIME_SHAPES); do \
		echo "=== $$shape ==="; \
		timeout $(ACTION_ACTC_ALINK_PROBE_TIMEOUT) $(PYTHON) tools/run_action_actc_alink_launch_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_LAUNCH_FS) --shape "$$shape" --attempts $(ACTION_ACTC_ALINK_PROBE_ATTEMPTS) --attempt-delay 4.0 || { \
			status=$$?; \
			echo "runtime shape $$shape failed with status $$status"; \
			PYTHONPATH=tools $(PYTHON) -c 'import vice_prg_probe as vp; vp.cleanup_stale_vice(settle_seconds=1.0)' || true; \
			exit $$status; \
		}; \
	done

vice-action-actchk: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTCHK_FS)
	mkdir -p $(ACTION_ACTCHK_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTCHK_FS)/
	rm -rf $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/src \
		$(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/bin \
		$(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	printf 'ACTION PROJECT READY\n' > $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/readme.txt
	printf 'ACTION PROJECT\rMAIN.ACT\rHELPER.ACT\r' > $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	printf 'D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF ACTCHK.PRG\nF README.TXT\n' > $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/UDOSDIR.TXT
	printf 'F MAIN.ACT\nF HELPER.ACT\n' > $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/src/UDOSDIR.TXT
	printf '' > $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/bin/UDOSDIR.TXT
	printf '' > $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/obj/UDOSDIR.TXT
	printf 'PROC MAIN()\rENDPROC\r' > $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/src/main.act
	printf 'PROC HELPER()\rENDPROC\r' > $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	cp $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/ACTCHK.PRG $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/ACTCHK.PRG
	ln -s PROJ3 $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/proj3
	ln -s ACTCHK.PRG $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/actchk.prg
	ln -s ACTION.PROJ $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/action.proj
	ln -s UDOSDIR.TXT $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/udosdir.txt
	ln -s src $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/SRC
	ln -s bin $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/BIN
	ln -s obj $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/OBJ
	ln -s UDOSDIR.TXT $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/src/udosdir.txt
	ln -s main.act $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/src/MAIN.ACT
	ln -s helper.act $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/src/HELPER.ACT
	ln -s UDOSDIR.TXT $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/bin/udosdir.txt
	ln -s UDOSDIR.TXT $(ACTION_ACTCHK_FS)/IMAGES/ACTION.DNP/PROJ3/obj/udosdir.txt
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTCHK_FS) \
		--command "ACTCHK" --run-marker "RUN ACTCHK.PRG" --done-fragment "ACTCHK OK" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--attempts 8 --attempt-delay 4.0 \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--contains "RUN ACTCHK.PRG" --contains "PROJECT YES" --contains "SRC YES" \
		--contains "BIN YES" --contains "OBJ YES" --contains "MODULES 2" \
		--contains "MISSING 0" --contains "ACTCHK OK"

vice-action-actmon-check: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTMON_FS)
	mkdir -p $(ACTION_ACTMON_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTMON_FS)/
	sleep 2
	$(PYTHON) tools/run_action_actmon_check_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTMON_FS) \
		--attempts 6 --attempt-delay 2.0

vice-action-actmon: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTMON_FS)
	mkdir -p $(ACTION_ACTMON_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTMON_FS)/
	sleep 2
	$(PYTHON) tools/run_action_actmon_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTMON_FS) \
		--attempts 4 --attempt-delay 2.0

vice-action-actinfo: $(RELEASE_DEPS)
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--command "ACTINFO ONE TWO" --run-marker "RUN ACTINFO.PRG" --done-fragment "ACTINFO DONE" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/>" \
		--attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTINFO.PRG" --contains "ACTINFO ABI 1" --contains "ARGS ONE TWO" --contains "ACTINFO DONE"

vice-action-actflow: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTFLOW_FS)
	mkdir -p $(ACTION_ACTFLOW_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTFLOW_FS)/
	rm -rf $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3
	printf 'D PROJ3\n' > $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/UDOSDIR.TXT
	printf 'F ACTWRITE.PRG\nF ACTCOPY.PRG\nF ACTMOVE.PRG\nF ACTDEL.PRG\n' > $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/UDOSDIR.TXT
	cp $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/ACTWRITE.PRG $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/ACTWRITE.PRG
	cp $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/ACTCOPY.PRG $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/ACTCOPY.PRG
	cp $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/ACTMOVE.PRG $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/ACTMOVE.PRG
	cp $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/ACTDEL.PRG $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/ACTDEL.PRG
	ln -s PROJ3 $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/proj3
	ln -s UDOSDIR.TXT $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/udosdir.txt
	ln -s ACTWRITE.PRG $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/actwrite.prg
	ln -s ACTCOPY.PRG $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/actcopy.prg
	ln -s ACTMOVE.PRG $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/actmove.prg
	ln -s ACTDEL.PRG $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/actdel.prg
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTFLOW_FS) \
		--command "ACTWRITE OUT.TXT" --run-marker "RUN ACTWRITE.PRG" --done-fragment "ACTWRITE OK" --prompt-count 2 \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTWRITE.PRG" \
		--contains "ACTWRITE OK"
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTFLOW_FS) \
		--command "ACTCOPY OUT.TXT COPY.TXT" --run-marker "RUN ACTCOPY.PRG" --done-fragment "" --prompt-count 1 \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTCOPY.PRG" \
		--not-contains "COPY FAIL"
	grep -Fq 'ACTION WRITE OK' $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/COPY.TXT
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTFLOW_FS) \
		--command "ACTMOVE COPY.TXT NEXT.TXT" --run-marker "RUN ACTMOVE.PRG" --done-fragment "" \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--attempts 4 --attempt-delay 2.0 --shell-timeout 20 \
		--contains "RUN ACTMOVE.PRG"
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTFLOW_FS) \
		--command "ACTDEL NEXT.TXT" --run-marker "RUN ACTDEL.PRG" --done-fragment "ACTDEL OK" --prompt-count 2 \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--attempts 4 --attempt-delay 2.0 \
		--post-command "TYPE NEXT.TXT" --post-done-fragment "NO SUCH FILE" \
		--contains "RUN ACTDEL.PRG" \
		--contains "ACTDEL OK" \
		--contains "NO SUCH FILE"
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTFLOW_FS) \
		--command "ECHO ACTFLOW OK" --run-marker "" --done-fragment "ACTFLOW OK" --prompt-count 2 \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--attempts 4 --attempt-delay 2.0 \
		--contains "ACTFLOW OK"
	grep -Fq 'ACTION WRITE OK' $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/OUT.TXT
	test ! -e $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/COPY.TXT
	test ! -e $(ACTION_ACTFLOW_FS)/IMAGES/ACTION.DNP/PROJ3/NEXT.TXT

vice-action-actcopy: $(RELEASE_DEPS)
	sleep 2
	rm -rf $(ACTION_ACTCOPY_FS)
	mkdir -p $(ACTION_ACTCOPY_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTCOPY_FS)/
	rm -rf $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/PROJ3
	printf 'D PROJ3\n' > $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/UDOSDIR.TXT
	printf 'F ACTWRITE.PRG\nF ACTCOPY.PRG\n' > $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/PROJ3/UDOSDIR.TXT
	cp $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/ACTWRITE.PRG $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/PROJ3/ACTWRITE.PRG
	cp $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/ACTCOPY.PRG $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/PROJ3/ACTCOPY.PRG
	ln -s PROJ3 $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/proj3
	ln -s UDOSDIR.TXT $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/PROJ3/udosdir.txt
	ln -s ACTWRITE.PRG $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/PROJ3/actwrite.prg
	ln -s ACTCOPY.PRG $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/PROJ3/actcopy.prg
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTCOPY_FS) \
		--command "ACTWRITE OUT.TXT" --run-marker "RUN ACTWRITE.PRG" --done-fragment "ACTWRITE OK" --prompt-count 2 \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--connect-delay 10.0 --attempts 4 --attempt-delay 3.0 \
		--contains "RUN ACTWRITE.PRG" \
		--contains "ACTWRITE OK"
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTCOPY_FS) \
		--command "ACTCOPY OUT.TXT COPY.TXT" --run-marker "RUN ACTCOPY.PRG" --done-fragment "" \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--attempts 4 --attempt-delay 3.0 --shell-timeout 60 \
		--contains "RUN ACTCOPY.PRG"
	grep -Fq 'ACTION WRITE OK' $(ACTION_ACTCOPY_FS)/IMAGES/ACTION.DNP/PROJ3/COPY.TXT

vice-action-copy-root: $(RELEASE_DEPS)
	rm -rf $(ACTION_COPY_ROOT_FS)
	mkdir -p $(ACTION_COPY_ROOT_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_COPY_ROOT_FS)/
	printf 'ACTION WRITE OK\n' > $(ACTION_COPY_ROOT_FS)/IMAGES/ACTION.DNP/OUT.TXT
	$(PYTHON) tools/vice_prg_probe.py --disk $(abspath $(RELEASE_DISK)) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(ACTION_COPY_ROOT_FS)) \
		--vice-arg=-fslongnames \
		--feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/ACTION.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "COPY OUT.TXT COPY2.TXT\r" \
		--feed-step "TYPE COPY2.TXT\r" \
		--expected "ACTION WRITE OK" --settle 2.0 --connect-delay 10.0 --timeout 25 --attempts 3 --attempt-delay 2.0
	grep -Fq 'ACTION WRITE OK' $(ACTION_COPY_ROOT_FS)/IMAGES/ACTION.DNP/COPY2.TXT

vice-action-actdel: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTDEL_FS)
	mkdir -p $(ACTION_ACTDEL_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTDEL_FS)/
	rm -rf $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/PROJ3
	printf 'D PROJ3\n' > $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/UDOSDIR.TXT
	printf 'F ACTWRITE.PRG\nF ACTDEL.PRG\n' > $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/PROJ3/UDOSDIR.TXT
	cp $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/ACTWRITE.PRG $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/PROJ3/ACTWRITE.PRG
	cp $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/ACTDEL.PRG $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/PROJ3/ACTDEL.PRG
	ln -s PROJ3 $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/proj3
	ln -s UDOSDIR.TXT $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/PROJ3/udosdir.txt
	ln -s ACTWRITE.PRG $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/PROJ3/actwrite.prg
	ln -s ACTDEL.PRG $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/PROJ3/actdel.prg
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTDEL_FS) \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--command "ACTWRITE OUT.TXT" --run-marker "RUN ACTWRITE.PRG" --done-fragment "ACTWRITE OK" --prompt-count 2 \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--contains "RUN ACTWRITE.PRG" \
		--contains "ACTWRITE OK"
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTDEL_FS) \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--command "ACTDEL OUT.TXT" --run-marker "RUN ACTDEL.PRG" --done-fragment "ACTDEL OK" --prompt-count 2 \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--contains "RUN ACTDEL.PRG" \
		--contains "ACTDEL OK"
	test ! -e $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/PROJ3/OUT.TXT
	! grep -q "OUT.TXT" $(ACTION_ACTDEL_FS)/IMAGES/ACTION.DNP/PROJ3/UDOSDIR.TXT

vice-action-actmkdir: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTMKDIR_FS)
	mkdir -p $(ACTION_ACTMKDIR_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTMKDIR_FS)/
	rm -rf $(ACTION_ACTMKDIR_FS)/IMAGES/ACTION.DNP/OBJ $(ACTION_ACTMKDIR_FS)/IMAGES/ACTION.DNP/obj
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTMKDIR_FS) \
		--command "ACTMKDIR OBJ" --run-marker "RUN ACTMKDIR.PRG" --done-fragment "ACTMKDIR OK" \
		--connect-delay 10.0 --attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTMKDIR.PRG" \
		--contains "ACTMKDIR OK"
	test -d $(ACTION_ACTMKDIR_FS)/IMAGES/ACTION.DNP/OBJ

vice-action-actmkdir-persist: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTMKDIR_PERSIST_FS)
	mkdir -p $(ACTION_ACTMKDIR_PERSIST_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTMKDIR_PERSIST_FS)/
	rm -rf $(ACTION_ACTMKDIR_PERSIST_FS)/IMAGES/ACTION.DNP/OBJ $(ACTION_ACTMKDIR_PERSIST_FS)/IMAGES/ACTION.DNP/obj
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTMKDIR_PERSIST_FS) \
		--command "ACTMKDIR OBJ" --run-marker "RUN ACTMKDIR.PRG" --done-fragment "ACTMKDIR OK" \
		--connect-delay 10.0 --attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTMKDIR.PRG" \
		--contains "ACTMKDIR OK"
	test -d $(ACTION_ACTMKDIR_PERSIST_FS)/IMAGES/ACTION.DNP/OBJ

vice-action-actmove: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTMOVE_FS)
	mkdir -p $(ACTION_ACTMOVE_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTMOVE_FS)/
	rm -rf $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/PROJ3
	printf 'D PROJ3\n' > $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/UDOSDIR.TXT
	printf 'F ACTWRITE.PRG\nF ACTMOVE.PRG\n' > $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/PROJ3/UDOSDIR.TXT
	cp $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/ACTWRITE.PRG $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/PROJ3/ACTWRITE.PRG
	cp $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/ACTMOVE.PRG $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/PROJ3/ACTMOVE.PRG
	ln -s PROJ3 $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/proj3
	ln -s UDOSDIR.TXT $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/PROJ3/udosdir.txt
	ln -s ACTWRITE.PRG $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/PROJ3/actwrite.prg
	ln -s ACTMOVE.PRG $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/PROJ3/actmove.prg
	sleep 2
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTMOVE_FS) \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--command "ACTWRITE OUT.TXT" --run-marker "RUN ACTWRITE.PRG" --done-fragment "ACTWRITE OK" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--connect-delay 10.0 --attempts 6 --attempt-delay 3.0 --shell-timeout 60 \
		--contains "RUN ACTWRITE.PRG" \
		--contains "ACTWRITE OK"
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTMOVE_FS) \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--command "ACTMOVE OUT.TXT NEXT.TXT" --run-marker "RUN ACTMOVE.PRG" --done-fragment "" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--connect-delay 10.0 --attempts 4 --attempt-delay 3.0 --shell-timeout 60 \
		--contains "RUN ACTMOVE.PRG"
	grep -Fq 'ACTION WRITE OK' $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/PROJ3/NEXT.TXT
	test ! -e $(ACTION_ACTMOVE_FS)/IMAGES/ACTION.DNP/PROJ3/OUT.TXT

vice-action-actmove-persist: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTMOVE_PERSIST_FS)
	mkdir -p $(ACTION_ACTMOVE_PERSIST_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTMOVE_PERSIST_FS)/
	rm -rf $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3
	printf 'D PROJ3\n' > $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/UDOSDIR.TXT
	printf 'F ACTWRITE.PRG\nF ACTMOVE.PRG\n' > $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/UDOSDIR.TXT
	cp $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/ACTWRITE.PRG $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/ACTWRITE.PRG
	cp $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/ACTMOVE.PRG $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/ACTMOVE.PRG
	ln -s PROJ3 $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/proj3
	ln -s UDOSDIR.TXT $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/udosdir.txt
	ln -s ACTWRITE.PRG $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/actwrite.prg
	ln -s ACTMOVE.PRG $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/actmove.prg
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTMOVE_PERSIST_FS) \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--command "ACTWRITE OUT.TXT" --run-marker "RUN ACTWRITE.PRG" --done-fragment "ACTWRITE OK" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--connect-delay 10.0 --attempts 4 --attempt-delay 3.0 --shell-timeout 30 \
		--contains "RUN ACTWRITE.PRG" \
		--contains "ACTWRITE OK"
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTMOVE_PERSIST_FS) \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--command "ACTMOVE OUT.TXT NEXT.TXT" --run-marker "RUN ACTMOVE.PRG" --done-fragment "" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--connect-delay 10.0 --attempts 4 --attempt-delay 3.0 --shell-timeout 30 \
		--contains "RUN ACTMOVE.PRG"
	grep -Fq 'ACTION WRITE OK' $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/NEXT.TXT
	test ! -e $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/OUT.TXT

vice-action-actrmdir: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTRMDIR_PERSIST_FS)
	mkdir -p $(ACTION_ACTRMDIR_PERSIST_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTRMDIR_PERSIST_FS)/
	rm -rf $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/TMPRMDIR $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/tmprmdir
	mkdir -p $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/TMPRMDIR
	printf 'D TMPRMDIR\n' >> $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/UDOSDIR.TXT
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTRMDIR_PERSIST_FS) \
		--command "ACTRMDIR TMPRMDIR" --run-marker "RUN ACTRMDIR.PRG" --done-fragment "ACTRMDIR OK" --skip-command-prompt \
		--contains "RUN ACTRMDIR.PRG" \
		--contains "ACTRMDIR OK"
	test ! -e $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/TMPRMDIR
	test ! -e $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/tmprmdir

vice-action-actrmdir-persist: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTRMDIR_PERSIST_FS)
	mkdir -p $(ACTION_ACTRMDIR_PERSIST_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTRMDIR_PERSIST_FS)/
	rm -rf $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/TMPRMDIR $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/tmprmdir
	mkdir -p $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/TMPRMDIR
	printf 'D TMPRMDIR\n' >> $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/UDOSDIR.TXT
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTRMDIR_PERSIST_FS) \
		--command "ACTRMDIR TMPRMDIR" --run-marker "RUN ACTRMDIR.PRG" --done-fragment "ACTRMDIR OK" --skip-command-prompt \
		--contains "RUN ACTRMDIR.PRG" \
		--contains "ACTRMDIR OK"
	test ! -e $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/TMPRMDIR
	test ! -e $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/tmprmdir

vice-action-actwrite: $(RELEASE_DEPS)
	rm -rf $(ACTION_ACTWRITE_FS)
	mkdir -p $(ACTION_ACTWRITE_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTWRITE_FS)/
	rm -f $(ACTION_ACTWRITE_FS)/IMAGES/ACTION.DNP/OUT.TXT
	$(PYTHON) tools/run_action_command_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTWRITE_FS) \
		--command "ACTWRITE OUT.TXT" --run-marker "RUN ACTWRITE.PRG" --done-fragment "ACTWRITE OK" \
		--attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTWRITE.PRG" \
		--contains "ACTWRITE OK"
	grep -Fq 'ACTION WRITE OK' $(ACTION_ACTWRITE_FS)/IMAGES/ACTION.DNP/OUT.TXT

vice-resident: $(RESIDENT_DEPS)
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--expected "A:D64/>" --settle 1.0 --absent "AUTOEXEC OK"

$(VICE_LAUNCH_FS): force $(RETURN_TEST_PRG) $(CLOBBER_TEST_PRG)
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $(VICE_LAUNCH_FS)
	rm -f $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/result.txt
	grep -v 'RESULT.TXT\|RETTEST.PRG\|CLOBBER.PRG' $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/UDOSDIR.TXT > $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/udosdir.base
	cp $(RETURN_TEST_PRG) $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/rettest.prg
	cp $(CLOBBER_TEST_PRG) $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/clobber.prg
	{ \
		printf 'F CLOBBER.PRG\n'; \
		printf 'F RETTEST.PRG\n'; \
		cat $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/udosdir.base; \
	} > $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/UDOSDIR.TXT
	cp $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/UDOSDIR.TXT $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/udosdir.txt
	rm -f $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/udosdir.base

$(VICE_REU_SERVICE_FS): force $(REU_SERVICE_TEST_PRG)
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $(VICE_REU_SERVICE_FS)
	grep -v 'REUTEST.PRG\|REU_STG.TXT' $(VICE_REU_SERVICE_FS)/IMAGES/WORK.DNP/SRC/UDOSDIR.TXT > $(VICE_REU_SERVICE_FS)/IMAGES/WORK.DNP/SRC/udosdir.base
	cp $(REU_SERVICE_TEST_PRG) $(VICE_REU_SERVICE_FS)/IMAGES/WORK.DNP/SRC/reutest.prg
	$(PYTHON) -c "from pathlib import Path; Path('$(VICE_REU_SERVICE_FS)/IMAGES/WORK.DNP/SRC/reu_stg.txt').write_bytes(bytes(65 + (i % 26) for i in range(600)))"
	{ \
		printf 'F REUTEST.PRG\n'; \
		printf 'F REU_STG.TXT\n'; \
		cat $(VICE_REU_SERVICE_FS)/IMAGES/WORK.DNP/SRC/udosdir.base; \
	} > $(VICE_REU_SERVICE_FS)/IMAGES/WORK.DNP/SRC/UDOSDIR.TXT
	cp $(VICE_REU_SERVICE_FS)/IMAGES/WORK.DNP/SRC/UDOSDIR.TXT $(VICE_REU_SERVICE_FS)/IMAGES/WORK.DNP/SRC/udosdir.txt
	rm -f $(VICE_REU_SERVICE_FS)/IMAGES/WORK.DNP/SRC/udosdir.base

$(VICE_TREE_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $(VICE_TREE_FS)

$(VICE_TREE_COPY_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $(VICE_TREE_COPY_FS)

$(VICE_TREE_WILD_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $(VICE_TREE_WILD_FS)

vice-launch: $(RESIDENT_DEPS) $(VICE_LAUNCH_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(abspath $(RESIDENT_DISK)) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(abspath $(BUILD_DIR)) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(VICE_LAUNCH_FS)) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.5 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "RETTEST DIR\r" \
		--timeout 120 --attempts 2 --attempt-delay 2.0 \
		--expected "B:DNP/SRC>" --contains "RUN RETTEST.PRG" --contains "ARGS DIR" \
		--check-byte 0xCFF6=0x02 --check-byte 0xCFF7=0x42

vice-clobber: $(RESIDENT_DEPS) $(VICE_LAUNCH_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(abspath $(RESIDENT_DISK)) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(abspath $(BUILD_DIR)) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(VICE_LAUNCH_FS)) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.5 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "CLOBBER DIR\r" \
		--timeout 120 --attempts 2 --attempt-delay 2.0 \
		--expected "B:DNP/SRC>" --contains "RUN CLOBBER.PRG" --contains "ARGS DIR" \
		--check-byte 0xCFF6=0x02 --check-byte 0xCFF7=0x24

vice-reu-services: $(RESIDENT_DEPS) $(VICE_REU_SERVICE_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(abspath $(RESIDENT_DISK)) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(abspath $(BUILD_DIR)) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(VICE_REU_SERVICE_FS)) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "REUTEST\r" \
		--timeout 120 --attempts 3 --attempt-delay 2.0 \
		--expected "B:DNP/SRC>" --contains "RUN REUTEST.PRG" --contains "REU OK"

vice-copy: $(RESIDENT_DEPS) $(VICE_TREE_COPY_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_COPY_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.5 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "COPY *.* /WORK\r" \
		--feed-step "CD /WORK\r" \
		--feed-step-after "B:WORK DNP" \
		--feed-step-after "B:DNP/>" \
		--feed-step-after "B:DNP/SRC" \
		--feed-step-after "COPIED" \
		--feed-step-after "B:DNP/WORK>" \
		--feed-step-after-settle 0.5 \
		--timeout 240 --attempts 4 --attempt-delay 3.0 \
		--expected "B:DNP/WORK>" --contains "COPIED"
	test -f $(VICE_TREE_COPY_FS)/IMAGES/WORK.DNP/WORK/BOOT.ASM
	test -f $(VICE_TREE_COPY_FS)/IMAGES/WORK.DNP/WORK/HELLO.PRG

vice-drive: $(RESIDENT_DEPS)
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--feed-after "A:D64/>" --feed-text "C:\rD:\r" \
		--expected "DRIVE NOT PRESENT" --contains "DRIVE NOT PRESENT"

vice-real-read: $(RESIDENT_DEPS) $(VICE_TREE_FS)
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "VOL\r" \
		--feed-step "B:\r" \
		--feed-step "DIR\r" \
		--feed-step "CD SRC\r" \
		--feed-step "DIR\r" \
		--feed-step "TYPE BOOT.ASM\r" \
		--expected "; BOOT.ASM VICE BACKEND SOURCE" --contains "A:SYSTEM D64 B:WORK DNP" --contains "BIN/ SRC/ WORK/" \
		--contains "BOOT.ASM" \
		--connect-delay 10.0 --attempts 4 --attempt-delay 3.0 \
		--check-byte 0xCFF0=0x01 --check-byte 0xCFEC=0x01 --check-byte 0xCFEE=0x02 --check-byte 0xCFF2=0x04

vice-real-tree-write: $(RESIDENT_DEPS) $(VICE_TREE_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "DEL /WORK/BOOT2.ASM\r" \
		--feed-step "DEL /WORK/BOOT3.PRG\r" \
		--feed-step "CD SRC\r" \
		--feed-step "COPY BOOT.ASM /WORK/BOOT2.ASM\r" \
		--feed-step "CD /WORK\r" \
		--feed-step "REN BOOT2.ASM BOOT3.PRG\r" \
		--feed-step "DEL BOOT3.PRG\r" \
		--feed-step "TYPE BOOT3.PRG\r" \
		--feed-step-after "B:WORK DNP" \
		--feed-step-after "B:DNP/>" \
		--feed-step-after "B:DNP/>" \
		--feed-step-after "B:DNP/>" \
		--feed-step-after "B:DNP/SRC" \
		--feed-step-after "COPIED" \
		--feed-step-after "B:DNP/WORK" \
		--feed-step-after "RENAMED" \
		--feed-step-after "DELETED" \
		--feed-step-after "NO SUCH FILE" \
		--feed-step-after-settle 0.5 \
		--connect-delay 10.0 --timeout 180 --attempts 4 --attempt-delay 3.0 \
		--expected "NO SUCH FILE" --contains "COPIED" --contains "RENAMED" --contains "DELETED"

vice-real-tree-rename: $(RESIDENT_DEPS) $(VICE_TREE_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.5 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "REN HELLO.PRG HELLO2.PRG\r" \
		--feed-step "TYPE HELLO2.PRG\r" \
		--feed-step "TYPE HELLO.PRG\r" \
		--connect-delay 10.0 --timeout 120 --attempts 4 --attempt-delay 3.0 \
		--expected "NO SUCH FILE" --contains "RENAMED" --contains "HELLO PROGRAM IMAGE"

vice-real-tree-wild-copy: $(RESIDENT_DEPS) $(VICE_TREE_WILD_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_WILD_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.5 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "COPY *.* /WORK\r" \
		--feed-step "CD /WORK\r" \
		--feed-step-after "B:WORK DNP" \
		--feed-step-after "B:DNP/>" \
		--feed-step-after "B:DNP/SRC" \
		--feed-step-after "COPIED" \
		--feed-step-after "B:DNP/WORK>" \
		--feed-step-after-settle 0.5 \
		--timeout 240 --attempts 4 --attempt-delay 3.0 \
		--expected "B:DNP/WORK>" --contains "COPIED"
	test -f $(VICE_TREE_WILD_FS)/IMAGES/WORK.DNP/WORK/BOOT.ASM
	test -f $(VICE_TREE_WILD_FS)/IMAGES/WORK.DNP/WORK/HELLO.PRG

vice-real-tree-wild-delete: $(RESIDENT_DEPS) $(VICE_TREE_WILD_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_WILD_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.5 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "DEL *.PRG\r" \
		--feed-step "DIR\r" \
		--timeout 120 --attempts 2 --attempt-delay 2.0 \
		--expected "B:DNP/SRC" --absent "HELLO.PRG"
	test ! -f $(VICE_TREE_WILD_FS)/IMAGES/WORK.DNP/SRC/HELLO.PRG

vice-real-tree-wild: vice-real-tree-wild-copy vice-real-tree-wild-delete

vice-real-tree-dir: $(RESIDENT_DEPS) $(VICE_TREE_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "MD NEW\r" \
		--feed-step "CD NEW\r" \
		--feed-step "CD /\r" \
		--feed-step "RD NEW\r" \
		--feed-step "CD NEW\r" \
		--feed-step-after "B:WORK DNP" \
		--feed-step-after "B:DNP/>" \
		--feed-step-after "CREATED" \
		--feed-step-after "B:DNP/NEW" \
		--feed-step-after "B:DNP/>" \
		--feed-step-after "REMOVED" \
		--feed-step-after "NO SUCH DIR" \
		--feed-step-after-settle 0.5 \
		--connect-delay 10.0 --timeout 120 --attempts 4 --attempt-delay 3.0 \
		--expected "NO SUCH DIR" --contains "CREATED" --contains "B:DNP/NEW" --contains "REMOVED"

vice-real-tree-rmdir: $(RESIDENT_DEPS) $(VICE_TREE_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "RD SRC\r" \
		--timeout 120 --attempts 2 --attempt-delay 2.0 \
		--expected "DIR NOT EMPTY"

vice-batch-args: $(RESIDENT_DEPS) $(VICE_TREE_FS)
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "ARGS ONE TWO THREE\r" \
		--connect-delay 10 --timeout 120 --attempts 2 --attempt-delay 2.0 \
		--expected "ONE/TWO/THREE" --contains "ECHO ONE/TWO/THREE"

vice-batch-stop: $(RESIDENT_DEPS) $(VICE_TREE_FS)
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(abspath $(BUILD_DIR)) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(VICE_TREE_FS)) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "STOP\r" \
		--connect-delay 10 --timeout 120 --attempts 4 --attempt-delay 3.0 \
		--expected "NO SUCH FILE" --contains "BEFORE" --absent "AFTER"

vice-autoexec:
	@echo "vice-autoexec retired: embedded resident AUTOEXEC.BAT is disabled to keep the resident image within memory."

$(SELFTEST_READ_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_COPY_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_RENAME_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_DELETE_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_DIR_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_BATCH_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_STOP_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_LAUNCH_FS): force $(RETURN_TEST_PRG)
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@
	grep -v 'RETTEST.PRG' $@/IMAGES/WORK.DNP/SRC/UDOSDIR.TXT > $@/IMAGES/WORK.DNP/SRC/udosdir.base
	cp $(RETURN_TEST_PRG) $@/IMAGES/WORK.DNP/SRC/rettest.prg
	{ \
		printf 'F RETTEST.PRG\n'; \
		cat $@/IMAGES/WORK.DNP/SRC/udosdir.base; \
	} > $@/IMAGES/WORK.DNP/SRC/UDOSDIR.TXT
	cp $@/IMAGES/WORK.DNP/SRC/UDOSDIR.TXT $@/IMAGES/WORK.DNP/SRC/udosdir.txt
	rm -f $@/IMAGES/WORK.DNP/SRC/udosdir.base

vice-selftest-read: $(SELFTEST_READ_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_READ_BUILD) RESIDENT_DEFINES="-D UDOS_INCLUDE_AUTOEXEC=0" resident
	cp $(SELFTEST_READ_BUILD)/udos-resident.d64 $(SELFTEST_READ_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(abspath $(SELFTEST_READ_ARTIFACT)) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(abspath $(SELFTEST_READ_BUILD)) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(SELFTEST_READ_FS)) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "DIR\r" \
		--feed-step "CD SRC\r" \
		--feed-step "TYPE BOOT.ASM\r" \
		--feed-step "ECHO READ OK\r" \
		--expected "READ OK" --settle 2.0 --connect-delay 10.0 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_READ_ACTUAL)
	diff -u $(SELFTEST_READ_EXPECTED) $(SELFTEST_READ_ACTUAL)

vice-selftest-copy: $(SELFTEST_COPY_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_COPY_BUILD) RESIDENT_DEFINES="-D UDOS_INCLUDE_AUTOEXEC=0" resident
	cp $(SELFTEST_COPY_BUILD)/udos-resident.d64 $(SELFTEST_COPY_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(abspath $(SELFTEST_COPY_ARTIFACT)) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(abspath $(SELFTEST_COPY_BUILD)) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(SELFTEST_COPY_FS)) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "COPY HELLO.PRG /WORK/HELLO2.PRG\r" \
		--feed-step "ECHO COPY OK\r" \
		--expected "COPY OK" --settle 2.0 --connect-delay 10.0 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_COPY_ACTUAL)
	diff -u $(SELFTEST_COPY_EXPECTED) $(SELFTEST_COPY_ACTUAL)

vice-selftest-rename: $(SELFTEST_RENAME_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_RENAME_BUILD) RESIDENT_DEFINES="-D UDOS_INCLUDE_AUTOEXEC=0" resident
	cp $(SELFTEST_RENAME_BUILD)/udos-resident.d64 $(SELFTEST_RENAME_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(abspath $(SELFTEST_RENAME_ARTIFACT)) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(abspath $(SELFTEST_RENAME_BUILD)) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(SELFTEST_RENAME_FS)) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step-after "b:work dnp" \
		--feed-step "B:\r" \
		--feed-step-after "b:dnp/" \
		--feed-step "CD SRC\r" \
		--feed-step-after "b:dnp/src" \
		--feed-step "COPY HELLO.PRG /WORK/HELLO2.PRG\r" \
		--feed-step-after "copied" \
		--feed-step "CD /WORK\r" \
		--feed-step-after "b:dnp/work" \
		--feed-step "REN HELLO2.PRG HELLO3.PRG\r" \
		--feed-step-after "renamed" \
		--feed-step "ECHO RENAME OK\r" \
		--expected "RENAME OK" --settle 2.0 --timeout 180 --connect-delay 10.0 --attempts $(SELFTEST_ATTEMPTS) --attempt-delay 3.0 --output $(SELFTEST_RENAME_ACTUAL)
	diff -u $(SELFTEST_RENAME_EXPECTED) $(SELFTEST_RENAME_ACTUAL)

vice-selftest-delete: $(SELFTEST_DELETE_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_DELETE_BUILD) RESIDENT_DEFINES="-D UDOS_INCLUDE_AUTOEXEC=0" resident
	cp $(SELFTEST_DELETE_BUILD)/udos-resident.d64 $(SELFTEST_DELETE_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(abspath $(SELFTEST_DELETE_ARTIFACT)) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(abspath $(SELFTEST_DELETE_BUILD)) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(SELFTEST_DELETE_FS)) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step-after "b:work dnp" \
		--feed-step "B:\r" \
		--feed-step-after "b:dnp/" \
		--feed-step "CD SRC\r" \
		--feed-step-after "b:dnp/src" \
		--feed-step "COPY HELLO.PRG /WORK/HELLO2.PRG\r" \
		--feed-step-after "copied" \
		--feed-step "CD /WORK\r" \
		--feed-step-after "b:dnp/work" \
		--feed-step "DEL HELLO2.PRG\r" \
		--feed-step-after "deleted" \
		--feed-step "DIR\r" \
		--feed-step "ECHO DELETE OK\r" \
		--expected "DELETE OK" --settle 2.0 --timeout 180 --connect-delay 10.0 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_DELETE_ACTUAL)
	diff -u $(SELFTEST_DELETE_EXPECTED) $(SELFTEST_DELETE_ACTUAL)

vice-selftest-dir: $(SELFTEST_DIR_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_DIR_BUILD) RESIDENT_DEFINES="-D UDOS_INCLUDE_AUTOEXEC=0" resident
	cp $(SELFTEST_DIR_BUILD)/udos-resident.d64 $(SELFTEST_DIR_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(abspath $(SELFTEST_DIR_ARTIFACT)) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(abspath $(SELFTEST_DIR_BUILD)) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(SELFTEST_DIR_FS)) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "MD NEW\r" \
		--feed-step "CD NEW\r" \
		--feed-step "CD /\r" \
		--feed-step "RD NEW\r" \
		--feed-step "ECHO DIR OK\r" \
		--expected "DIR OK" --settle 2.0 --connect-delay 10.0 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_DIR_ACTUAL)
	diff -u $(SELFTEST_DIR_EXPECTED) $(SELFTEST_DIR_ACTUAL)

vice-selftest-batch: $(SELFTEST_BATCH_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_BATCH_BUILD) resident
	cp $(SELFTEST_BATCH_BUILD)/udos-resident.d64 $(SELFTEST_BATCH_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(abspath $(SELFTEST_BATCH_ARTIFACT)) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(abspath $(SELFTEST_BATCH_BUILD)) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(SELFTEST_BATCH_FS)) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "ARGS ONE TWO THREE\r" \
		--expected "ONE/TWO/THREE" --settle 2.0 --timeout 120 --connect-delay 10.0 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_BATCH_ACTUAL)
	diff -u $(SELFTEST_BATCH_EXPECTED) $(SELFTEST_BATCH_ACTUAL)

vice-selftest-stop: $(SELFTEST_STOP_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_STOP_BUILD) resident
	cp $(SELFTEST_STOP_BUILD)/udos-resident.d64 $(SELFTEST_STOP_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(abspath $(SELFTEST_STOP_ARTIFACT)) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(abspath $(SELFTEST_STOP_BUILD)) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(SELFTEST_STOP_FS)) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "STOP\r" \
		--expected "NO SUCH FILE" --settle 2.0 --timeout 120 --connect-delay 10.0 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_STOP_ACTUAL)
	diff -u $(SELFTEST_STOP_EXPECTED) $(SELFTEST_STOP_ACTUAL)

vice-selftest-launch: $(SELFTEST_LAUNCH_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_LAUNCH_BUILD) resident
	cp $(SELFTEST_LAUNCH_BUILD)/udos-resident.d64 $(SELFTEST_LAUNCH_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(abspath $(SELFTEST_LAUNCH_ARTIFACT)) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(abspath $(SELFTEST_LAUNCH_BUILD)) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(SELFTEST_LAUNCH_FS)) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "RETTEST DIR\r" \
		--expected "ARGS DIR" --settle 2.0 --connect-delay 10.0 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_LAUNCH_ACTUAL)
	diff -u $(SELFTEST_LAUNCH_EXPECTED) $(SELFTEST_LAUNCH_ACTUAL)

vice-selftest:
	$(PYTHON) tools/run_selftests.py

test: vice-resident vice-drive vice-selftest vice-reu-services
