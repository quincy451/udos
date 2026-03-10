# Building UDOS

## Scope

UDOS is currently built and validated as a standalone Commodore 64 program path.
This build does not depend on CP/M-65.

## Prerequisites

Required:
- `make`
- `ca65`
- `ld65`
- `python3`
- `c1541`

Optional for emulator validation:
- `x64sc`

Local dependency path assumed by this repo:
- AcheronVM source at `/mnt/c/test/action/acheronvm`

## Build The Proof Image

```sh
cd /mnt/c/test/action/udos
make proof
```

Outputs:
- `build/udos-proof.prg`
- `build/udos-proof.labels`
- `build/udos-proof.map`
- `build/udosboot.prg`
- `build/udos-proof.d64`

## Build The Resident Image

```sh
cd /mnt/c/test/action/udos
make resident
```

Outputs:
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

Current validated proof facts:
- autostarts `build/udosboot.prg` in `x64sc`
- linked entrypoint: `$1810`
- banner: `UDOS VM OK`
- marker byte: `$CFFF = $42`
- proof code footprint: `$002E`

### Resident

```sh
cd /mnt/c/test/action/udos
make vice-resident
```

Current `vice-resident` behavior:
- builds `build/udosres.prg`
- autostarts the BASIC wrapper PRG in `x64sc`
- binds `A:` as `D64` and `B:` as `DNP`
- drives the live resident shell with:
  - `CDB:`
  - `CDSRC`
  - `COPYBOOTASMWORKBOOTASM`
  - `CDWORK`
  - `RENBOOTASMBOOT2ASM`
  - `RUNBOOT2ASM:DIR`
  - `DELBOOT2ASM`
  - `DIR`
- verifies the final listing `B:DNP/WORK EMPTY`
- verifies resident snapshots:
  - `A:` bind = `D64/flat`
  - `B:` bind = `DNP/tree`
  - current drive = `B:`
  - transport mode = `mock`
  - mount kind = `DNP`
  - ABI version = `1`
  - program state after `RUN` = exited with `0` status on `B:/WORK`

Current validated resident transcript:

```text
UDOS FOR COMMODORE 64
  A:D64/> CDB:
B:DNP/
  B:DNP/> CDSRC
B:DNP/SRC
  B:DNP/SRC> COPYBOOTASMWORKBOOTASM
COPIED
  B:DNP/SRC> CDWORK
B:DNP/WORK
  B:DNP/WORK> RENBOOTASMBOOT2ASM
RENAMED
  B:DNP/WORK> RUNBOOT2ASM:DIR
RUN BOOT2ASM
ARGS DIR
  B:DNP/WORK> DELBOOT2ASM
DELETED
  B:DNP/WORK> DIR
B:DNP/WORK EMPTY
  B:DNP/WORK>
```

Current resident map facts:
- linked entrypoint: `$1810`
- Acheron dispatcher: `$00E6`
- Acheron runtime body: `$072A`
- resident core code: `$2171`
- resident load window in [udos_c64.cfg](/mnt/c/test/action/udos/src/asm/udos_c64.cfg): `$3000`

## Tests

```sh
cd /mnt/c/test/action/udos
python3 -m unittest discover -s tests -q
```

Notes:
- build tests always run
- VICE-backed tests are skipped automatically when `x64sc` is not installed

## Hardware Validation

No target hardware validation has been performed from this environment.

If you want to try the current resident image on real C64 Ultimate hardware:

1. Copy `build/udos-resident.d64` or `build/udosres.prg` to media the machine can mount.
2. Boot or autostart the program.
3. Reproduce this smoke sequence manually:

```text
  A:D64/> CDB:
B:DNP/
  B:DNP/> CDSRC
B:DNP/SRC
  B:DNP/SRC> COPYBOOTASMWORKBOOTASM
COPIED
  B:DNP/SRC> CDWORK
B:DNP/WORK
  B:DNP/WORK> RENBOOTASMBOOT2ASM
RENAMED
  B:DNP/WORK> RUNBOOT2ASM:DIR
RUN BOOT2ASM
ARGS DIR
  B:DNP/WORK> DELBOOT2ASM
DELETED
  B:DNP/WORK> DIR
B:DNP/WORK EMPTY
```

Until that run happens on real hardware, all current validation should be described as emulator validation only.
