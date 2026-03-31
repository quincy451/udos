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

## Build The Release Image

```sh
cd /mnt/c/test/action/udos
make release
```

Outputs:
- `build/udos-release.d64`
- `build/udos-release-fs`

Release behavior:
- the release boot image omits the resident `AUTOEXEC.BAT` file entry
- boot reaches the shell prompt directly:
  - `A:D64/>`
- the staged VICE workspace tree for `B:` is under:
  - `build/udos-release-fs/IMAGES/WORK.DNP`
- if the sibling `actionc64u` exporter is present, the staged workspace also
  includes:
  - `build/udos-release-fs/IMAGES/ACTION.DNP`

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
- validates the boot path reaches the resident prompt:
  - `A:D64/>`
- validates the default boot-root `AUTOEXEC.BAT` output:
  - `AUTOEXEC OK`
- verifies `MEM` separately through the Python test suite:
  - derives the launch-capable REU reservation from `build/udos-resident.labels`
  - checks the live shell prints launch-capable RAM usage/free values when REU is present
  - checks the live shell prints the matching REU reservation/free values

Separate VICE smoke targets:
- `make vice-launch`
  - validates implicit launch plus controlled return with `RETTEST DIR`
- `make vice-clobber`
  - validates REU-backed launch/restore with a program that overwrites resident code before returning
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
- `make vice-release`
  - validates the release boot image reaches `A:D64/>` without printing `AUTOEXEC OK`
- `make vice-action-workspace`
  - validates the release workspace exposes `IMAGES/ACTION.DNP`
  - mounts the exported Action bridge payload, lists its root entries, and reads `README.TXT` through the live shell
- `make vice-action-actdir`
  - uses an autoexec-backed Action test image on top of the release workspace
  - validates `ACTDIR.PRG` launches from mounted `ACTION.DNP`
  - enumerates the current directory through the preserved external-tool directory ABI
  - prints the mounted Action workspace root entries and returns to the shell
- `make vice-action-actadd`
  - uses the release image with deterministic typed input on top of the release workspace
  - seeds a project root marked by `ACTION.PROJ`
  - validates `ACTADD.PRG` creates `SRC/HELPER.ACT`
  - reads the created source back through the shell and verifies `PROC HELPER()` / `ENDPROC`
- `make vice-action-actadd-persist`
  - uses the release image with deterministic typed input on top of the release workspace
  - seeds a project root marked by `ACTION.PROJ`
  - reruns `ACTADD.PRG HELPER` and verifies duplicate creation is refused with `EXISTS`
  - verifies the created `src/helper.act` persists on the host fs tree after VICE exits
- `make vice-action-act2save`
  - uses the release image with deterministic typed input on top of the release workspace
  - seeds a project root marked by `ACTION.PROJ`
  - validates `ACT2SAVE.PRG HELPER` launches from mounted `ACTION.DNP`
  - rewrites `SRC/HELPER.ACT` through the preserved external-tool file-save ABI
  - verifies the rewritten host file now contains `PROC HELPER()` instead of `PROC OLDHELPER()`
- `make vice-action-actc`
  - uses the release image with deterministic typed input on top of the release workspace
  - seeds a project root marked by `ACTION.PROJ`
  - validates `ACTC.PRG MAIN` launches from mounted `ACTION.DNP`
  - emits a deterministic `OBJ/MAIN.AVO` object stub as the first UDOS-native compiler front-end slice, including extracted top-level `PROC` export offset/size triplets, compiler-emitted `body_ops`, folded narrow decimal `PrintI` / `PrintIE` `+` / `-` expression chains with inline spaces, current source-inferred runtime-import metadata, and explicit `payload_bytes`
  - verifies the generated host-side object file contents directly because `OBJ/UDOSDIR.TXT` is not yet refreshed reliably enough for stable shell-side `TYPE OBJ/...` readback
