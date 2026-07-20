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

Larger or less frequently used commands use native command overlays.

Current overlay policy:
- the resident core derives `<COMMAND>.OVL` from the parsed command token
- version-1 modules use a load-address prefix plus a 14-byte `UDOV` header
- the header declares format version, required Tool ABI, command ID, load
  address, entry address, and exact image length
- the complete module is staged in REU and validated before control transfer
- overlay code is native 6502 and uses the resident Tool ABI
- `TREE.OVL`, `XCOPY.OVL`, and `DELTREE.OVL` are production command modules
- staging supports both VICE tree files and hardware/UCI tree files; the UCI
  path uses repeated `READ_DATA` transfers into the shared REU launch area, but
  remains unvalidated on real Ultimate hardware
- Action compiler pass overlays own `$A000-$BFFF` while an external tool runs.
  The linker enforces that all tool-callable resident code ends at or below
  `$A000`; only shell/post-return code may occupy the resident tail above that
  boundary, where REU-backed return restores it before use.
- fixed tool-callable code that must survive the low-resident swap begins at
  `$9800`; the current exclusive safe-end label is `$9FCE`, leaving 50 bytes
  before the Action overlay window
- tool-callable backend selection reads the preserved `TRANSPORT_SNAPSHOT`
  instead of calling the low resident `uci_probe`; large tools may overwrite
  `$1810` while running and still use the fixed Tool ABI safely

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
- resident code loads at `$1810`, enters at `$18D3`, and must stay below `$C000`
- the `$A000`-`$BFFF` tail is RAM banked under BASIC ROM; resident execution
  keeps BASIC ROM out and KERNAL/I/O visible with processor-port value `$36`
- mutable high-RAM state occupies `$C000`-`$CEFB` and must stay below the fixed
  Tool ABI page at `$CF00`
- REU is used as cache/workspace and for launch-time resident spill/restore
- resident-private REU state uses bank `$FF`; bank `$FE` holds the temporary
  low-resident/tool swap, and bank `$FD` holds bounded fixed-tool file loads
- the resident-private bank contains VICE tree slots, resident/HIRAM restore
  images, 48 mutation replay records, and one 32-byte streamed-write filename
  shadow; streamed file payloads are not mirrored a second time
- shell boot must not require REU

These assumptions must stay explicit until measured on real hardware.

## Current Milestone Summary

### What works
- the resident shell boots under VICE
- mounted workspace images launch direct `.PRG` programs
- resident spill/restore returns from launched tools under VICE
- the validated `UDOV` loader runs recursive `TREE.OVL` and safely falls back
  when the module is absent or malformed
- the same loader runs bounded recursive `XCOPY.OVL` and rejects an invalid
  module without entering it
- the loader runs bounded post-order `DELTREE.OVL`, rejects flat images and
  malformed modules, and protects the current directory before mutation

### What is unverified
- real hardware UCI behavior
- hardware/UCI overlay staging and execution on a real Ultimate target
- hardware/UCI recursive Tool ABI enumeration and mutation behavior
- realistic resident footprint once more tools are resident-aware

### Next concrete step
- keep resident code below `$C000` and high-RAM state below `$CF00`, run focused
  VICE launch/return tests,
  then hardware-validate UCI-backed overlay staging and fix any observed target
  failures in the recursive Tool ABI paths while continuing direct Action
  object/link work
