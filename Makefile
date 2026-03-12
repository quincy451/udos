ACHERON_DIR := /mnt/c/test/action/acheronvm
BUILD_DIR := build
ASM_DIR := src/asm
PYTHON := python3
CA65 := ca65
LD65 := ld65
C1541 := c1541
VICE_FS_ROOT := tests/vicefs

PROOF_OBJ := $(BUILD_DIR)/udos_proof.o
PROOF_PRG := $(BUILD_DIR)/udos-proof.prg
PROOF_AUTO_PRG := $(BUILD_DIR)/udosboot.prg
PROOF_DISK := $(BUILD_DIR)/udos-proof.d64
PROOF_LABELS := $(BUILD_DIR)/udos-proof.labels
PROOF_MAP := $(BUILD_DIR)/udos-proof.map

RESIDENT_OBJ := $(BUILD_DIR)/udos_resident.o
RESIDENT_PRG := $(BUILD_DIR)/udos-resident.prg
RESIDENT_AUTO_PRG := $(BUILD_DIR)/udosres.prg
RESIDENT_DISK := $(BUILD_DIR)/udos-resident.d64
RESIDENT_LABELS := $(BUILD_DIR)/udos-resident.labels
RESIDENT_MAP := $(BUILD_DIR)/udos-resident.map

.PHONY: all clean acheron-dep proof vice-proof resident vice-resident vice-launch vice-copy vice-drive vice-real-read vice-real-tree-write vice-real-tree-rename vice-real-tree-wild vice-real-tree-dir vice-real-tree-rmdir test

all: proof resident

clean:
	rm -rf $(BUILD_DIR)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

acheron-dep:
	$(MAKE) -C $(ACHERON_DIR) acheron

$(PROOF_OBJ): $(ASM_DIR)/udos_proof.asm | $(BUILD_DIR)
	$(CA65) -g -o $@ $< -I $(ACHERON_DIR)/bin -I $(ACHERON_DIR)/src

proof: acheron-dep $(PROOF_OBJ)
	$(LD65) -Ln $(PROOF_LABELS) -C $(ASM_DIR)/udos_c64.cfg -m $(PROOF_MAP) -o $(PROOF_PRG) $(PROOF_OBJ) $(ACHERON_DIR)/obj/acheron.o
	$(PYTHON) tools/make_basic_autostart.py --input $(PROOF_PRG) --labels $(PROOF_LABELS) --output $(PROOF_AUTO_PRG)
	$(C1541) -format "udos,01" d64 $(PROOF_DISK) -write $(PROOF_AUTO_PRG) udosboot

$(RESIDENT_OBJ): $(ASM_DIR)/udos_resident.asm | $(BUILD_DIR)
	$(CA65) -g -o $@ $< -I $(ACHERON_DIR)/bin -I $(ACHERON_DIR)/src

resident: acheron-dep $(RESIDENT_OBJ)
	$(LD65) -Ln $(RESIDENT_LABELS) -C $(ASM_DIR)/udos_c64.cfg -m $(RESIDENT_MAP) -o $(RESIDENT_PRG) $(RESIDENT_OBJ) $(ACHERON_DIR)/obj/acheron.o
	$(PYTHON) tools/make_basic_autostart.py --input $(RESIDENT_PRG) --labels $(RESIDENT_LABELS) --output $(RESIDENT_AUTO_PRG)
	$(C1541) -format "udos,01" d64 $(RESIDENT_DISK) -write $(RESIDENT_AUTO_PRG) udosres

vice-proof: proof
	$(PYTHON) tools/vice_prg_probe.py --disk $(PROOF_AUTO_PRG) --expected "UDOS VM OK"

vice-resident: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_AUTO_PRG) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rVOL\rB:\rCD SRC\rDIR\rTYPE BOOT.ASM\rDELBOOT3\rC:\rD:\r" \
		--expected "DRIVE NOT PRESENT" --contains "A:SYSTEM D64 B:WORK DNP" --contains "BOOT.ASM HELLO.PRG" --contains "; BOOT.ASM VICE BACKEND SOURCE" --contains "PROGRAM NOT FOUND"

vice-launch: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_AUTO_PRG) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rCD SRC\rCOPY BOOT.ASM WORK/BOOT2.PRG\rCD WORK\rREN BOOT2.PRG BOOT3.PRG\rBOOT3 DIR\r" \
		--expected "ARGS DIR" --contains "RUN BOOT3.PRG"

vice-copy: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_AUTO_PRG) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rCD SRC\rCOPY *.* WORK\rCD WORK\rDIR\r" \
		--expected "BOOT.ASM HELLO.PRG" --contains "COPIED"

vice-drive: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_AUTO_PRG) --feed-after "A:D64/>" --feed-text "C:\rD:\r" --expected "DRIVE NOT PRESENT" --contains "DRIVE NOT PRESENT"

vice-real-read: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_AUTO_PRG) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rVOL\rB:\rDIR\rCD SRC\rDIR\rTYPE BOOT.ASM\rHELLO DIR\r" \
		--expected "ARGS DIR" --contains "A:SYSTEM D64 B:WORK DNP" --contains "BIN/ SRC/ WORK/" \
		--contains "BOOT.ASM HELLO.PRG" --contains "; BOOT.ASM VICE BACKEND SOURCE" --contains "RUN HELLO.PRG" \
		--check-byte 0xCFF0=0x01 --check-byte 0xCFEC=0x01 --check-byte 0xCFEE=0x02 --check-byte 0xCFF2=0x04

vice-real-tree-write: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_AUTO_PRG) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rCD SRC\rCOPY BOOT.ASM WORK/BOOT2.ASM\rCD WORK\rREN BOOT2.ASM BOOT3.PRG\rDEL BOOT3.PRG\rTYPE BOOT3.PRG\r" \
		--expected "NO SUCH FILE" --contains "COPIED" --contains "RENAMED" --contains "DELETED"

vice-real-tree-rename: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_AUTO_PRG) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rCD SRC\rREN HELLO.PRG HELLO2.PRG\rTYPE HELLO2.PRG\rTYPE HELLO.PRG\r" \
		--expected "NO SUCH FILE" --contains "RENAMED" --contains "HELLO PROGRAM IMAGE"

vice-real-tree-wild: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_AUTO_PRG) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rCD SRC\rCOPY *.* WORK\rCD WORK\rDIR\rCD /\rCD SRC\rDEL *.PRG\rDIR\r" \
		--expected "B:DNP/SRC BOOT.ASM" --contains "B:DNP/WORK BOOT.ASM HELLO.PRG" --contains "COPIED" --contains "DELETED"

vice-real-tree-dir: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_AUTO_PRG) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rMD NEW\rCD NEW\rCD /\rRD NEW\rCD NEW\r" \
		--expected "NO SUCH DIR" --contains "CREATED" --contains "B:DNP/NEW" --contains "REMOVED"

vice-real-tree-rmdir: resident
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_AUTO_PRG) \
		--vice-arg=-iecdevice8 --vice-arg=-device8 --vice-arg=1 --vice-arg=-fs8 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-iecdevice9 --vice-arg=-device9 --vice-arg=1 --vice-arg=-fs9 --vice-arg=$(VICE_FS_ROOT) \
		--vice-arg=-fslongnames --feed-after "A:D64/>" \
		--feed-text "MOUNT B: /IMAGES/WORK.DNP\rB:\rRD SRC\r" \
		--expected "DIR NOT EMPTY"

test: vice-proof vice-resident vice-launch vice-copy vice-drive vice-real-read vice-real-tree-write vice-real-tree-rename vice-real-tree-wild vice-real-tree-dir vice-real-tree-rmdir
