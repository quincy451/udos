# UDOS Status

## Milestone

Current milestone: Phase 0 complete, Phase 1 complete.

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
- added a D64 build path for the proof image
- validated the proof under VICE by autostarting the D64 and reading screen RAM through the binary monitor

## Current Verified Facts

- linked proof entrypoint: `$1810`
- screen banner seen in VICE: `UDOS VM OK`
- marker byte at `$CFFF`: `0x42`
- Acheron dispatcher footprint: `$00E6`
- Acheron runtime footprint: `$072A`
- UDOS proof code footprint: `$002E`

## In Progress

- resident ABI definition for the first shell-facing services
- resident bootstrap/core planning beyond the proof

## Not Started

- native bootstrap beyond the proof program
- resident command dispatcher
- UCI transport
- filesystem abstraction
- logical drive manager
- shell parser and resident commands
- overlay command loader

## What Works

- the local VM dependency builds in the current environment
- the new project area and build scripts exist
- the Phase 1 AcheronVM proof executes in VICE and can be asserted non-interactively

## What Is Unverified

- real C64 Ultimate execution
- resident memory pressure under actual shell workload
- UCI hardware contract
- D64/D71/D81/DNP filesystem layer

## Next Concrete Step

- implement the Phase 2 resident bootstrap skeleton and freeze the first service ABI for console, memory, mount/query, and command dispatch entrypoints
