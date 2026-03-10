ACHERON_DIR := /mnt/c/test/action/acheronvm
BUILD_DIR := build
ASM_DIR := src/asm
PYTHON := python3
CA65 := ca65
LD65 := ld65
C1541 := c1541

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

.PHONY: all clean acheron-dep proof vice-proof resident vice-resident test

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
	$(PYTHON) tools/vice_prg_probe.py --disk $(RESIDENT_AUTO_PRG) --feed-after "A:D64/>" --feed-text "CD B:\rCD SRC\rCOPY BOOT.ASM WORK/BOOTASM\rCD WORK\rREN BOOTASM BOOT2ASM\rDELBOOT2ASM\rRUN BOOT2ASM DIR\rDEL BOOT2ASM\rDIR\r" --expected "B:DNP/WORK EMPTY" --contains "PROGRAM NOT FOUND" --contains "RUN BOOT2ASM" --check-byte 0xCFE4=0x01 --check-byte 0xCFE5=0x05 --check-byte 0xCFE8=0x01 --check-byte 0xCFE9=0x01 --check-byte 0xCFEA=0x04 --check-byte 0xCFEB=0x02 --check-byte 0xCFEC=0x01 --check-byte 0xCFEE=0x02 --check-byte 0xCFF0=0x01 --check-byte 0xCFF2=0x04 --check-byte 0xCFF4=0x01 --check-byte 0xCFF6=0x02 --check-byte 0xCFF7=0x00 --check-byte 0xCFF8=0x01 --check-byte 0xCFF9=0x03

test: vice-proof vice-resident
