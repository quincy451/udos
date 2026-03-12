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
- drives the live resident shell with real mount syntax, direct drive switching, and explicit separators:
  - `MOUNT B: /IMAGES/ALT.D81`
  - `VOL`
  - `MOUNT B: /IMAGES/WORK.DNP`
  - `VOL`
  - `B:`
  - `CD SRC`
  - `COPY BOOT.ASM WORK/BOOT2.PRG`
  - `COPY BOOT.ASM WORK/BOOT4.ASM`
  - `CD WORK`
  - `REN BOOT2.PRG BOOT3.PRG`
  - `DELBOOT3`
  - `DEL *.PRG`
  - `DIR`
- verifies command-keyword separation:
  - `DELBOOT3` must not be treated as `DEL BOOT3.PRG`
  - it is treated as a bare program token and returns `PROGRAM NOT FOUND`
- verifies reserved-but-unimplemented drive tokens:
  - `C:` returns `DRIVE NOT PRESENT`
  - `D:` returns `DRIVE NOT PRESENT`
- verifies implicit program launch separately through `make vice-launch`:
  - `BOOT3 DIR` resolves as `BOOT3.PRG`
  - `DIR` is passed as the command line
- verifies wildcard copy separately through `make vice-copy`:
  - `COPY *.* WORK` copies both `BOOT.ASM` and `HELLO.PRG`
- verifies reserved drive-token handling separately through `make vice-drive`:
  - `C:` returns `DRIVE NOT PRESENT`
  - `D:` returns `DRIVE NOT PRESENT`
- verifies real VICE tree write behavior separately:
  - `make vice-real-tree-write`
  - `make vice-real-tree-rename`
  - `make vice-real-tree-wild`
 - verifies resident batch support separately:
  - `make vice-batch-args`
  - `make vice-batch-stop`
  - `make vice-autoexec`
- verifies `MEM` separately through the Python test suite:
  - derives resident usage from `build/udos-resident.labels`
  - checks the live shell prints matching decimal RAM usage/free values
  - checks the current REU placeholder line remains `REU USED 0 FREE 16777216`
- verifies mounted-image parsing and label derivation:
  - `MOUNT B: /IMAGES/ALT.D81` yields `B:ALT D81`
  - `MOUNT B: /IMAGES/WORK.DNP` restores `A:SYSTEM D64 B:WORK DNP`
- verifies limited wildcard delete:
  - `DEL *.PRG` deletes `BOOT3.PRG`
  - `DIR` still shows `BOOT4.ASM`
- verifies real VICE tree write-side lifecycles:
  - exact `COPY` / `REN` / `DEL` on created files
  - exact host-backed `REN`
  - wildcard `COPY` and `DEL`
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
  - loaded program image length = `22` bytes (`BOOT3.PRG` from the mock `BOOT.ASM` content)

Current validated resident transcript from `make vice-resident`:

```text
UDOS FOR COMMODORE 64
  A:D64/> MOUNT B: /IMAGES/WORK.DNP
  A:D64/> VOL
A:SYSTEM D64 B:WORK DNP
  A:D64/> B:
B:DNP/
  B:DNP/> CD SRC
B:DNP/SRC
  B:DNP/SRC> COPY BOOT.ASM WORK/BOOT2.PRG
COPIED
  B:DNP/SRC> COPY BOOT.ASM WORK/BOOT4.ASM
COPIED
  B:DNP/SRC> CD WORK
  B:DNP/WORK
  B:DNP/WORK> REN BOOT2.PRG BOOT3.PRG
RENAMED
  B:DNP/WORK> DELBOOT3
PROGRAM NOT FOUND
  B:DNP/WORK> DEL *.PRG
DELETED
  B:DNP/WORK> DIR
B:DNP/WORK BOOT4.ASM
```

Separate VICE smoke targets:
- `make vice-launch`
  - validates implicit launch with `BOOT3 DIR`
- `make vice-copy`
  - validates wildcard copy with `COPY *.* WORK`
- `make vice-drive`
  - validates reserved `C:` / `D:` drive tokens
- `make vice-real-tree-write`
  - validates exact VICE tree `COPY` / `REN` / `DEL`
- `make vice-real-tree-rename`
  - validates host-backed VICE tree `REN`
- `make vice-real-tree-wild`
  - validates VICE tree wildcard `COPY` and `DEL`
- `make vice-real-tree-dir`
  - validates VICE tree `MD`, `CD`, and empty-directory `RD`
- `make vice-real-tree-rmdir`
  - validates VICE tree non-empty `RD` rejection
- `make vice-batch-args`
  - validates `%1` / `%2` / `%3` expansion through `ARGS.BAT`
- `make vice-batch-stop`
  - validates stop-on-error through `STOP.BAT`
- `make vice-autoexec`
  - validates boot `AUTOEXEC.BAT` from the default `A:` boot root

