# UDOS

UDOS is a new Commodore 64 Ultimate shell/runtime project centered on AcheronVM.

This repo is intentionally separate from the existing `actionc64u/` and `cpm65-u64/`
work so the shell/runtime can move forward without continuing CP/M-65 feature work.

Current milestone:
- Phase 0 complete: pivot notes and project area established.
- Phase 1 complete.
- Phase 2 bootstrap/core slice complete.
- Phase 3 native UCI seam complete at the control/status boundary.
- Phase 4 mounted-image abstraction seam complete with flat-vs-tree policy.
- Phase 5 resident shell milestone in progress with `DIR`, `CD`, `VOL`, `MOUNT`,
  `MEM`, `TYPE`, `COPY`, `REN`, `DEL`, direct `A:`/`B:` drive switching, and
  implicit program launch validated under VICE.
- Phase 5 now also includes a hardware-backed directory-enumeration path in code:
  - resident path synchronization through Ultimate DOS `CHANGE_DIR`
  - backend-path refresh through `GET_PATH`
  - directory cache fill through `OPEN_DIR` / `READ_DIR`
  - mock fallback retained for VICE and failure cases
- Phase 5 now also includes a hardware-backed `TYPE` read path in code:
  - resident path synchronization through `CHANGE_DIR`
  - file open/read/close through `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE`
  - mock fallback retained for VICE and failure cases
- Phase 5 now also includes a hardware-backed `DEL` path in code:
  - resident path synchronization through `CHANGE_DIR`
  - file delete through `DELETE_FILE`
  - mock deletion is used only when hardware UCI is unavailable
  - hardware-side delete failures return an explicit shell error

Current command parser rule:
- shell keywords require a separator before arguments
- direct drive tokens like `A:` and `B:` switch the current logical drive
- a non-keyword token implies program launch; if it has no extension, `.PRG` is appended
- example: `DEL BOOT3.PRG` deletes the file, while `DELBOOT3` is treated as a bare program token and returns `PROGRAM NOT FOUND`

See:
- `PIVOT_PLAN.md`
- `ARCHITECTURE.md`
- `BUILDING.md`
- `MILESTONE_HANDOFF.md`
- `STATUS_UDOS.md`
- `TODO_UDOS.md`
