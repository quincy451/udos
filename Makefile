ACHERON_DIR := /mnt/c/test/action/acheronvm
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
SELFTEST_ATTEMPTS := 2
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
ACTION_ALINK_AVMRUN_BUILD := build/action-alink-avmrun
ACTION_ACTC_ALINK_AVMRUN_BUILD := build/action-actc-alink-avmrun
ACTION_ACTFILE_BUILD := build/action-actfile
ACTION_ACTSRC_BUILD := build/action-actsrc
ACTION_ACTWORK_BUILD := build/action-actwork
ACTION_ACTNEW_BUILD := build/action-actnew
ACTION_ACTNEW_PRG_PERSIST_BUILD := build/actnew-prg-persist
ACTION_ACTINFO_BUILD := build/action-actinfo
ACTION_ACTWRITE_BUILD := build/action-actwrite
ACTION_AVMINFO_BUILD := build/action-avminfo
ACTION_AVMRUN_BUILD := build/action-avmrun
ACTION_AVMRUN_FLOW_BUILD := build/action-avmrun-flow
ACTION_AVMRUN_RUNTIME_FS := build/action-avmrun-runtime-fs
ACTION_ACTSRC_FS := build/action-actsrc-fs
ACTION_ACTFILE_FS := build/action-actfile-fs
ACTION_ACTADD_FS := build/action-actadd-fs
ACTION_ACT2SAVE_FS := build/action-act2save-fs
ACTION_ACTC_FS := build/action-actc-fs
ACTION_ALINK_FS := build/action-alink-fs
ACTION_ALINK_AVMRUN_FS := build/action-alink-avmrun-fs
ACTION_ACTC_ALINK_AVMRUN_FS := build/action-actc-alink-avmrun-fs
ACTION_ACTCHK_FS := build/action-actchk-fs
ACTION_ACTMON_FS := build/action-actmon-fs
ACTION_ACTWORK_FS := build/action-actwork-fs
ACTION_ACTADD_PERSIST_FS := build/actadd-persist-fs
ACTION_ACTNEW_PRG_PERSIST_FS := build/actnew-prg-persist-fs
ACTION_ACTMKDIR_PERSIST_FS := build/action-actmkdir-persist-fs
ACTION_ACTMOVE_PERSIST_FS := build/action-actmove-persist-fs
ACTION_ACTRMDIR_PERSIST_FS := build/action-actrmdir-persist-fs
ACTION_WORKSPACE_ARTIFACT := build/udos-action-workspace.d64
ACTION_ACTDIR_ARTIFACT := build/udos-action-actdir.d64
ACTION_ACTADD_ARTIFACT := build/udos-action-actadd.d64
ACTION_ACTC_ARTIFACT := build/udos-action-actc.d64
ACTION_ALINK_ARTIFACT := build/udos-action-alink.d64
ACTION_ALINK_AVMRUN_ARTIFACT := build/udos-action-alink-avmrun.d64
ACTION_ACTFILE_ARTIFACT := build/udos-action-actfile.d64
ACTION_ACTSRC_ARTIFACT := build/udos-action-actsrc.d64
ACTION_ACTWORK_ARTIFACT := build/udos-action-actwork.d64
ACTION_ACTNEW_ARTIFACT := build/udos-action-actnew.d64
ACTION_ACTINFO_ARTIFACT := build/udos-action-actinfo.d64
ACTION_ACTWRITE_ARTIFACT := build/udos-action-actwrite.d64
ACTION_AVMINFO_ARTIFACT := build/udos-action-avminfo.d64
ACTION_AVMRUN_ARTIFACT := build/udos-action-avmrun.d64
ACTION_AVMRUN_FLOW_ARTIFACT := build/udos-action-avmrun-flow.d64

PROOF_OBJ := $(BUILD_DIR)/udos_proof.o
PROOF_PRG := $(BUILD_DIR)/udos-proof.prg
PROOF_AUTO_PRG := $(BUILD_DIR)/udosboot.prg
PROOF_DISK := $(BUILD_DIR)/udos-proof.d64
PROOF_LABELS := $(BUILD_DIR)/udos-proof.labels
PROOF_MAP := $(BUILD_DIR)/udos-proof.map

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
RETURN_TEST_PRG := $(BUILD_DIR)/RETTEST.PRG
CLOBBER_TEST_OBJ := $(BUILD_DIR)/udos_clobber_test.o
CLOBBER_TEST_BIN := $(BUILD_DIR)/udos_clobber_test.bin
CLOBBER_TEST_PRG := $(BUILD_DIR)/CLOBBER.PRG
RELEASE_BUILD := build/release
RELEASE_DISK := build/udos-release.d64
RELEASE_FS := build/udos-release-fs
ACTIONC64U_DIR := /mnt/c/test/action/actionc64u
ACTC_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actc_udos.sh
ALINK_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_alink_udos.sh
ACTMON_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actmon_udos.sh
ACTCHK_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actchk_udos.sh
ACTDIR_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actdir_udos.sh
ACTFILE_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actfile_udos.sh
ACTINFO_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actinfo_udos.sh
ACTSRC_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actsrc_udos.sh
ACTWORK_UDOS_BUILD := $(ACTIONC64U_DIR)/tools/build_actwork_udos.sh
ACTC_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTC.PRG
ALINK_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ALINK.PRG
ACTMON_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTMON.PRG
ACTCHK_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTCHK.PRG
ACTDIR_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTDIR.PRG
ACTFILE_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTFILE.PRG
ACTINFO_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTINFO.PRG
ACTSRC_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTSRC.PRG
ACTWORK_UDOS_PRG := $(ACTIONC64U_DIR)/build/udos_tools/ACTWORK.PRG

