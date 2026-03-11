# UDOS Service ABI

## Status

This is the current resident ABI draft for standalone UDOS.

It now covers:
- resident bootstrap/core services
- transport selection
- drive bind/query state
- filesystem enumeration and metadata seams
- mounted-image path parsing and label derivation
- console I/O
- live command input
- first program handoff/return services for implicit program launch

## Calling Convention

- VM code calls native services with AcheronVM `calln`.
- `rP` carries the primary argument or return value.
- native code sees `.X` pointing at the current `rP` storage.
- return values are written back through `0,X` and `1,X`.
- native services return with `RTS`.

## ABI Version

Current ABI version:
- `1`

## Current Services

### `svc_get_abi_version`
- input: none
- output: `rP = 1`

### `svc_transport_get_mode`
- input: none
- output: `rP = transport mode`
- current values:
  - `0`: unavailable
  - `1`: mock backend
  - `2`: hardware UCI backend

### `svc_drive_get_current`
- input: none
- output: `rP = current logical drive`
- current values:
  - `0`: `A:`
  - `1`: `B:`

### `svc_drive_set_current`
- input: `rP = logical drive`
- output: `rP = resulting logical drive`
- current behavior:
  - accepts `0` or `1`
  - rejects larger values

### `svc_fs_get_mount_type`
- input: `rP = logical drive`
- output: `rP = mount kind`
- current values:
  - `0`: none
  - `1`: `D64`
  - `2`: `D71`
  - `3`: `D81`
  - `4`: `DNP`

### `svc_fs_get_mount_flags`
- input: `rP = logical drive`
- output: `rP = mount flags`
- current values:
  - `0`: none
  - `1`: flat
  - `2`: tree-capable

### `svc_fs_bind_drive`
- input: packed in `rP`
  - low byte: logical drive
  - high byte: mount kind
- output: packed in `rP`
  - low byte: resulting mount kind
  - high byte: derived mount flags
- current behavior:
  - `D64` / `D71` / `D81` -> flat
  - `DNP` -> tree-capable
  - installs the current mounted-image descriptor for the drive
  - this remains the low-level bind-by-kind service used during bootstrap
  - the user-facing `MOUNT` command now parses an image path and derives kind from the extension

### `svc_fs_get_dir_state`
- input: `rP = logical drive`
- output: `rP = resident directory id`
- current values:
  - `0`: root
  - `1`: `BIN`
  - `2`: `SRC`
  - `3`: `WORK`

### `svc_fs_get_volume_ptr`
- input: `rP = logical drive`
- output: `rP = pointer to null-terminated volume label`

### `svc_fs_get_backend_path_ptr`
- input: `rP = logical drive`
- output: `rP = pointer to null-terminated backend path text`
- current behavior:
  - mock mode synthesizes a path from resident directory state:
    - `/`
    - `/BIN`
    - `/SRC`
    - `/WORK`
  - hardware mode first attempts to synchronize the mapped Ultimate DOS target through `DOS_CMD_CHANGE_DIR (0x11)`
  - hardware mode then attempts a real Ultimate DOS `DOS_CMD_GET_PATH (0x12)` query for the mapped DOS target
  - on hardware query failure, the service falls back to the mock path text

### `svc_fs_get_dir_listing_ptr`
- input: packed in `rP`
  - low byte: logical drive
  - high byte: resident directory id
- output: `rP = pointer to a compatibility listing string`
- note:
  - kept only as a compatibility seam while `DIR` uses iterator-backed enumeration

### `svc_fs_enum_begin`
- input: packed in `rP`
  - low byte: logical drive
  - high byte: resident directory id
- output: `rP = entry count`
- current behavior:
  - mock mode selects the resident descriptor-backed entry tables
  - hardware mode attempts:
    - `DOS_CMD_CHANGE_DIR (0x11)`
    - `DOS_CMD_OPEN_DIR (0x13)`
    - repeated `DOS_CMD_READ_DIR (0x14)`
  - hardware results are cached into a small resident table:
    - up to `6` entries
    - names capped at `20` bytes
  - on hardware failure it falls back to the mock tables

### `svc_fs_enum_next`
- input: none
- output: `rP = pointer to next entry name`, or `0` when exhausted

### `TYPE` backend note
- the resident `TYPE` command now attempts a real file read when hardware UCI is present
- current sequence:
  - `DOS_CMD_CHANGE_DIR (0x11)`
  - `DOS_CMD_OPEN_FILE (0x02)` with `FA_READ`
  - `DOS_CMD_READ_DATA (0x04)`
  - `DOS_CMD_CLOSE_FILE (0x03)`
- reads are bounded to the resident response buffer
- on failure the command falls back to the current descriptor-backed mock content

### `DEL` backend note
- the resident `DEL` command now attempts a real file delete when hardware UCI is present
- current sequence:
  - `DOS_CMD_CHANGE_DIR (0x11)`
  - `DOS_CMD_DELETE_FILE (0x09)`
- when hardware UCI is unavailable, the shell still uses the current resident mutable `WORK` model
- when hardware UCI is present and the delete request fails, the shell returns an explicit delete error instead of mutating mock state

### `REN` backend note
- the resident `REN` command now attempts a real file rename when hardware UCI is present
- current sequence:
  - `DOS_CMD_CHANGE_DIR (0x11)`
  - `DOS_CMD_RENAME_FILE (0x0a)`
