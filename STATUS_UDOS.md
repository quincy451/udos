# UDOS Status

## Milestone

Current milestone: Phase 0 complete, Phase 1 complete, Phase 2 resident bootstrap/core complete, Phase 3 native UCI seam complete, Phase 4 filesystem abstraction seam complete, tenth Phase 5 resident shell slice complete.

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
  - `RUN`
  - `QUIT` / `EXIT`
- added a first resident program ABI slice for `RUN`:
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
- command keywords now require a separator before arguments:
  - `DEL BOOT2ASM` -> delete `BOOT2ASM`
  - `DELBOOT2ASM` -> bare program token, resolved through `RUN`, then `PROGRAM NOT FOUND`
- backend-path cache seam is now live behind the filesystem ABI:
  - mock mode synthesizes `/`, `/BIN`, `/SRC`, `/WORK`
  - hardware mode is wired for Ultimate DOS `GET_PATH`, but remains unverified
- current VICE-validated transcript:
  - `UDOS FOR COMMODORE 64`
  - `A:D64/> CD B:`
  - `B:DNP/`
  - `B:DNP/> CD SRC`
  - `B:DNP/SRC`
  - `B:DNP/SRC> COPY BOOT.ASM WORK/BOOTASM`
  - `COPIED`
  - `B:DNP/SRC> CD WORK`
  - `B:DNP/WORK`
  - `B:DNP/WORK> REN BOOTASM BOOT2ASM`
  - `RENAMED`
  - `B:DNP/WORK> DELBOOT2ASM`
  - `PROGRAM NOT FOUND`
  - `B:DNP/WORK> RUN BOOT2ASM DIR`
  - `RUN BOOT2ASM`
  - `ARGS DIR`
  - `B:DNP/WORK> DEL BOOT2ASM`
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
- program ABI snapshots after `RUN`:
  - `$CFF6 = $02` -> program exited
  - `$CFF7 = $00` -> exit status `0`
  - `$CFF8 = $01` -> program drive `B:`
  - `$CFF9 = $03` -> program directory `WORK`
- resident core code footprint: `$2560`
- resident load window in `udos_c64.cfg`: `$3000`

## What Works

- standalone UDOS build and VICE validation
- resident AcheronVM runtime
- resident service ABI
- native UCI detection seam
- synchronous native UCI transfer primitives
- drive bind/query abstraction
- backend-path metadata query seam with mock fallback
- flat-image rejection for directory-tree semantics
- prompt rendering from live drive/kind/path state
- resident file-oriented mock workflow:
  - `DIR`
  - `TYPE`
  - `COPY`
  - `REN`
  - `DEL`
- resident program-handoff mock workflow:
  - `RUN`
  - command-line separation with normal spaces
  - return to shell after program exit

## What Is Unverified

- no real C64 Ultimate hardware execution
- no hardware-validated UCI command/data path
- no real image-backed `D64`/`D71`/`D81`/`DNP` enumeration yet
- no real mounted-image metadata yet
- no real image-backed file mutation yet
- no real program-image loading yet behind `RUN`
- no overlay command loader yet

## Next Concrete Step

- replace the current descriptor-backed mock filesystem with real image-backed services behind the existing ABI
- first targets:
  - real mounted-image metadata for `VOL` / `MOUNT`
  - real directory enumeration for `DIR`
  - real file lookup/read/write/rename/delete behind `TYPE` / `COPY` / `REN` / `DEL`
  - real program lookup/load behind `RUN`
- keep shell semantics stable while swapping the backend