.PHONY: all clean acheron-dep force proof vice-proof resident release vice-release vice-action-workspace vice-action-actadd vice-action-actadd-persist vice-action-act2save vice-action-actc vice-action-alink vice-action-alink-avmrun vice-action-actc-alink-avmrun vice-action-actchk vice-action-actmon-check vice-action-actmon vice-action-actcopy vice-action-actdir vice-action-actfile vice-action-actflow vice-action-actinfo vice-action-actnew vice-action-actnew-prg vice-action-actnew-prg-persist vice-action-actdel vice-action-actmkdir vice-action-actmkdir-persist vice-action-actmove vice-action-actmove-persist vice-action-actrmdir vice-action-actrmdir-persist vice-action-actsrc vice-action-actwork vice-action-actwrite vice-action-avminfo vice-action-avmrun vice-action-avmrun-flow vice-action-avmrun-runtime vice-resident vice-launch vice-clobber vice-copy vice-drive vice-real-read vice-real-tree-write vice-real-tree-rename vice-real-tree-wild vice-real-tree-wild-copy vice-real-tree-wild-delete vice-real-tree-dir vice-real-tree-rmdir vice-batch-args vice-batch-stop vice-autoexec vice-selftest-read vice-selftest-copy vice-selftest-rename vice-selftest-delete vice-selftest-dir vice-selftest-batch vice-selftest-stop vice-selftest-launch vice-selftest test

all: proof resident

clean:
	rm -rf $(BUILD_DIR)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

acheron-dep:
	$(MAKE) -C $(ACHERON_DIR) acheron

force:

$(PROOF_OBJ): force $(ASM_DIR)/udos_proof.asm | $(BUILD_DIR)
	$(CA65) -g -o $@ $(ASM_DIR)/udos_proof.asm -I $(ACHERON_DIR)/bin -I $(ACHERON_DIR)/src

proof: acheron-dep $(PROOF_OBJ)
	$(LD65) -Ln $(PROOF_LABELS) -C $(ASM_DIR)/udos_c64.cfg -m $(PROOF_MAP) -o $(PROOF_PRG) $(PROOF_OBJ) $(ACHERON_DIR)/obj/acheron.o
	$(PYTHON) tools/make_basic_autostart.py --input $(PROOF_PRG) --labels $(PROOF_LABELS) --output $(PROOF_AUTO_PRG)
	$(C1541) -format "udos,01" d64 $(PROOF_DISK) -write $(PROOF_AUTO_PRG) udosboot

$(AUTOEXEC_INC): $(AUTOEXEC_SRC) | $(BUILD_DIR)
	$(PYTHON) tools/make_autoexec_include.py --input $< --output $@

$(RESIDENT_OBJ): force $(ASM_DIR)/udos_resident.asm $(AUTOEXEC_INC) | $(BUILD_DIR)
	$(CA65) -g $(RESIDENT_DEFINES) -o $@ $(ASM_DIR)/udos_resident.asm -I $(BUILD_DIR) -I $(ACHERON_DIR)/bin -I $(ACHERON_DIR)/src

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

resident: acheron-dep $(RESIDENT_OBJ) $(RESIDENT_BOOT_OBJ)
	$(LD65) -Ln $(RESIDENT_LABELS) -C $(ASM_DIR)/udos_c64.cfg -m $(RESIDENT_MAP) -o $(RESIDENT_PRG) $(RESIDENT_OBJ) $(ACHERON_DIR)/obj/acheron.o
	cp $(RESIDENT_PRG) $(RESIDENT_RAW)
	$(LD65) -Ln $(RESIDENT_BOOT_LABELS) -C $(ASM_DIR)/udos_boot.cfg -m $(RESIDENT_BOOT_MAP) -o $(RESIDENT_BOOT_PRG) $(RESIDENT_BOOT_OBJ)
	$(PYTHON) -c "from pathlib import Path; data=Path('$(RESIDENT_BOOT_PRG)').read_bytes(); Path('$(RESIDENT_BOOT_LOAD_PRG)').write_bytes(bytes((0x10,0x08))+data)"
	$(PYTHON) tools/make_basic_autostart.py --input $(RESIDENT_BOOT_LOAD_PRG) --labels $(RESIDENT_BOOT_LABELS) --output $(RESIDENT_AUTO_PRG) --expected-load-addr 0x0810
	$(C1541) -format "udos,01" d64 $(RESIDENT_DISK) -write $(RESIDENT_AUTO_PRG) udosboot -write $(RESIDENT_RAW) udoscore

release:
	$(MAKE) BUILD_DIR=$(RELEASE_BUILD) RESIDENT_DEFINES="-D UDOS_INCLUDE_AUTOEXEC=0" resident
	bash $(ACTC_UDOS_BUILD)
	bash $(ALINK_UDOS_BUILD)
	bash $(ACTMON_UDOS_BUILD)
	bash $(ACTCHK_UDOS_BUILD)
	bash $(ACTDIR_UDOS_BUILD)
	bash $(ACTFILE_UDOS_BUILD)
	bash $(ACTINFO_UDOS_BUILD)
	bash $(ACTSRC_UDOS_BUILD)
	bash $(ACTWORK_UDOS_BUILD)
	$(PYTHON) tools/prepare_release_fs.py --base $(VICE_FS_ROOT) --output $(RELEASE_FS)
	cp $(RELEASE_BUILD)/udos-resident.d64 $(RELEASE_DISK)
	-$(C1541) $(RELEASE_DISK) -delete ACTC.PRG
	-$(C1541) $(RELEASE_DISK) -delete ALINK.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTMON.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTCHK.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTDIR.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTFILE.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTINFO.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTSRC.PRG
	-$(C1541) $(RELEASE_DISK) -delete ACTWORK.PRG
	$(C1541) $(RELEASE_DISK) -write $(ACTC_UDOS_PRG) ACTC.PRG -write $(ALINK_UDOS_PRG) ALINK.PRG -write $(ACTMON_UDOS_PRG) ACTMON.PRG -write $(ACTCHK_UDOS_PRG) ACTCHK.PRG -write $(ACTDIR_UDOS_PRG) ACTDIR.PRG -write $(ACTFILE_UDOS_PRG) ACTFILE.PRG -write $(ACTINFO_UDOS_PRG) ACTINFO.PRG -write $(ACTSRC_UDOS_PRG) ACTSRC.PRG -write $(ACTWORK_UDOS_PRG) ACTWORK.PRG

