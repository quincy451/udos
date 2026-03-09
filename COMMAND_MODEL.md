# UDOS Command And Module Model

## Resident vs Overlay

Resident components hold the always-needed execution environment:
- native bootstrap
- resident AcheronVM runtime
- native service ABI
- shell dispatcher
- first built-in commands

Overlay components hold less common commands and larger features:
- `XCOPY`
- `DELTREE`
- `TREE`
- batch execution
- later development tools

## Command Resolution

Planned command resolution order:
1. built-in resident command
2. mounted executable/module lookup on current drive
3. overlay lookup by command name
4. explicit error message

## Module Format Direction

Near-term direction:
- bootstrap and core remain a single D64-loadable image
- overlay/module format stays simple and native-project-specific at first
- AcheronVM remains resident; later modules provide VM code payloads plus minimal metadata

Minimum metadata planned for loadable modules:
- module name
- ABI version requirement
- entry symbol or entry offset
- optional exported command name

## Flat vs Tree Filesystems

Command semantics must respect mounted image type.

- `D64`, `D71`, `D81`: flat namespace only
- `DNP`: subdirectories allowed

Any command that requires tree semantics on a flat image must fail explicitly.
