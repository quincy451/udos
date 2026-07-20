# UDOS Hardware Validation Runbook

This runbook is for real Commodore 64 Ultimate hardware validation of the UDOS
resident image and its Ultimate Command Interface paths.

No target hardware validation has been completed from this environment. VICE
validation is necessary, but it does not prove the `Hardware/UCI` column in
`COMMAND_MATRIX.md` because VICE does not provide the Ultimate UCI block.

## Scope

Validate that the resident image works when `svc_transport_get_mode` selects the
hardware UCI backend (`2`) and that failures do not silently fall back to mock
mutation behavior.

Covered hardware-facing paths:

- `MOUNT_DISK` for mounted image binding
- `CHANGE_DIR` and `GET_PATH` for backend path synchronization
- `OPEN_DIR` and `READ_DIR` for tree directory enumeration
- `OPEN_FILE`, `READ_DATA`, and `CLOSE_FILE` for file reads
- `FILE_SEEK` plus `READ_DATA` for flat-image header/root/file traversal
- `CREATE_DIR` for tree directory creation
- `DELETE_FILE` for tree file and empty-directory deletion
- `RENAME_FILE` for tree file rename
- `COPY_FILE` for same-drive tree copies
- `OPEN_FILE`, `READ_DATA`, and `WRITE_DATA` for streamed cross-drive copies
- `FILE_STAT`, `OPEN_FILE`, repeated `READ_DATA`, and `CLOSE_FILE` for implicit
  program and native `UDOV` module loads
- fixed external-tool file rename through same-directory `RENAME_FILE` or
  cross-directory/cross-drive copy followed by `DELETE_FILE`
- fixed external-tool file load/probe through `FILE_STAT`, bounded repeated
  `READ_DATA`, and `CLOSE_FILE`
- fixed external-tool file save through write/create/overwrite `OPEN_FILE`,
  bounded repeated `WRITE_DATA`, and `CLOSE_FILE`
- fixed external-tool streamed binary output through write begin, repeated
  chunk calls, and close
- fixed external-tool source staging through `FILE_STAT`, repeated `READ_DATA`
  into REU, exact-count validation, and `CLOSE_FILE`
- raw flat-image `WRITE_DATA` paths for directory/BAM mutation
- native `UDOV` staging plus recursive `TREE.OVL`, `XCOPY.OVL`, and
  `DELTREE.OVL` execution

The current release implements hardware/UCI tree-file staging for direct PRGs
and native `UDOV` modules through `FILE_STAT`, `OPEN_FILE`, repeated `READ_DATA`
into REU, and `CLOSE_FILE`. That path has not been run on target hardware.
The nested hardware Tool ABI mutation paths are implemented: `TREE` enumerates
through `OPEN_DIR` / `READ_DIR`, `XCOPY` uses `CREATE_DIR`, `COPY_FILE`, or
cross-drive read/write streaming, and `DELTREE` uses `DELETE_FILE` for files and
empty directories. None of these paths has been run on target hardware, so VICE
results for these modules must not be recorded as hardware validation.
The fixed `svc_file_load_sc0` hardware path is also implemented, including
existence-only probes and too-large prefix loads, but remains target-unvalidated.
The fixed `svc_file_save_sc0` hardware path is implemented for explicit-length,
empty, and bounded null-terminated compatibility writes, but also remains
target-unvalidated.
The fixed streamed-write services are implemented for binary payloads and
close-error reporting, but remain target-unvalidated.
The fixed `svc_file_stage_reu_sc0` hardware path is implemented with 24-bit REU
capacity checks and exact-count validation, but remains target-unvalidated.

Do not mark a row in `COMMAND_MATRIX.md` as `Yes` for `Hardware/UCI` until the
relevant sequence below has been run on real hardware and recorded.

## Prerequisites

1. Build from a clean host tree:

```sh
cd ~/action
make clean
make -C udos release
```

2. Copy these outputs to media that the Ultimate can mount or load:

