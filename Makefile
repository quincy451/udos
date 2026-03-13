ACHERON_DIR := /mnt/c/test/action/acheronvm
BUILD_DIR := build
ASM_DIR := src/asm
PYTHON := python3
CA65 := ca65
LD65 := ld65
C1541 := c1541
VICE_FS_ROOT := tests/vicefs
AUTOEXEC_SRC ?= $(ASM_DIR)/autoexec_default.txt
AUTOEXEC_INC := $(BUILD_DIR)/autoexec_script.inc
RESIDENT_DEFINES ?=
SELFTEST_ROOT := tests/selftest
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
RELEASE_BUILD := build/release
RELEASE_DISK := build/udos-release.d64
RELEASE_FS := build/udos-release-fs

.PHONY: all clean acheron-dep force proof vice-proof resident release vice-release vice-resident vice-launch vice-copy vice-drive vice-real-read vice-real-tree-write vice-real-tree-rename vice-real-tree-wild vice-real-tree-dir vice-real-tree-rmdir vice-batch-args vice-batch-stop vice-autoexec vice-selftest-read vice-selftest-copy vice-selftest-rename vice-selftest-delete vice-selftest-dir vice-selftest-batch vice-selftest-stop vice-selftest-launch vice-selftest test

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

resident: acheron-dep $(RESIDENT_OBJ) $(RESIDENT_BOOT_OBJ)
	$(LD65) -Ln $(RESIDENT_LABELS) -C $(ASM_DIR)/udos_c64.cfg -m $(RESIDENT_MAP) -o $(RESIDENT_PRG) $(RESIDENT_OBJ) $(ACHERON_DIR)/obj/acheron.o
	cp $(RESIDENT_PRG) $(RESIDENT_RAW)
	$(LD65) -Ln $(RESIDENT_BOOT_LABELS) -C $(ASM_DIR)/udos_boot.cfg -m $(RESIDENT_BOOT_MAP) -o $(RESIDENT_BOOT_PRG) $(RESIDENT_BOOT_OBJ)
	$(PYTHON) -c "from pathlib import Path; data=Path('$(RESIDENT_BOOT_PRG)').read_bytes(); Path('$(RESIDENT_BOOT_LOAD_PRG)').write_bytes(bytes((0x10,0x08))+data)"
	$(PYTHON) tools/make_basic_autostart.py --input $(RESIDENT_BOOT_LOAD_PRG) --labels $(RESIDENT_BOOT_LABELS) --output $(RESIDENT_AUTO_PRG) --expected-load-addr 0x0810
	$(C1541) -format "udos,01" d64 $(RESIDENT_DISK) -write $(RESIDENT_AUTO_PRG) udosboot -write $(RESIDENT_RAW) udoscore

release:
	$(MAKE) BUILD_DIR=$(RELEASE_BUILD) RESIDENT_DEFINES="-D UDOS_INCLUDE_AUTOEXEC=0" resident
	$(PYTHON) tools/prepare_release_fs.py --base $(VICE_FS_ROOT) --output $(RELEASE_FS)
	cp $(RELEASE_BUILD)/udos-resident.d64 $(RELEASE_DISK)

vice-release: release
	$(PYTHON) tools/vice_prg_probe.py --disk $(RELEASE_DISK) \
		--expected "A:D64/>" --settle 1.0 --absent "AUTOEXEC OK"

vice-proof: proof
	$(PYTHON) tools/vice_prg_probe.py --disk $(PROOF_AUTO_PRG) --expected "UDOS VM OK"

vice-resident: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--expected "A:D64/>" --settle 1.0 --contains "AUTOEXEC OK"

vice-launch: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rCD SRC\rCOPY BOOT.ASM WORK/BOOT2.PRG\rCD WORK\rREN BOOT2.PRG BOOT3.PRG\rBOOT3 DIR\r" \
		--expected "ARGS DIR" --contains "RUN BOOT3.PRG"

vice-copy: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rCD SRC\rCOPY *.* WORK\rCD WORK\rDIR\r" \
		--expected "BOOT.ASM" --contains "COPIED"

vice-drive: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--feed-after "A:D64/>" --feed-text "C:\rD:\r" \
		--expected "DRIVE NOT PRESENT" --contains "DRIVE NOT PRESENT"

