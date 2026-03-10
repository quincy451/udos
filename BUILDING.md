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
- builds the resident D64 image and BASIC wrapper
- autostarts the BASIC wrapper PRG in `x64sc` for more reliable repeated emulator runs
- enters the resident bootstrap/core image
- binds `A:` as `D64` and `B:` as `DNP`
- renders the prompt from resident drive/path state
- runs the current live command loop
- drives the resident shell under VICE with `-keybuf "help\rvol\rmountb:d81\rvol\rcdbin\rmountb:dnp\rcdb:\rdir\rcdsrc\rtypebootasm\rdir\rquit\r"`
- applies `-keybuf-delay 300` so the injected shell transcript does not race VICE's own autostart sequence
- screen transcript includes:
  - `UDOS CORE`
  - `A:D64/> HELP`
  - `HELP VER VOL MEM DIR CD MOUNT TYPE`
  - `A:D64/> VOL`
  - `A:SYSTEM D64 B:WORK DNP`
  - `A:D64/> MOUNTB:D81`
  - `B:WORK D81`
  - `A:D64/> VOL`
  - `A:SYSTEM D64 B:WORK D81`
  - `A:D64/> CDBIN`
  - `FLAT IMAGE`
  - `A:D64/> MOUNTB:DNP`
  - `B:WORK DNP`
  - `A:D64/> CDB:`
  - `B:DNP/`
  - `B:DNP/> DIR`
  - `B:DNP/ BIN/ SRC/ WORK/`
  - `B:DNP/> CDSRC`
  - `B:DNP/SRC`
  - `B:DNP/SRC> TYPEBOOTASM`
  - `; BOOT.ASM MOCK SOURCE`
  - `B:DNP/SRC> DIR`
  - `B:DNP/SRC BOOT.ASM FS.AVM`
  - `B:DNP/SRC> QUIT`
- `$CFE8 == $01`, `$CFE9 == $01` confirm `A:` bind result `D64/flat`
- `$CFEA == $04`, `$CFEB == $02` confirm `B:` bind result `DNP/tree`
- `$CFEC == $01` confirms current drive `B:` after the `CD` sequence
- `$CFEE == $02` confirms current-drive mount flags `tree`
- `$CFF0 == $01` confirms transport mode `mock`
- `$CFF2 == $04` confirms current-drive mount kind `DNP`
- `$CFF4 == $01` confirms ABI version snapshot from VM-side `stma`
- `$CFFF == $52` confirms resident-ready marker

Current note:
- `svc_line_read` now uses live keyboard input on the resident path
- emulator validation still remains deterministic because `make vice-resident` injects a fixed VICE key buffer
- the resident parser now accepts a command word plus one argument
- `CD`, `DIR`, `MOUNT`, and `TYPE` also accept inline shorthand such as `CDB:`, `CDSRC`, `MOUNTB:D81`, and `TYPEBOOTASM` because VICE `-keybuf` spacing is not reliable
- `VOL` now renders resident volume labels plus mount kind
- `TYPE` resolves descriptor-backed mock file content and currently tolerates optional `.` in filename matching

Current validated linked resident entrypoint:
- `.start = $1810`

Current resident footprint from the map:
- Acheron dispatcher: `$00E6`
- Acheron runtime body: `$072A`
- resident core code: `$14FC`

Current validation note:
- `make vice-resident` now waits for the stable `UDOS CORE` banner plus the ready marker and byte snapshots
- it autostarts `build/udosres.prg` instead of the D64 image because repeated VICE disk autostarts were timing-sensitive
- it delays the injected shell commands so VICE autostart can finish before resident input begins
- disk-image creation is still verified by `make resident` and the build tests

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
  A:D64/> HELP
HELP VER VOL MEM DIR CD MOUNT
  A:D64/> VOL
A:SYSTEM D64 B:WORK DNP
  A:D64/> MOUNTB:D81
B:WORK D81
  A:D64/> VOL
A:SYSTEM D64 B:WORK D81
  A:D64/> CDBIN
FLAT IMAGE
  A:D64/> MOUNTB:DNP
B:WORK DNP
  A:D64/> CDB:
B:DNP/
  B:DNP/> DIR
B:DNP/ BIN/ SRC/ WORK/
  B:DNP/> CDSRC
B:DNP/SRC
  B:DNP/SRC> TYPEBOOTASM
; BOOT.ASM MOCK SOURCE
  B:DNP/SRC> DIR
B:DNP/SRC BOOT.ASM FS.AVM
  B:DNP/SRC> QUIT
```

Until that run happens on target hardware, all validation here must be described
as emulator validation only.
