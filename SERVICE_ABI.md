# UDOS Service ABI

## Status

This is the first concrete resident ABI draft for UDOS.

It started as a Phase 2 console/bootstrap ABI and now includes the first Phase 3
transport selector, the first Phase 4 drive/bind/query seam, and the first
Phase 5 live command-input seam.

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

## Current Services

### `svc_get_abi_version`
- input: none
- output: `rP = 1`
- purpose: allow VM code to check the resident service ABI level

### `svc_transport_get_mode`
- input: none
- output: `rP = transport mode`
- current codes:
  - `0`: unavailable
  - `1`: mock backend
  - `2`: hardware UCI backend
- current selector:
  - if `$DF1D == $C9`, report hardware mode
  - otherwise report mock mode
- purpose: keep the hardware seam explicit and testable under emulation

### `svc_drive_get_current`
- input: none
- output: `rP = current logical drive index`
- current codes:
  - `0`: `A:`
  - `1`: `B:`
- purpose: expose resident drive state to VM-side shell logic

### `svc_drive_set_current`
- input: `rP = desired logical drive index`
- output: `rP = resulting logical drive index`
- current behavior:
  - accepts `0` or `1`
  - rejects larger values and leaves the current drive unchanged
- purpose: establish the resident drive-selection boundary early

### `svc_fs_get_mount_type`
- input: `rP = logical drive index`
- output: `rP = mount kind`
- current mount-kind codes:
  - `0`: none
  - `1`: D64
  - `2`: D71
  - `3`: D81
  - `4`: DNP
- purpose: expose image-type policy to VM-side shell logic

### `svc_fs_get_mount_flags`
- input: `rP = logical drive index`
- output: `rP = mount flags`
- current flags:
  - `0`: none
  - `1`: flat filesystem
  - `2`: tree-capable filesystem
- purpose: let VM code distinguish flat vs tree semantics before command logic exists

### `svc_fs_bind_drive`
- input: packed in `rP`
  - low byte: logical drive index
  - high byte: mount kind
- output: packed in `rP`
  - low byte: resulting mount kind
  - high byte: derived mount flags
- current behavior:
  - updates the resident mount-kind and mount-flag tables for valid drives
  - derives flags from kind: `D64/D71/D81 -> flat`, `DNP -> tree`, `none -> none`
  - installs the current drive's mounted-image descriptor and volume pointer cache
  - invalid drive indices return `none/none`
- purpose: move from hardcoded query values to actual resident bind state

### `svc_fs_get_dir_state`
- input: `rP = logical drive index`
- output: `rP = current resident directory id`
- current directory ids:
  - `0`: root
  - `1`: `BIN`
  - `2`: `SRC`
  - `3`: `WORK`
- purpose: expose per-drive current-directory state through the resident filesystem boundary

### `svc_fs_get_volume_ptr`
- input: `rP = logical drive index`
- output: `rP = pointer to a null-terminated resident volume-label string`
- current mock labels:
  - `A:` -> `SYSTEM`
  - `B:` -> `WORK`
- current behavior:
  - returns the volume pointer from the current drive's mounted-image descriptor
- purpose: let `VOL` and later `MOUNT` report metadata beyond mount kind alone

### `svc_fs_get_dir_listing_ptr`
- input: packed in `rP`
  - low byte: logical drive index
  - high byte: resident directory id
- output: `rP = pointer to a null-terminated resident listing string`
- current behavior:
  - returns the current compatibility listing string for the requested resident directory
  - remains available while the shell moves to entry-by-entry enumeration
- purpose: preserve a simple listing-pointer seam while the resident shell transitions to iterator-style enumeration

### `svc_fs_enum_begin`
- input: packed in `rP`
  - low byte: logical drive index
  - high byte: resident directory id
- output: `rP = entry count`
- current behavior:
  - selects the current resident mounted-image descriptor for the requested drive
  - chooses the root or subtree entry table from that descriptor
  - resets the resident enumeration cursor
- purpose: establish a directory-enumeration ABI shape that can later be backed by real mounted-image I/O

### `svc_fs_enum_next`
- input: none
- output: `rP = pointer to the next entry name`, or `0` when enumeration is exhausted
- current behavior:
  - walks the currently selected resident mock entry table
  - is the path the built-in `DIR` command now uses
- purpose: move the shell off prebuilt listing strings and toward real filesystem iteration

### `svc_console_reset`
- input: none
- output: none
- purpose: clear screen RAM and reset the resident text cursor to home

### `svc_console_write_sc0`
- input: `rP = pointer to null-terminated screen-code string`
- output: cursor advanced past written text
- purpose: minimal console output primitive for resident VM code

### `svc_console_write_prompt`
- input: none
- output: none
- current behavior:
  - renders `"  <drive>:<kind>/<dir> >"` from resident drive, mount, and current-directory state
  - currently formats `D64`, `D71`, `D81`, `DNP`, or `?`
  - flat images stay rooted at `/`
- purpose: keep the prompt tied to resident state instead of a fixed string

### `svc_console_newline`
- input: none
- output: none
- current behavior:
  - advances to the next 40-column boundary using the full 16-bit resident cursor
- purpose: keep multiline transcript output stable once the shell writes past the first 256 bytes of screen RAM

### `svc_line_read`
- input: none
- output: `rP = command token`
- current tokens:
  - `0`: empty line / no command token
  - `1`: `HELP`
  - `2`: `VER`
  - `3`: `VOL`
  - `4`: `MEM`
  - `5`: `QUIT` or `EXIT`
  - `6`: `DIR`
  - `7`: `CD`
  - `8`: `MOUNT`
  - `9`: `TYPE`
  - `10`: `COPY`
- current behavior:
  - reads live keyboard input through C64 KERNAL `GETIN`
  - echoes typed characters to the console
  - accepts both carriage return and linefeed as command terminators for VICE automation compatibility
  - tokenizes a command word plus one resident argument buffer
  - accepts inline `CD`/`DIR`/`MOUNT`/`TYPE`/`COPY` shorthand such as `CDB:`, `CDSRC`, `MOUNTB:D81`, `TYPEBOOTASM`, and `COPYBOOTASMWORKBOOTASM` to keep VICE `-keybuf` automation reliable
  - advances the resident cursor to the next line
- current emulator validation:
  - `make vice-resident` drives this path through VICE `-keybuf`
- purpose: provide the first real resident shell input path without moving shell control flow out of the VM

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

- memory/status queries
- mounted-image open/bind metadata beyond kind/flags
- directory enumeration against real mounted images behind the current `svc_fs_enum_*` seam
- file open/read/write/rename/delete/copy
- overlay/program load
- full hardware Ultimate UCI transport
