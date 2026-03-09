# UDOS Filesystem Abstraction

## Goal

Expose a single VM-facing mounted-image model while keeping image-format policy
explicit.

## Logical Drives

- `A:` is the default system drive
- `B:` is the workspace drive
- each drive maintains its own mounted image and current directory state

Current resident skeleton state:
- current drive defaults to `A:`
- `A:` mount kind defaults to `D64`
- `B:` mount kind defaults to `none`

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

The resident image currently exposes query-level state only:
- current drive query
- mount-kind query for logical drive
- mount-flag query for logical drive

This is deliberate. Query semantics can be validated in VICE with a mock or
selector backend before real UCI-backed image operations exist.
