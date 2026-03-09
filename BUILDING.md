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

Expected proof outputs:
- `build/udos-proof.prg`
- `build/udos-proof.labels`
- `build/udos-proof.map`
- `build/udosboot.prg`
- `build/udos-proof.d64`

## Phase 2 Resident Core Build

Build the resident bootstrap/core slice:

```sh
cd /mnt/c/test/action/udos
make resident
```

Expected resident outputs:
- `build/udos-resident.prg`
- `build/udos-resident.labels`
- `build/udos-resident.map`
- `build/udosres.prg`
- `build/udos-resident.d64`

## Emulator Validation

### Proof

```sh
cd /mnt/c/test/action/udos
make vice-proof
```

Validated proof behavior:
- autostarts a D64 in `x64sc`
- runs the BASIC wrapper into the linked Acheron entrypoint
- reads screen RAM through the VICE binary monitor
- verifies `UDOS VM OK`
- verifies `$CFFF == $42`

Current validated linked proof entrypoint:
- `.start = $1810`

Current proof footprint from the map:
- Acheron dispatcher: `$00E6`
- Acheron runtime body: `$072A`
- UDOS proof code: `$002E`

### Resident Core

```sh
cd /mnt/c/test/action/udos
make vice-resident
```

Validated resident behavior:
- autostarts a D64 in `x64sc`
- enters the resident bootstrap/core image
- Acheron code calls the native Phase 2 services
- screen shows `UDOS CORE  A>`
- `$CFFE == $01` confirms ABI version snapshot from VM-side `stma`
- `$CFFF == $52` confirms resident-ready marker

Current validated linked resident entrypoint:
- `.start = $1810`

Current resident footprint from the map:
- Acheron dispatcher: `$00E6`
- Acheron runtime body: `$072A`
- resident core code: `$009B`

## Tests

Run the current test surface with the standard library test runner:

```sh
cd /mnt/c/test/action/udos
python3 -m unittest discover -s tests -q
```

Notes:
- build tests always run
- VICE-backed tests are skipped automatically when `x64sc` is not installed

## Hardware Validation

No target hardware validation has been performed from this environment.

For a real C64 Ultimate test, copy either `build/udos-proof.d64` or
`build/udos-resident.d64` to media the machine can mount and boot the first
program on the disk. Until that happens, all validation here must be described
as emulator validation only.
