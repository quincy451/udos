# UDOS Operator Guide

UDOS is a native Commodore 64 Ultimate shell and resident service environment.
It boots to a DOS-like prompt and launches direct `.PRG` programs. Linked Action
programs are ordinary PRGs produced by `ALINK`; there is no separate runtime
runner in the maintained path.

## Prompt

The prompt has this form:

```text
A:D64/>
B:DNP/SRC>
```

Prompt fields:

- `A:` or `B:` is the current logical drive.
- `D64`, `D71`, `D81`, or `DNP` is the mounted image type.
- `/` or `/SRC` is the current directory for that logical drive.

Each logical drive keeps its own current directory. Switching from `B:` back to
`A:` does not reset `B:`.

## Drive And Image Policy

UDOS exposes two active logical drives:

- `A:` is the system drive and defaults to a flat `D64` image.
- `B:` is the workspace drive and is normally mounted to a `DNP` tree image.

Image semantics are intentionally strict:

- `D64`, `D71`, and `D81` are flat images.
- `DNP` is tree-capable and supports subdirectories.
- Commands that need tree behavior on a flat image must fail clearly instead of
  pretending flat images have directories.

`C:` and `D:` are reserved direct-drive tokens. They currently return `DRIVE NOT
PRESENT`.

## Command Rules

Command keywords require a separator before arguments.

Examples:

```text
DEL BOOT3.PRG
DELBOOT3
```

The first example runs the resident `DEL` command. The second is not a keyword
match, so UDOS treats it as a bare program name and tries to launch
`DELBOOT3.PRG`.

Current command resolution order is:

1. resident built-in command
2. token-derived `<COMMAND>.OVL` lookup for built-ins that have one
3. direct drive token
4. implicit `.PRG` launch from the current mounted image
5. implicit `.BAT` launch from the current mounted image
6. resident fallback or explicit error message

## Action Tool Workflow

The full Action development set is distributed in `ACTION.DNP`. The system
`D64` is capacity-limited and is only a boot/tool subset. Mount `ACTION.DNP` on
`B:` before using the complete compiler, linker, editor, and debugger set.

From an Action project directory:

```text
ACTC MAIN
ACTC MAIN,
ACTC MAIN:
```

The plain form compiles only. A trailing comma compiles and chains directly to
`ALINK`; a trailing colon compiles, links, and chains directly to `ACTDBG`.
Every stage is an ordinary PRG, and `ALINK` emits the complete runnable PRG.

`TREE`, `XCOPY`, and `DELTREE` resolve token-derived `.OVL` modules. UDOS
validates each `UDOV` header, Tool ABI requirement, command ID, load range,
entry address, and exact image length before executing it. `TREE` retains its
one-level resident fallback. Invalid `XCOPY` or `DELTREE` modules report
`OVERLAY INVALID`. Hardware/UCI overlay staging is implemented but not
hardware-validated. Nested hardware/UCI Tool ABI enumeration, directory create,
file copy/delete, and empty-directory removal are also implemented but not
hardware-validated.

## Built-In Commands

### HELP

Prints resident help text.

```text
HELP
```

### VER

Prints the UDOS version banner.

```text
VER
```

### MEM

Reports launch-capable lower RAM and REU reservation state.

```text
MEM
```

When REU is present, `RAM USED` is the preserved lower-RAM footprint after the
resident spill path, `RAM FREE` is launch-available lower RAM, and `REU USED`
includes resident spill and VICE tree-cache reservation.

### VOL

Prints mounted volume state for `A:` and `B:`.

```text
VOL
```

### MOUNT

Mounts an image path on a logical drive and resets that drive to `/`.

```text
MOUNT B: /IMAGES/WORK.DNP
MOUNT A: /IMAGES/SYSTEM.D64
```

UDOS infers the image type from `.D64`, `.D71`, `.D81`, or `.DNP`.

### Drive Switch

Switches current logical drive.

```text
A:
B:
```

### DIR

Lists the current directory.

```text
DIR
```

On a `DNP`, directory entries end with `/`.

### TREE

Lists a tree-capable directory. When a valid `TREE.OVL` module is available,
UDOS runs it for recursive traversal. Otherwise it uses the current one-level
resident scaffold.

```text
TREE
TREE SRC
```

With `TREE.OVL` present, `TREE SRC` recursively traverses the selected directory.
Without a valid module, bare `TREE` at the root expands the root child directories
one level and `TREE SRC` lists the selected directory without deeper recursion.
Flat images reject `TREE` with a flat-image error. Full recursive traversal
through the overlay path is VICE-validated. Hardware/UCI overlay staging is
implemented but not hardware-validated; its nested `OPEN_DIR` / `READ_DIR`
traversal path is likewise awaiting target validation.

### XCOPY

