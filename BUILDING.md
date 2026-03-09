# Building UDOS

## Prerequisites

Required in the current environment:
- `make`
- `ca65`
- `ld65`
- `python3`
- `c1541`

Optional for emulator validation:
- `x64sc`

Local dependency path assumed by this repo:
- AcheronVM source at `/mnt/c/test/action/acheronvm`

## Phase 1 Proof Build

Build the local AcheronVM dependency, the UDOS proof PRG, a BASIC wrapper, and a
D64 image:

```sh
cd /mnt/c/test/action/udos
make proof
```

Expected proof outputs:
- `build/udos-proof.prg`
- `build/udos-proof.labels`
- `build/udos-proof.map`
- `build/udosboot.prg`
- `build/udos-proof.d64`

## Resident Core Build

Build the resident bootstrap/core slice:

```sh
cd /mnt/c/test/action/udos
make resident
```

Expected resident outputs:
- `build/udos-resident.prg`
- `build/udos-resident.labels`
- `build/udos-resident.map`
- `build/udosres.prg`
- `build/udos-resident.d64`

## Emulator Validation

### Proof

```sh
cd /mnt/c/test/action/udos
make vice-proof
```

Validated proof behavior:
- autostarts a D64 in `x64sc`
- runs the BASIC wrapper into the linked Acheron entrypoint
- reads screen RAM through the VICE binary monitor
- verifies `UDOS VM OK`
- verifies `$CFFF == $42`

Current validated linked proof entrypoint:
- `.start = $1810`

Current proof footprint from the map:
- Acheron dispatcher: `$00E6`
- Acheron runtime body: `$072A`
- UDOS proof code: `$002E`

### Resident Core

```sh
cd /mnt/c/test/action/udos
make vice-resident
```

Validated resident behavior:
- autostarts a D64 in `x64sc`
- enters the resident bootstrap/core image
- binds `A:` as `D64` and `B:` as `DNP`
- renders the prompt from resident state
- runs the current live command loop
- drives the resident shell under VICE with `-keybuf "help\rver\rvol\rmem\rquit\r"`
- screen transcript includes:
  - `UDOS CORE`
  - `A:D64> HELP`
  - `HELP VER VOL MEM`
  - `A:D64> VER`
  - `UDOS ALPHA MOCK`
  - `A:D64> VOL`
  - `A:D64 B:DNP`
  - `A:D64> MEM`
  - `CORE 011E`
  - `A:D64> QUIT`
- `$CFE8 == $01`, `$CFE9 == $01` confirm `A:` bind result `D64/flat`
- `$CFEA == $04`, `$CFEB == $02` confirm `B:` bind result `DNP/tree`
- `$CFEC == $00` confirms current drive `A:`
- `$CFEE == $01` confirms current-drive mount flags `flat`
- `$CFF0 == $01` confirms transport mode `mock`
- `$CFF2 == $01` confirms current-drive mount kind `D64`
- `$CFF4 == $01` confirms ABI version snapshot from VM-side `stma`
- `$CFFF == $52` confirms resident-ready marker

Current note:
- `svc_line_read` now uses live keyboard input on the resident path
- emulator validation still remains deterministic because `make vice-resident` injects a fixed VICE key buffer
- the first resident parser still tokenizes only the first command word

Current validated linked resident entrypoint:
- `.start = $1810`

Current resident footprint from the map:
- Acheron dispatcher: `$00E6`
- Acheron runtime body: `$072A`
- resident core code: `$011E`

## Tests

Run the current test surface with the standard library test runner:

```sh
cd /mnt/c/test/action/udos
python3 -m unittest discover -s tests -q
```

Notes:
- build tests always run
- VICE-backed tests are skipped automatically when `x64sc` is not installed

## Hardware Validation

No target hardware validation has been performed from this environment.

For a real C64 Ultimate test, copy either `build/udos-proof.d64` or
`build/udos-resident.d64` to media the machine can mount and boot the first
program on the disk. For the resident image, the current expected interactive smoke sequence is:

```text
UDOS CORE
  A:D64> HELP
HELP VER VOL MEM
  A:D64> VER
UDOS ALPHA MOCK
  A:D64> VOL
A:D64 B:DNP
  A:D64> MEM
CORE 011E
  A:D64> QUIT
```

Until that run happens on target hardware, all validation here must be described
as emulator validation only.
