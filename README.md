# UDOS

UDOS is a new Commodore 64 Ultimate shell/runtime project centered on AcheronVM.

This repo is intentionally separate from the existing `actionc64u/` and `cpm65-u64/`
work so the shell/runtime can move forward without continuing CP/M-65 feature work.

Current milestone:
- Phase 0 complete: pivot notes and project area established.
- Phase 1 complete.
- Phase 2 bootstrap/core slice complete.
- Phase 3 native UCI seam complete at the control/status boundary.
- Phase 4 mounted-image abstraction seam complete with flat-vs-tree policy.
- Phase 5 resident shell milestone in progress with `DIR`, `CD`, `VOL`, `MOUNT`,
  `MEM`, `TYPE`, `COPY`, `REN`, `DEL`, `MD`, `RD`, direct `A:`/`B:` drive
  switching, and implicit program launch validated under VICE.
- Phase 5 now includes real VICE tree read/write validation on the fsdevice-backed
  `DNP` path:
  - `DIR`, `CD`, `TYPE`, and implicit launch
  - exact and limited wildcard `COPY`
  - exact `REN`
  - exact and limited wildcard `DEL`
  - exact `MD`
  - exact `RD` for empty directories plus non-empty rejection
- Phase 5 now also includes a hardware-backed directory-enumeration path in code:
  - flat-image root mounts now first try raw image parsing through `OPEN_FILE` / `FILE_SEEK` / `READ_DATA`
  - tree-capable mounts still synchronize through `CHANGE_DIR`, refresh through `GET_PATH`, and enumerate through `OPEN_DIR` / `READ_DIR`
  - mock fallback retained for VICE and failure cases
- Phase 5 now also includes a hardware-backed `TYPE` read path in code:
  - flat-image mounts now first try raw image file lookup plus chained-sector reads through `OPEN_FILE` / `FILE_SEEK` / `READ_DATA`
  - tree-capable mounts still use resident path synchronization plus `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE`
  - mock fallback retained for VICE and failure cases
- Phase 5 now also includes a hardware-backed `DEL` path in code:
  - flat-image mounts now first try raw root-directory lookup plus BAM release through image `OPEN_FILE` / repeated `FILE_SEEK` / `READ_DATA` / `WRITE_DATA`
  - tree-capable mounts still use resident path synchronization plus `DELETE_FILE`
  - mock deletion is used only when hardware UCI is unavailable
  - hardware-side delete failures return an explicit shell error
- Phase 5 now also includes a hardware-backed `REN` path in code:
  - flat-image mounts now first try raw root-directory lookup plus direct directory-entry rewrite through image `OPEN_FILE` / `FILE_SEEK` / `READ_DATA` / `WRITE_DATA`
  - tree-capable mounts still use resident path synchronization plus `RENAME_FILE`
  - mock rename is used only when hardware UCI is unavailable
  - hardware-side rename failures return an explicit shell error
- Phase 5 now also includes a hardware-backed `COPY` path in code:
  - tree-only same-drive copy through `COPY_FILE`
  - tree-only cross-drive copy through source `OPEN_FILE`/`READ_DATA` and destination `OPEN_FILE`/`WRITE_DATA`
  - flat-image copies now also have a raw image path in code:
    - raw root-directory lookup
    - BAM allocation
    - chained sector streaming
    - direct directory-entry creation through image `OPEN_FILE` / `FILE_SEEK` / `READ_DATA` / `WRITE_DATA`
  - mock copy is used only when hardware UCI is unavailable
  - hardware-side copy failures return an explicit shell error
- Phase 5 now also includes a real mounted-image `MOUNT` path in code:
  - shell syntax: `MOUNT A: /path/to/system.d81` or `MOUNT B: /path/to/work.dnp`
  - image kind is inferred from the extension
  - hardware mode attempts Ultimate DOS `MOUNT_DISK`
  - flat-image hardware mounts now also try Ultimate DOS `OPEN_FILE` / `FILE_SEEK` / `READ_DATA` to import the filesystem header label for `D64` / `D71` / `D81`
  - when that header read is unavailable or fails, the resident label falls back to the mounted image basename
  - mock mode preserves the same semantics under VICE
