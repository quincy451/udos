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

.PHONY: all clean acheron-dep proof vice-proof test

all: proof

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

vice-proof: proof
	$(PYTHON) tools/vice_prg_probe.py --disk $(PROOF_DISK) --expected "UDOS VM OK"

test: vice-proof
