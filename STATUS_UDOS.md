# UDOS Status

## Milestone

Current milestone: Phase 0 complete, Phase 1 complete, Phase 2 bootstrap/core slice complete, Phase 3/4 drive-bind/query seam complete, seventh Phase 5 resident shell slice complete.

## Completed

- created a separate `udos` repo/work area
- preserved the prior CP/M-65 and Action toolchain state in notes
- audited the local AcheronVM repo enough to confirm the build shape
- verified local AcheronVM buildability with:
  - `make -C /mnt/c/test/action/acheronvm test`
- verified local tools exist:
  - `ca65`
  - `ld65`
  - `make`
  - `c1541`
  - `x64sc`
- added a minimal UDOS proof program that:
  - clears the Acheron register stack
  - enters AcheronVM
  - uses VM-side `calln` to reach a native banner routine
  - stamps `UDOS VM OK` into C64 screen RAM
  - writes a marker byte to `$CFFF`
- added a BASIC wrapper generator that parses the linked `.start` label and SYSes to the real entrypoint
- added D64 build paths for the proof and resident images
- validated the proof under VICE by autostarting the D64 and reading screen RAM through the binary monitor
- defined the first resident service ABI draft in `SERVICE_ABI.md`
- defined the first command/module loading notes in `COMMAND_MODEL.md`
- added a resident bootstrap/core image that:
  - enters AcheronVM and stays resident in an idle loop
  - snapshots ABI version `1` from VM-side code
  - uses native services to clear the screen and write VM-provided screen-code strings
  - presents the resident prompt text `UDOS CORE  A:D64>`
  - writes the resident-ready marker `$52` to `$CFFF`
- added the Phase 3/4 drive-bind/query seam:
  - transport selector based on the documented UCI ident register
  - current drive query/set boundary
  - mount-kind query for logical drive
  - mount-flags query for logical drive
  - bind-by-kind service for logical drive
  - prompt rendering from resident drive/mount state
  - mock-mode fallback under VICE
- validated the resident image under VICE by checking screen RAM and service snapshots
- added the first resident command-loop slice:
  - VM-side shell loop with resident prompt rendering
  - live `GETIN`-backed line input with tokenization for first resident commands
  - VICE validation through `-keybuf` instead of the old script-only seam
  - resident transcript for `HELP`, `VER`, `VOL`, `MEM`, and `QUIT`
  - common response emission path driven from command tokens
  - full-screen cursor handling past the first 256 bytes of screen RAM
  - dynamic `VER` mode suffix and dynamic `VOL` output from resident state
- added the second resident shell slice:
  - command + single-argument parsing in the resident line path
  - resident `DIR` and `CD`
  - per-drive current-directory state
  - path-aware prompt rendering
  - explicit flat-image rejection for tree-style `CD`
  - mock directory listings for the current resident mount model
  - VICE-stable inline command shorthand for `CD`/`DIR` because `-keybuf` spacing is not reliable
- added the third resident shell slice:
  - resident `MOUNT`
  - volume-label metadata for `A:` and `B:`
  - `VOL` now reports `label + kind`
  - resident filesystem service exports for current directory, volume metadata, and directory listing lookup
  - `MOUNT` can change `B:` between flat and tree-capable policy during the session
  - VICE-stable inline `MOUNT` shorthand because `-keybuf` spacing is not reliable
- added the fourth resident shell slice:
  - `DIR` now iterates resident entry tables instead of emitting prebuilt listing strings
  - resident `svc_fs_enum_begin` / `svc_fs_enum_next` services
  - directory output stays stable while the shell moves onto an enumeration seam closer to the final filesystem layer
- added the fifth resident shell slice:
  - per-drive mounted-image descriptors now back resident volume metadata and directory enumeration
  - `svc_fs_bind_drive` installs mounted-image metadata when a drive is rebound
  - `VOL` and `DIR` now consume the same descriptor-backed mock image model instead of separate ad hoc tables
  - VICE validation now waits for both a stable banner and the ready marker instead of relying on late-screen `QUIT` text
  - VICE resident automation now uses a delayed key buffer so shell input does not race the autostart path
- added the sixth resident shell slice:
  - resident `TYPE`
  - descriptor-backed mock file record tables under the mounted-image model
  - file path resolution for current directory, explicit drive prefixes, and one directory component
  - dot-tolerant filename matching so emulator automation and normal dotted names resolve the same file
