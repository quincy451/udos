# UDOS Filesystem Abstraction

## Goal

Expose a single VM-facing mounted-image model while keeping image-format policy
explicit.

## Logical Drives

- `A:` is the default system drive
- `B:` is the workspace drive
- each drive maintains its own mounted image and current directory state

## Image Kinds

Current planned mount-kind codes:
- `0`: none
- `1`: D64
- `2`: D71
- `3`: D81
- `4`: DNP

These codes are internal ABI values, not user-facing strings.

## Tree Semantics Policy

- `D64`, `D71`, `D81`: flat only
- `DNP`: subdirectories allowed

Any tree command on a flat image must fail explicitly.

## Phase 3/4 Skeleton

The current resident image exposes only query-level placeholders:
- transport mode query
- mount-kind query for logical drive

This is deliberate. Query semantics can be validated in VICE with a mock backend
before real UCI transport exists.
