# UDOS Filesystem Behavior Guide

This guide documents the user-visible filesystem rules for UDOS. It is the
behavior-level companion to the lower-level `FS_ABSTRACTION.md` implementation
notes and the backend status in `COMMAND_MATRIX.md`.

Use this file when deciding whether a command should succeed, fail, or remain a
planned feature. Use `OPERATOR_GUIDE.md` for command examples and
`HARDWARE_VALIDATION.md` before changing any real Ultimate `Hardware/UCI` status.

## Image Policy

UDOS intentionally treats mounted image types as different filesystems.

Flat images:

- `D64`
- `D71`
- `D81`

Flat images have one root namespace. They do not have subdirectories. A command
that requires subdirectory behavior on a flat image must fail with a clear
flat-image error instead of pretending directories exist.

Tree-capable images:

- `DNP`

`DNP` images expose subdirectories and are the normal workspace format for Action
projects, generated source trees, object output, linked programs, and test data.

## Logical Drives

UDOS currently exposes two active logical drives:

- `A:` is the system drive and defaults to a flat `D64` image.
- `B:` is the workspace drive and normally points at a tree-capable `DNP` image.

Each drive has independent mounted-image state and independent current-directory
state. Switching from `A:` to `B:` and back must not reset either drive's current
directory.

`C:` and `D:` are reserved direct-drive tokens. They must return `DRIVE NOT
PRESENT` until real extra-drive support is implemented.

## Path Rules

The shell accepts bare names, rooted paths, and simple relative paths.

Examples:

```text
TYPE README.TXT
TYPE SRC/MAIN.ACT
COPY SRC/MAIN.ACT /WORK/MAIN.ACT
CD /
CD SRC
```

Rules:

- `/` means the root of the current mounted image.
- relative paths resolve from the current directory of the current drive.
- direct drive tokens switch the current logical drive before later commands run.
- flat images accept only root-level file operations.
- `DNP` images may traverse named subdirectories.

The resident implementation keeps path handling deliberately bounded. Nested
file paths and path-scoped directory traversal are supported on the VICE tree
backend; recursive commands additionally enforce their documented path, stack,
entry, and mutation limits.

## Directory Commands

`DIR` lists the current directory.

- On flat images, `DIR` lists the root directory.
- On `DNP`, `DIR` lists the current tree directory.
- Directory entries on a tree-capable image are displayed with a trailing `/`.

`TREE` resolves and validates the native `TREE.OVL` command module for recursive
traversal, with a one-level resident scaffold as fallback.

- `TREE` lists the selected `DNP` directory using the current directory
  enumeration path.
- `TREE` at a tree root expands the root child directories one level.
- `TREE NAME` resolves `NAME` relative to the current directory.
- `TREE` on `D64`, `D71`, or `D81` must report a flat-image error.
- Full recursive tree traversal through `TREE.OVL` is VICE-validated when the
  module is present and valid.
- Missing, truncated, and malformed overlay modules fall back without receiving
  control.
- Hardware/UCI overlay staging is implemented but not hardware-validated.

`XCOPY` resolves and validates `XCOPY.OVL` for recursive directory copy.

```text
XCOPY <source-dir> <destination-dir>
```

- exactly two directory paths are required
- the source must exist on a tree-capable image
- destination directories are created as needed and existing destination
  directories are merged
- files are copied through the fixed Tool ABI file-copy service
- an equal source/destination or a destination nested inside the source is
  rejected with `BAD XCOPY`
- flat images reject the command with `FLAT IMAGE`
- invalid modules report `OVERLAY INVALID` and are never entered; there is no
  resident recursive-copy fallback
- paths are limited to 31 characters, each directory snapshot to 6 entries,
  traversal depth to 16 pending directories, and one invocation to 48 created
  directories/files
- limit failures report `PATH TOO LONG` or `XCOPY TOO LARGE`
- copy is not transactional; work completed before a later error remains on the
  destination

`DELTREE` resolves and validates `DELTREE.OVL` for recursive directory removal.

```text
DELTREE <directory>
```

- exactly one tree directory path is required
- files are deleted before their containing directories in bounded post-order
- `/`, `.`, bare drive roots, and the current directory are protected
- current-directory preflight occurs before any child is deleted
- flat images reject the command with `FLAT IMAGE`
- invalid modules report `OVERLAY INVALID` and are never entered
- paths are limited to 31 characters, each directory snapshot to 6 entries,
  traversal depth to 16 pending directories, and one invocation to 48 deleted
  files/directories
- parent catalogs are rewritten as line streams and are not limited to a
  255-byte total catalog size
- limit failures report `PATH TOO LONG` or `DELTREE TOO LARGE`
- delete is not transactional; work completed before a later error remains
  deleted

`CD` changes the current directory only on tree-capable images.

- `CD /` returns to the current drive root.
- `CD NAME` enters a child directory.
- `CD` into a missing directory must report `NO SUCH DIR`.
- `CD` into a subdirectory on `D64`, `D71`, or `D81` must report a flat-image error.

`MD` and `RD` are tree-only directory mutation commands.

