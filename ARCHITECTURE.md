# UDOS Architecture

## Scope

UDOS is a DOS-like shell and resident service environment for the Commodore 64
Ultimate.

The shell, service layer, filesystem logic, and process/command logic are to be
implemented in AcheronVM wherever practical. Native 6502 code is reserved for
bootstrap and hardware-edge glue.

## Design Rules

- shell/services logic does not live in C
- AcheronVM is the primary resident programming environment
- native 6502 is only for bootstrap, VM trampolines, UCI transport, IRQ-safe glue, and tiny hardware primitives
- resident memory pressure must stay visible in documentation
- D64/D71/D81 are flat from the shell's perspective
- DNP is the only format with subdirectory semantics

## Proven Baseline

The current Phase 1 proof validates these assumptions in VICE:
- local AcheronVM runtime can be linked into a C64-target PRG
- a VM-side `calln` can invoke native glue
- a tiny native routine can update screen RAM and a marker byte deterministically
- the linked entrypoint is not the VM base address; wrapper generation must use the real linked `.start`

Current measured proof layout:
- dispatcher: `$00E6`
- runtime body: `$072A`
- proof code: `$002E`
- proof entrypoint: `$1810`

## Resident Core

The resident core is planned as these layers:

1. Native bootstrap
   - machine bring-up
   - initial loader
   - resident image relocation if needed
   - AcheronVM entry/exit trampolines
2. Resident AcheronVM runtime
   - the VM dispatcher and enabled instruction set
   - resident enough that later commands can execute in the same VM environment
3. Resident service ABI
   - fixed jump/service entry convention from VM code into native services
   - versioned and documented
4. Native UCI transport driver
   - direct Ultimate-facing register transport
   - tiny, synchronous first cut
5. VM-facing filesystem abstraction
   - logical drives `A:` and `B:`
   - mount table
   - current directory state per drive
6. Resident command dispatcher
   - command tokenization
   - lookup of built-in vs overlay command
   - argument handoff
7. Resident commands
   - `DIR`, `CD`, `VOL`, `MOUNT`, `MEM`, `TYPE`, `COPY`, `REN`, `DEL`, `RUN`, `HELP`, `VER`

## Overlay Model

Overlays are planned for larger or less frequently used commands:
- `XCOPY`
- `DELTREE`
- `TREE`
- batch/scripting support
- later developer utilities

Overlay policy draft:
- resident core resolves overlay image by command name
- overlay code executes in the same AcheronVM environment
- native bootstrap is responsible only for loading and transferring control
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

## Service ABI Draft

This is a draft for the first stable resident ABI boundary.

### VM-to-native call shape
- AcheronVM code uses `calln` into a native service trampoline
- `rP` and the visible register window carry scalar parameters
- native service writes return values back into the current register window
- service calls preserve VM invariants and return to VM mode cleanly

### First ABI groups
- console I/O
- memory/status
- image mount/query
- directory enumeration
- file open/read/write/rename/delete/copy
- program/overlay load
- UCI transport primitives

### Versioning
- a resident ABI version word will be exported in native glue and mirrored in VM-visible state
- overlays must declare the ABI version they require

## Memory Model Assumptions

Current assumptions, not yet hardware-validated:
- resident VM/runtime loaded in main RAM
- REU available as cache/workspace, not as a hidden requirement for the first proof
- overlay and filesystem scratch space may move into REU once the base shell loop is stable

These assumptions must stay explicit until measured on real hardware.

## Current Milestone Summary

### What works
- local AcheronVM runtime can be built from assembly sources
- a minimal AcheronVM proof runs under VICE from a D64 image

### What is unverified
- final ABI details
- UCI transport register map and calling costs
- realistic resident footprint once filesystem services are present

### Next concrete step
- implement the Phase 2 resident bootstrap skeleton and freeze the first resident ABI around console, memory, mount/query, and command dispatch services
