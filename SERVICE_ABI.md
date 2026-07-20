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
- path-scoped tool directory enumeration for overlay/external command traversal
- bounded external-tool file load/probe on VICE tree and hardware/UCI tree paths
- nested-path tool file copy used by recursive command overlays
- nested-path tool directory remove and file delete used by recursive command
  overlays
- validated native `UDOV` command-module staging on the VICE tree backend and
  an implemented, not yet hardware-validated, UCI staging path

## Calling Convention

- Public tool callers use the fixed service jump table addresses generated in
  `udos_services.inc`.
- Backend-generic tool paths select UCI versus non-UCI behavior from the
  preserved `TRANSPORT_SNAPSHOT`; they do not call low resident transport code
  that a large launched tool may overwrite.
- `rP` carries the primary argument or return value.
- native code sees `.X` pointing at the current `rP` storage.
- return values are written back through `0,X` and `1,X`.
- native services return with `RTS`.

## ABI Version

Current ABI version:
- `6`

## Current Services

### `svc_get_abi_version`
- input: none
- output: `rP = 6`

### `svc_transport_get_mode`
- input: none
- output: `rP = transport mode`
- current values:
  - `0`: unavailable
  - `1`: mock backend
  - `2`: hardware UCI backend
  - `3`: VICE filesystem backend
- current behavior:
  - probes the live UCI and VICE transports and preserves the caller's `X`
    register while writing the result

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
  - VICE mode streams the complete `UDOSDIR.TXT` catalog one logical line at a
    time; the six-entry snapshot is bounded, but catalog input is not capped at
    255 bytes
  - when a full VICE snapshot encounters a later directory, it evicts a cached
    file before dropping the directory so nested traversal remains possible
  - on hardware failure it falls back to the mock tables

### `svc_fs_enum_next`
- input: none
- output: `rP = pointer to next entry name`, or `0` when exhausted

### Fixed tool `svc_dir_begin_sc0`
- input:
  - `0,X` / `1,X`: pointer to a null-terminated directory path
- output:
  - `0,X` / `1,X`: entry count when status is OK, otherwise `0`
  - `2,X`: directory status
- current status values:
  - `0`: failed
  - `1`: OK
  - `2`: exists
  - `3`: not found
  - `4`: not empty
  - `5`: busy
  - `6`: flat image
  - `7`: unmounted
  - `8`: bad path
- current behavior:
  - starts resolution from the launched program's drive/directory snapshot
  - accepts drive prefixes plus absolute, relative, and nested tree paths
  - rejects flat images explicitly
  - hardware/UCI mode resolves each component through `OPEN_DIR` / `READ_DIR`
    and seeds the resident hardware directory cache
  - VICE mode resolves each component through the manifest-backed tree cache
  - seeds the same iterator used by `svc_dir_begin_current` on either backend
  - callers consume entries with `svc_dir_next`
- purpose:
  - gives later recursive external/overlay commands a real path-scoped
    traversal primitive without changing the user's current shell prompt

### Fixed tool `svc_file_load_sc0`
- input:
  - `0,X` / `1,X`: pointer to a null-terminated file path
  - `2,X` / `3,X`: destination pointer
  - `4,X` / `5,X`: unsigned 16-bit destination limit
- output:
  - `6,X`: file status
  - `7,X` / `8,X`: unsigned 16-bit loaded length
- current status values:
  - `0`: failed
  - `1`: OK
  - `2`: too large
  - `3`: not found
- current behavior:
  - destination and limit both zero request an existence-only probe
  - normal paths resolve from the launched program's drive/directory snapshot;
    a leading `!` resolves from the directory containing the launched tool
  - hardware/UCI tree mode uses `FILE_STAT` for the existence probe and 32-bit
    file size, then `OPEN_FILE`, repeated `READ_DATA` chunks of at most 255
    bytes, and `CLOSE_FILE`
  - an existence-only probe does not open the file
  - a file at or below the limit returns `OK` with its exact loaded length
  - a file above the limit fills exactly the allowed prefix and returns
    `too large` with loaded length equal to the limit
  - a short read before the `FILE_STAT` size is satisfied, a read error, or a
    close error returns `failed`
  - backend selection uses the preserved transport snapshot and does not call
    overwrite-prone low resident probe code
  - the VICE tree behavior remains covered by `ACTFILE`, ACTC/ALINK, and ACTMON
    gates; the hardware/UCI path is implemented but has not been validated on
    a real C64 Ultimate

### Fixed tool `svc_file_save_sc0`
- input:
  - `0,X` / `1,X`: pointer to a null-terminated destination file path
  - `2,X` / `3,X`: source pointer
  - `4,X` / `5,X`: unsigned 16-bit source length
- output:
  - `6,X`: file status (`0` failed, `1` OK)
