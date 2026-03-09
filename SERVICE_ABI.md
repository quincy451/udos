# UDOS Service ABI

## Status

This is the first concrete resident ABI draft for UDOS Phase 2.

It is intentionally small and biased toward getting a resident bootstrap/core
running under AcheronVM before filesystem and UCI work start.

## Calling Convention

- VM code calls native services with AcheronVM `calln`.
- `rP` carries the primary argument or return value.
- Native code sees `.X` pointing at the current `rP` storage.
- Return values are written back to `0,X` and `1,X`.
- Native services must preserve VM invariants and return with `RTS`.

## ABI Version

Current ABI version:
- `1`

Version policy:
- incompatible changes bump the version
- overlays and later commands must declare the minimum ABI they require

## Phase 2 Services

### `svc_get_abi_version`
- input: none
- output: `rP = 1`
- purpose: allow VM code to check the resident service ABI level

### `svc_console_reset`
- input: none
- output: none
- purpose: clear screen RAM and reset the resident text cursor to home

### `svc_console_write_sc0`
- input: `rP = pointer to null-terminated screen-code string`
- output: cursor advanced past written text
- purpose: minimal console output primitive for resident VM code

### `svc_mark_ready`
- input: none
- output: none
- side effects:
  - writes ready marker at `$CFFF`
- purpose: deterministic validation hook for emulator tests

### `svc_idle`
- input: none
- output: none
- purpose: hold the resident environment in a stable loop after bootstrap

## Planned Next ABI Groups

- console cursor positioning and line input
- memory/status queries
- mounted-image query and binding
- directory enumeration
- file open/read/write/rename/delete/copy
- overlay/program load
- Ultimate UCI transport
