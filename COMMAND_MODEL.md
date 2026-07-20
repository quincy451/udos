# UDOS Command And Module Model

## Resident vs Overlay

Resident components hold the always-needed execution environment:
- native bootstrap
- native service ABI
- shell dispatcher
- first built-in commands
- `TREE` dispatch glue with a one-level resident fallback
- parsed-command overlay-name construction and `UDOV` validation
- path-scoped directory enumeration service for overlay tools

Overlay components hold less common commands and larger features:
- recursive `TREE` (`TREE.OVL`)
- recursive `XCOPY` (`XCOPY.OVL`)
- recursive `DELTREE` (`DELTREE.OVL`)
- batch execution
- later development tools

## Command Resolution

Current command resolution order:
1. built-in resident command
2. token-derived `<COMMAND>.OVL` lookup for built-ins that have an overlay payload
3. mounted `.PRG` / `.BAT` lookup for non-keyword command lines
4. resident fallback or explicit error message

## Module Format Direction

The first native command-overlay format is `UDOV` version `1`. A module file
contains a two-byte C64 load address followed by this 14-byte loaded header:

| Offset | Size | Meaning |
| --- | ---: | --- |
| `0` | 4 | magic `UDOV` |
| `4` | 1 | format version |
| `5` | 1 | minimum Tool ABI version |
| `6` | 1 | exported resident command ID |
| `7` | 1 | flags, zero in version 1 |
| `8` | 2 | expected C64 load address |
| `10` | 2 | absolute entry address |
| `12` | 2 | exact loaded-image byte length |

The resident stages the complete module in REU, validates all header fields,
checks that the entry lies inside the bounded loaded image, then spills itself,
copies the module into C64 RAM, and calls the validated entry. A missing,
truncated, incompatible, or malformed module is never entered.

Current traversal path:
- fixed tool service `svc_dir_begin_sc0` lets an overlay command enumerate a
  selected tree path and then consume entries through `svc_dir_next`
- this is intentionally path-scoped rather than a shell `CD`, so recursive
  overlays can walk child paths without moving the visible prompt
- `TREE.OVL` walks nested paths by
  enumerating one directory at a time and pushing child paths onto its own
  bounded stack
- resident `TREE` resolves `TREE.OVL` from the parsed command token; if
  the module is unavailable or invalid, the one-level resident scaffold remains
  the fallback
- `XCOPY.OVL` snapshots each selected directory, creates or merges matching
  destination directories, and copies files through `svc_file_copy_sc0` while
  maintaining its own bounded source/destination path stack
- resident `XCOPY` validates command ID `21`; invalid modules report
  `OVERLAY INVALID` and are never entered
- `DELTREE.OVL` performs bounded post-order traversal through path-scoped
  directory remove and file delete services; preflight rejects the current
  directory before any child mutation
- resident `DELTREE` validates command ID `22`; invalid modules report
  `OVERLAY INVALID` and flat images report `FLAT IMAGE`
- module staging supports both VICE and hardware/UCI tree backends; the UCI
  direct-PRG/`UDOV` stager plus nested Tool ABI enumerate/create/copy/delete/
  remove paths are implemented but not validated on real Ultimate hardware

## Flat vs Tree Filesystems

Command semantics must respect mounted image type.

- `D64`, `D71`, `D81`: flat namespace only
- `DNP`: subdirectories allowed

Any command that requires tree semantics on a flat image must fail explicitly.