- current behavior:
  - resolves tree destinations from the launched program's drive/directory
    snapshot and restores the resolver state before returning
  - in hardware/UCI mode, a nonzero source length writes exactly that many bytes
  - in hardware/UCI mode, a zero source length retains the existing text
    compatibility behavior by measuring a null-terminated source through at
    most `PROGRAM_IMAGE_MAX-1` bytes; a zero pointer and zero length create or
    truncate an empty file
  - hardware/UCI mode uses `OPEN_FILE` with write/create/overwrite flags,
    repeated `WRITE_DATA` chunks of at most `MAX_RESPONSE_LEN` (`128`) bytes,
    and `CLOSE_FILE`
  - an empty payload still opens and closes the destination so an existing file
    is truncated and a missing file is created
  - backend selection uses the preserved transport snapshot and does not call
    overwrite-prone low resident probe code
  - open, write, or close errors return `failed`; replacement is not atomic, so
    a hardware failure after open can leave a truncated or partial destination
  - VICE tree mode retains the queued post-return, null-terminated text
    writeback behavior bounded by the resident `PROGRAM_IMAGE_MAX` slot
  - the hardware/UCI path is implemented but has not been validated on a real
    C64 Ultimate

### Fixed tool streamed write services

`svc_file_write_begin_sc0`:

- input:
  - `0,X` / `1,X`: pointer to a null-terminated destination file path
- output:
  - `2,X`: file status (`0` failed, `1` OK)

`svc_file_write_chunk_sc0`:

- input:
  - `0,X` / `1,X`: source pointer
  - `2,X` / `3,X`: unsigned 16-bit source length
- output:
  - `4,X`: file status (`0` failed, `1` OK)

`svc_file_write_close_sc0`:

- output:
  - `0,X`: file status (`0` failed, `1` OK)

Current behavior:

- one streamed output file may be open at a time
- begin resolves normal paths from the launched program's drive/directory
  snapshot; a leading `!` resolves from the directory containing the launched
  tool
- hardware/UCI begin accepts tree destinations only, uses write/create/overwrite
  `OPEN_FILE`, and retains the target drive plus open state in fixed HIRAM
  scratch that survives between service calls
- each hardware/UCI chunk writes exactly its unsigned 16-bit requested length,
  splitting it into `WRITE_DATA` payloads of at most `128` bytes
- hardware/UCI close issues `CLOSE_FILE`, clears the open state, and reports
  open/write/close failures instead of falling back to another backend
- hardware begin clears the VICE writeback shadow so program return cannot
  replay a hardware stream as a host-fs mutation
- VICE mode writes file bytes directly through IEC and retains only a bounded
  REU filename shadow for post-return catalog writeback; it does not reserve a
  second file-payload mirror
- callers must close a successfully opened stream, including after a chunk
  failure; replacement is not atomic and a failed stream can leave partial data
- backend selection uses the preserved transport snapshot and does not call
  overwrite-prone low resident probe code
- the hardware/UCI path is implemented but has not been validated on a real
  C64 Ultimate

### Fixed tool `svc_file_stage_reu_sc0`
- input:
  - `0,X` / `1,X`: pointer to a null-terminated source file path
  - `2,X` / `3,X` / `4,X`: 24-bit REU destination address, little-endian
- output:
  - `5,X`: file status (`0` failed, `1` OK, `3` not found)
  - `6,X` / `7,X` / `8,X`: 24-bit staged byte count, little-endian
- current behavior:
  - normal paths resolve from the launched program's drive/directory snapshot;
    a leading `!` resolves from the directory containing the launched tool
  - hardware/UCI mode accepts tree files only and uses `FILE_STAT` before open
    to distinguish missing files, reject sizes wider than 24 bits, and ensure
    destination plus size does not exceed the 16 MiB REU address space
  - hardware/UCI mode then uses `OPEN_FILE`, repeated `READ_DATA` chunks of at
    most `PROGRAM_IMAGE_MAX` (`240`) bytes, REU transfers, and `CLOSE_FILE`
  - the final 24-bit staged count must exactly match the `FILE_STAT` size;
    short reads, growth races, transfer-count overflow, and close errors fail
  - failures return a zero staged count even though an already transferred REU
    prefix is not erased; missing files return `not found` with a zero count
  - resolver state is restored on every hardware return and backend selection
    uses the preserved transport snapshot without calling low resident probe code
  - VICE mode retains the existing IEC read and REU transfer path
  - VICE mode reloads the caller's REU destination after path resolution so
    resolver scratch transfers cannot redirect the staged payload
  - the hardware/UCI path is implemented but has not been validated on a real
    C64 Ultimate

### Fixed tool `svc_dir_make_sc0`
- input:
  - `0,X` / `1,X`: pointer to a null-terminated directory path
- output:
  - `2,X`: directory status using the `svc_dir_begin_sc0` status values
