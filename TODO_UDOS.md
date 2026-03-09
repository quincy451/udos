# UDOS TODO

## Phase 1

- validate `udos-proof.prg` in VICE
- record proof memory footprint from map output
- decide which AcheronVM features stay enabled for the resident shell build

## Phase 2

- define bootstrap image layout
- define resident ABI entry numbering and register conventions
- implement native trampoline table
- implement a tiny resident shell loop stub in VM code

## Phase 3

- document C64 Ultimate UCI assumptions and unknowns
- implement native UCI transport primitives
- add VM-callable wrappers and a host-side seam where possible

## Phase 4

- implement mounted-image model for `A:` and `B:`
- add flat-filesystem enforcement for D64/D71/D81
- add DNP directory semantics and explicit flat-image errors
- define path parser and canonical drive/path rules

## Phase 5

- expand live line input from token-only parsing to command + argument parsing
- keep the current resident `HELP`, `VER`, `VOL`, and `MEM` loop working while moving them toward real filesystem/state services
- implement resident commands:
  - `DIR`
  - `CD`
  - `MOUNT`
  - `TYPE`
  - `COPY`
  - `REN`
  - `DEL`
  - `RUN`
  - real `VOL`
  - real `MEM`
  - real `HELP`
  - real `VER`

## Phase 6

- implement overlay loader
- implement `XCOPY`
- implement `DELTREE`
- implement `TREE`
- implement batch/scripting support
- evaluate REU cache/workspace policy with measurements

## Phase 7

- add operator guide
- add detailed filesystem behavior guide
- add hardware runbook for real C64 Ultimate testing
- write milestone handoff before resuming Action development tools work