- `make vice-action-alink`
  - uses the release image with deterministic typed input on top of a copied Action workspace
  - seeds a project root marked by `ACTION.PROJ` plus deterministic `OBJ/*.AVO` fixtures
  - validates `ALINK.PRG MAIN` through host-side artifact creation instead of screen scraping
  - emits a deterministic `BIN/MAIN.AVM` binary final-image artifact as the first UDOS-native linker slice, using compiler-emitted export sizes plus `body_ops` for direct byte emission
  - current focused proof resolves a wider unresolved external closure with sibling externals from `main`, a shared child object, and a deeper leaf, while carrying child-object integer and string literal pools in the emitted payload
  - verifies the generated host-side binary directly by checking the exact emitted `AVM1` bytes and proving an unused local export is stripped from the final image
- `make vice-action-alink-avmrun`
  - uses the release image with deterministic typed input on top of a copied Action workspace
  - launches `ALINK.PRG MAIN` to generate `BIN/MAIN.AVM`
  - launches `AVMRUN.PRG BIN/MAIN.AVM` against that live linker artifact
  - proves the current linked image executes by printing `HELLOWORLD`, `TOOL7`, and `12342` before returning to `B:DNP/PROJ3>`
- `make vice-action-actc-alink-avmrun`
  - uses the release image with deterministic typed input on top of a copied Action workspace
  - launches `ACTC.PRG MAIN` to generate `OBJ/MAIN.AVO`
  - launches `ALINK.PRG MAIN` to generate `BIN/MAIN.AVM`
  - launches `AVMRUN.PRG BIN/MAIN.AVM` against that live compiler/linker artifact
  - proves the integrated pipeline prints `HELLO`, `TOOL7`, and `12455` before returning to `B:DNP/PROJ3>`
- `make vice-action-actchk`
  - uses the release image with deterministic typed input on top of the release workspace
  - seeds a healthy project root marked by `ACTION.PROJ`
  - validates `ACTCHK.PRG` launches from mounted `ACTION.DNP`
  - verifies expected `SRC/`, `BIN/`, and `OBJ/` directories plus tracked source presence
  - proves the focused healthy-project integrity path returns `ACTCHK OK`
- `make vice-action-actsrc`
  - uses an autoexec-backed Action test image on top of the release workspace
  - seeds a project root marked by `ACTION.PROJ`
  - validates `ACTSRC.PRG` launches from mounted `ACTION.DNP`
  - prints the tracked `ACTION.PROJ` source entries and returns to the shell
- `make vice-action-actfile`
  - uses an autoexec-backed Action test image on top of the release workspace
  - seeds a project root marked by `ACTION.PROJ`
  - validates `ACTFILE.PRG MAIN` launches from mounted `ACTION.DNP`
  - prints `SRC/MAIN.ACT` through the preserved file-load ABI and returns to the shell
- `make vice-action-actwork`
  - uses an autoexec-backed Action test image on top of the release workspace
  - seeds a project root marked by `ACTION.PROJ`
  - validates `ACTWORK.PRG` launches from mounted `ACTION.DNP`
  - reports project-marker presence, expected directories, and manifest module count
- `make vice-action-actmon`
  - uses dedicated typed-input `ACTMON` probes on top of the release workspace
  - the current composite probe script targets `WORK`, `ADD EXTRA`, `REN HELPER RENAMED`, and `DEL HELPER` on seeded Action project states
  - the `ACTMON` front end itself now also carries `COPY <OLD> <NEW>` for tracked-module duplication through the preserved file-copy ABI
  - the intended proof is nested `SRC/<NAME>.ACT` rename/removal, `ACTION.PROJ` update, and shell-side `NO SUCH FILE` readback for `TYPE SRC/HELPER.ACT`
  - the combined target is green again through the generic mounted-tree runner, with a clean host-tree reseed before each phase attempt so partial mutation attempts do not poison later retries
- `make vice-action-actmon-check`
  - uses the focused generic mounted-tree runner on top of the release workspace
  - seeds a healthy Action project root marked by `ACTION.PROJ`
  - validates `ACTMON CHECK` launches from mounted `ACTION.DNP`
  - remains the narrower control proof for the recovered `WORK`/workspace-summary side by requiring `PROJECT YES`, `SRC YES`, `BIN YES`, `OBJ YES`, `MODULES 2`, `MISSING 0`, and `ACTMON OK`
