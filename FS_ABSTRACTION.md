# UDOS Filesystem Abstraction

## Goal

Expose a single VM-facing mounted-image model while keeping image-format policy
explicit.

## Logical Drives

- `A:` is the default system drive
- `B:` is the workspace drive
- each drive maintains its own mounted image and current directory state

Current resident skeleton state after bootstrap:
- `A:` is bound as `D64`
- `B:` is bound as `DNP`
- current drive is `A:`
- both drives start at `/`

## Image Kinds

Current mount-kind codes:
- `0`: none
- `1`: D64
- `2`: D71
- `3`: D81
- `4`: DNP

Current mount-flag codes:
- `0`: none
- `1`: flat filesystem
- `2`: tree-capable filesystem

These codes are internal ABI values, not user-facing strings.

## Tree Semantics Policy

- `D64`, `D71`, `D81`: flat only
- `DNP`: subdirectories allowed

Any tree command on a flat image must fail explicitly.

## Current Skeleton Surface

The resident image currently exposes:
- current drive query/set
- mount-kind query for logical drive
- mount-flags query for logical drive
- bind-by-kind for logical drive
- backend-path query per logical drive
- per-drive mounted-image descriptors
- per-drive current-directory state
- per-drive resident volume labels
- directory-listing lookup for the current mock backend
- directory enumeration begin/next over resident mock entry tables
- descriptor-backed mock file record tables
- mutable `WORK` directory slots per logical drive
- resident `CD` policy for flat vs tree-capable mounts
- resident `MOUNT` policy that can switch a drive between flat and tree-capable kinds
- resident `MOUNT` syntax that accepts a logical drive plus an image path
- resident `DIR` against a mock directory model
- resident `TYPE` against a mock file-content model
- resident `COPY` against the mutable `WORK` model when hardware UCI is unavailable
- resident `DEL` against the mutable `WORK` model when hardware UCI is unavailable
- resident `REN` against the mutable `WORK` model when hardware UCI is unavailable

This is still a state model, not real image I/O. That is deliberate: command,
prompt, and path-policy logic can now consume resident state before UCI-backed
operations exist.

Current resident mounted-image model:
- each logical drive points at a descriptor for the currently mounted image kind
- the descriptor carries:
  - volume-label pointer
  - root entry-table pointers and count
  - `BIN` entry-table pointers and count
  - `SRC` entry-table pointers and count
  - `WORK` entry-table pointers and count
  - root file-record table pointer and count
  - `BIN` file-record table pointer and count
  - `SRC` file-record table pointer and count
  - `WORK` file-record table pointer and count
- flat images still expose only the root listing to shell logic
- tree-capable images can expose the subtree tables when current-directory state changes
- the `WORK` subtree can override descriptor tables with mutable resident slots when files are copied in
- the user-facing `MOUNT` command now accepts:
  - `MOUNT A: /path/to/system.d81`
  - `MOUNT B: /path/to/work.dnp`
- the shell currently infers image kind from the file extension:
  - `.D64`
  - `.D71`
  - `.D81`
  - `.DNP`
- the shell currently maps logical drives to IEC ids as:
  - `A:` -> `8`
  - `B:` -> `9`
- on successful mount:
  - resident directory state resets to `/`
  - the mounted-image descriptor is rebound by kind
  - the resident volume label is refreshed from mounted-image metadata
- each drive also maintains a small backend-path cache buffer
  - mock mode fills this from resident directory state
  - hardware mode first synchronizes the Ultimate DOS target path through `CHANGE_DIR`
  - hardware mode then refreshes the cache through Ultimate DOS `GET_PATH`
- each drive now also has a small hardware directory cache
  - current cache budget is `6` entries per drive
  - each cached name is capped at `20` bytes plus a terminator
  - directory attributes with the `DIR` bit set are surfaced with a trailing `/`
  - flat-image root enumeration now first tries raw image parsing:
    - `OPEN_FILE`
    - `FILE_SEEK`
    - `READ_DATA`
  - on transport/query failure the shell falls back to the resident descriptor tables

Current mock directory model:
- flat images report a root-only listing
- `DNP` root reports `BIN/`, `SRC/`, and `WORK/`
- `DNP` `SRC` reports `BOOT.ASM` and `FS.AVM`
- `DNP` `BIN` reports `SHELL.AVM` and `DIR.AVM`
- resident labels are currently:
  - `A:` -> `SYSTEM`
  - `B:` -> `WORK`
- after a successful `MOUNT`:
  - flat-image hardware mode now tries to import the filesystem-header label from the image itself for `D64` / `D71` / `D81`
  - `DNP` and failure cases still fall back to the mounted image basename
  - example fallback: `/IMAGES/ALT.D81` -> `ALT`
  - example fallback: `/IMAGES/WORK.DNP` -> `WORK`
- resident mock file contents currently include:
  - flat root `SYSTEM`, `COMMANDS`, `README`
  - `DNP/SRC` `BOOT.ASM`, `FS.AVM`
  - `DNP/BIN` `SHELL.AVM`, `DIR.AVM`