```text
udos/build/udos-release.d64
udos/build/udosres.prg
udos/build/udos-release-fs/IMAGES/WORK.DNP
udos/build/udos-release-fs/IMAGES/ACTION.DNP
```

3. On the Ultimate, arrange the same logical paths used by the VICE probes:

```text
/IMAGES/WORK.DNP
/IMAGES/ACTION.DNP
```

4. Boot `udos-release.d64` or autostart `udosres.prg`.

5. Record the exact Ultimate firmware version, storage device, image paths, and
   UDOS git revisions before running commands.

## Result Record

For each sequence, record:

```text
Date:
Machine / firmware:
Storage device:
UDOS revision:
ActionC64U revision:
Boot artifact:
Sequence name:
Commands typed:
Observed transcript:
Expected transcript matched: yes/no
Artifacts changed on media:
Failure notes:
```

A failure is useful data. Do not change documentation from `Partial`/`No` to
`Yes` until the failure is explained and the fixed image is rerun.

## Smoke Sequence

Expected purpose: prove boot, prompt, hardware path detection boundary, volume
reporting, mounted image bind, tree navigation, file read, and launch-capable
memory reporting.

```text
A:D64/> MEM
A:D64/> MOUNT B: /IMAGES/WORK.DNP
A:D64/> VOL
A:D64/> B:
B:DNP/> DIR
B:DNP/> CD SRC
B:DNP/SRC> TYPE BOOT.ASM
```

Expected observations:

- `MEM` returns a prompt without corrupting the shell.
- `MOUNT` reports `B:WORK DNP` or an explicit mount failure.
- `VOL` reports mounted `A:` and `B:` names.
- `DIR` lists `BIN/`, `SRC/`, and `WORK/`.
- `TYPE BOOT.ASM` prints the known test source text.

Validated rows if successful: `MEM`, `MOUNT`, `VOL`, `DIR`, `CD`, `TYPE` for the
hardware-backed DNP tree path.

## Tree Mutation Sequence

Expected purpose: prove hardware tree `COPY`, `REN`, `DEL`, and wildcard delete
without relying on the mock backend.

```text
B:DNP/SRC> COPY BOOT.ASM /WORK/BOOT2.ASM
B:DNP/SRC> COPY HELLO.PRG /WORK/HELLO2.PRG
B:DNP/SRC> CD /WORK
B:DNP/WORK> TYPE BOOT2.ASM
B:DNP/WORK> REN BOOT2.ASM BOOT3.ASM
B:DNP/WORK> TYPE BOOT3.ASM
B:DNP/WORK> DEL HELLO2.PRG
B:DNP/WORK> DIR
```

Expected observations:

- Copies report `COPIED` and create files visible after changing directories.
- Rename reports `RENAMED`; the new name can be read and the old name is absent.
- Delete reports `DELETED`; `HELLO2.PRG` no longer appears in `DIR`.

Validated rows if successful: `COPY`, `REN`, `DEL`, `TYPE`, and `DIR` for the
hardware-backed DNP tree mutation path.

## External Tool Load Sequence

Expected purpose: prove that launched Action tools can probe and load hardware
tree files through the fixed ABI after low resident code has been overwritten.

Before copying `ACTION.DNP` to media, prepare `PROJ3` with:

- `SRC/ORPHAN.ACT`: a small source file not listed in `ACTION.PROJ`
- `SRC/LARGE.ACT`: a source file longer than 255 bytes
- `ACTION.PROJ`: add `LARGE.ACT` and `MISSING.ACT`; leave `MISSING.ACT` absent

```text
A:D64/> MOUNT B: /IMAGES/ACTION.DNP
A:D64/> B:
B:DNP/> CD PROJ3
B:DNP/PROJ3> ACTADD ORPHAN
B:DNP/PROJ3> ACTFILE MAIN
B:DNP/PROJ3> ACTFILE LARGE
B:DNP/PROJ3> ACTFILE MISSING
```

Expected observations:

- `ACTADD ORPHAN` reports `EXISTS`, proving the zero-destination/zero-limit
  existence probe found the untracked file without opening it for a load
