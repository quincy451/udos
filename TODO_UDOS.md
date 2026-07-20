# UDOS TODO

This file tracks remaining work only. Completed milestone history lives in
`STATUS_UDOS.md`, and the handoff summary lives in `MILESTONE_HANDOFF.md`.

Current behavior contracts are documented in `FILESYSTEM_BEHAVIOR.md` and
`OPERATOR_GUIDE.md`. Real hardware validation procedure and result-recording
rules are documented in `HARDWARE_VALIDATION.md`.

## Active Baseline

- UDOS is the maintained native shell/runtime path.
- Action tooling runs as UDOS-aware `.PRG` programs.
- The maintained Action build path is direct object/link output:
  `ACTC.PRG -> OBJ/<MODULE>.OBJ -> ALINK.PRG -> BIN/<MODULE>.PRG`.
- Linked Action programs are direct 6502 `.PRG` files; there is no separate
  runtime runner in the maintained path.
- `D64`, `D71`, and `D81` are flat images.
- `DNP` is tree-capable.

## Phase 5 Remaining Resident Work

- Hardware-validate and harden the existing UCI-backed paths on real C64
  Ultimate hardware before changing any `Hardware/UCI` status to `Yes`:
  - `MOUNT_DISK`
  - `CHANGE_DIR` / `GET_PATH`
  - `OPEN_DIR` / `READ_DIR`
  - `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE`
  - raw flat-image `FILE_SEEK` / `READ_DATA` traversal
  - raw flat-image `WRITE_DATA` mutation paths
  - `CREATE_DIR`, `DELETE_FILE`, `RENAME_FILE`, and `COPY_FILE`
  - implicit program-image loads
  - fixed external-tool file probe/load, including bounded too-large results
  - fixed external-tool file save, including explicit-length, empty, and
    zero-length text-compatibility writes
  - external-tool streamed write begin/chunk/close, including binary payloads
    and close-error handling
  - fixed external-tool file stage-to-REU, including 24-bit capacity and exact
    final-count validation
- Extend `VOL` from flat-image header import and mount-derived tree metadata to
  true mounted-image metadata across the remaining formats.
- Keep the REU-backed resident spill/restore path measured as command and
  program-launch headroom changes.

## Phase 6 Overlay Commands

- Hardware-validate the native `UDOV` loader's UCI tree-file staging path plus
  the implemented hardware Tool ABI operations used by `TREE`, `XCOPY`, and
  `DELTREE`, then fix any target-specific failures.
- Keep flat-image behavior explicit: recursive commands must reject flat images
  clearly instead of pretending flat images have directories.
- Evaluate REU cache/workspace policy with measurements after overlay commands
  have real payloads.

## Action Toolchain Work

- Keep `ACTC.PRG` emitting `.OBJ` records for `ALINK.PRG`.
- Keep `ALINK.PRG` producing direct `BIN/<MODULE>.PRG` output.
- Continue widening ACTC source coverage and source-backed object emission.
- The fixed register-entry ABI is implemented for ASMBLOCK and core raw
  machine bodies. Decimal/hexadecimal/binary calls, character/signed/sum raw
  constants, local-routine/current-address/storage relocations, and explicit
  signature/16-byte rejection are covered. Complete named compiler constants
  and external/fixed-address expressions next.
- Use `actionc64u/docs/idun_feature_parity.md` as the ordered cross-product
  backlog. General REAL calls/returns and multi-function MATH1 come next;
  arrays/pointers/records and recursive typed frames remain separate bounded
  native compiler work rather than assumptions inherited from the Linux host.
- Continue widening ALINK object closure, relocation, and helper-selection edge
  cases.
- Keep optional runtime/library helpers as link-selected `.OBJ` modules that are
  included only when referenced.
- Continue moving large ACTC and ALINK lookup payloads into REU-backed tables as
  capacity pressure appears.
- Implement the imported `actionc64u/docs/new_math_func.txt` contract in
  dependency order: general REAL function ABI and constants first, then the
  portable utility, exponential/logarithmic, trigonometric, hyperbolic, and
  angle-conversion source families with target-known-value coverage.
- Implement the imported `actionc64u/docs/new_gfx_func.txt` contract: validated
  global graphics resources and relocatable asset exports, ACTSPRITE/
  ACTBITMAP plus ACTEDIT F8 dispatch, and the tracked high-level GFX1 source
  surface. Generated programs must keep graphics code/data link-selected and
  must not depend on resident UDOS calls.

## Documentation And Release Hygiene

- Maintain `OPERATOR_GUIDE.md` as the user-facing command and launch guide.
- Maintain `FILESYSTEM_BEHAVIOR.md` as the detailed filesystem behavior guide.
- Maintain `HARDWARE_VALIDATION.md` as the real-hardware runbook and update
  status files only after recorded target runs.
- Maintain `MILESTONE_HANDOFF.md` before resuming major Action development
  batches or moving the project to another machine.