- the current hardware path keeps the existing shell semantics:
  - source and destination must resolve to the same logical drive
  - source and destination must resolve to the same resident directory
- when hardware UCI is unavailable, the shell still uses the current resident mutable `WORK` model
- when hardware UCI is present and the rename request fails, the shell returns an explicit rename error instead of mutating mock state

### `COPY` backend note
- the resident `COPY` command now attempts a real file copy when hardware UCI is present
- current same-drive sequence:
  - `DOS_CMD_COPY_FILE (0x0b)`
- current cross-drive sequence:
  - source `DOS_CMD_CHANGE_DIR (0x11)`
  - source `DOS_CMD_OPEN_FILE (0x02)` with `FA_READ`
  - repeated source `DOS_CMD_READ_DATA (0x04)`
  - destination `DOS_CMD_CHANGE_DIR (0x11)`
  - destination `DOS_CMD_OPEN_FILE (0x02)` with write/create flags
  - repeated destination `DOS_CMD_WRITE_DATA (0x05)`
  - source and destination `DOS_CMD_CLOSE_FILE (0x03)`
- when hardware UCI is unavailable, the shell still uses the current resident mutable `WORK` model
- when hardware UCI is present and the copy request fails, the shell returns an explicit copy error instead of mutating mock state

### `svc_console_reset`
- input: none
- output: none

### `svc_console_write_sc0`
- input: `rP = pointer to null-terminated text`
- output: none
- note:
  - current implementation normalizes ASCII uppercase text into C64 screen codes on write

### `svc_console_write_prompt`
- input: none
- output: none
- current behavior:
  - renders the resident prompt from drive, mount kind, and directory state

### `svc_console_newline`
- input: none
- output: none

### `svc_line_read`
- input: none
- output: `rP = shell command token`
- current values:
  - `0`: none
  - `1`: `HELP`
  - `2`: `VER`
  - `3`: `VOL`
  - `4`: `MEM`
  - `5`: `QUIT` / `EXIT`
  - `6`: `DIR`
  - `7`: `CD`
  - `8`: `MOUNT`
  - `9`: `TYPE`
  - `10`: `COPY`
  - `11`: `REN`
  - `12`: `DEL`
  - `13`: internal program-launch dispatch
- current behavior:
  - uses live C64 KERNAL `GETIN`
  - tokenizes one command plus one argument buffer
  - command keywords require a separator before arguments
  - direct drive tokens `A:` and `B:` dispatch through the resident `CD` path
  - a bare non-keyword line falls back to implicit program launch
  - example:
    - `DEL BOOT3.PRG` -> `DEL` with `BOOT3.PRG`
    - `DELBOOT3` -> bare token, then implicit launch of `DELBOOT3.PRG`
    - `BOOT3 DIR` -> implicit launch of `BOOT3.PRG` with command line `DIR`
    - `MOUNT B: /IMAGES/WORK.DNP` -> `MOUNT` with a drive token plus image path

### `svc_program_prepare_run`
- input: current shell argument buffer
- output: `rP = run status`
- current values:
  - `0`: ready
  - `1`: bad invocation
  - `2`: flat-image path error
  - `3`: unmounted
  - `4`: target not found
  - `5`: target too large for the resident image buffer
  - `6`: program load failed
- current behavior:
  - splits the command target from the command line
  - appends `.PRG` when the target name has no extension
  - resolves the current file target through the same resident path logic used by `TYPE`
  - loads the resolved target into a bounded resident image buffer
    - mock mode copies from the current descriptor-backed file content
    - hardware mode first attempts `FILE_STAT` for existence/size
    - hardware mode then attempts `OPEN_FILE`, `READ_DATA`, and `CLOSE_FILE`
  - snapshots the drive and directory context for the program
  - marks program state as running on success

### `svc_program_get_status`
- input: none
- output: `rP = last run status`
- current behavior:
  - exposes the resident `RUN_STATUS_*` result stored by `svc_program_prepare_run`
  - used by the shell to branch cleanly between implicit launch and error reporting

### `svc_program_error_ptr`
- input: `rP = run status`
- output: `rP = pointer to error text`

### `svc_program_get_target_ptr`
- input: none
- output: `rP = pointer to resolved target name`

### `svc_program_get_cmdline_ptr`
- input: none
- output: `rP = pointer to the command-line buffer`

### `svc_program_get_cmdline_len`
- input: none
- output: `rP = command-line length`

### `svc_program_get_image_ptr`
- input: none
- output: `rP = pointer to the loaded resident program image buffer`

### `svc_program_get_image_len`
- input: none
- output: `rP = loaded program image length in bytes`

### `svc_program_exit`
- input: none
- output: none
- current behavior:
  - marks program state as exited
  - records exit status `0`

### `svc_mark_ready`
- input: none
- output: none
- side effect:
  - writes `$52` to `$CFFF`

### `svc_idle`
- input: none
- output: none

## Program Snapshot Bytes

Current VICE validation uses these resident snapshots:
- `$CFE4`: cached backend-path length for `A:`
- `$CFE5`: cached backend-path length for `B:`
- `$CFF6`: program state
  - `0`: none
  - `1`: running
  - `2`: exited
- `$CFF7`: exit status
- `$CFF8`: program drive
- `$CFF9`: program directory
- `$CFFA`: program image length low byte
- `$CFFB`: program image length high byte

## Planned Next ABI Groups

- real image-backed directory enumeration
- overlay/program module loading
- full hardware UCI transport
