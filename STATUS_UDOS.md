# UDOS Status

## Milestone

Current milestone: Phase 0 complete, Phase 1 complete, Phase 2 resident bootstrap/core complete, Phase 3 native UCI seam complete, Phase 4 filesystem abstraction seam complete, thirteenth Phase 5 resident shell slice complete.

UDOS remains a standalone C64 program path. It is not using CP/M-65 as the runtime environment for this work.

## Completed

- created a separate `udos` repo/work area
- preserved prior CP/M-65 and Action state in notes so the shell/runtime pivot stayed reversible
- audited and built the local AcheronVM dependency
- added a proof image that validates a minimal AcheronVM-to-native banner path in VICE
- added a resident bootstrap/core image that:
  - enters AcheronVM
  - keeps the VM resident
  - exposes a first resident service ABI
  - renders a state-driven shell prompt
- added a native UCI transport seam in `src/asm/uci_transport.inc`
- added the mounted-image abstraction seam for `A:` and `B:`
- added a hardware-backed directory-cache path behind `svc_fs_enum_*`
  - synchronizes the Ultimate DOS backend path with resident drive/directory state through `CHANGE_DIR`
  - queries backend path through `GET_PATH`
  - fills a small resident directory cache through `OPEN_DIR` / `READ_DIR`
  - falls back to the descriptor-backed mock model when hardware transport is unavailable or a query fails
- added a hardware-backed `TYPE` read path
  - synchronizes the backend path through `CHANGE_DIR`
  - opens files through `OPEN_FILE`
  - reads a bounded text buffer through `READ_DATA`
  - closes the handle through `CLOSE_FILE`
  - falls back to the descriptor-backed mock content on hardware/query failure
- added a hardware-backed `DEL` path
  - synchronizes the backend path through `CHANGE_DIR`
  - deletes files through `DELETE_FILE`
  - uses mock deletion only when hardware UCI is unavailable
  - returns an explicit delete failure string on hardware-side errors
- added a hardware-backed `REN` path
  - synchronizes the backend path through `CHANGE_DIR`
  - renames files through `RENAME_FILE`
  - uses mock rename only when hardware UCI is unavailable
  - returns an explicit rename failure string on hardware-side errors
- added a hardware-backed `COPY` path
  - same-drive copies use `COPY_FILE`
  - cross-drive copies stream through source `OPEN_FILE`/`READ_DATA` and destination `OPEN_FILE`/`WRITE_DATA`
  - uses mock copy only when hardware UCI is unavailable
  - returns an explicit copy failure string on hardware-side errors
- enforced flat-vs-tree policy:
  - `D64`/`D71`/`D81` -> flat
  - `DNP` -> tree-capable
- validated the resident shell under VICE with live `GETIN`-backed input
- implemented resident commands:
  - `HELP`
  - `VER`
  - `VOL`
  - `MEM`
  - `DIR`
  - `CD`
  - `MOUNT`
  - `TYPE`
  - `COPY`
  - `REN`
  - `DEL`
  - `QUIT` / `EXIT`
- added a first resident program ABI slice for implicit program launch:
  - prepare program handoff
  - expose resolved target pointer
  - expose command-line pointer and length
  - snapshot run state and exit state
  - return cleanly to the resident shell

## Current Verified Facts

### Phase 1 proof

- autostarts `build/udosboot.prg` in VICE for stable validation
- linked proof entrypoint: `$1810`
- screen banner seen in VICE: `UDOS VM OK`
- marker byte at `$CFFF`: `0x42`
- Acheron dispatcher footprint: `$00E6`
- Acheron runtime footprint: `$072A`
- UDOS proof code footprint: `$002E`

### Resident shell milestone

- linked resident entrypoint: `$1810`
- command keywords now require a separator before arguments
- direct drive tokens now work on the resident path:
  - `A:` -> switch to logical drive `A:`
  - `B:` -> switch to logical drive `B:`
- bare non-keyword input now implies program launch:
  - `DEL BOOT3.PRG` -> delete `BOOT3.PRG`
  - `DELBOOT3` -> implicit launch attempt of `DELBOOT3.PRG`, then `PROGRAM NOT FOUND`
  - `BOOT3 DIR` -> implicit launch of `BOOT3.PRG` with command line `DIR`
- backend-path cache seam is now live behind the filesystem ABI:
  - mock mode synthesizes `/`, `/BIN`, `/SRC`, `/WORK`
  - hardware mode now synchronizes through Ultimate DOS `CHANGE_DIR` and queries `GET_PATH`, but remains unverified
- hardware-backed directory enumeration is now wired behind `svc_fs_enum_*`:
  - hardware mode issues `OPEN_DIR` / `READ_DIR` into a small resident cache
  - current cache budget is `6` entries with names capped at `20` bytes plus terminator
  - VICE still validates only the mock path because no Ultimate UCI transport exists there
- hardware-backed file read is now wired behind `TYPE`:
  - hardware mode issues `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE`
  - the current text read is bounded to the resident response buffer
  - VICE still validates only the mock path because no Ultimate UCI transport exists there
- hardware-backed delete is now wired behind `DEL`:
  - hardware mode issues `DELETE_FILE`
  - VICE still validates only the mock path because no Ultimate UCI transport exists there
