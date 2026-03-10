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
- per-drive mounted-image descriptors
- per-drive current-directory state
- per-drive resident volume labels
- directory-listing lookup for the current mock backend
- directory enumeration begin/next over resident mock entry tables
- descriptor-backed mock file record tables
- resident `CD` policy for flat vs tree-capable mounts
- resident `MOUNT` policy that can switch a drive between flat and tree-capable kinds
- resident `DIR` against a mock directory model
- resident `TYPE` against a mock file-content model

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

Current mock directory model:
- flat images report a root-only listing
- `DNP` root reports `BIN/`, `SRC/`, and `WORK/`
- `DNP` `SRC` reports `BOOT.ASM` and `FS.AVM`
- `DNP` `BIN` reports `SHELL.AVM` and `DIR.AVM`
- resident labels are currently:
  - `A:` -> `SYSTEM`
  - `B:` -> `WORK`
- resident mock file contents currently include:
  - flat root `SYSTEM`, `COMMANDS`, `README`
  - `DNP/SRC` `BOOT.ASM`, `FS.AVM`
  - `DNP/BIN` `SHELL.AVM`, `DIR.AVM`

This mock model now sits behind both a resident mounted-image descriptor layer
and the resident enumeration seam. It still must be replaced by real
image-backed enumeration, file lookup, and metadata once the filesystem layer
exists.