vice-real-read: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rVOL\rB:\rDIR\rCD SRC\rDIR\rTYPE BOOT.ASM\rHELLO DIR\r" \
		--expected "ARGS DIR" --contains "A:SYSTEM D64 B:WORK DNP" --contains "BIN/ SRC/ WORK/" \
		--contains "BOOT.ASM" --contains "; BOOT.ASM VICE BACKEND SOURCE" --contains "RUN HELLO.PRG" \
		--check-byte 0xCFF0=0x01 --check-byte 0xCFEC=0x01 --check-byte 0xCFEE=0x02 --check-byte 0xCFF2=0x04

vice-real-tree-write: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rCD SRC\rCOPY BOOT.ASM WORK/BOOT2.ASM\rCD WORK\rREN BOOT2.ASM BOOT3.PRG\rDEL BOOT3.PRG\rTYPE BOOT3.PRG\r" \
		--expected "NO SUCH FILE" --contains "COPIED" --contains "RENAMED" --contains "DELETED"

vice-real-tree-rename: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rCD SRC\rREN HELLO.PRG HELLO2.PRG\rTYPE HELLO2.PRG\rTYPE HELLO.PRG\r" \
		--expected "NO SUCH FILE" --contains "RENAMED" --contains "HELLO PROGRAM IMAGE"

vice-real-tree-wild: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rCD SRC\rCOPY *.* WORK\rCD WORK\rDIR\rCD /\rCD SRC\rDEL *.PRG\rDIR\r" \
		--expected "DELETED" --contains "B:DNP/WORK" --contains "B:DNP/SRC" --contains "BOOT.ASM" --contains "COPIED"

vice-real-tree-dir: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rMD NEW\rCD NEW\rCD /\rRD NEW\rCD NEW\r" \
		--expected "NO SUCH DIR" --contains "CREATED" --contains "B:DNP/NEW" --contains "REMOVED"

vice-real-tree-rmdir: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rRD SRC\r" \
		--expected "DIR NOT EMPTY"

vice-batch-args: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rCD SRC\rARGS ONE TWO THREE\r" \
		--expected "ONE/TWO/THREE" --contains "ECHO ONE/TWO/THREE"

vice-batch-stop: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rCD SRC\rSTOP\r" \
		--expected "NO SUCH FILE" --contains "BEFORE" --absent "AFTER"

vice-autoexec: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_DISK) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(BUILD_DIR) \
		--expected "A:D64/>" --settle 1.0 --contains "ECHO AUTOEXEC OK" --contains "AUTOEXEC OK"

$(SELFTEST_READ_FS):
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_COPY_FS):
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_RENAME_FS):
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_DELETE_FS):
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_DIR_FS):
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_BATCH_FS):
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_STOP_FS):
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

$(SELFTEST_LAUNCH_FS):
	$(PYTHON) tools/prepare_selftest_fs.py --base $(VICE_FS_ROOT) --output $@

