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
| `MD` | Yes | No | Yes | Yes | No | Tree-only command. Flat images reject with `FLAT IMAGE`. VICE tree create/remove is now passing. Hardware create path is not implemented yet. |
| `RD` | Yes | No | Yes | Yes | No | Tree-only command. Flat images reject with `FLAT IMAGE`. VICE tree empty-dir remove and non-empty rejection are now passing. Hardware remove path is not implemented yet. |
| `MOUNT` | Yes | Yes | Partial | Yes | Partial | Syntax and logical binding work. VICE tree bind/read/write flow is now passing on the fsdevice-backed path. Hardware `MOUNT_DISK` path exists but is unverified. |
| `TYPE` | Yes | Yes | Yes | Yes | Partial | Mock and flat work. Real VICE tree file reads are now passing. |
| `COPY` | Yes | Yes | Yes | Yes | Partial | Mock and flat copy work. VICE tree exact and limited wildcard copy are now passing on the fsdevice-backed path. |
| `REN` | Yes | Yes | Yes | Yes | Partial | Mock and flat rename work. VICE tree exact rename is now passing for overlay-created and host-backed files. |
| `DEL` | Yes | Yes | Yes | Yes | Partial | Mock and flat delete work. VICE tree exact and limited wildcard delete are now passing on the fsdevice-backed path. |
| `A:` | Yes | Yes | N/A | N/A | N/A | Resident direct drive token; switches drives without resetting that drive's current directory. |
| `B:` | Yes | Yes | N/A | N/A | N/A | Resident direct drive token; switches drives without resetting that drive's current directory. |
| `C:` | Yes | Yes | N/A | N/A | N/A | Reserved token, returns `DRIVE NOT PRESENT`. |
| `D:` | Yes | Yes | N/A | N/A | N/A | Reserved token, returns `DRIVE NOT PRESENT`. |
| bare program launch | Yes | Yes | Yes | Yes | Partial | Mock and flat launch paths exist. Real VICE tree launch now passes for existing programs and returns `PROGRAM NOT FOUND` for missing ones. |
| batch `.BAT` | No | No | No | No | No | Not started. |
| `AUTOEXEC.BAT` | No | No | No | No | No | Not started. |
| `XCOPY` | No | No | No | No | No | Planned overlay/external command. |
| `DELTREE` | No | No | No | No | No | Planned overlay/external command. |
| `TREE` | No | No | No | No | No | Planned overlay/external command. |

Current priority:

1. implement batch support, including `AUTOEXEC.BAT`
2. add REU-backed resident spill/shrink after the command surface is stable
3. build a self-test image flow that reports success or failure through batch
4. hardware-validate the existing UCI paths on a real Ultimate target
