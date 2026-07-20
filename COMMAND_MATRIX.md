# UDOS Command Matrix

This file tracks command status by backend. A command is only "done" when the
required backends for that command are all green.

Backend meanings:

- `Mock`: resident in-memory filesystem/state used to prove shell behavior
- `Flat`: raw image-backed `D64` / `D71` / `D81` support
- `VICE tree`: emulator-specific tree backend for `DNP`-style behavior in VICE
- `Hardware/UCI`: real Commodore 64 Ultimate backend through the UCI interface

Legend:

- `Yes`: implemented and usable
- `Partial`: code path exists but is incomplete or not sufficiently validated
- `No`: not implemented
- `N/A`: not meaningfully backend-dependent

| Command | Syntax/Dispatch | Mock | Flat `D64/D71/D81` | VICE tree `DNP` | Hardware/UCI | Notes |
|---|---:|---:|---:|---:|---:|---|
| `HELP` | Yes | Yes | N/A | N/A | N/A | Resident static help text. |
| `VER` | Yes | Yes | N/A | N/A | N/A | Resident version response. |
| `MEM` | Yes | Yes | N/A | N/A | N/A | Resident memory report. |
| `VOL` | Yes | Yes | Partial | Partial | Partial | Mock works. Flat label-import code exists. VICE tree currently reports mount-derived metadata, not a real DNP label. |
| `DIR` | Yes | Yes | Yes | Yes | Partial | Mock and flat work. Real VICE tree read path is now passing. |
| `CD` | Yes | Yes | Yes | Yes | Partial | Flat rejection logic works. VICE tree directory changes are now passing on the read path. |
| `MD` | Yes | No | Yes | Yes | Partial | Tree-only command. Flat images reject with `FLAT IMAGE`. VICE tree creation passes; the UCI `FILE_STAT` / `CREATE_DIR` path is implemented but not hardware-validated. |
| `RD` | Yes | No | Yes | Yes | Partial | Tree-only command. Flat images reject with `FLAT IMAGE`. VICE tree empty-dir removal and non-empty rejection pass; the UCI `OPEN_DIR` / `READ_DIR` / `DELETE_FILE` path is implemented but not hardware-validated. |
| `MOUNT` | Yes | Yes | Partial | Yes | Partial | Syntax and logical binding work. VICE tree bind/read/write flow is now passing on the fsdevice-backed path. Hardware `MOUNT_DISK` path exists but is unverified. |
| `TYPE` | Yes | Yes | Yes | Yes | Partial | Mock and flat work. Real VICE tree file reads are now passing. |
| `COPY` | Yes | Yes | Yes | Yes | Partial | Mock and flat copy work. VICE tree exact and limited wildcard copy are now passing on the fsdevice-backed path. |
| `REN` | Yes | Yes | Yes | Yes | Partial | Mock and flat rename work. VICE tree exact rename is passing. Shell and fixed external-tool UCI rename paths exist but remain hardware-unvalidated. |
| `DEL` | Yes | Yes | Yes | Yes | Partial | Mock and flat delete work. VICE tree exact and limited wildcard delete are now passing on the fsdevice-backed path. |
| `A:` | Yes | Yes | N/A | N/A | N/A | Resident direct drive token; switches drives without resetting that drive's current directory. |
| `B:` | Yes | Yes | N/A | N/A | N/A | Resident direct drive token; switches drives without resetting that drive's current directory. |
| `C:` | Yes | Yes | N/A | N/A | N/A | Reserved token, returns `DRIVE NOT PRESENT`. |
| `D:` | Yes | Yes | N/A | N/A | N/A | Reserved token, returns `DRIVE NOT PRESENT`. |
| bare program launch | Yes | Yes | Yes | Yes | Partial | Mock and flat launch paths exist. Real VICE tree launch now passes for existing programs, captures exit status, and returns through the resident trampoline under VICE. Missing programs still return `PROGRAM NOT FOUND`. |
| batch `.BAT` | Yes | Yes | Partial | Yes | Partial | Implicit `.BAT` fallback is working. `%1` / `%2` / `%3`, `ECHO`, and stop-on-error are validated on VICE. Default flat boot-root batch is working; real mounted flat-image batch validation is still incomplete. |
| `AUTOEXEC.BAT` | Yes | No | Partial | N/A | Partial | Batch support remains, but default embedded resident `AUTOEXEC.BAT` is disabled so the resident image stays within memory. Real mounted flat-image and hardware validation are still incomplete. |
| `XCOPY` | Yes | No | Yes | Yes | Partial | `XCOPY.OVL` provides bounded recursive merge-copy on the VICE tree backend and rejects flat images with `FLAT IMAGE`. UCI module staging plus nested directory creation and file-copy Tool ABI paths are implemented but not hardware-validated. |
| `DELTREE` | Yes | No | Yes | Yes | Partial | `DELTREE.OVL` provides bounded post-order recursive removal on the VICE tree backend, rejects flat images, and protects the current directory before mutation. UCI module staging plus nested file and empty-directory deletion Tool ABI paths are implemented but not hardware-validated. |
| `TREE` | Yes | Partial | Yes | Yes | Partial | The native `TREE.OVL` module provides recursive VICE tree traversal through the validated `UDOV` loader. The resident one-level scaffold remains the missing/invalid-module fallback. UCI module staging and nested `OPEN_DIR` / `READ_DIR` traversal are implemented but not hardware-validated. |

Current priority:

1. keep the release package, root `make test`, and focused VICE gates green while
   Action linker/runtime changes are staged
2. hardware-validate the existing UCI paths on a real Ultimate target using
   `HARDWARE_VALIDATION.md`
3. hardware-validate UCI overlay staging and the recursive Tool ABI operations
   used by `TREE`, `XCOPY`, and `DELTREE`
4. continue widening the UDOS-native Action toolchain:
   `ACTC.PRG -> OBJ/<MODULE>.OBJ -> ALINK.PRG -> BIN/<MODULE>.PRG`