- `make vice-action-actinfo`
  - uses an autoexec-backed Action test image on top of the release workspace
  - validates `ACTINFO.PRG` launches from mounted `ACTION.DNP` and returns to the shell
- `make vice-action-actflow`
  - uses the release image plus deterministic typed input
  - validates `ACTFLOW.BAT` launches from mounted `ACTION.DNP`
  - exercises preserved file save/copy/move/delete/load behavior in one composite Action-side workspace flow
  - proves the final deleted target is gone through shell-side `TYPE`
- `make vice-action-actnew-prg`
  - uses the release image plus deterministic typed input
  - validates `ACTNEW.PRG` launches from mounted `ACTION.DNP`
  - creates `SRC/`, `BIN/`, `OBJ/`, `ACTION.PROJ`, `README.TXT`, and `SRC/MAIN.ACT`
  - returns to UDOS and then reaches `B:DNP/DEMO/SRC>` on a follow-up `CD`
- `make vice-action-actnew-prg-persist`
  - builds a focused resident autoexec image
  - validates `ACTNEW.PRG` creates a host-persistent project tree after VICE exits
  - requires `IMAGES/ACTION.DNP/PROJ2/bin`, `obj`, and `src` to exist
  - requires `IMAGES/ACTION.DNP/PROJ2/ACTION.PROJ` to exist
  - validates host-created file contents through `PROJ2/readme.txt` and `PROJ2/src/main.act`
- `make vice-action-actcopy`
  - uses the release image plus deterministic typed input
  - validates `ACTCOPY.PRG` launches from mounted `ACTION.DNP`
  - copies `OUT.TXT` to `COPY.TXT` through the preserved external-tool file-copy ABI
  - reads `COPY.TXT` back through the shell and verifies `ACTION WRITE OK`
- `make vice-action-actdel`
  - uses the release image plus deterministic typed input
  - validates `ACTDEL.PRG` launches from mounted `ACTION.DNP`
  - deletes `OUT.TXT` through the preserved external-tool file-delete ABI
  - proves the shell reports `NO SUCH FILE` for the deleted file
- `make vice-action-actmove`
  - uses the resident image plus a retrying mounted-tree probe
  - validates `ACTMOVE.PRG` launches from mounted `ACTION.DNP`
  - renames `OUT.TXT` to `NEXT.TXT` through the preserved external-tool file-rename ABI
  - requires `IMAGES/ACTION.DNP/NEXT.TXT` to exist with `ACTION WRITE OK`
- `make vice-action-actmove-persist`
  - uses the resident image plus a retrying mounted-tree probe
  - validates `ACTMOVE.PRG` launches from mounted `ACTION.DNP`
  - validates the host-persistent VICE tree rename path after VICE exits
  - requires `IMAGES/ACTION.DNP/NEXT.TXT` to exist and `OUT.TXT` to be absent
- `make vice-action-actmkdir`
  - uses the release image plus deterministic typed input
  - validates `ACTMKDIR.PRG` launches from mounted `ACTION.DNP`
  - creates `OBJ` through the preserved external-tool directory-mutation ABI
  - proves the shell can enter `B:DNP/OBJ>`
- `make vice-action-actmkdir-persist`
  - uses the resident image plus a retrying mounted-tree probe
  - validates `ACTMKDIR.PRG` launches from mounted `ACTION.DNP`
  - validates the host-persistent VICE tree create-dir path after VICE exits
  - requires `IMAGES/ACTION.DNP/OBJ` to exist
- `make vice-action-actrmdir`
  - uses the release image plus deterministic typed input
  - validates `ACTRMDIR.PRG` launches from mounted `ACTION.DNP`
  - removes `OBJ` through the preserved external-tool directory-mutation ABI
  - proves the shell reports `NO SUCH DIR` for `CD OBJ`