- hardware-backed rename is now wired behind `REN`:
  - hardware mode issues `RENAME_FILE`
  - VICE still validates only the mock path because no Ultimate UCI transport exists there
- hardware-backed copy is now wired behind `COPY`:
  - same-drive hardware mode issues `COPY_FILE`
  - cross-drive hardware mode issues source `OPEN_FILE` / `READ_DATA` and destination `OPEN_FILE` / `WRITE_DATA`
  - VICE still validates only the mock path because no Ultimate UCI transport exists there
- implicit program launch now loads a real resident program image:
  - mock mode copies the resolved file content into a bounded resident image buffer
  - hardware mode first attempts `FILE_STAT`
  - hardware mode then attempts `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE`
  - hardware mode can now distinguish `PROGRAM NOT FOUND` from a generic load failure before opening the file
  - VICE validates the loaded image length through resident snapshots
- current VICE-validated transcript:
  - `UDOS FOR COMMODORE 64`
  - `A:D64/> B:`
  - `B:DNP/`
  - `B:DNP/> CD SRC`
  - `B:DNP/SRC`
  - `B:DNP/SRC> COPY BOOT.ASM WORK/BOOT2.PRG`
  - `COPIED`
  - `B:DNP/SRC> CD WORK`
  - `B:DNP/WORK`
  - `B:DNP/WORK> REN BOOT2.PRG BOOT3.PRG`
  - `RENAMED`
  - `B:DNP/WORK> DELBOOT3`
  - `PROGRAM NOT FOUND`
  - `B:DNP/WORK> BOOT3 DIR`
  - `RUN BOOT3.PRG`
  - `ARGS DIR`
  - `B:DNP/WORK> DEL BOOT3.PRG`
  - `DELETED`
  - `B:DNP/WORK> DIR`
  - `B:DNP/WORK EMPTY`
- bind snapshots:
  - `$CFE4 = $01` -> cached backend-path length for `A:` (`/`)
  - `$CFE5 = $05` -> cached backend-path length for `B:` (`/WORK`) after the smoke sequence
  - `$CFE8/$CFE9 = $01/$01` -> `A:` = `D64/flat`
  - `$CFEA/$CFEB = $04/$02` -> `B:` = `DNP/tree`
- current-drive snapshots:
  - `$CFEC = $01` -> current drive `B:`
  - `$CFEE = $02` -> current-drive flags `tree`
  - `$CFF0 = $01` -> transport mode `mock`
  - `$CFF2 = $04` -> current-drive mount kind `DNP`
  - `$CFF4 = $01` -> ABI version
- program ABI snapshots after implicit launch:
  - `$CFF6 = $02` -> program exited
  - `$CFF7 = $00` -> exit status `0`
  - `$CFF8 = $01` -> program drive `B:`
  - `$CFF9 = $03` -> program directory `WORK`
  - `$CFFA = $16` -> loaded image length low byte (`22`)
  - `$CFFB = $00` -> loaded image length high byte
- resident core code footprint: `$3416`
- resident load window in `udos_c64.cfg`: `$4000`

## What Works

- standalone UDOS build and VICE validation
- resident AcheronVM runtime
- resident service ABI
- native UCI detection seam
- synchronous native UCI transfer primitives
- drive bind/query abstraction
- backend-path metadata query seam with hardware `CHANGE_DIR` / `GET_PATH` attempt plus mock fallback
- directory enumeration seam with hardware `OPEN_DIR` / `READ_DIR` attempt plus mock fallback
- file-read seam for `TYPE` with hardware `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE` attempt plus mock fallback
- file-delete seam for `DEL` with hardware `DELETE_FILE` attempt and explicit hardware-error reporting
- file-rename seam for `REN` with hardware `RENAME_FILE` attempt and explicit hardware-error reporting
- file-copy seam for `COPY` with same-drive `COPY_FILE`, cross-drive read/write streaming, and explicit hardware-error reporting
- flat-image rejection for directory-tree semantics
- prompt rendering from live drive/kind/path state
- direct drive-token switching for `A:` and `B:`
- resident file-oriented mock workflow:
  - `DIR`
  - `TYPE`
  - `COPY`
  - `REN`
  - `DEL`
- resident program-handoff mock workflow:
- resident program-handoff and image-load workflow:
  - implicit program launch from a bare non-keyword line
  - `.PRG` suffix added when the target has no extension
  - command-line separation with normal spaces
  - bounded resident image load before handoff
  - return to shell after program exit

## What Is Unverified

- no real C64 Ultimate hardware execution
- no hardware-validated UCI command/data path
- no real mounted-image metadata yet
- no hardware-validated image-backed file delete yet
- no hardware-validated image-backed file rename yet
- no hardware-validated image-backed file copy yet
- no hardware-validated program-image loading yet behind implicit program launch
- no overlay command loader yet

## Next Concrete Step

- replace the current descriptor-backed mock filesystem with real image-backed services behind the existing ABI
- first targets:
  - real mounted-image metadata for `VOL` / `MOUNT`
  - hardware-validate and harden the new program-image load path
- keep shell semantics stable while swapping the backend