- `ACTFILE MAIN` prints the complete known source and returns to the same prompt
- `ACTFILE LARGE` prints the first 255 bytes followed by `TRUNCATED`, proving
  that too-large status is returned only after the bounded prefix is loaded
- `ACTFILE MISSING` reports `NO FILE`
- none of the commands corrupts the current shell drive or directory

Validated component if successful: fixed external-tool `svc_file_load_sc0`
probe, bounded load, too-large, and missing-file hardware/UCI paths.

## External Tool Save Sequence

Expected purpose: prove that launched Action tools can create and overwrite
hardware tree files through the fixed save ABI after low resident code has been
overwritten.

Before copying `ACTION.DNP` to media, ensure `SAVETEST` does not exist and place
a longer preexisting `PROJ3/OUT.TXT` file on the image.

```text
A:D64/> MOUNT B: /IMAGES/ACTION.DNP
A:D64/> B:
B:DNP/> ACTNEW SAVETEST
B:DNP/> CD SAVETEST
B:DNP/SAVETEST> TYPE ACTION.PROJ
B:DNP/SAVETEST> TYPE SRC/MAIN.ACT
B:DNP/SAVETEST> CD /PROJ3
B:DNP/PROJ3> ACTWRITE OUT.TXT
B:DNP/PROJ3> TYPE OUT.TXT
```

Expected observations:

- `ACTNEW SAVETEST` reports `ACTNEW OK`, proving repeated explicit-length saves
  created the project marker, README, source, and directory manifests
- both `TYPE` commands in `SAVETEST` print the generated project content
- `ACTWRITE OUT.TXT` reports `ACTWRITE OK`, proving the zero-length
  null-terminated compatibility path
- the final `TYPE OUT.TXT` prints exactly `ACTION WRITE OK`, with no tail from
  the longer preexisting file
- all commands return to the expected drive and directory prompt

Validated component if successful: fixed external-tool `svc_file_save_sc0`
explicit-length, overwrite/truncate, and null-terminated hardware/UCI paths.

## External Tool Stream Write Sequence

Expected purpose: prove write begin/chunk/close preserves binary zero bytes and
keeps one hardware target open across separate fixed ABI calls.

Before copying `ACTION.DNP` to media, prepare `STREAMTEST` with a valid
`ACTION.PROJ` that tracks `MAIN.ACT` and an `OBJ/MAIN.OBJ` file containing:

```text
OBJ1
ONELOAD DIAGNOSTIC
```

Then run:

```text
A:D64/> MOUNT B: /IMAGES/ACTION.DNP
A:D64/> B:
B:DNP/> CD STREAMTEST
B:DNP/STREAMTEST> ACTSAVE MAIN
B:DNP/STREAMTEST> BIN/MAIN.PRG
```

Expected observations:

- `ACTSAVE MAIN` reports `ACT2SAVE OK`
- `BIN/MAIN.PRG` is exactly 18 bytes and contains
  `00 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF`
- launching `BIN/MAIN.PRG` returns to `B:DNP/STREAMTEST>` without a load or
  program failure
- no VICE/host writeback record is involved in creating the hardware file

Validated component if successful: fixed external-tool
`svc_file_write_begin_sc0`, `svc_file_write_chunk_sc0`, and
`svc_file_write_close_sc0` hardware/UCI paths.

## External Tool REU Stage Sequence

Expected purpose: prove that ACTC can stage and page a hardware tree source file
through the fixed REU service after its compiler image has overwritten low
resident code.

Before copying `ACTION.DNP` to media, prepare `STAGETEST` with normal `SRC/`,
`OBJ/`, and `BIN/` directories plus an `ACTION.PROJ` tracking `MAIN.ACT`. Make
`SRC/MAIN.ACT` larger than 20 KiB by placing legal comments or whitespace before
a small `PROC MAIN()` body, and retain the exact host byte count for comparison.