- `make vice-action-actrmdir-persist`
  - uses the resident image plus a retrying mounted-tree probe
  - validates `ACTRMDIR.PRG` launches from mounted `ACTION.DNP`
  - seeds `OBJ` on the host fs before launch, removes it through
    `ACTRMDIR.PRG`, and validates the host-persistent VICE tree remove-dir path
    after VICE exits
  - requires `IMAGES/ACTION.DNP/OBJ` to be absent
- `make vice-action-actwrite`
  - uses the release image plus deterministic typed input
  - validates `ACTWRITE.PRG` launches from mounted `ACTION.DNP`
  - writes `OUT.TXT` through the preserved external-tool file-save ABI
  - reads `OUT.TXT` back through the shell and verifies `ACTION WRITE OK`
- `make vice-action-avminfo`
  - uses the release image plus deterministic typed input
  - validates `AVMINFO.PRG` launches from mounted `ACTION.DNP`
  - loads `HELLO.AVM` through the preserved external-tool file-load ABI
  - validates the `AVM1` header and prints `AVM OK`
- `make vice-action-avmrun`
  - uses the release image plus deterministic typed input
  - validates `AVMRUN.PRG` launches from mounted `ACTION.DNP`
  - loads `UDOSHELLO.AVM` through the preserved external-tool file-load ABI
  - executes the current constrained flagged Acheron-backed `AVM1` subset
  - prints `UDOS AVM OK` and returns to the shell
- `make vice-action-avmrun-flow`
  - uses the release image plus deterministic typed input
  - validates `AVMRUN.PRG` can run `UDOSFLOW.AVM`
  - proves the current constrained subset can execute `jump`, `call`, and `ret`
  - prints `UDOS AVM FLOW OK` and returns to the shell
- `make vice-selftest`
  - builds focused `AUTOEXEC.BAT` images for read, copy, rename, delete, directory, batch, stop-on-error, and implicit launch
  - writes the generated D64 artifacts under `build/udos-selftest-*.d64`
  - writes final-screen captures under `build/udos-selftest-*.actual.txt`
  - diffs those captures against `tests/selftest/expected_*.txt`

Current resident map facts:
- linked entrypoint: `$1810`
- Acheron dispatcher: `$00E6`
- Acheron runtime body: `$072A`
- resident core code: `$662D`
- resident load window in [udos_c64.cfg](/mnt/c/test/action/udos/src/asm/udos_c64.cfg): `$9000`
- VICE validation now enables a `16 MiB` REU by default
- current direct `MEM` probe:
  - `RAM USED 0 FREE 65535 REU USED 35377 FREE 16741839`
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
- `make test` now includes `make vice-selftest`, so the transcript-backed self-test images are part of the normal VICE validation path

## Transcript Self-Test Images

```sh
cd /mnt/c/test/action/udos
make vice-selftest
```

Generated images:
- `build/udos-selftest-read.d64`
- `build/udos-selftest-copy.d64`
- `build/udos-selftest-rename.d64`
- `build/udos-selftest-delete.d64`
- `build/udos-selftest-dir.d64`
- `build/udos-selftest-batch.d64`
- `build/udos-selftest-stop.d64`
- `build/udos-selftest-launch.d64`

Generated transcript captures:
- `build/udos-selftest-read.actual.txt`
- `build/udos-selftest-copy.actual.txt`
- `build/udos-selftest-rename.actual.txt`
- `build/udos-selftest-delete.actual.txt`
- `build/udos-selftest-dir.actual.txt`
- `build/udos-selftest-batch.actual.txt`
- `build/udos-selftest-stop.actual.txt`
- `build/udos-selftest-launch.actual.txt`

Expected transcripts:
- `tests/selftest/expected_read.txt`
- `tests/selftest/expected_copy.txt`
- `tests/selftest/expected_rename.txt`
- `tests/selftest/expected_delete.txt`
- `tests/selftest/expected_dir.txt`
- `tests/selftest/expected_batch.txt`
- `tests/selftest/expected_stop.txt`
- `tests/selftest/expected_launch.txt`

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