- current behavior:
  - resolves the parent path from the launched program's drive/directory snapshot
  - rejects flat, unmounted, malformed, and already-existing targets
  - hardware/UCI mode probes with `FILE_STAT`, issues `CREATE_DIR`, and records
    the new nested directory mapping
  - VICE mode creates the host directory and persists its parent manifest
- purpose:
  - provides the directory-create primitive used by `XCOPY.OVL`

### Fixed tool `svc_file_copy_sc0`
- input:
  - `0,X` / `1,X`: pointer to a null-terminated source file path
  - `2,X` / `3,X`: pointer to a null-terminated destination file path
- output:
  - `4,X`: file status
- current behavior:
  - resolves every directory component from the launched program's
    drive/directory snapshot
  - rejects flat, unmounted, unresolved source, and unresolved destination paths
  - hardware/UCI mode probes the source with `FILE_STAT`, uses `COPY_FILE` for
    same-drive copies, and streams cross-drive copies through `OPEN_FILE`,
    `READ_DATA`, `WRITE_DATA`, and `CLOSE_FILE`
  - VICE mode persists the copied file and destination manifest immediately and
    releases the transient resident file-cache slot, so a recursive caller is
    not limited to six total file copies
- purpose:
  - provides the file mutation primitive used by `XCOPY.OVL` without changing
    the user's current shell prompt

### Fixed tool `svc_dir_remove_sc0`
- input:
  - `0,X` / `1,X`: pointer to a null-terminated directory path
- output:
  - `2,X`: directory status using the `svc_dir_begin_sc0` status values
- current behavior:
  - resolves every directory component from the launched program snapshot
  - rejects flat and unmounted paths explicitly
  - compares both drive and directory ID before returning `busy`
  - enumerates the target on the selected backend and rejects non-empty targets
  - hardware/UCI mode uses `OPEN_DIR` / `READ_DIR` for the empty check and
    `DELETE_FILE` to remove the empty directory
  - VICE mode removes hidden `UDOSDIR.TXT` metadata before the physical
    directory, persists the parent manifest, and queues the directory-cache
    tombstone for resident restore
- purpose:
  - provides the post-order directory mutation used by `DELTREE.OVL`

### Fixed tool `svc_file_delete_sc0`
- input:
  - `0,X` / `1,X`: pointer to a null-terminated file path
- output:
  - `2,X`: file status
- current behavior:
  - resolves nested paths from the launched program snapshot
  - hardware/UCI mode probes with `FILE_STAT` and removes the file with
    `DELETE_FILE`
  - VICE mode persists host-file and manifest deletion immediately, records an
    empty replay state, and releases the transient cache slot, so a recursive
    caller is not limited to six total file deletes
- purpose:
  - provides the file mutation used by `DELTREE.OVL`

### Fixed tool `svc_file_rename_sc0`
- input:
  - `0,X` / `1,X`: pointer to a null-terminated source file path
  - `2,X` / `3,X`: pointer to a null-terminated destination file path
- output:
  - `4,X`: file status
- current behavior:
  - resolves both nested paths from the launched program snapshot
  - reports `nofile` for a missing source and `exists` without overwriting an
    existing destination
  - hardware/UCI mode probes both paths with `FILE_STAT` and uses
    `RENAME_FILE` when both names are in the same directory
  - hardware/UCI cross-directory or cross-drive moves reuse the generic
    `COPY_FILE` or read/write stream followed by `DELETE_FILE`; if source
    deletion fails after a successful copy, the new destination is removed
  - VICE mode retains the manifest-backed host rename and immediate mutation
    writeback behavior
  - the hardware/UCI path is implemented but has not been validated on a real
    C64 Ultimate

Tool mutation replay retains up to `48` fixed 71-byte records in REU. This
matches the bounded mutation limit used by `XCOPY.OVL` and `DELTREE.OVL`.
Resident-private REU state uses bank `$FF`; the temporary low-resident/tool swap
uses bank `$FE`, and bounded fixed-tool file staging uses bank `$FD`.

### Fixed tool `svc_program_chain_sc0`
- input:
  - `0,X` / `1,X`: pointer to a null-terminated command line
- output:
  - carry clear when queued, set when rejected
- current behavior:
  - accepts a non-empty command of at most 31 bytes
  - normalizes ASCII command text through the resident shell input rules before
    resolving the successor
  - stores the command in the resident-private stream-shadow REU slot so
    restoring UDOS cannot erase it
  - launches the queued command through the normal resident program loader only
    after the caller exits successfully through `svc_program_exit`
  - discards the request when the caller exits with a nonzero status
  - queues one successor only; the successor may queue its own next stage
  - must be the final Tool ABI operation before `svc_program_exit`
  - does not embed a runner in the linked program or bypass ALINK's direct PRG
    output

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
  - `5`: reserved / not user-facing
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

- real-hardware validation and target-specific correction of the existing UCI
  transport, module staging, and recursive mutation paths