- Phase 5 now also includes a real resident image-load path behind implicit program launch:
  - mock mode copies the resolved target into a bounded resident image buffer
  - flat-image mounts now first try raw image file lookup plus chained-sector reads
  - tree-capable hardware mode still probes with `FILE_STAT` and then attempts `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE`
  - VICE validates the loaded image length through resident snapshots
- Phase 5 now also includes resident batch support on VICE:
  - implicit `.BAT` fallback after `.PRG`
  - `%1` / `%2` / `%3`
  - `ECHO`
  - stop-on-error flow
  - boot `AUTOEXEC.BAT` from the default `A:` boot root
- Phase 5 now also includes transcript-backed VICE self-test images:
  - focused `AUTOEXEC.BAT` images for read, copy, rename, delete, directory, batch, stop-on-error, and implicit launch
  - checked-in expected final-screen transcripts
  - generated actual transcripts for direct `diff -u` comparison
- Phase 5 now also includes a release-style boot image:
  - `build/udos-release.d64`
  - boots directly to `A:D64/>` with no resident `AUTOEXEC.BAT`
  - companion VICE workspace tree staged under `build/udos-release-fs`
  - when the sibling `actionc64u` exporter is present, the release workspace
    also includes `IMAGES/ACTION.DNP`
  - `make vice-action-workspace` now builds an autoexec-backed Action test image
    that mounts the exported Action workspace, lists its root entries, and reads
    `README.TXT` from the shell
  - `make vice-action-actinfo` now builds an autoexec-backed Action test image
    that launches `ACTINFO.PRG` from the mounted Action workspace through the
    preserved launch-safe external-tool ABI and returns to the UDOS prompt
  - `make vice-action-avminfo` now builds an autoexec-backed Action test image
    that launches `AVMINFO.PRG`, loads `HELLO.AVM` through the preserved
    launch-safe file-load ABI, and returns to the UDOS prompt
  - `make vice-action-avmrun` now mounts the exported Action workspace from the
    release image, launches `AVMRUN.PRG`, loads `UDOSHELLO.AVM` through the
    preserved launch-safe file-load ABI, executes the current constrained
    flagged Acheron-backed `AVM1` subset, and returns to the UDOS prompt
  - `make vice-action-avmrun-flow` now runs `UDOSFLOW.AVM` from the mounted
    Action workspace and proves the current constrained subset can handle
    `jump`, `call`, and `ret` before returning to the UDOS prompt

Current command parser rule:
- shell keywords require a separator before arguments
- direct drive tokens like `A:` and `B:` switch the current logical drive and keep that drive's current directory
- direct `C:` and `D:` tokens are recognized but currently return `DRIVE NOT PRESENT`
- a non-keyword token implies program launch; if it has no extension, `.PRG` is appended
- example: `DEL BOOT3.PRG` deletes the file, while `DELBOOT3` is treated as a bare program token and returns `PROGRAM NOT FOUND`
- `DEL` now also supports limited resident wildcards:
  - `*`
  - `*.*`
  - `*.EXT`
  - `NAME.*`
- `COPY` now also supports the same limited wildcard forms
- wildcard `COPY` preserves each matched source filename and expects the destination to resolve to a directory target
- `MEM` now reports launch-capable RAM when REU is present:
  - `RAM USED` is treated as the preserved lower-RAM footprint after an aggressive spill
  - `RAM FREE` is treated as launch-available lower RAM
  - `REU USED` includes the current VICE tree cache reservation plus the spill
    reservation for the resident image and HIRAM workspace
- the VICE backend now spills VICE tree content payloads into REU and keeps only a
  single slot cache in RAM
- UDOS-aware external launch now returns through a resident trampoline under VICE
- the current launch/return validation includes a clobber test that overwrites
  resident code and still returns to the shell through REU-backed restore
- current direct `MEM` probe:
  - `RAM USED 0 FREE 65535 REU USED 35377 FREE 16741839`

See:
- `PIVOT_PLAN.md`
- `ARCHITECTURE.md`
- `BUILDING.md`
- `COMMAND_MATRIX.md`
- `MILESTONE_HANDOFF.md`
- `STATUS_UDOS.md`
- `TODO_UDOS.md`