vice-release: release
	$(PYTHON) tools/vice_prg_probe.py --disk $(RELEASE_DISK) \
		--expected "A:D64/>" --settle 1.0 --absent "AUTOEXEC OK"

vice-action-workspace: release
	$(MAKE) BUILD_DIR=$(ACTION_WORKSPACE_BUILD) AUTOEXEC_SRC=$(ACTIONTEST_ROOT)/autoexec_workspace.txt resident
	cp $(ACTION_WORKSPACE_BUILD)/udos-resident.d64 $(ACTION_WORKSPACE_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(ACTION_WORKSPACE_ARTIFACT) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(RELEASE_FS) \
		--vice-arg=-fslongnames --expected "B:ACTION DNP" --settle 8.0 --timeout 120 --attempts 2 --attempt-delay 2.0 \
		--contains "ACTIONC64U FOR UDOS" --contains "BIN/ DOC/ LIB/ SRC/" --contains "ACTINFO.PRG" --contains "README.TXT" \
		--contains "ACTION WORKSPACE OK"

vice-action-actadd: release
	rm -rf $(ACTION_ACTADD_BUILD) $(ACTION_ACTADD_FS)
	mkdir -p $(ACTION_ACTADD_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTADD_FS)/
	rm -rf $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/src \
		$(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/bin \
		$(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	printf 'ACTION PROJECT READY\n' > $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/readme.txt
	printf 'ACTION PROJECT\rMAIN.ACT\r' > $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	printf 'PROC MAIN()\rENDPROC\r' > $(ACTION_ACTADD_FS)/IMAGES/ACTION.DNP/PROJ3/src/main.act
	$(MAKE) BUILD_DIR=$(ACTION_ACTADD_BUILD) AUTOEXEC_SRC=$(ACTIONTEST_ROOT)/autoexec_actadd.txt resident
	cp $(ACTION_ACTADD_BUILD)/udos-resident.d64 $(ACTION_ACTADD_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(ACTION_ACTADD_ARTIFACT) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(ACTION_ACTADD_FS) \
		--vice-arg=-fslongnames --expected "ACTADD DONE" --settle 8.0 --timeout 120 --attempts 2 --attempt-delay 2.0 \
		--contains "RUN ACTADD.PRG" --contains "ACTADD OK" --contains "PROC HELPER()" --contains "ENDPROC" \
		--contains "MAIN.ACT" --contains "HELPER.ACT" --contains "B:DNP/PROJ3>"

vice-action-actdir: release
	bash $(ACTDIR_UDOS_BUILD)
	$(MAKE) BUILD_DIR=$(ACTION_ACTDIR_BUILD) AUTOEXEC_SRC=$(ACTIONTEST_ROOT)/autoexec_actdir.txt resident
	cp $(ACTION_ACTDIR_BUILD)/udos-resident.d64 $(ACTION_ACTDIR_ARTIFACT)
	-$(C1541) $(ACTION_ACTDIR_ARTIFACT) -delete ACTDIR.PRG
	$(C1541) $(ACTION_ACTDIR_ARTIFACT) -write $(ACTDIR_UDOS_PRG) ACTDIR.PRG
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(ACTION_ACTDIR_ARTIFACT) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(RELEASE_FS) \
		--vice-arg=-fslongnames --expected "B:DNP/>" --settle 8.0 --timeout 120 --attempts 2 --attempt-delay 2.0 \
		--contains "RUN ACTDIR.PRG" --contains "BIN/" --contains "DOC/" --contains "LIB/" --contains "SRC/"

vice-action-actsrc: release
	rm -rf $(ACTION_ACTSRC_FS)
	mkdir -p $(ACTION_ACTSRC_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTSRC_FS)/
	rm -rf $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/src \
		$(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/bin \
		$(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	printf 'ACTION PROJECT READY\n' > $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/readme.txt
	printf 'ACTION PROJECT\rMAIN.ACT\rHELPER.ACT\r' > $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	printf 'PROC MAIN()\rENDPROC\r' > $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/src/main.act
	printf 'PROC HELPER()\rENDPROC\r' > $(ACTION_ACTSRC_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	bash $(ACTSRC_UDOS_BUILD)
	$(MAKE) BUILD_DIR=$(ACTION_ACTSRC_BUILD) AUTOEXEC_SRC=$(ACTIONTEST_ROOT)/autoexec_actsrc.txt resident
	cp $(ACTION_ACTSRC_BUILD)/udos-resident.d64 $(ACTION_ACTSRC_ARTIFACT)
	-$(C1541) $(ACTION_ACTSRC_ARTIFACT) -delete ACTSRC.PRG
	$(C1541) $(ACTION_ACTSRC_ARTIFACT) -write $(ACTSRC_UDOS_PRG) ACTSRC.PRG
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(ACTION_ACTSRC_ARTIFACT) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(ACTION_ACTSRC_FS) \
		--vice-arg=-fslongnames --expected "ACTSRC OK" --settle 8.0 --timeout 120 --attempts 2 --attempt-delay 2.0 \
		--contains "RUN ACTSRC.PRG" --contains "MAIN.ACT" --contains "HELPER.ACT" --contains "B:DNP/PROJ3>"

vice-action-actfile: release
	rm -rf $(ACTION_ACTFILE_FS)
	mkdir -p $(ACTION_ACTFILE_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTFILE_FS)/
	rm -rf $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/src \
		$(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/bin \
		$(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	printf 'ACTION PROJECT READY\n' > $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/readme.txt
	printf 'ACTION PROJECT\rMAIN.ACT\rHELPER.ACT\r' > $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	printf 'PROC MAIN()\rENDPROC\r' > $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/src/main.act
	printf 'PROC HELPER()\rENDPROC\r' > $(ACTION_ACTFILE_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	bash $(ACTFILE_UDOS_BUILD)
	$(MAKE) BUILD_DIR=$(ACTION_ACTFILE_BUILD) AUTOEXEC_SRC=$(ACTIONTEST_ROOT)/autoexec_actfile.txt resident
	cp $(ACTION_ACTFILE_BUILD)/udos-resident.d64 $(ACTION_ACTFILE_ARTIFACT)
	-$(C1541) $(ACTION_ACTFILE_ARTIFACT) -delete ACTFILE.PRG
	$(C1541) $(ACTION_ACTFILE_ARTIFACT) -write $(ACTFILE_UDOS_PRG) ACTFILE.PRG
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(ACTION_ACTFILE_ARTIFACT) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(ACTION_ACTFILE_FS) \
		--vice-arg=-fslongnames --expected "ACTFILE OK" --settle 8.0 --timeout 120 --attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTFILE.PRG" --contains "PROC MAIN()" --contains "ENDPROC" --contains "B:DNP/PROJ3>"

vice-action-actwork: release
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
	bash $(ACTWORK_UDOS_BUILD)
	$(MAKE) BUILD_DIR=$(ACTION_ACTWORK_BUILD) AUTOEXEC_SRC=$(ACTIONTEST_ROOT)/autoexec_actwork.txt resident
	cp $(ACTION_ACTWORK_BUILD)/udos-resident.d64 $(ACTION_ACTWORK_ARTIFACT)
	-$(C1541) $(ACTION_ACTWORK_ARTIFACT) -delete ACTWORK.PRG
	$(C1541) $(ACTION_ACTWORK_ARTIFACT) -write $(ACTWORK_UDOS_PRG) ACTWORK.PRG
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(ACTION_ACTWORK_ARTIFACT) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(ACTION_ACTWORK_FS) \
		--vice-arg=-fslongnames --expected "ACTWORK OK" --settle 8.0 --timeout 120 --attempts 4 --attempt-delay 2.0 \
		--contains "RUN ACTWORK.PRG" --contains "PROJECT YES" --contains "SRC YES" --contains "BIN YES" \
		--contains "OBJ YES" --contains "MODULES 2" --contains "B:DNP/PROJ3>"

vice-action-actnew: release
	sleep 2
	$(PYTHON) tools/run_action_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--command "ACTNEW.BAT DEMO" --run-marker "" --done-fragment "ACTNEW OK" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/DEMO>" \
		--attempts 4 --attempt-delay 2.0 \
		--post-command "DIR" --post-done-fragment "README.TXT" \
		--contains "ACTNEW OK" --contains "BIN/" --contains "OBJ/" --contains "SRC/" \
		--contains "README.TXT"

vice-action-actnew-prg: release
	sleep 2
	$(PYTHON) tools/run_action_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--command "ACTNEW DEMO" --run-marker "RUN ACTNEW.PRG" --done-fragment "ACTNEW OK" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/>" \
		--attempts 4 --attempt-delay 2.0 \
		--post-command "CD DEMO/SRC" --post-done-fragment "B:DNP/DEMO/SRC>" \
		--contains "RUN ACTNEW.PRG" --contains "ACTNEW OK" --contains "B:DNP/DEMO/SRC>"

vice-action-actnew-prg-persist: release
	rm -rf $(ACTION_ACTNEW_PRG_PERSIST_BUILD) $(ACTION_ACTNEW_PRG_PERSIST_FS)
	mkdir -p $(ACTION_ACTNEW_PRG_PERSIST_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTNEW_PRG_PERSIST_FS)/
	rm -rf $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ2 $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/proj2
	$(MAKE) BUILD_DIR=$(ACTION_ACTNEW_PRG_PERSIST_BUILD) AUTOEXEC_SRC=$(ACTIONTEST_ROOT)/autoexec_actnew_prg_persist.txt resident
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(abspath $(ACTION_ACTNEW_PRG_PERSIST_BUILD))/udos-resident.d64 \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(abspath $(ACTION_ACTNEW_PRG_PERSIST_FS)) \
		--vice-arg=-fslongnames --expected "ACTNEW OK" --contains "ACTNEW PRG DONE" \
		--settle 8.0 --timeout 120 --attempts 4 --attempt-delay 2.0
	test -d $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ2/bin
	test -d $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ2/obj
	test -d $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ2/src
	test -f $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ2/ACTION.PROJ
	grep -q "MAIN.ACT" $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ2/ACTION.PROJ
	grep -q "ACTION PROJECT READY" $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ2/readme.txt
	grep -q "PROC MAIN()" $(ACTION_ACTNEW_PRG_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ2/src/main.act

vice-action-actadd-persist: release
	rm -rf $(ACTION_ACTADD_PERSIST_FS)
	mkdir -p $(ACTION_ACTADD_PERSIST_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTADD_PERSIST_FS)/
	rm -rf $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src \
		$(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/bin \
		$(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	printf 'ACTION PROJECT READY\n' > $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/readme.txt
	printf 'ACTION PROJECT\rMAIN.ACT\r' > $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	printf 'PROC MAIN()\rENDPROC\r' > $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/main.act
	printf 'PROC OLDHELPER()\rENDPROC\r' > $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	sleep 2
	$(PYTHON) tools/run_action_actadd_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTADD_PERSIST_FS) \
		--project PROJ3 --module HELPER --expect exists --attempts 4 --attempt-delay 2.0
	test -d $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/bin
	test -d $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	test -d $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src
	test -f $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	grep -q "MAIN.ACT" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	! grep -q "HELPER.ACT" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	grep -q "ACTION PROJECT READY" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/readme.txt
	grep -q "PROC MAIN()" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/main.act
	grep -q "PROC OLDHELPER()" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	! grep -q "PROC HELPER()" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	grep -q "ENDPROC" $(ACTION_ACTADD_PERSIST_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act

vice-action-act2save: release
	rm -rf $(ACTION_ACT2SAVE_FS)
	mkdir -p $(ACTION_ACT2SAVE_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACT2SAVE_FS)/
	rm -rf $(ACTION_ACT2SAVE_FS)/IMAGES/ACTION.DNP/PROJ3 $(ACTION_ACT2SAVE_FS)/IMAGES/ACTION.DNP/proj3
	mkdir -p $(ACTION_ACT2SAVE_FS)/IMAGES/ACTION.DNP/PROJ3/src \
		$(ACTION_ACT2SAVE_FS)/IMAGES/ACTION.DNP/PROJ3/bin \
		$(ACTION_ACT2SAVE_FS)/IMAGES/ACTION.DNP/PROJ3/obj
	printf 'ACTION PROJECT READY\n' > $(ACTION_ACT2SAVE_FS)/IMAGES/ACTION.DNP/PROJ3/readme.txt
	printf 'ACTION PROJECT\rMAIN.ACT\rHELPER.ACT\r' > $(ACTION_ACT2SAVE_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ
	printf 'PROC MAIN()\rENDPROC\r' > $(ACTION_ACT2SAVE_FS)/IMAGES/ACTION.DNP/PROJ3/src/main.act
	printf 'PROC OLDHELPER()\rENDPROC\r' > $(ACTION_ACT2SAVE_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	sleep 2
	$(PYTHON) tools/run_action_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACT2SAVE_FS) \
		--command "ACT2SAVE HELPER" --run-marker "RUN ACT2SAVE.PRG" --done-fragment "ACT2SAVE OK" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--attempts 4 --attempt-delay 2.0 \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--post-command "TYPE SRC/HELPER.ACT" --post-done-fragment "ENDPROC" \
		--contains "RUN ACT2SAVE.PRG" --contains "UPDATED" --contains "ACT2SAVE OK" \
		--contains "PROC HELPER()" --contains "B:DNP/PROJ3>"
	grep -q "PROC HELPER()" $(ACTION_ACT2SAVE_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	! grep -q "PROC OLDHELPER()" $(ACTION_ACT2SAVE_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	grep -q "ENDPROC" $(ACTION_ACT2SAVE_FS)/IMAGES/ACTION.DNP/PROJ3/src/helper.act
	grep -q "HELPER.ACT" $(ACTION_ACT2SAVE_FS)/IMAGES/ACTION.DNP/PROJ3/ACTION.PROJ

vice-action-actc: release
	rm -rf $(ACTION_ACTC_FS)
	mkdir -p $(ACTION_ACTC_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_FS)/
	sleep 2
	$(PYTHON) tools/run_action_actc_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_FS) \
		--attempts 3 --attempt-delay 4.0

vice-action-alink: release
	bash /mnt/c/test/action/actionc64u/tools/build_alink_udos.sh
	rm -rf $(ACTION_ALINK_FS)
	mkdir -p $(ACTION_ALINK_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_FS)/
	$(PYTHON) tools/run_action_alink_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_FS) \
		--attempts 3 --attempt-delay 4.0

vice-action-alink-avmrun: release
	bash /mnt/c/test/action/actionc64u/tools/build_alink_udos.sh
	bash /mnt/c/test/action/actionc64u/tools/build_avmrun_udos.sh
	rm -rf $(ACTION_ALINK_AVMRUN_FS)
	mkdir -p $(ACTION_ALINK_AVMRUN_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ALINK_AVMRUN_FS)/
	$(PYTHON) tools/run_action_alink_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ALINK_AVMRUN_FS) \
		--attempts 3 --attempt-delay 4.0

vice-action-actc-alink-avmrun: release
	bash /mnt/c/test/action/actionc64u/tools/build_actc_udos.sh
	bash /mnt/c/test/action/actionc64u/tools/build_alink_udos.sh
	bash /mnt/c/test/action/actionc64u/tools/build_avmrun_udos.sh
	rm -rf $(ACTION_ACTC_ALINK_AVMRUN_FS)
	mkdir -p $(ACTION_ACTC_ALINK_AVMRUN_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTC_ALINK_AVMRUN_FS)/
	$(PYTHON) tools/run_action_actc_alink_avmrun_probe_direct.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTC_ALINK_AVMRUN_FS) \
		--attempts 2 --attempt-delay 4.0

vice-action-actchk: release
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
	sleep 2
	$(PYTHON) tools/run_action_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTCHK_FS) \
		--command "ACTCHK" --run-marker "RUN ACTCHK.PRG" --done-fragment "ACTCHK OK" \
		--b-prompt "B:DNP/>" --final-prompt "B:DNP/PROJ3>" \
		--attempts 8 --attempt-delay 4.0 \
		--pre-command "CD PROJ3" --pre-prompt "B:DNP/PROJ3>" \
		--contains "RUN ACTCHK.PRG" --contains "PROJECT YES" --contains "SRC YES" \
		--contains "BIN YES" --contains "OBJ YES" --contains "MODULES 2" \
		--contains "MISSING 0" --contains "ACTCHK OK"

vice-action-actmon-check: release
	rm -rf $(ACTION_ACTMON_FS)
	mkdir -p $(ACTION_ACTMON_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTMON_FS)/
	sleep 2
	$(PYTHON) tools/run_action_actmon_check_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTMON_FS) \
		--attempts 6 --attempt-delay 2.0

vice-action-actmon: release
	rm -rf $(ACTION_ACTMON_FS)
	mkdir -p $(ACTION_ACTMON_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTMON_FS)/
	sleep 2
	$(PYTHON) tools/run_action_actmon_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_ACTMON_FS) \
		--attempts 4 --attempt-delay 2.0

vice-action-actinfo: release
	bash $(ACTINFO_UDOS_BUILD)
	$(MAKE) BUILD_DIR=$(ACTION_ACTINFO_BUILD) AUTOEXEC_SRC=$(ACTIONTEST_ROOT)/autoexec_actinfo.txt resident
	cp $(ACTION_ACTINFO_BUILD)/udos-resident.d64 $(ACTION_ACTINFO_ARTIFACT)
	-$(C1541) $(ACTION_ACTINFO_ARTIFACT) -delete ACTINFO.PRG
	$(C1541) $(ACTION_ACTINFO_ARTIFACT) -write $(ACTINFO_UDOS_PRG) ACTINFO.PRG
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(ACTION_ACTINFO_ARTIFACT) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(RELEASE_FS) \
		--vice-arg=-fslongnames --expected "B:DNP/>" --settle 8.0 --timeout 120 --attempts 2 --attempt-delay 2.0 \
		--contains "RUN ACTINFO.PRG" --contains "ACTINFO ABI 1" --contains "ARGS ONE TWO" --contains "ACTINFO DONE"

vice-action-actflow: release
	sleep 2
	$(PYTHON) tools/run_action_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--command "ACTFLOW.BAT" --run-marker "" --done-fragment "ACTFLOW OK" --prompt-count 2 \
		--attempts 4 --attempt-delay 2.0 \
		--post-command "TYPE NEXT.TXT" --post-done-fragment "NO SUCH FILE" \
		--contains "ACTFLOW OK" \
		--contains "NO SUCH FILE"

vice-action-actcopy: release
	sleep 2
	$(PYTHON) tools/run_action_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--pre-command "ACTWRITE OUT.TXT" \
		--command "ACTCOPY OUT.TXT COPY.TXT" --run-marker "RUN ACTCOPY.PRG" --done-fragment "" --prompt-count 2 \
		--attempts 1 \
		--post-command "TYPE COPY.TXT" --post-done-fragment "ACTION WRITE OK" \
		--contains "RUN ACTCOPY.PRG" \
		--contains "ACTION WRITE OK"

vice-action-actdel: release
	sleep 2
	$(PYTHON) tools/run_action_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--pre-command "ACTWRITE OUT.TXT" \
		--command "ACTDEL OUT.TXT" --run-marker "RUN ACTDEL.PRG" --done-fragment "ACTDEL OK" --prompt-count 2 \
		--post-command "TYPE OUT.TXT" --post-done-fragment "NO SUCH FILE" \
		--contains "RUN ACTDEL.PRG" \
		--contains "ACTDEL OK" \
		--contains "NO SUCH FILE"

vice-action-actmkdir: release
	sleep 2
	$(PYTHON) tools/run_action_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--command "ACTMKDIR OBJ" --run-marker "RUN ACTMKDIR.PRG" --done-fragment "ACTMKDIR OK" --prompt-count 2 \
		--post-command "CD OBJ" --post-done-fragment "B:DNP/OBJ>" \
		--contains "RUN ACTMKDIR.PRG" \
		--contains "ACTMKDIR OK" \
		--contains "B:DNP/OBJ>"

vice-action-actmkdir-persist: resident release
	rm -rf $(ACTION_ACTMKDIR_PERSIST_FS)
	mkdir -p $(ACTION_ACTMKDIR_PERSIST_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTMKDIR_PERSIST_FS)/
	$(PYTHON) tools/run_vice_tree_persist_probe.py --disk $(RESIDENT_DISK) --fs-root $(ACTION_ACTMKDIR_PERSIST_FS) \
		--command "ACTMKDIR OBJ" \
		--contains "RUN ACTMKDIR.PRG" \
		--contains "ACTMKDIR OK"
	test -d $(ACTION_ACTMKDIR_PERSIST_FS)/IMAGES/ACTION.DNP/OBJ

vice-action-actmove: resident release
	rm -rf $(ACTION_ACTMOVE_PERSIST_FS)
	mkdir -p $(ACTION_ACTMOVE_PERSIST_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTMOVE_PERSIST_FS)/
	printf 'ACTION WRITE OK' > $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/OUT.TXT
	$(PYTHON) tools/run_vice_tree_persist_probe.py --disk $(RESIDENT_DISK) --fs-root $(ACTION_ACTMOVE_PERSIST_FS) \
		--command "ACTMOVE OUT.TXT NEXT.TXT" \
		--contains "RUN ACTMOVE.PRG" \
		--expect-file-text "IMAGES/ACTION.DNP/NEXT.TXT=ACTION WRITE OK"

vice-action-actmove-persist: resident release
	rm -rf $(ACTION_ACTMOVE_PERSIST_FS)
	mkdir -p $(ACTION_ACTMOVE_PERSIST_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTMOVE_PERSIST_FS)/
	printf 'ACTION WRITE OK' > $(ACTION_ACTMOVE_PERSIST_FS)/IMAGES/ACTION.DNP/OUT.TXT
	$(PYTHON) tools/run_vice_tree_persist_probe.py --disk $(RESIDENT_DISK) --fs-root $(ACTION_ACTMOVE_PERSIST_FS) \
		--command "ACTMOVE OUT.TXT NEXT.TXT" \
		--contains "RUN ACTMOVE.PRG" \
		--expect-file-text "IMAGES/ACTION.DNP/NEXT.TXT=ACTION WRITE OK" \
		--absent-file "IMAGES/ACTION.DNP/OUT.TXT"

vice-action-actrmdir: release
	sleep 2
	$(PYTHON) tools/run_action_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--pre-command "MD OBJ" \
		--command "ACTRMDIR OBJ" --run-marker "RUN ACTRMDIR.PRG" --done-fragment "ACTRMDIR OK" --prompt-count 2 \
		--post-command "CD OBJ" --post-done-fragment "NO SUCH DIR" \
		--contains "RUN ACTRMDIR.PRG" \
		--contains "ACTRMDIR OK" \
		--contains "NO SUCH DIR"

vice-action-actrmdir-persist: resident release
	rm -rf $(ACTION_ACTRMDIR_PERSIST_FS)
	mkdir -p $(ACTION_ACTRMDIR_PERSIST_FS)
	cp -a $(RELEASE_FS)/. $(ACTION_ACTRMDIR_PERSIST_FS)/
	mkdir -p $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/OBJ
	$(PYTHON) tools/run_vice_tree_persist_probe.py --disk $(RESIDENT_DISK) --fs-root $(ACTION_ACTRMDIR_PERSIST_FS) \
		--command "ACTRMDIR OBJ" \
		--contains "RUN ACTRMDIR.PRG" \
		--contains "ACTRMDIR OK"
	test ! -e $(ACTION_ACTRMDIR_PERSIST_FS)/IMAGES/ACTION.DNP/OBJ

vice-action-actwrite: release
	sleep 2
	$(PYTHON) tools/run_action_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--command "ACTWRITE OUT.TXT" --run-marker "RUN ACTWRITE.PRG" --done-fragment "ACTWRITE OK" --prompt-count 2 \
		--post-command "TYPE OUT.TXT" --post-done-fragment "ACTION WRITE OK" \
		--contains "RUN ACTWRITE.PRG" \
		--contains "ACTWRITE OK" \
		--contains "ACTION WRITE OK"

vice-action-avminfo: release
	sleep 2
	$(PYTHON) tools/run_action_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--command "AVMINFO HELLO.AVM" --run-marker "RUN AVMINFO.PRG" --done-fragment "AVM OK" --prompt-count 2 \
		--contains "RUN AVMINFO.PRG" \
		--contains "AVM OK"

vice-action-avmrun: release
	sleep 2
	$(PYTHON) tools/run_action_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--command "AVMRUN UDOSHELLO.AVM" --run-marker "RUN AVMRUN.PRG" --done-fragment "UDOS AVM OK" --prompt-count 2 \
		--contains "UDOS AVM OK"

vice-action-avmrun-flow: release
	sleep 2
	$(PYTHON) tools/run_action_avmrun_probe.py --disk $(RELEASE_DISK) --fs-root $(RELEASE_FS) \
		--command "AVMRUN UDOSFLOW.AVM" --run-marker "RUN AVMRUN.PRG" --done-fragment "UDOS AVM FLOW OK" --prompt-count 2 \
		--contains "UDOS AVM FLOW OK"

vice-action-avmrun-runtime: release
	sleep 2
	$(PYTHON) tools/run_action_avmrun_runtime_probe.py --disk $(RELEASE_DISK) --fs-root $(ACTION_AVMRUN_RUNTIME_FS)

vice-proof: proof
	$(PYTHON) tools/vice_prg_probe.py --disk $(PROOF_AUTO_PRG) --expected "UDOS VM OK"

vice-resident: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--expected "A:D64/>" --settle 1.0 --contains "AUTOEXEC OK"

$(VICE_LAUNCH_FS): force $(RETURN_TEST_PRG) $(CLOBBER_TEST_PRG)
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $(VICE_LAUNCH_FS)
	rm -f $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/RESULT.TXT
	grep -v 'RESULT.TXT\|RETTEST.PRG\|CLOBBER.PRG' $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/UDOSDIR.TXT > $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/UDOSDIR.BASE
	cp $(RETURN_TEST_PRG) $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/RETTEST.PRG
	cp $(CLOBBER_TEST_PRG) $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/CLOBBER.PRG
	{ \
		printf 'F CLOBBER.PRG\n'; \
		printf 'F RETTEST.PRG\n'; \
		cat $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/UDOSDIR.BASE; \
	} > $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/UDOSDIR.TXT
	rm -f $(VICE_LAUNCH_FS)/IMAGES/WORK.DNP/SRC/UDOSDIR.BASE

$(VICE_TREE_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $(VICE_TREE_FS)

$(VICE_TREE_COPY_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $(VICE_TREE_COPY_FS)

$(VICE_TREE_WILD_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $(VICE_TREE_WILD_FS)

vice-launch: resident $(VICE_LAUNCH_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_LAUNCH_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.5 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "RETTEST DIR\r" \
		--timeout 120 --attempts 2 --attempt-delay 2.0 \
		--expected "B:DNP/SRC>" --contains "RUN RETTEST.PRG" --contains "ARGS DIR" \
		--check-byte 0xCFF6=0x02 --check-byte 0xCFF7=0x42

vice-clobber: resident $(VICE_LAUNCH_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_LAUNCH_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.5 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "CLOBBER DIR\r" \
		--timeout 120 --attempts 2 --attempt-delay 2.0 \
		--expected "B:DNP/SRC>" --contains "RUN CLOBBER.PRG" --contains "ARGS DIR" \
		--check-byte 0xCFF6=0x02 --check-byte 0xCFF7=0x24

vice-copy: resident $(VICE_TREE_COPY_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_COPY_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.5 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "COPY *.* WORK\r" \
		--feed-step "CD WORK\r" \
		--feed-step "DIR\r" \
		--timeout 120 --attempts 2 --attempt-delay 2.0 \
		--expected "BOOT.ASM" --contains "COPIED"

vice-drive: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--feed-after "A:D64/>" --feed-text "C:\rD:\r" \
		--expected "DRIVE NOT PRESENT" --contains "DRIVE NOT PRESENT"

vice-real-read: resident $(VICE_TREE_FS)
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
		--check-byte 0xCFF0=0x01 --check-byte 0xCFEC=0x01 --check-byte 0xCFEE=0x02 --check-byte 0xCFF2=0x04

vice-real-tree-write: resident $(VICE_TREE_FS)
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "COPY BOOT.ASM WORK/BOOT2.ASM\r" \
		--feed-step "CD WORK\r" \
		--feed-step "REN BOOT2.ASM BOOT3.PRG\r" \
		--feed-step "DEL BOOT3.PRG\r" \
		--feed-step "TYPE BOOT3.PRG\r" \
		--expected "NO SUCH FILE" --contains "COPIED" --contains "RENAMED" --contains "DELETED"

vice-real-tree-rename: resident $(VICE_TREE_FS)
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
		--timeout 120 --attempts 2 --attempt-delay 2.0 \
		--expected "NO SUCH FILE" --contains "RENAMED" --contains "HELLO PROGRAM IMAGE"

vice-real-tree-wild-copy: resident $(VICE_TREE_WILD_FS)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_WILD_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.5 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "COPY *.* WORK\r" \
		--feed-step "CD WORK\r" \
		--feed-step "DIR\r" \
		--timeout 120 --attempts 2 --attempt-delay 2.0 \
		--expected "B:DNP/WORK" --contains "BOOT.ASM" --contains "COPIED"

vice-real-tree-wild-delete: resident $(VICE_TREE_WILD_FS)
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
		--expected "DELETED" --contains "B:DNP/SRC" --contains "BOOT.ASM"

vice-real-tree-wild: vice-real-tree-wild-copy vice-real-tree-wild-delete

vice-real-tree-dir: resident $(VICE_TREE_FS)
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
		--expected "NO SUCH DIR" --contains "CREATED" --contains "B:DNP/NEW" --contains "REMOVED"

vice-real-tree-rmdir: resident $(VICE_TREE_FS)
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

vice-batch-args: resident $(VICE_TREE_FS)
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "ARGS ONE TWO THREE\r" \
		--expected "ONE/TWO/THREE" --contains "ECHO ONE/TWO/THREE"

vice-batch-stop: resident $(VICE_TREE_FS)
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(VICE_TREE_FS) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" --feed-step-settle 2.0 \
		--feed-step "MOUNT B: /IMAGES/WORK.DNP\r" \
		--feed-step "B:\r" \
		--feed-step "CD SRC\r" \
		--feed-step "STOP\r" \
		--expected "NO SUCH FILE" --contains "BEFORE" --absent "AFTER"

vice-autoexec: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--expected "A:D64/>" --settle 1.0 --contains "ECHO AUTOEXEC OK" --contains "AUTOEXEC OK"

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

$(SELFTEST_LAUNCH_FS): force
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

vice-selftest-read: $(SELFTEST_READ_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_READ_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_read.txt resident
	cp $(SELFTEST_READ_BUILD)/udos-resident.d64 $(SELFTEST_READ_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_READ_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_READ_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(SELFTEST_READ_FS) \
		--vice-arg=-fslongnames --expected "READ OK" --settle 2.0 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_READ_ACTUAL)
	diff -u $(SELFTEST_READ_EXPECTED) $(SELFTEST_READ_ACTUAL)

vice-selftest-copy: $(SELFTEST_COPY_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_COPY_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_copy.txt resident
	cp $(SELFTEST_COPY_BUILD)/udos-resident.d64 $(SELFTEST_COPY_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_COPY_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_COPY_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(SELFTEST_COPY_FS) \
		--vice-arg=-fslongnames --expected "COPY OK" --settle 2.0 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_COPY_ACTUAL)
	diff -u $(SELFTEST_COPY_EXPECTED) $(SELFTEST_COPY_ACTUAL)

vice-selftest-rename: $(SELFTEST_RENAME_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_RENAME_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_rename.txt resident
	cp $(SELFTEST_RENAME_BUILD)/udos-resident.d64 $(SELFTEST_RENAME_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_RENAME_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_RENAME_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(SELFTEST_RENAME_FS) \
		--vice-arg=-fslongnames --expected "RENAME OK" --settle 2.0 --timeout 120 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_RENAME_ACTUAL)
	diff -u $(SELFTEST_RENAME_EXPECTED) $(SELFTEST_RENAME_ACTUAL)

vice-selftest-delete: $(SELFTEST_DELETE_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_DELETE_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_delete.txt resident
	cp $(SELFTEST_DELETE_BUILD)/udos-resident.d64 $(SELFTEST_DELETE_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_DELETE_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_DELETE_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(SELFTEST_DELETE_FS) \
		--vice-arg=-fslongnames --expected "DELETE OK" --settle 2.0 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_DELETE_ACTUAL)
	diff -u $(SELFTEST_DELETE_EXPECTED) $(SELFTEST_DELETE_ACTUAL)

vice-selftest-dir: $(SELFTEST_DIR_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_DIR_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_dir.txt resident
	cp $(SELFTEST_DIR_BUILD)/udos-resident.d64 $(SELFTEST_DIR_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_DIR_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_DIR_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(SELFTEST_DIR_FS) \
		--vice-arg=-fslongnames --expected "DIR OK" --settle 2.0 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_DIR_ACTUAL)
	diff -u $(SELFTEST_DIR_EXPECTED) $(SELFTEST_DIR_ACTUAL)

vice-selftest-batch: $(SELFTEST_BATCH_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_BATCH_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_batch.txt resident
	cp $(SELFTEST_BATCH_BUILD)/udos-resident.d64 $(SELFTEST_BATCH_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_BATCH_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_BATCH_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(SELFTEST_BATCH_FS) \
		--vice-arg=-fslongnames --expected "ONE/TWO/THREE" --settle 2.0 --timeout 120 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_BATCH_ACTUAL)
	diff -u $(SELFTEST_BATCH_EXPECTED) $(SELFTEST_BATCH_ACTUAL)

vice-selftest-stop: $(SELFTEST_STOP_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_STOP_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_stop.txt resident
	cp $(SELFTEST_STOP_BUILD)/udos-resident.d64 $(SELFTEST_STOP_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_STOP_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_STOP_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(SELFTEST_STOP_FS) \
		--vice-arg=-fslongnames --expected "NO SUCH FILE" --settle 2.0 --timeout 120 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_STOP_ACTUAL)
	diff -u $(SELFTEST_STOP_EXPECTED) $(SELFTEST_STOP_ACTUAL)

vice-selftest-launch: $(SELFTEST_LAUNCH_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_LAUNCH_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_launch.txt resident
	cp $(SELFTEST_LAUNCH_BUILD)/udos-resident.d64 $(SELFTEST_LAUNCH_ARTIFACT)
	sleep 2
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_LAUNCH_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_LAUNCH_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-fs9 --vice-arg=$(SELFTEST_LAUNCH_FS) \
		--vice-arg=-fslongnames --expected "ARGS DIR" --settle 2.0 --attempts $(SELFTEST_ATTEMPTS) --output $(SELFTEST_LAUNCH_ACTUAL)
	diff -u $(SELFTEST_LAUNCH_EXPECTED) $(SELFTEST_LAUNCH_ACTUAL)

vice-selftest:
	$(PYTHON) tools/run_selftests.py

test: vice-proof vice-resident vice-drive vice-autoexec vice-selftest