- added the seventh resident shell slice:
  - resident `COPY`
  - mutable `WORK` directory slots per logical drive
  - `DIR` and `TYPE` now observe copied files through the same resident state
  - VICE validation now uses a shorter copy-focused script and checks final screen state plus resident snapshots instead of a late `QUIT` marker

## Current Verified Facts

### Phase 1 proof
- linked proof entrypoint: `$1810`
- screen banner seen in VICE: `UDOS VM OK`
- marker byte at `$CFFF`: `0x42`
- Acheron dispatcher footprint: `$00E6`
- Acheron runtime footprint: `$072A`
- UDOS proof code footprint: `$002E`

### Resident core, drive-bind/query seam, and resident shell
- linked resident entrypoint: `$1810`
- screen transcript seen in VICE:
  - `UDOS CORE`
  - `A:D64/> CDB:`
  - `B:DNP/`
  - `B:DNP/> CDSRC`
  - `B:DNP/SRC`
  - `B:DNP/SRC> COPYBOOTASMWORKBOOTASM`
  - `COPIED`
  - `B:DNP/SRC> CDWORK`
  - `B:DNP/WORK`
  - `B:DNP/WORK> TYPEBOOTASM`
  - `; BOOT.ASM MOCK SOURCE`
- `A:` bind snapshot at `$CFE8/$CFE9`: `D64/flat`
- `B:` bind snapshot at `$CFEA/$CFEB`: `DNP/tree`
- current drive snapshot at `$CFEC`: `B:`
- current flags snapshot at `$CFEE`: `tree`
- transport mode snapshot at `$CFF0`: `mock`
- current mount-kind snapshot at `$CFF2`: `DNP`
- ABI snapshot at `$CFF4`: `1`
- resident core code footprint: `$1A64`
- resident load window in `udos_c64.cfg`: `$2400`

## In Progress

- expanding the transport selector into a real backend
- defining the resident command dispatcher shape

## Not Started

- hardware UCI transport
- mounted-image metadata and open/bind operations beyond kind/flags
- real directory enumeration and file operations
- overlay command loader

## What Works

- the local VM dependency builds in the current environment
- the new project area and build scripts exist
- the Phase 1 AcheronVM proof executes in VICE and can be asserted non-interactively
- the resident bootstrap/core executes in VICE and exposes a first service ABI boundary
- the drive-bind/query seam can be validated under VICE without pretending real Ultimate hardware exists
- the resident loop now exercises live line input under VICE via `-keybuf`
- the resident shell now proves prompting, current-directory state, and `HELP`, `VOL`, `DIR`, `CD`, `MOUNT`, `TYPE`, `COPY`, and `QUIT`
- `VOL` now renders resident label + kind metadata rather than a fixed literal
- `VER` now reflects the current transport mode suffix (`MOCK` in emulator validation)
- `DIR`, `CD`, and `MOUNT` now exercise the flat-image vs DNP tree policy on the resident path
- `DIR` now walks a resident entry iterator instead of reading a prebuilt listing string
- `VOL` and `DIR` now share a descriptor-backed mounted-image mock model per logical drive
- `TYPE` now resolves mock file content through the mounted-image descriptor model
- `COPY` now mutates a resident `WORK` directory model that `DIR` and `TYPE` can read back immediately

## What Is Unverified

- real C64 Ultimate execution
- hardware UCI register behavior on target
- resident memory pressure under actual shell workload
- real D64/D71/D81/DNP filesystem operations
- real C64 Ultimate keyboard behavior on target hardware
- image-backed directory enumeration instead of the current descriptor-backed resident mock listings
- image-backed file metadata and content instead of the current descriptor-backed resident mock file tables
- image-backed mutable file operations instead of the current resident `WORK` slot mock for `COPY`
- file-backed `TYPE`, `COPY`, `REN`, `DEL`, and `RUN`
- real mounted-image metadata instead of the current descriptor-backed resident mock

## Next Concrete Step

- replace the current resident enum tables with image-backed enumeration through the existing `svc_fs_enum_*` seam
- replace the current descriptor-backed mock file tables behind `TYPE` with image-backed file lookup/content
- replace the current mutable `WORK` slot mock behind `COPY` with real image-backed create/update semantics
- replace the current resident volume-label mock with mounted-image metadata from the filesystem layer
- keep `CD` semantics and prompt state stable while the underlying image I/O becomes real