Recursively copies one tree-capable directory into another through
`XCOPY.OVL`.

```text
XCOPY <source-dir> <destination-dir>
XCOPY XCSRC XCDST
XCOPY SRC BACKUP/SRC
```

The destination directory is created when absent and merged when it already
exists. The command rejects flat images, equal source/destination paths, and a
destination nested inside the source. It uses bounded 31-character paths, a
16-directory traversal stack, 6-entry directory snapshots, and a 48-mutation
invocation limit. `PATH TOO LONG` or `XCOPY TOO LARGE` reports a bound violation.
The operation is not transactional, so successful copies completed before a
later error remain in the destination. Hardware/UCI directory creation and
same-drive/cross-drive file-copy paths are implemented but not hardware-validated.

### DELTREE

Recursively removes one tree-capable directory through `DELTREE.OVL`.

```text
DELTREE <directory>
DELTREE BUILD/OLD
```

Files are removed before their containing directories using post-order
traversal. The command rejects flat images and protects `/`, `.`, drive roots,
and the current directory. It uses
bounded 31-character paths, a 16-directory traversal stack, 6-entry directory
snapshots, and a 48-mutation invocation limit. `PATH TOO LONG` or `DELTREE TOO
LARGE` reports a bound violation. The operation is not transactional, so
successful removals completed before a later error remain deleted.
Hardware/UCI file deletion and empty-directory removal paths are implemented
but not hardware-validated.

### CD

Changes directory on a tree-capable image.

```text
CD SRC
CD /WORK
CD /
```

On flat images, subdirectory changes are rejected.

### MD

Creates a directory on a tree-capable image.

```text
MD NEW
```

Flat images reject directory creation with a flat-image error.

### RD

Removes an empty directory on a tree-capable image.

```text
RD NEW
```

Non-empty directories are rejected.

### TYPE

Reads and prints a text file.

```text
TYPE README.TXT
TYPE SRC/BOOT.ASM
```

### COPY

Copies a file.

```text
COPY BOOT.ASM /WORK/BOOT2.ASM
COPY HELLO.PRG /WORK/HELLO2.PRG
```

Limited wildcard forms are supported:

```text
COPY *.* /WORK
COPY *.PRG /WORK
COPY NAME.* /WORK
COPY * /WORK
```

Wildcard copy preserves the matched source filename and expects the destination
to resolve to a directory.

### REN

Renames a file within the same resolved directory.

```text
REN BOOT2.ASM BOOT3.ASM
```

### DEL

Deletes a file.

```text
DEL BOOT3.ASM
```

Limited wildcard forms are supported:

```text
DEL *.*
DEL *.PRG
DEL NAME.*
DEL *
```

## Program Launch

A non-keyword token launches a program from the current image. If no extension is
provided, UDOS appends `.PRG`.

```text
RETTEST DIR
ACTC.PRG MAIN
ALINK.PRG MAIN
BIN/MAIN.PRG
```

Launched UDOS-aware programs return through the resident program ABI. The command
line is exposed to the launched program, and the resident shell prompt is
restored after return.

`ACTEDIT.PRG` can drive the same direct-program workflow:

```text
Ctrl-O  save and compile
Ctrl-B  save, compile, and link
Ctrl-D  save, compile, link, and enter ACTDBG
```

The build and debug paths queue one successor at a time through the fixed Tool
ABI. ACTC queues ALINK only after writing `OBJ/<MODULE>.OBJ`; ALINK queues ACTDBG
only after writing both `BIN/<MODULE>.PRG` and `BIN/<MODULE>.DBG`.

`Ctrl-O` uses the compact `ACTC <MODULE>;` compile-only form. If ACTC reports a
source diagnostic, compile, build, and debug workflows reopen
`ACTEDIT <MODULE>:<LINE>` at the failing line. A plain `ACTC <MODULE>` command
still returns the compiler failure directly to the shell.

The maintained Action tool path is:

```text
ACTC.PRG -> OBJ/<MODULE>.OBJ -> ALINK.PRG -> BIN/<MODULE>.PRG
```

`ALINK.PRG` owns all bytes that go into the final runnable PRG.

## Batch Launch

If a `.PRG` lookup fails, UDOS can fall back to a `.BAT` file with the same base
name.

Supported batch behavior:

- `%1`, `%2`, and `%3` argument expansion
- `ECHO`
- stop on command failure

Example:

```text
ARGS ONE TWO THREE
STOP
```

## Current Validation Boundary

VICE validates the resident shell, filesystem semantics, REU-backed launch and
restore, and Action tool launch gates. VICE does not provide the Ultimate UCI
hardware block.

Use `HARDWARE_VALIDATION.md` for real C64 Ultimate testing before changing any
`Hardware/UCI` command status to `Yes`.
