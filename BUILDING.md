# Building UDOS

## Prerequisites

Required in the current environment:
- `make`
- `ca65`
- `ld65`
- `python3`
- `c1541`

Optional for emulator validation:
- `x64sc`

Local dependency path assumed by this repo:
- AcheronVM source at `/mnt/c/test/action/acheronvm`

## Phase 1 Proof Build

Build the local AcheronVM dependency, the UDOS proof PRG, a BASIC wrapper, and a
D64 image:

```sh
cd /mnt/c/test/action/udos
make proof
```

Expected output:
- `build/udos-proof.prg`
- `build/udos-proof.labels`
- `build/udos-proof.map`
- `build/udosboot.prg`
- `build/udos-proof.d64`

## Emulator Validation

Run the proof under VICE and verify the screen banner plus a marker byte:

```sh
cd /mnt/c/test/action/udos
make vice-proof
```

The proof flow is:
- link the AcheronVM runtime with the UDOS proof object
- parse the linked `.start` address from `build/udos-proof.labels`
- generate a BASIC wrapper that executes `SYS <linked-start>`
- place that wrapper on `build/udos-proof.d64`
- autostart the D64 in `x64sc`
- read screen RAM through the VICE binary monitor
- verify `UDOS VM OK` appears and `$CFFF == $42`

Current validated linked entrypoint:
- `.start = $1810`

Current resident/runtime footprint from the proof map:
- Acheron dispatcher: `$00E6` bytes
- Acheron runtime body: `$072A` bytes
- UDOS proof code: `$002E` bytes
- linked code entrypoint: `$1810`

## Tests

Run the current test surface with the standard library test runner:

```sh
cd /mnt/c/test/action/udos
python3 -m unittest -q
```

Notes:
- the build test always runs
- the VICE-backed test is skipped automatically when `x64sc` is not installed

## Hardware Validation

No target hardware validation has been performed from this environment.

For a real C64 Ultimate test, copy `build/udos-proof.d64` to media the machine
can mount, boot it, and load the first program on the disk. Until that happens,
all validation here must be described as emulator validation only.