- resident mutable copy model currently supports:
  - a small `WORK` file table per logical drive
  - create/update semantics for `COPY`
  - rename/delete semantics for `REN` and `DEL`
  - immediate visibility through `DIR` and `TYPE`

This mock model now sits behind both a resident mounted-image descriptor layer
and the resident enumeration seam. It still must be replaced by real
image-backed file lookup and mutation once the filesystem layer exists.

Current file-read seam:
- `TYPE` now attempts a real Ultimate DOS file read when UCI hardware is present
- flat-image mounts now first attempt:
  - raw root-directory lookup against the mounted image
  - chained sector reads through image `OPEN_FILE`, repeated `FILE_SEEK`, and repeated `READ_DATA`
- tree-capable mounts still use:
  - `CHANGE_DIR`
  - `OPEN_FILE`
  - `READ_DATA`
  - `CLOSE_FILE`
- reads are currently bounded to the resident response buffer for text display
- on hardware/query failure the shell falls back to the resident mock content tables

Current file-delete seam:
- `DEL` now attempts a real Ultimate DOS file delete when UCI hardware is present
- flat-image mounts now first attempt:
  - raw root-directory lookup against the mounted image
  - chained sector traversal to discover the file allocation
  - BAM release plus directory-entry clear through image `OPEN_FILE`, `FILE_SEEK`, `READ_DATA`, and `WRITE_DATA`
- tree-capable mounts still use:
  - `CHANGE_DIR`
  - `DELETE_FILE`
- when hardware UCI is unavailable, the shell still uses the resident mutable `WORK` model
- when hardware UCI is present and delete fails, the shell returns an explicit delete error instead of mutating mock state

Current file-rename seam:
- `REN` now attempts a real Ultimate DOS rename when UCI hardware is present
- the current call sequence is:
  - `CHANGE_DIR`
  - `RENAME_FILE`
- the current hardware path keeps the existing shell semantics:
  - source and destination must stay on the same logical drive
  - source and destination must stay in the same resolved resident directory
- when hardware UCI is unavailable, the shell still uses the resident mutable `WORK` model
- when hardware UCI is present and rename fails, the shell returns an explicit rename error instead of mutating mock state

Current file-copy seam:
- `COPY` now attempts a real Ultimate DOS copy when UCI hardware is present
- same-drive copies currently use:
  - `COPY_FILE`
- cross-drive copies currently use:
  - source `CHANGE_DIR`
  - source `OPEN_FILE`
  - repeated source `READ_DATA`
  - destination `CHANGE_DIR`
  - destination `OPEN_FILE`
  - repeated destination `WRITE_DATA`
  - source and destination `CLOSE_FILE`
- when hardware UCI is unavailable, the shell still uses the resident mutable `WORK` model
- when hardware UCI is present and copy fails, the shell returns an explicit copy error instead of mutating mock state

Current mount seam:
- `MOUNT` now attempts a real Ultimate DOS disk mount when UCI hardware is present
- the current call sequence is:
  - `MOUNT_DISK`
- current mount assumptions are:
  - logical `A:` uses IEC `8`
  - logical `B:` uses IEC `9`
- on hardware mount failure the shell distinguishes:
  - not a disk image
  - drive not present
  - generic mount failure
- on hardware success for flat images, the shell now also attempts:
  - `OPEN_FILE`
  - `FILE_SEEK`
  - `READ_DATA`
  - `CLOSE_FILE`
- current flat-image label offsets implemented in the resident path:
  - `D64` / `D71`: directory header label at image offset `$00016590`
  - `D81`: directory header label at image offset `$00061804`
- when the header import is unavailable or fails, the shell falls back to the mounted image basename

Current backend-path seam:
- `svc_fs_get_backend_path_ptr` returns a path-like metadata string per drive
- hardware mode now attempts to push the resident drive/path state into the mapped Ultimate DOS target before calling `GET_PATH`
- in VICE/mock mode the cache currently validates as:
  - `A:` -> `/`
  - `B:` -> `/WORK` after the resident smoke sequence
- fixed VICE snapshots currently record the cached path lengths:
  - `$CFE4 = 1` for `A:`
  - `$CFE5 = 5` for `B:` after `CD WORK`

Current hardware enumeration seam:
- `svc_fs_enum_begin` now attempts a real Ultimate DOS directory walk when UCI hardware is detected
- flat-image root mounts now first attempt:
  - `OPEN_FILE`
  - repeated `FILE_SEEK`
  - repeated `READ_DATA`
- tree-capable mounts still attempt:
  - `CHANGE_DIR`
  - `OPEN_DIR`
  - repeated `READ_DIR`
- cached entries are then exposed back to the shell through the existing iterator ABI
- this path is build-complete, but not hardware-validated from this environment

Current implicit-launch seam:
- bare non-keyword input still drives the resident program ABI
- flat-image mounts now first attempt:
  - raw root-directory lookup against the mounted image
  - chained sector reads into the resident program buffer
- tree-capable mounts still use:
  - `FILE_STAT`
  - `OPEN_FILE`
  - `READ_DATA`
  - `CLOSE_FILE`
- this path is build-complete, but not hardware-validated from this environment
