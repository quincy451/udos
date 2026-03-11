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
- drives the live resident shell with direct drive switching and explicit separators:
  - `B:`
  - `CD SRC`
  - `COPY BOOT.ASM WORK/BOOT2.PRG`
  - `CD WORK`
  - `REN BOOT2.PRG BOOT3.PRG`
  - `DELBOOT3`
  - `BOOT3 DIR`
  - `DEL BOOT3.PRG`
  - `DIR`
- verifies command-keyword separation:
  - `DELBOOT3` must not be treated as `DEL BOOT3.PRG`
  - it is treated as a bare program token and returns `PROGRAM NOT FOUND`
- verifies implicit program launch:
  - `BOOT3 DIR` resolves as `BOOT3.PRG`
  - `DIR` is passed as the command line
- verifies the final listing `B:DNP/WORK EMPTY`
- verifies resident snapshots:
  - cached backend-path length:
    - `A:` = `1` (`/`)
    - `B:` = `5` (`/WORK`) after the smoke sequence
  - `A:` bind = `D64/flat`
  - `B:` bind = `DNP/tree`
  - current drive = `B:`
  - transport mode = `mock`
  - mount kind = `DNP`
  - ABI version = `1`
  - program state after implicit launch = exited with `0` status on `B:/WORK`

Current validated resident transcript:

```text
UDOS FOR COMMODORE 64
  A:D64/> B:
B:DNP/
  B:DNP/> CD SRC
B:DNP/SRC
  B:DNP/SRC> COPY BOOT.ASM WORK/BOOT2.PRG
COPIED
  B:DNP/SRC> CD WORK
B:DNP/WORK
  B:DNP/WORK> REN BOOT2.PRG BOOT3.PRG
RENAMED
  B:DNP/WORK> DELBOOT3
PROGRAM NOT FOUND
  B:DNP/WORK> BOOT3 DIR
RUN BOOT3.PRG
ARGS DIR
  B:DNP/WORK> DEL BOOT3.PRG
DELETED
  B:DNP/WORK> DIR
B:DNP/WORK EMPTY
  B:DNP/WORK>
```

Current resident map facts:
- linked entrypoint: `$1810`
- Acheron dispatcher: `$00E6`
- Acheron runtime body: `$072A`
- resident core code: `$30ED`
- resident load window in [udos_c64.cfg](/mnt/c/test/action/udos/src/asm/udos_c64.cfg): `$4000`
- hardware directory cache budget:
  - `6` entries per drive
  - `20` bytes per cached name
- hardware `TYPE` read budget:
  - one bounded resident text buffer per command
  - fallback to mock content when UCI/file access fails

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
  A:D64/> B:
B:DNP/
  B:DNP/> CD SRC
B:DNP/SRC
  B:DNP/SRC> COPY BOOT.ASM WORK/BOOT2.PRG
COPIED
  B:DNP/SRC> CD WORK
B:DNP/WORK
  B:DNP/WORK> REN BOOT2.PRG BOOT3.PRG
RENAMED
  B:DNP/WORK> DELBOOT3
PROGRAM NOT FOUND
  B:DNP/WORK> BOOT3 DIR
RUN BOOT3.PRG
ARGS DIR
  B:DNP/WORK> DEL BOOT3.PRG
DELETED
  B:DNP/WORK> DIR
B:DNP/WORK EMPTY
```

Until that run happens on real hardware, all current validation should be described as emulator validation only.

Hardware-specific note:
- the resident image now contains a real Ultimate DOS directory-enumeration path using `CHANGE_DIR`, `GET_PATH`, `OPEN_DIR`, and `READ_DIR`
- the resident image now also contains a real Ultimate DOS `TYPE` path using `CHANGE_DIR`, `OPEN_FILE`, `READ_DATA`, and `CLOSE_FILE`
- the resident image now also contains a real Ultimate DOS `DEL` path using `CHANGE_DIR` and `DELETE_FILE`
- the resident image now also contains a real Ultimate DOS `REN` path using `CHANGE_DIR` and `RENAME_FILE`
- the resident image now also contains a real Ultimate DOS `COPY` path using same-drive `COPY_FILE` and cross-drive `OPEN_FILE` / `READ_DATA` / `WRITE_DATA`
- this path has been build-validated only
- it has not been executed on real Ultimate hardware from this environment