- `MD NAME` creates a directory on `DNP`.
- `RD NAME` removes an empty directory on `DNP`.
- `RD` must reject non-empty directories with `DIR NOT EMPTY`.
- `MD` and `RD` on flat images must report a flat-image error.

Recursive `TREE`, bounded recursive `XCOPY`, and bounded recursive `DELTREE`
through the general overlay loader are implemented on the VICE tree backend.
Hardware/UCI overlay staging is implemented but not hardware-validated. The
hardware Tool ABI mutations for nested directory creation, file copy/delete,
and empty-directory removal are implemented but not hardware-validated.

### VICE Catalog Persistence

The VICE tree backend persists directory membership in `UDOSDIR.TXT`.

- each mutation reads the existing catalog one logical line at a time
- the matching file or directory line is suppressed and a live replacement is
  appended when required
- unrelated lines are preserved exactly even when the complete catalog exceeds
  255 bytes or its final line has no newline
- an existing catalog is streamed through `UDOSDIR.TMP`, copied back only after
  the temporary output closes successfully, and the temporary file is then
  removed
- a missing catalog is created directly for its first live entry
- successful operations leave no `UDOSDIR.TMP`; a failed replacement may retain
  the temporary file as recovery evidence

Catalog persistence does not remove the six-entry directory-snapshot limit used
by one enumeration call. Total catalog size and one traversal snapshot are
separate limits.

- enumeration reads the complete catalog as a line stream rather than stopping
  after 255 bytes
- if the six-entry snapshot is full and a later catalog entry is a directory,
  one cached file is evicted so recursive traversal can still discover it
- exact file operations can fall back to a physical host-file probe when a file
  was not retained in the bounded snapshot
- VICE-created data directories and files use lowercase physical host names;
  logical catalog records remain uppercase, and metadata files retain the
  physical name `UDOSDIR.TXT`

## File Read And Mutation Commands

`TYPE` reads a text file from the current mounted image.

- missing files report `NO SUCH FILE`.
- text display is bounded by resident buffers.
- binary-safe streaming is not implied by `TYPE`.

`COPY` copies a file.

- exact file copy is supported.
- wildcard copy is limited to the patterns listed below.
- wildcard copy preserves each matched source filename.
- wildcard copy expects the destination to resolve to a directory target.

Supported wildcard copy patterns:

```text
COPY *.* /WORK
COPY *.PRG /WORK
COPY NAME.* /WORK
COPY * /WORK
```

`REN` renames a file within the same resolved directory.

- cross-directory rename is not the current behavior contract.
- missing source files report `NO SUCH FILE`.
- conflicting destination handling must remain explicit in command tests.

`DEL` deletes files.

Supported wildcard delete patterns:

```text
DEL *.*
DEL *.PRG
DEL NAME.*
DEL *
```

Wildcard delete affects only the resolved current directory. Recursive delete
uses the bounded `DELTREE` overlay command.

## Program And Batch Lookup

A non-keyword token launches a program from the current image. If no extension is
provided, UDOS appends `.PRG`.

If `.PRG` lookup fails, UDOS may fall back to a same-base `.BAT` file.

Current batch behavior includes:

- `%1`, `%2`, and `%3` argument expansion
- `ECHO`
- stop on command failure

Linked Action programs are direct `.PRG` outputs produced by `ALINK.PRG`; there
is no separate runtime runner in the maintained filesystem or launch path.

## Backend Behavior

`COMMAND_MATRIX.md` is authoritative for backend completion status. The behavior
contract currently distinguishes these backend classes:

- `Mock`: resident in-memory fallback used when hardware UCI is unavailable.
- `Flat`: raw image-backed `D64`, `D71`, and `D81` behavior.
- `VICE tree`: emulator-backed `DNP` tree behavior through VICE fsdevice support.
- `Hardware/UCI`: real Ultimate Command Interface behavior on C64 Ultimate hardware.

Green VICE tests prove the `VICE tree` behavior only. They do not prove
`Hardware/UCI` behavior because VICE does not provide the Ultimate UCI hardware
block.

Hardware rows in `COMMAND_MATRIX.md` must stay `Partial` or `No` until the
matching sequence in `HARDWARE_VALIDATION.md` is run on real C64 Ultimate
hardware and recorded.

## Failure Policy

Filesystem errors must be explicit and deterministic.

Required examples:

- tree command on a flat image: flat-image error
- missing file: `NO SUCH FILE`
- missing directory: `NO SUCH DIR`
- non-empty directory removal: `DIR NOT EMPTY`
- missing program: `PROGRAM NOT FOUND`
- unavailable reserved drive: `DRIVE NOT PRESENT`

When the hardware backend is present and a hardware file operation fails, UDOS
must report an operation failure instead of silently mutating mock state. Mock
fallback is only acceptable when the hardware UCI backend is unavailable.

## Validation Pointers

Use these docs together:

- `OPERATOR_GUIDE.md`: command syntax and examples
- `FS_ABSTRACTION.md`: low-level mounted-image service model
- `COMMAND_MATRIX.md`: backend completion status
- `HARDWARE_VALIDATION.md`: real hardware validation runbook
- `BUILDING.md`: build and VICE target list