vice-selftest-read: $(SELFTEST_READ_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_READ_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_read.txt resident
	cp $(SELFTEST_READ_BUILD)/udos-resident.d64 $(SELFTEST_READ_ARTIFACT)
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_READ_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_READ_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(SELFTEST_READ_FS) \
		--vice-arg=-fslongnames --expected "READ OK" --settle 2.0 > $(SELFTEST_READ_ACTUAL)
	diff -u $(SELFTEST_READ_EXPECTED) $(SELFTEST_READ_ACTUAL)

vice-selftest-copy: $(SELFTEST_COPY_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_COPY_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_copy.txt resident
	cp $(SELFTEST_COPY_BUILD)/udos-resident.d64 $(SELFTEST_COPY_ARTIFACT)
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_COPY_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_COPY_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(SELFTEST_COPY_FS) \
		--vice-arg=-fslongnames --expected "COPY OK" --settle 2.0 > $(SELFTEST_COPY_ACTUAL)
	diff -u $(SELFTEST_COPY_EXPECTED) $(SELFTEST_COPY_ACTUAL)

vice-selftest-rename: $(SELFTEST_RENAME_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_RENAME_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_rename.txt resident
	cp $(SELFTEST_RENAME_BUILD)/udos-resident.d64 $(SELFTEST_RENAME_ARTIFACT)
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_RENAME_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_RENAME_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(SELFTEST_RENAME_FS) \
		--vice-arg=-fslongnames --expected "RENAME OK" --settle 2.0 > $(SELFTEST_RENAME_ACTUAL)
	diff -u $(SELFTEST_RENAME_EXPECTED) $(SELFTEST_RENAME_ACTUAL)

vice-selftest-delete: $(SELFTEST_DELETE_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_DELETE_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_delete.txt resident
	cp $(SELFTEST_DELETE_BUILD)/udos-resident.d64 $(SELFTEST_DELETE_ARTIFACT)
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_DELETE_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_DELETE_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(SELFTEST_DELETE_FS) \
		--vice-arg=-fslongnames --expected "DELETE OK" --settle 2.0 > $(SELFTEST_DELETE_ACTUAL)
	diff -u $(SELFTEST_DELETE_EXPECTED) $(SELFTEST_DELETE_ACTUAL)

vice-selftest-dir: $(SELFTEST_DIR_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_DIR_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_dir.txt resident
	cp $(SELFTEST_DIR_BUILD)/udos-resident.d64 $(SELFTEST_DIR_ARTIFACT)
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_DIR_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_DIR_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(SELFTEST_DIR_FS) \
		--vice-arg=-fslongnames --expected "DIR OK" --settle 2.0 > $(SELFTEST_DIR_ACTUAL)
	diff -u $(SELFTEST_DIR_EXPECTED) $(SELFTEST_DIR_ACTUAL)

vice-selftest-batch: $(SELFTEST_BATCH_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_BATCH_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_batch.txt resident
	cp $(SELFTEST_BATCH_BUILD)/udos-resident.d64 $(SELFTEST_BATCH_ARTIFACT)
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_BATCH_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_BATCH_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(SELFTEST_BATCH_FS) \
		--vice-arg=-fslongnames --expected "ONE/TWO/THREE" --settle 2.0 > $(SELFTEST_BATCH_ACTUAL)
	diff -u $(SELFTEST_BATCH_EXPECTED) $(SELFTEST_BATCH_ACTUAL)

vice-selftest-stop: $(SELFTEST_STOP_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_STOP_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_stop.txt resident
	cp $(SELFTEST_STOP_BUILD)/udos-resident.d64 $(SELFTEST_STOP_ARTIFACT)
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_STOP_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_STOP_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(SELFTEST_STOP_FS) \
		--vice-arg=-fslongnames --expected "NO SUCH FILE" --settle 2.0 > $(SELFTEST_STOP_ACTUAL)
	diff -u $(SELFTEST_STOP_EXPECTED) $(SELFTEST_STOP_ACTUAL)

vice-selftest-launch: $(SELFTEST_LAUNCH_FS)
	$(MAKE) BUILD_DIR=$(SELFTEST_LAUNCH_BUILD) AUTOEXEC_SRC=$(SELFTEST_ROOT)/autoexec_launch.txt resident
	cp $(SELFTEST_LAUNCH_BUILD)/udos-resident.d64 $(SELFTEST_LAUNCH_ARTIFACT)
	$(PYTHON) tools/vice_prg_probe.py --disk $(SELFTEST_LAUNCH_ARTIFACT) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(SELFTEST_LAUNCH_BUILD) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(SELFTEST_LAUNCH_FS) \
		--vice-arg=-fslongnames --expected "ARGS DIR" --settle 2.0 > $(SELFTEST_LAUNCH_ACTUAL)
	diff -u $(SELFTEST_LAUNCH_EXPECTED) $(SELFTEST_LAUNCH_ACTUAL)

vice-selftest: vice-selftest-read vice-selftest-copy vice-selftest-rename vice-selftest-delete vice-selftest-dir vice-selftest-batch vice-selftest-stop vice-selftest-launch

test: vice-proof vice-resident vice-launch vice-copy vice-drive vice-real-read vice-real-tree-write vice-real-tree-rename vice-real-tree-wild vice-real-tree-dir vice-real-tree-rmdir vice-batch-args vice-batch-stop vice-autoexec vice-selftest
