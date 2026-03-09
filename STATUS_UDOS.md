# UDOS Status

## Milestone

Current milestone: Phase 0 complete, Phase 1 complete, Phase 2 bootstrap/core slice complete, Phase 3/4 state-query seam complete.

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
- added the Phase 3/4 state-query seam:
  - transport selector based on the documented UCI ident register
  - current drive query/set boundary
  - mount-kind query for logical drive
  - mount-flags query for logical drive
  - mock-mode fallback under VICE
- validated the resident image under VICE by checking screen RAM and service snapshots

## Current Verified Facts

### Phase 1 proof
- linked proof entrypoint: `$1810`
- screen banner seen in VICE: `UDOS VM OK`
- marker byte at `$CFFF`: `0x42`
- Acheron dispatcher footprint: `$00E6`
- Acheron runtime footprint: `$072A`
- UDOS proof code footprint: `$002E`

### Resident core and state-query seam
- linked resident entrypoint: `$1810`
- screen prompt seen in VICE: `UDOS CORE  A:D64>`
- current drive snapshot at `$CFF4`: `0x00`
- mount-flags snapshot at `$CFF6`: `0x01`
- transport mode snapshot at `$CFF8`: `0x01`
- mount-kind snapshot at `$CFFA`: `0x01`
- ABI snapshot at `$CFFC`: `0x01`
- ready marker at `$CFFF`: `0x52`
- resident core code footprint: `$00BD`

## In Progress

- expanding the transport selector into a real backend
- defining the resident command dispatcher shape

## Not Started

- hardware UCI transport
- mounted-image bind/mount operations
- logical drive directory state
- shell parser and resident commands
- overlay command loader

## What Works

- the local VM dependency builds in the current environment
- the new project area and build scripts exist
- the Phase 1 AcheronVM proof executes in VICE and can be asserted non-interactively
- the resident bootstrap/core executes in VICE and exposes a first service ABI boundary
- the state-query seam can be validated under VICE without pretending real Ultimate hardware exists

## What Is Unverified

- real C64 Ultimate execution
- hardware UCI register behavior on target
- resident memory pressure under actual shell workload
- real D64/D71/D81/DNP filesystem operations
- command input and dispatch inside the resident loop

## Next Concrete Step

- add mounted-image bind/query expansion and make the transport selector feed a real hardware backend when the UCI ident probe succeeds
