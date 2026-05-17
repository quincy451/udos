# UDOS Architecture

## Scope

UDOS is a DOS-like shell and resident service environment for the Commodore 64
Ultimate.

The current resident shell/runtime is native 6502. Linked Action output is
launched as a direct `.PRG`; no resident interpreter or separate launcher is
part of the normal program path.

## Design Rules

- shell/services logic does not live in C
- native 6502 owns bootstrap, resident services, command dispatch, UCI transport, and hardware primitives
- resident memory pressure must stay visible in documentation
- D64/D71/D81 are flat from the shell's perspective
- DNP is the only format with subdirectory semantics
- `alink` decides what goes into the linked Action `.PRG`

## Proven Baseline

The active baseline is the native resident shell plus the release workspace
image. The old standalone VM banner proof and separate runtime-runner path have
been removed from the active build surface.

## Resident Core

The resident core is layered as:

1. Native bootstrap
   - initial loader
   - resident image load and entry
   - launch/return restore stubs
2. Native resident shell/runtime
   - command tokenization
   - built-in command dispatch
   - implicit direct `.PRG` program launch
3. Resident service ABI
   - fixed tool-facing service page
   - versioned and documented
4. Native UCI transport driver
   - direct Ultimate-facing register transport
   - synchronous first cut
5. Filesystem abstraction
   - logical drives `A:` and `B:`
   - mount table
   - current directory state per drive

## Overlay Model

Overlays remain planned for larger or less frequently used commands.

Overlay policy draft:
- resident core resolves overlay image by command name
- overlay code should be native and use the resident service ABI
- overlays may use REU as staging/cache if that meaningfully reduces disk churn

## Filesystem Model

### Logical Drives
- `A:` boots first and defaults to the system image
- `B:` is secondary workspace/storage
- each drive has its own mounted image and current directory state

### Image Types
- `D64`: flat filesystem only
- `D71`: flat filesystem only
- `D81`: flat filesystem only
- `DNP`: flat root plus subdirectory support

Required behavior:
- any command needing subdirectory semantics on D64/D71/D81 must fail clearly
- no fake nested-path emulation on flat images

## Service ABI

The resident exports a fixed tool ABI page for external tools and launched
programs. Tools call native resident services directly through that page.

First ABI groups:
- console I/O
- memory/status
- image mount/query
- directory enumeration
- file open/read/write/rename/delete/copy
- program launch/return state
- UCI transport primitives

Versioning:
- a resident ABI version word is exported by the native service layer
- external tools must tolerate additive ABI growth

## Memory Model

Current assumptions:
- resident image loads at `$1810` and enters at `$18D3`
- resident code/data must stay below `$A000`
- REU is used as cache/workspace and for launch-time resident spill/restore
- shell boot must not require REU

These assumptions must stay explicit until measured on real hardware.

## Current Milestone Summary

### What works
- the resident shell boots under VICE
- mounted workspace images launch direct `.PRG` programs
- resident spill/restore returns from launched tools under VICE

### What is unverified
- real hardware UCI behavior
- final overlay ABI details
- realistic resident footprint once more tools are resident-aware

### Next concrete step
- keep the native resident below `$A000`, run focused VICE launch/return tests,
  then hardware-validate the UCI-backed filesystem paths