Current resident map facts:
- linked entrypoint: `$1810`
- Acheron dispatcher: `$00E6`
- Acheron runtime body: `$072A`
- resident core code: `$6A50`
- resident load window in [udos_c64.cfg](/mnt/c/test/action/udos/src/asm/udos_c64.cfg): `$9000`
- hardware directory cache budget:
  - `6` entries per drive
  - `20` bytes per cached name
  - flat-image root parsing currently reads `247` bytes from each directory sector because only entry metadata and names are needed
- hardware `TYPE` read budget:
  - one bounded resident text buffer per command
  - flat-image hardware mode now also carries a `256` byte raw sector buffer for chained sector reads
  - fallback to mock content when UCI/file access fails
- hardware `DEL` flat-image budget:
  - one raw sector scratch buffer
  - one raw directory-sector buffer
  - one primary BAM sector buffer
  - one secondary BAM sector buffer for `D71`
- hardware `REN` flat-image budget:
  - one raw sector scratch buffer
  - one raw directory-sector buffer
  - exact-only rename with no wildcard expansion
- hardware implicit-launch budget:
  - one bounded resident image buffer per command
  - current buffer size: `255` bytes
  - flat-image hardware mode now first resolves the file through raw root-directory parsing and chained sector reads
  - tree-capable hardware mode still probes size/existence with `FILE_STAT` before opening the file
- hardware mount path:
  - shell syntax is `MOUNT <drive>: <image-path>`
  - the resident shell currently maps `A:` to IEC `8` and `B:` to IEC `9`
  - hardware mode issues Ultimate DOS `MOUNT_DISK (0x23)`
  - flat-image hardware mode now also attempts `OPEN_FILE (0x02)` + `FILE_SEEK (0x06)` + `READ_DATA (0x04)` against the mounted image path to import the filesystem header label for `D64` / `D71` / `D81`
  - when that header import is unavailable or fails, the resident label falls back to the mounted image basename

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
  A:D64/> MOUNT B: /IMAGES/WORK.DNP
  A:D64/> VOL
A:SYSTEM D64 B:WORK DNP
  A:D64/> B:
B:DNP/
  B:DNP/> CD SRC
B:DNP/SRC
  B:DNP/SRC> COPY BOOT.ASM WORK/BOOT2.PRG
COPIED
  B:DNP/SRC> COPY BOOT.ASM WORK/BOOT4.ASM
COPIED
  B:DNP/SRC> CD WORK
  B:DNP/WORK
  B:DNP/WORK> REN BOOT2.PRG BOOT3.PRG
RENAMED
  B:DNP/WORK> DELBOOT3
PROGRAM NOT FOUND
  B:DNP/WORK> DEL *.PRG
DELETED
  B:DNP/WORK> DIR
B:DNP/WORK BOOT4.ASM
```

Until that run happens on real hardware, all current validation should be described as emulator validation only.

Hardware-specific note:
- the resident image now contains a real flat-image root-directory path using `OPEN_FILE`, `FILE_SEEK`, and `READ_DATA`
- the resident image also retains the Ultimate DOS directory-enumeration path using `CHANGE_DIR`, `GET_PATH`, `OPEN_DIR`, and `READ_DIR` for tree-capable mounts
- the resident image now also contains a real Ultimate DOS `TYPE` path using `CHANGE_DIR`, `OPEN_FILE`, `READ_DATA`, and `CLOSE_FILE`
- flat-image mounts now additionally contain a raw file-content path using image `OPEN_FILE`, repeated `FILE_SEEK`, and chained `READ_DATA`
- the resident image now also contains a real Ultimate DOS `DEL` path using `CHANGE_DIR` and `DELETE_FILE`
- flat-image mounts now additionally contain a raw delete path using root-directory lookup, chained sector traversal, and BAM updates through image `OPEN_FILE`, `FILE_SEEK`, `READ_DATA`, and `WRITE_DATA`
- the resident image now also contains a real Ultimate DOS `REN` path using `CHANGE_DIR` and `RENAME_FILE`
- flat-image mounts now additionally contain a raw rename path using root-directory lookup and direct directory-entry rewrite through image `OPEN_FILE`, `FILE_SEEK`, `READ_DATA`, and `WRITE_DATA`
- the resident image now also contains a real Ultimate DOS `COPY` path using same-drive `COPY_FILE` and cross-drive `OPEN_FILE` / `READ_DATA` / `WRITE_DATA`
- the resident image now also contains a real Ultimate DOS `MOUNT` path using `MOUNT_DISK`
- the resident image now also contains a flat-image label-import path using `OPEN_FILE`, `FILE_SEEK`, and `READ_DATA`
- the resident image now also contains a flat-image implicit-launch path using raw directory lookup and chained sector reads
- this path has been build-validated only
- it has not been executed on real Ultimate hardware from this environment