```text
A:D64/> MOUNT B: /IMAGES/ACTION.DNP
A:D64/> B:
B:DNP/> CD STAGETEST
B:DNP/STAGETEST> ACTC MAIN
B:DNP/STAGETEST> TYPE OBJ/MAIN.OBJ
```

Expected observations:

- `ACTC MAIN` completes without `SOURCE FAIL`, `SOURCE TOO LARGE`, or
  `COMPILE FAIL`
- the compiler discovers `PROC MAIN()` beyond the first source window and emits
  `OBJ/MAIN.OBJ`
- `TYPE OBJ/MAIN.OBJ` begins with `OBJ1` and includes the `MAIN` export
- the recorded source size plus ACTC's REU destination remains within the
  24-bit REU address space
- the shell returns to `B:DNP/STAGETEST>` with no resolver-state corruption

Validated component if successful: fixed external-tool
`svc_file_stage_reu_sc0` hardware/UCI `FILE_STAT`, read-to-REU, final-count,
close, and return paths.

## External Tool Rename Sequence

Expected purpose: prove that a launched Action tool can call the fixed rename
ABI after its image has overwritten low resident code, including both the
same-directory UCI command and the cross-directory copy/delete fallback.

```text
A:D64/> MOUNT B: /IMAGES/ACTION.DNP
A:D64/> B:
B:DNP/> COPY SRC/HELLO.ACT RENAME1.ACT
B:DNP/> ACTMOVE RENAME1.ACT RENAME2.ACT
B:DNP/> TYPE RENAME2.ACT
B:DNP/> TYPE RENAME1.ACT
B:DNP/> MD MOVETMP
B:DNP/> ACTMOVE RENAME2.ACT MOVETMP/RENAME3.ACT
B:DNP/> TYPE MOVETMP/RENAME3.ACT
B:DNP/> TYPE RENAME2.ACT
B:DNP/> DEL MOVETMP/RENAME3.ACT
B:DNP/> RD MOVETMP
```

Expected observations:

- the first `ACTMOVE` returns without `MOVE FAIL`, uses `RENAME_FILE`, and leaves
  only `RENAME2.ACT`
- the second `ACTMOVE` returns without `MOVE FAIL`, copies into `MOVETMP`, then
  removes the source
- both destination `TYPE` commands print the sample source, while
  `TYPE RENAME1.ACT` and the final `TYPE RENAME2.ACT` report `NO SUCH FILE`
- cleanup removes both the staged file and temporary directory

Validated component if successful: fixed external-tool `svc_file_rename_sc0`
for same-directory and cross-directory hardware/UCI paths.

## Directory Mutation Sequence

Expected purpose: prove tree directory creation/removal and non-empty directory
rejection.

```text
B:DNP/> MD NEW
B:DNP/> CD NEW
B:DNP/NEW> CD /
B:DNP/> RD NEW
B:DNP/> CD NEW
B:DNP/> RD SRC
```

Expected observations:

- `MD NEW` reports `CREATED`.
- `CD NEW` succeeds.
- `RD NEW` reports `REMOVED`.
- `CD NEW` reports `NO SUCH DIR` after removal.
- `RD SRC` reports `DIR NOT EMPTY`.

Validated rows if successful: `MD` and `RD` for hardware-backed DNP tree paths.

## Wildcard Sequence

Expected purpose: prove wildcard copy/delete patterns against a real tree mount.

```text
B:DNP/> CD SRC
B:DNP/SRC> COPY *.* /WORK
B:DNP/SRC> CD /WORK
B:DNP/WORK> DIR
B:DNP/WORK> CD /SRC
B:DNP/SRC> DEL *.PRG
B:DNP/SRC> DIR
```

Expected observations:

- `COPY *.* /WORK` reports `COPIED` and copied `BOOT.ASM` plus `HELLO.PRG` are visible in `/WORK`.
- `DEL *.PRG` reports `DELETED` and `HELLO.PRG` is absent from the final `DIR`.

Validated rows if successful: wildcard `COPY` and wildcard `DEL` for the
hardware-backed DNP tree path.

## Program Launch Sequence

