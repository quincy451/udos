# UDOS Pivot Plan

## Direction Change

This workspace is pivoting away from additional CP/M-65 feature work for the new
shell/runtime effort.

The new target is a Commodore 64 Ultimate resident shell/runtime environment
implemented primarily in AcheronVM, with only small native 6502 glue for the
hardware edge.

## Preserved Prior State

As of 2026-03-09, the prior repositories remain in place and are preserved as
reference state rather than active implementation bases for UDOS shell logic.

- `../acheronvm` at `bc09f42` on `master`
  - locally dirty worktree
  - treated as a dependency and reference ISA/runtime source
- `../actionc64u` at `412c898` on `master`
  - local changes only in `docs/blockers.md` and `docs/inspiration/action_manual.txt`
  - preserved as the current Action toolchain work state
- `../cpm65-u64` at `3a89f51` on `master`
  - heavily dirty worktree from prior image/boot experiments
  - explicitly out of scope for new shell/runtime feature development

Preserved artifacts of interest:
- `../actionc64u/build/actionc64u_c64.d64`
- `../actionc64u/build/verify_transcript.txt`
- `../cpm65-u64/images/c64_iec_1581.d81`
- `../cpm65-u64/images/c64_iec_1581_raw.d81`
- `../cpm65-u64/images/c64_iec_workspace.d2m`

## Project Area

UDOS now lives in this separate repo/work area:
- `/mnt/c/test/action/udos`
- current working branch: `pivot/udos-shell`

This separation is deliberate:
- no new shell/services logic goes into CP/M-65
- AcheronVM remains a build dependency, not a place to bury product-specific shell code
- the Action development tooling can resume later without mixing its history with UDOS bootstrap work

## Implementation Phases

### Phase 0
- capture pivot summary
- preserve prior repo states in notes
- create separate UDOS repo/work area

Status:
- complete

### Phase 1
- audit local AcheronVM source and build workflow
- verify buildability in the current environment
- produce a minimal C64 proof that enters AcheronVM and runs VM-side code

Status:
- complete
- validated in VICE with a D64 image and binary-monitor screen check

### Phase 2
- build a minimal native bootstrap for UDOS
- keep the AcheronVM runtime resident after first load
- define the resident service table ABI
- define module/overlay loading rules

### Phase 3
- implement native Ultimate UCI transport glue
- expose UCI through VM-callable services
- add host/emulator seam where feasible

### Phase 4
- implement filesystem abstraction over mounted images
- support image types: D64, D71, D81, DNP
- enforce flat-filesystem semantics on D64/D71/D81
- restrict subdirectory semantics to DNP

### Phase 5
- implement shell parser and resident commands
- first resident commands: `DIR`, `CD`, `VOL`, `MOUNT`, `MEM`, `TYPE`, `COPY`, `REN`, `DEL`, `RUN`, `HELP`, `VER`

### Phase 6
- implement overlays: `XCOPY`, `DELTREE`, `TREE`, batch support
- use REU as managed cache/workspace where that reduces resident pressure

### Phase 7
- complete tests, build docs, operator notes, and resident memory tracking
- write milestone handoff once DIR/CD/COPY are working through the VM-first shell

## Current Milestone Summary

### What works
- a separate UDOS repo exists
- local AcheronVM build succeeds with `ca65`/`ld65`
- VICE `x64sc` exists locally for emulator validation
- a D64-based proof image boots under VICE and executes AcheronVM code

### What is unverified
- target hardware execution on a real C64 Ultimate
- Ultimate UCI register protocol details in this codebase
- the final resident memory map for bootstrap + VM + services

### Next concrete step
- move into Phase 2 with a resident bootstrap skeleton and a frozen first-pass service ABI
