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
  `MEM`, `TYPE`, `COPY`, `REN`, `DEL`, and `RUN` validated under VICE.

See:
- `PIVOT_PLAN.md`
- `ARCHITECTURE.md`
- `BUILDING.md`
- `MILESTONE_HANDOFF.md`
- `STATUS_UDOS.md`
- `TODO_UDOS.md`