Expected purpose: prove hardware-backed implicit PRG loading, argument passing,
return to resident shell, and resident recovery after launched code returns.

```text
B:DNP/> CD SRC
B:DNP/SRC> RETTEST DIR
B:DNP/SRC> CLOBBER
B:DNP/SRC> DIR
```

Expected observations:

- `RETTEST DIR` prints `RUN RETTEST.PRG` and `ARGS DIR`.
- Prompt returns to `B:DNP/SRC>`.
- `CLOBBER` returns to the prompt and a following `DIR` still works.

Validated rows if successful: bare program launch for hardware-backed tree PRG
loads and REU-backed resident restore.

## Command Overlay Sequence

Expected purpose: prove hardware/UCI tree-file staging into REU, native `UDOV`
validation, module entry, Tool ABI calls, and return to the resident shell.

```text
B:DNP/> TREE SRC
B:DNP/> XCOPY SRC OVCOPY
B:DNP/> TREE OVCOPY
B:DNP/> DELTREE OVCOPY
B:DNP/> DIR
```

Expected observations:

- `TREE SRC` loads `TREE.OVL`, recursively lists the source tree, and returns to
  the prompt.
- `XCOPY` creates the recursive `OVCOPY` tree and `DELTREE` removes it through
  the hardware Tool ABI mutation paths.
- A missing, truncated, malformed, wrong-command, or wrong-ABI module never
  receives control.
- The final `DIR` and prompt remain usable after every module return.

The hardware Tool ABI mutation implementation remains diagnostic until this
sequence passes on target. Do not mark the hardware rows `Yes` unless the full
filesystem effects and post-return state are verified.

Validated rows if successful: `TREE`, `XCOPY`, and `DELTREE` for hardware-backed
DNP trees, limited to the commands whose complete expected effects pass.

## Flat Image Sequence

Expected purpose: prove raw flat-image handling for `D64`, `D71`, and `D81`
mounts. Run the sequence once per image type.

```text
A:D64/> MOUNT B: /IMAGES/FLAT.D64
A:D64/> VOL
A:D64/> B:
B:D64/> DIR
B:D64/> TYPE HELLO
B:D64/> COPY HELLO COPY1
B:D64/> REN COPY1 COPY2
B:D64/> DEL COPY2
B:D64/> TYPE COPY2
```

Repeat with equivalent `D71` and `D81` image names.

Expected observations:

- `VOL` imports the flat-image label instead of using only path-derived text.
- `DIR` lists root entries.
- `TYPE HELLO` reads through raw directory/sector traversal.
- `COPY`, `REN`, and `DEL` mutate the flat image and report explicit errors on failure.
- `TYPE COPY2` reports `NO SUCH FILE` after delete.

Validated rows if successful: `VOL`, `DIR`, `TYPE`, `COPY`, `REN`, `DEL`, and
bare launch if a PRG is also tested on `D64`, `D71`, and `D81` flat images.

## Batch Sequence

Expected purpose: prove mounted-image `.BAT` execution and stop-on-error behavior
outside the VICE fsdevice path.

```text
B:DNP/> CD SRC
B:DNP/SRC> ARGS ONE TWO THREE
B:DNP/SRC> STOP
```

Expected observations:

- `ARGS ONE TWO THREE` expands `%1`, `%2`, and `%3` and prints `ONE/TWO/THREE`.
- `STOP` prints `BEFORE`, then stops after the expected missing-file error and does not print `AFTER`.

Validated rows if successful: batch `.BAT` for hardware-backed tree mounts.

## Updating Project Status

After a successful hardware run:

1. Save the result records under a dated local archive outside tracked build output.
2. Update `COMMAND_MATRIX.md` only for rows whose full sequence passed.
3. Update `STATUS_UDOS.md` and `MILESTONE_HANDOFF.md` to replace the relevant
   `no hardware-validated ...` line with a concrete date and scope.
4. Keep failures documented as `Partial`, not `Yes`.
5. Rerun host validation after any fix:

```sh
make clean
make test
```
