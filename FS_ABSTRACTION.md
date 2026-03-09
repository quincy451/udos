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
- per-drive current-directory state
- per-drive resident volume labels
- directory-listing lookup for the current mock backend
- resident `CD` policy for flat vs tree-capable mounts
- resident `MOUNT` policy that can switch a drive between flat and tree-capable kinds
- resident `DIR` against a mock directory model

This is still a state model, not real image I/O. That is deliberate: command,
prompt, and path-policy logic can now consume resident state before UCI-backed
operations exist.

Current mock directory model:
- flat images report a root-only listing
- `DNP` root reports `BIN/`, `SRC/`, and `WORK/`
- `DNP` `SRC` reports `BOOT.ASM` and `FS.AVM`
- `DNP` `BIN` reports `SHELL.AVM` and `DIR.AVM`
- resident labels are currently:
  - `A:` -> `SYSTEM`
  - `B:` -> `WORK`

This mock model exists only to exercise shell semantics. It must be replaced by
real image-backed enumeration once the filesystem layer exists.
