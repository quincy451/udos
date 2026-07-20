# UDOS Status

## Milestone

Current milestone: Phase 0 complete, Phase 1 complete, Phase 2 resident bootstrap/core complete, Phase 3 native UCI seam complete, Phase 4 filesystem abstraction seam complete, Phase 5 resident shell/backend slice complete through VICE tree read/write validation and REU-backed UDOS-aware program return.

UDOS remains a standalone C64 program path. It is not using CP/M-65 as the runtime environment for this work.

Command/backend status is tracked separately in `COMMAND_MATRIX.md`.

## Completed

- created a separate `udos` repo/work area
- preserved prior CP/M-65 and Action state in notes so the shell/runtime pivot stayed reversible
- added a resident bootstrap/core image that:
  - enters the native resident shell
  - exposes a first resident service ABI
  - renders a state-driven shell prompt
- added a native UCI transport seam in `src/asm/uci_transport.inc`
- added the mounted-image abstraction seam for `A:` and `B:`
- added a hardware-backed directory-cache path behind `svc_fs_enum_*`
  - flat-image root mounts now first try raw image parsing through `OPEN_FILE` / `FILE_SEEK` / `READ_DATA`
  - tree-capable mounts still synchronize through `CHANGE_DIR`, query `GET_PATH`, and fill a small resident directory cache through `OPEN_DIR` / `READ_DIR`
  - falls back to the descriptor-backed mock model when hardware transport is unavailable or a query fails
- added a VICE tree read backend for `DNP`-style mounts
  - tree listings are now populated from a VICE-side manifest-backed directory cache
  - file reads and implicit launch now resolve through the VICE tree backend instead of the older descriptor-only mock path
- added a VICE tree write backend for `DNP`-style mounts
  - exact and wildcard `COPY` now populate a VICE-side overlay over the manifest-backed tree view
  - exact `REN` now works for both overlay-created files and host-backed files
  - exact and wildcard `DEL` now hide host-backed files and remove overlay-created files
  - implicit launch now returns `PROGRAM NOT FOUND` correctly for missing tree-backed programs under VICE
- added a REU-backed UDOS-aware external launch/return path under VICE
  - implicit launch now stages `.PRG` payloads into REU and launches them through a native trampoline
  - UDOS-aware programs now return through a fixed low-memory return stub and resume the resident shell
  - exit status is captured into `PROGRAM_EXIT_SNAPSHOT`
  - the current validation includes a clobber test that overwrites resident code and still returns to the prompt
- added host-side `DNP` layout coverage for the next raw tree backend slice
  - the synthetic probe image now covers a native-partition root, one subdirectory, and chained file reads
  - the same probe image now also covers reference-sector semantics for `REN`, `DEL`, and `COPY`
- added a hardware-backed `TYPE` read path
  - flat-image mounts now first try raw root-directory lookup plus chained-sector reads through image `OPEN_FILE` / repeated `FILE_SEEK` / repeated `READ_DATA`
  - tree-capable mounts still synchronize the backend path through `CHANGE_DIR`, then use `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE`
  - falls back to the descriptor-backed mock content on hardware/query failure
- added a hardware-backed `DEL` path
  - flat-image mounts now first try raw root-directory lookup, chained sector traversal, and BAM release through image `OPEN_FILE` / repeated `FILE_SEEK` / repeated `READ_DATA` / repeated `WRITE_DATA`
  - tree-capable mounts still synchronize the backend path through `CHANGE_DIR` and delete files through `DELETE_FILE`
  - uses mock deletion only when hardware UCI is unavailable
  - returns an explicit delete failure string on hardware-side errors
- added a hardware-backed `REN` path
  - flat-image mounts now first try raw root-directory lookup plus direct directory-entry rewrite through image `OPEN_FILE` / repeated `FILE_SEEK` / repeated `READ_DATA` / repeated `WRITE_DATA`
  - tree-capable mounts still synchronize the backend path through `CHANGE_DIR` and rename files through `RENAME_FILE`
  - uses mock rename only when hardware UCI is unavailable
  - returns an explicit rename failure string on hardware-side errors
- added a hardware-backed `COPY` path
  - tree-only same-drive copies use `COPY_FILE`
  - tree-only cross-drive copies stream through source `OPEN_FILE`/`READ_DATA` and destination `OPEN_FILE`/`WRITE_DATA`
  - flat-image copies now also have a raw image path:
    - source-side raw root-directory lookup plus chained sector reads when the source mount is flat
    - destination-side raw BAM allocation plus direct directory-entry creation when the destination mount is flat
    - direct image writes through `OPEN_FILE` / repeated `FILE_SEEK` / repeated `READ_DATA` / repeated `WRITE_DATA`
  - uses mock copy only when hardware UCI is unavailable
  - returns an explicit copy failure string on hardware-side errors
- enforced flat-vs-tree policy:
  - `D64`/`D71`/`D81` -> flat
  - `DNP` -> tree-capable
- validated the resident shell under VICE with live `GETIN`-backed input
- implemented resident commands:
  - `HELP`
  - `VER`
  - `VOL`
  - `MEM`
  - `DIR`
  - `CD`
  - `MD`
  - `RD`
  - `TREE`
  - `MOUNT`
  - `TYPE`
  - `COPY`
  - `REN`
  - `DEL`
- added a VICE tree directory mutation path for `DNP`-style mounts
  - `MD` now creates tree directories on the VICE backend
  - `RD` now removes empty tree directories on the VICE backend
  - `RD` now rejects non-empty tree directories on the VICE backend
- added a first one-level resident `TREE` scaffold
  - flat images are rejected explicitly
  - root child directories are expanded one level on tree-capable mounts
  - selected non-root tree directories reuse the current directory enumeration path
  - this remains the fallback when no valid recursive module can be loaded
- added the first recursive-overlay traversal prerequisite to the fixed Tool ABI
  - `svc_dir_begin_sc0` enumerates a selected tree path without changing the
    visible shell prompt
  - fixed service include generation now exposes `svc_dir_begin_sc0` at `$CF3F`
  - `ACTDIR.PRG` can use the service through `ACTDIR <path>`, while bare
    `ACTDIR` still lists the current directory
- added the general native command-overlay loader and first recursive payload
  - module names are derived from parsed command tokens as `<COMMAND>.OVL`
  - version-1 modules carry a `UDOV` header with format version, minimum Tool
    ABI, command ID, load address, entry address, and exact image length
  - the loader stages the complete module in REU and validates its header,
    bounds, entry, and length before spilling the resident or transferring control
  - `TREE.OVL` uses a bounded path stack plus `svc_dir_begin_sc0` /
    `svc_dir_next` to walk nested tree-capable directories
  - missing and malformed modules retain the one-level resident fallback
  - the batch command scratch buffer moved from the main resident payload to
    high-RAM BSS to reduce the loadable resident footprint
  - additional mutable directory state moved to high-RAM BSS, guarded by a
    link-time assertion against the fixed `$CF00` Tool ABI page
  - `make vice-action-tree-overlay` proves `TREE SRC` loads `TREE.OVL` and
    reaches `SRC/NEST/DEEP/FINAL.ACT`
  - `make vice-action-tree-overlay-invalid` proves a truncated invalid module
    is rejected before entry and falls back safely
- added bounded recursive `XCOPY.OVL` through the same validated loader
  - command ID `21` is validated before entry
  - source/destination path pairs use a bounded depth-first stack
  - destination directories are created or merged and files are copied through
    the fixed Tool ABI
  - nested file resolution now consumes every directory component
  - VICE file copies persist immediately and release their transient cache slot,
    allowing the focused gate to copy eleven files across three levels
  - invalid modules report `OVERLAY INVALID`; flat images report `FLAT IMAGE`
  - `make vice-action-xcopy-overlay`,
    `make vice-action-xcopy-overlay-invalid`, and
    `make vice-action-xcopy-overlay-flat` cover those paths
- added bounded recursive `DELTREE.OVL` through the validated loader
  - command ID `22` is validated before entry
  - one path is traversed in post-order with 31-character paths, 6-entry
    snapshots, a 16-entry stack, and a 48-mutation limit
  - nested directory remove now uses component-wise path resolution and
    preserves directory cache slots across host path construction
  - host-backed file delete persists immediately and releases transient cache
    slots, allowing eleven files and three directories in the focused gate
  - `/`, `.`, drive roots, and the current directory are protected; current
    directory preflight occurs before child mutation
  - invalid modules report `OVERLAY INVALID`; flat images report `FLAT IMAGE`
  - focused valid, invalid, flat-image, and busy VICE gates are present
- removed the 255-byte VICE catalog rewrite ceiling
  - `UDOSDIR.TXT` mutations now filter existing catalogs one line at a time
    through `UDOSDIR.TMP` and stream the completed catalog back
  - missing catalogs are created directly, unrelated lines beyond byte 255 are
    preserved exactly, and unterminated final lines remain valid
  - VICE deferred file-not-found status is checked on the first read so newly
    created files are not misclassified as pre-existing hidden entries
  - the oversized gate covers directory create/remove, first-file catalog
    creation, copy, rename, delete, and recursive `DELTREE` with exact catalog
    comparison and no temporary residue
- removed the matching 255-byte VICE catalog enumeration ceiling
  - `UDOSDIR.TXT` enumeration now consumes the complete IEC stream one logical
    line at a time while retaining the six-entry resident snapshot limit
  - a later directory displaces a cached file when the snapshot is full, and
    exact file probes retain a physical-host fallback
  - nested dynamic names are normalized before IEC path emission so generated
    data paths remain lowercase host artifacts while catalog records remain
    uppercase and metadata remains `UDOSDIR.TXT`
- added a first resident program ABI slice for implicit program launch:
  - prepare program handoff
  - expose resolved target pointer
  - expose command-line pointer and length
  - snapshot run state and exit state
  - return cleanly to the resident shell
  - flat-image mounts now first try raw root-directory lookup plus chained-sector reads into the resident image buffer
  - tree-capable mounts still use `FILE_STAT` plus `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE`
- added resident batch execution:
  - implicit `.BAT` fallback after `.PRG` lookup
  - `%1` / `%2` / `%3` expansion
  - `ECHO`
  - stop-on-error flow
  - default embedded resident `AUTOEXEC.BAT` is disabled so the resident image stays within memory
- added transcript-backed VICE self-test images:
  - focused command-feed images for read, copy, rename, delete, directory, batch, stop-on-error, and implicit launch
  - checked-in expected final-screen transcripts under `tests/selftest`
  - generated `build/udos-selftest-*.d64` and `build/udos-selftest-*.actual.txt` artifacts through `make vice-selftest`
- added release-style boot packaging for VICE:
  - `build/udos-release.d64`
  - `build/udos-release-fs`
  - release boot now reaches `A:D64/>` without a resident `AUTOEXEC.BAT`
  - the D64 keeps ACTC, passes 0 through H, ALINK, resident `COPY`, and compact
    delete/directory/tree commands. The redundant `ACTCOPY.PRG` wrapper,
    project creation/mutation commands, and larger development tools remain
    workspace-only. The full-capacity D64 has zero blocks free; the exported
    Action workspace retains every tool and is the complete development set
  - when the sibling Action exporter is present, the staged release workspace
    also includes `build/udos-release-fs/IMAGES/ACTION.DNP`
  - `make vice-action-workspace` now builds an autoexec-backed Action test
    image that mounts the exported Action workspace, lists its root entries,
    and reads `README.TXT`
  - `make vice-action-actdir` now uses an autoexec-backed Action test image on
    top of the release workspace, launches `ACTDIR.PRG`, enumerates the current mounted
    directory through the preserved external-tool directory ABI, and returns to
    the UDOS prompt
  - `make vice-action-tree-overlay` now uses the release image with a nested
    Action workspace, loads the validated native `TREE.OVL` module, and proves
    recursive traversal reaches `SRC/NEST/DEEP/FINAL.ACT`
  - `make vice-action-actadd` now uses the release image with deterministic
    typed input on top of the release workspace, seeds a project root marked
    by `ACTION.PROJ`, runs `ACTADD.PRG`, writes `SRC/HELPER.ACT` through the
    preserved external-tool file-save ABI, and proves the created source can
    be read back through the shell
  - `make vice-action-actadd-persist` now uses the release image with
    deterministic typed input on top of the release workspace, seeds a
    project root marked by `ACTION.PROJ`, reruns `ACTADD.PRG HELPER` to prove
    duplicate module creation is refused with `EXISTS`, and proves the
    created `src/helper.act` persists on the host fs tree after VICE exits
  - `make vice-action-act2save` now uses the release image with deterministic
    typed input on top of the release workspace, seeds a project root marked
    by `ACTION.PROJ`, launches `ACTSAVE HELPER`, rewrites
    `SRC/HELPER.ACT` through the preserved external-tool file-save ABI, and
    proves the updated source persists on the host fs tree after VICE exits
  - `make vice-action-actc` now uses the release image with deterministic
    typed input on top of the release workspace, seeds a project root marked
    by `ACTION.PROJ`, launches `ACTC.PRG MAIN`, and proves the first
    UDOS-native compiler front-end slice can emit a deterministic
    `OBJ/MAIN.OBJ` object stub on the host fs tree, including extracted
    top-level `PROC` export offset/size triplets, compiler-emitted `body_ops`,
    folded narrow decimal `PrintI` / `PrintIE` `+` / `-` / `*` / `/`
    expressions with inline spaces, simple precedence, parenthesized
    grouping, and simple `=` / `<` / `>` / `<=` / `>=` / `<>`
    comparisons,
    current source-inferred runtime-import metadata, and explicit
    `payload_bytes`;
    the current focused proof verifies the host-side object and
    `OBJ/UDOSDIR.TXT` catalog, then shell-reads `TYPE OBJ/MAIN.OBJ` to prove
    the object is visible through UDOS
  - `make vice-action-alink` now uses the release image with deterministic
    typed input on top of a copied Action workspace, seeds a project root
    marked by `ACTION.PROJ` plus deterministic `OBJ/*.OBJ` fixtures, launches
    `ALINK.PRG MAIN`, and proves the first UDOS-native linker slice can emit a
    deterministic `BIN/MAIN.PRG` final-image artifact on the host fs tree.
    `ALINK` now uses compiler-emitted export sizes plus `body_ops` for direct
    program emission instead of inferring them only from the payload shape.
    The current focused proof also resolves a wider unresolved external closure
    with sibling externals from `main`, a shared child object, and a deeper
    leaf, while carrying child-object integer and string literal pools into the
    linked program image. Project objects are now emitted and documented only as
    `OBJ/*.OBJ`.
  - `make vice-action-alink-prg-matrix` now enumerates 1334 direct-PRG
    object/link shapes from the probe table and validates ALINK output for each
    shape. The matrix includes object-code graph closure, rejection cases,
    link-selected runtime helper families, and seeded input-helper closure
    cases such as joystick state plus joystick button 1 and 2 state feeding
    graphics, SID volume, SID frequency, SID pulse, SID cutoff, SID wave,
    SID attack/decay, SID sustain/release, and sprite helpers, joystick state
    plus joystick button 1 and 2 state feeding source-emitted stored-result and
    nested graphics, sprite color, SID volume, SID frequency, SID pulse,
    SID cutoff, SID wave, SID attack/decay, and SID sustain/release helpers,
    joystick and mouse presence state feeding source-emitted stored-result and
    nested graphics, SID volume, SID frequency, SID pulse, SID cutoff,
    SID wave, SID attack/decay, SID sustain/release, and sprite color helpers,
    mouse button state
    plus mouse button 1 and 2 state feeding source-emitted and nested graphics,
    source-emitted and nested sprite color, source-emitted and nested SID
    frequency, SID pulse, SID cutoff, SID wave, SID attack/decay, and
    SID sustain/release helpers, source-emitted SID volume helpers, direct
    SID volume, SID frequency, SID pulse, SID cutoff, SID wave,
    SID attack/decay, and SID sustain/release helpers, mouse button state feeding sprite color helpers,
    mouse button 1 and 2 state feeding direct sprite helpers, and mouse button 1
    and 2 state feeding direct graphics helpers
    without unrelated input modules.
    The added integer product cases compile dynamic `*` and `/` with normal
    precedence. ACTC lowers them to native OBJ1 machine records with generic
    local-data and helper relocations; ALINK links those records without a
    dedicated integer compiler and selects `RT_I_MUL.OBJ`, `RT_I_DIV.OBJ`, and
    `RT_PRINT_I.OBJ` only when referenced. Live VICE probes prove assignment
    store/readback and divide-by-zero behavior, while unsupported legacy bodies
    still reject without emitting a PRG.
    Plain word assignments and load/store copies now use the same compiler-owned
    native object path; ALINK no longer carries templates for `p0S0r` or
    `p0S0L0S1r`, and those compact forms are rejection-only fixtures.
    Dynamic word add/subtract updates inside WHILE control now use
    `ACTC_OVL9.BIN` machine records with ordinary loop, nested branch, EXIT,
    data, and pointer relocations. The live proof exits with both state words
    equal to three and links no unused integer helper object.
    `PrintI` and `PrintIE` inside the same native WHILE path now emit ordinary
    `rt_print_i` call relocations. Live coverage prints `1` and `2`, finishes
    with the loop variable equal to four, links print and multiply, and prunes
    the available divide module.
    Core `ASMBLOCK [ ... ]` source now assembles official NMOS 6502 code in
    pass 4 and emits it through pass 9 as ordinary OBJ machine bytes and named
    relocations. A direct launch case executes block-local JMP labels and
    references current globals, PROC parameters, and locals without adding an
    assembler path to ALINK.
    Typed word functions may combine ASMBLOCK with one-word runtime calls through
    `ACTC_OVLH.BIN`. The live direct PRG returns 42, stores trace value 41, and
    writes SID volume 8 while ALINK selects only the referenced SID closure.
    ASMBLOCK-visible REAL globals and locals now retain four-byte exports and
    data allocation. A helper-free live direct PRG writes and reads offsets zero
    and three and observes `$033C-$033F` as `$11,$44,$22,$55`.
    Local no-argument `REAL FUNC` direct returns now derive source, destination,
    each two- or four-byte module-global export, aggregate data size, and pointer
    placement from declarations instead of fixed first/second REAL slots. Live
    direct PRGs return 42.0 from the second slot into the third for both all-REAL
    and leading-CARD layouts while ALINK selects only `RT_I_TO_F.OBJ`. A
    one-parameter extension binds either a direct literal or an immediately
    initialized named module word scalar to a typed parameter, converts it into
    named REAL storage, returns that pointer, and copies 42.0 into the caller
    destination through the same generic OBJ/ALINK path. The named-storage case
    emits ordinary relocations for all argument stores and loads.
    The bounded two-REAL-parameter pass-A form now captures return storage
    independently from caller argument storage. A reordered shared fixture
    returns its second parameter as 2.0 and verifies all five caller/callee REAL
    cells through the unchanged generic OBJ/ALINK path. Pass A is 7,418 bytes
    with 774 bytes free under its 768-byte reserve.
    Pass K extends the two-REAL-parameter ABI with one bounded finite
    comparison/select body. Its root closure includes integer conversion and
    comparison; its function export remains comparison-only. The rebuilt
    release and live VICE probe verify 2.0/1.0 caller values, matching callee
    copies, result 1.0, transitive `RT_F_SPECIAL.OBJ` selection, and pruning of
    unrelated REAL helpers. A second shared fixture permutes module declarations
    and parameter names; pass K captures every caller, bind, comparison, and
    return storage role, and live VICE verifies all five REAL cells. General
    REAL function control and MATH1 remain compiler work.
    Pass K also captures every named-storage role in its bounded four-REAL
    `FClamp` assignment/print root. A direct source-backed PRG permutes the
    initializer, argument, destination, and print slots, produces 5.0 in VICE,
    and preserves ordinary ALINK-selected clamp closure.
    Pass K is 4,594 bytes with 3,598 bytes free in its 8 KiB window.
    Empty-return, single-call, and fanout root programs likewise use native
    machine objects; ALINK no longer carries templates for `r`, `c0r`, or
    `c0c1r`, and those root-body forms are rejection-only fixtures.
    Simple equality `IF/ELSE` now uses ACTC-emitted `__if0` and `__if1` local
    branch targets. ALINK no longer carries that compact-body template, and
    live probes cover both the true and false paths through the shared join.
    Plain, ELSE, and nested REAL comparisons now use relocatable machine OBJ
    from `ACTC_OVLB.BIN`. ALINK's fixed-address REAL IF strategy is gone; all
    36 variants pass exact compile/link checks and representative layouts run
    successfully under VICE.
    REAL `DO ... UNTIL` now uses the same compiler pass for all six comparisons
    and eight REAL add/sub update loops. ALINK's matching fixed-address strategy
    and compact signatures are gone; all 14 exact compile/link and live VICE
    cases pass. `ACTC_OVLB.BIN` is 5,655 bytes with 2,537 bytes free,
    Pass H adds mixed ASMBLOCK/runtime-function ownership, and the release D64
    retains all compiler passes at zero free blocks while omitting only the
    redundant `ACTCOPY.PRG` wrapper from the flat-image subset.
    REAL `WHILE`, runtime conditions, runtime call sequences, and nested
    readbacks now use compiler passes C through F. One-word byte-in-A and
    word-in-X/Y runtime calls inside integer control use pass G; mixed ASMBLOCK/
    runtime units use pass H. Source-backed
    `SidVol(I+10)` and `SidCutoff(I+300)` WHILE cases prove ABI-specific setup,
    loop-variable value one, transitive SID selection, and unrelated-helper
    pruning. The final 102 seeded runtime
    fixtures are machine objects, and ALINK's runtime recognizers, compact-body
    compiler, fixed-address templates, and synthesis queues are gone.
    Production `ALINK.PRG` is 13,806 bytes; all accepted bodies are OBJ1 machine
    records, and all helper code is selected through reachable `RT_*.OBJ`
    imports and relocations.
  - `make vice-action-actc-alink-launch-printmath` is green again as the
    named higher-level direct-launch proof for the imported `printmath` shape.
    It uses the release image with deterministic typed input on top of a copied
    Action workspace, launches `ACTC.PRG MAIN`, then `ALINK.PRG MAIN`, then
    direct `BIN/MAIN.PRG`, and proves the live screen reaches `hello`, `tool7`,
    and `5459` before returning to the UDOS prompt
  - `make vice-action-actc-alink-launch` is now the helper-free higher-level
    default, using the release image with deterministic typed input on top of
    a copied Action workspace, launching `ACTC.PRG MAIN`, then `ALINK.PRG MAIN`,
    then direct `BIN/MAIN.PRG` under VICE with no separate runner dependency
  - `make vice-action-actc-alink-launch-if-else-chain` is the named helper-free
    higher-level proof for the base local-call chain shape
  - `make vice-action-actc-alink-launch-nested-else-chain` is the named
    helper-free higher-level proof for the nested false-path local-call chain
    shape
  - `make vice-action-actchk` now uses the release image with deterministic
    typed input on top of the release workspace, seeds a healthy project root
    marked by `ACTION.PROJ`, launches `ACTCHK.PRG`, validates expected
    project directories plus tracked source presence, and proves the focused
    healthy-project integrity path returns `ACTCHK OK`
  - `make vice-action-actsrc` now uses an autoexec-backed Action test image on
    top of the release workspace, seeds a project root marked by
    `ACTION.PROJ`, launches `ACTSRC.PRG`, lists the tracked source entries
    from that project manifest, and returns to the UDOS prompt
  - `make vice-action-actfile` now uses an autoexec-backed Action test image on
    top of the release workspace, seeds a project root marked by
    `ACTION.PROJ`, launches `ACTFILE.PRG MAIN`, loads `SRC/MAIN.ACT` through
    the preserved external-tool file-load ABI, prints the source text, and
    returns to the UDOS prompt
  - `make vice-action-actwork` now uses an autoexec-backed Action test image on
    top of the release workspace, seeds a project root marked by
    `ACTION.PROJ`, launches `ACTWORK.PRG`, reports current
    project/workspace state through the preserved directory and file-load ABI,
    and returns to the UDOS prompt
  - the `ACTMON` proof path now uses dedicated typed-input probes on top of
    the release workspace; current direct validations cover `WORK`, `ADD
    EXTRA`, `REN HELPER RENAMED`, and `DEL HELPER` on seeded Action project
    states, and the nested source-delete/source-rename paths now mutate
    host-backed `SRC/<NAME>.ACT` files while updating `ACTION.PROJ`; the
    front-end command surface now also includes tracked-module
    `COPY <OLD> <NEW>` through the preserved file-copy ABI
  - shared `ACTION.PROJ` helper includes now back `ACTADD`, `ACT2SAVE`,
    `ACTFILE`, `ACTSRC`, `ACTWORK`, and `ACTMON`, replacing the previous
    per-tool manifest/path routine copies
  - the current `ACTMON` probe script now targets the combined `WORK` /
    `ADD EXTRA` / `REN HELPER RENAMED` / `DEL HELPER` proof and is intended
    to confirm `NO SUCH FILE` for `TYPE SRC/HELPER.ACT` after the rename and
    delete paths return; the earlier `WORK`/`CHECK` launch failure was a real
    launch-window overlap caused by `ACTMON.PRG` growing past the current
    `$0900-$180F` safe region and clobbering resident code at `$1810+`, and
    the monitor was reduced back under that limit so focused headless
    `ACTMON WORK` and `ACTMON CHECK` runs are now green again
  - `make vice-action-actmon-check` now keeps the recovered workspace-summary
    and integrity proof in the Make surface through the focused generic
    mounted-tree runner, and `make vice-action-actmon` is green again as the
    broader mutation proof after moving the composite runner onto the generic
    mounted-tree probe path with a clean host-tree reseed before each phase
    attempt
  - `make vice-action-actinfo` now uses an autoexec-backed Action test image on
    top of the release workspace, launches `ACTINFO.PRG` from the mounted Action workspace
    through the preserved launch-safe external-tool ABI, and returns to the
    UDOS prompt
  - `make vice-action-actflow` now uses the release image with deterministic
    typed input, launches `ACTFLOW.BAT`, exercises preserved file
    save/copy/move/delete/load behavior in one composite Action-side workspace
    flow, and proves the deleted target is gone through shell-side `TYPE`
  - `make vice-action-actnew-prg` now uses the release image with deterministic
    typed input, launches `ACTNEW.PRG`, creates a project skeleton through the
    preserved directory/file ABI, writes `ACTION.PROJ`, and proves the created
    tree is reachable by changing into `B:DNP/DEMO/SRC>` after the tool returns
  - `make vice-action-actnew-prg-persist` now builds a focused resident
    autoexec image, runs `ACTNEW.PRG`, and proves the created project persists
    on the host fs tree after VICE exits
  - host-backed VICE persistence for that path now preserves the expected file
    names on disk as `readme.txt` and `src/main.act`
  - `make vice-action-actcopy` now uses the release image with deterministic
    typed input, launches `ACTCOPY.PRG`, copies `OUT.TXT` to `COPY.TXT`
    through the preserved external-tool file-copy ABI, and proves the shell
    reads back `ACTION WRITE OK` from `COPY.TXT`
  - `make vice-action-actdel` now uses the release image with deterministic
    typed input, launches `ACTDEL.PRG`, deletes `OUT.TXT` through the
    preserved external-tool file-delete ABI, and proves the shell reports
    `NO SUCH FILE` for the deleted file
  - `make vice-action-actmove` now uses the resident image with a retrying
    mounted-tree probe and proves the renamed file persists on the host fs
    tree with `ACTION WRITE OK`
  - `make vice-action-actmove-persist` now uses the resident image with a
    retrying mounted-tree probe and proves the same rename persists on the
    host fs tree after VICE exits
  - `make vice-action-actmkdir` now uses the release image with deterministic
    typed input, launches `ACTMKDIR.PRG`, creates `OBJ` through the preserved
    external-tool directory-mutation ABI, and proves the shell can enter
    `B:DNP/OBJ>`
  - `make vice-action-actmkdir-persist` now uses the resident image with a
    retrying mounted-tree probe and proves the new `OBJ` directory persists on
    the host fs tree after VICE exits
  - `make vice-action-actrmdir` now uses the release image with deterministic
    typed input, launches `ACTRMDIR.PRG`, removes `OBJ` through the preserved
    external-tool directory-mutation ABI, and proves the shell reports
    `NO SUCH DIR` for `CD OBJ`
  - `make vice-action-actrmdir-persist` now uses the resident image with a
    retrying mounted-tree probe, removes a host-preseeded `OBJ` directory
    through `ACTRMDIR.PRG`, and proves the directory is absent on the host fs
    tree after VICE exits
  - `make vice-action-actwrite` now uses the release image with deterministic
    typed input, launches `ACTWRITE.PRG`, writes `OUT.TXT` through the
    preserved external-tool file-save ABI, reads it back through the shell,
    and returns to the UDOS prompt
  - obsolete runner/tool probes were removed from the active release path; the
    current Action validation surface is direct tool launch and direct linked
    `.PRG` execution
- the tool-side VICE tree file-mutation ABI now resolves nested tree paths for
  host-backed Action project files:
  - direct `ACTDEL SRC/...` validation now removes host-backed source files
  - direct `ACTCOPY SRC/... SRC/...` validation now creates nested copies on the host tree
  - direct `ACTMOVE SRC/... SRC/...` validation now renames nested source files on the host tree
  - direct `ACTMON.PRG DEL <NAME>` validation now removes `SRC/<NAME>.ACT` and updates `ACTION.PROJ`
- added a first REU-backed resident shrink path:
  - VICE tree content payloads now spill into REU
  - the resident image now keeps one shared `PROGRAM_IMAGE_MAX` slot cache in RAM instead of two full in-RAM payload banks
  - VICE validation now enables a `16 MiB` REU by default
- updated resident `MEM` to report decimal usage:
  - launch-capable RAM used bytes when REU is present
  - launch-capable RAM free bytes using the current `FFFF-used` policy
  - REU used bytes including the current VICE tree reservation plus the
    spill reservation for the resident image and HIRAM workspace
  - REU free bytes from the current `16 MiB-used` budget
- replaced the placeholder mount form with a real image-path `MOUNT` syntax:
  - `MOUNT A: /path/to/system.d81`
  - `MOUNT B: /path/to/work.dnp`
- added a hardware-backed `MOUNT` path
  - current assumptions:
    - `A:` -> IEC `8`
    - `B:` -> IEC `9`
  - hardware mode attempts Ultimate DOS `MOUNT_DISK`
  - flat-image hardware mounts now also try `OPEN_FILE` / `FILE_SEEK` / `READ_DATA` to import the filesystem-header label for `D64` / `D71` / `D81`
  - when that import is unavailable or fails, the resident label falls back to the mounted image basename

## Current Verified Facts

### Resident shell milestone

- linked resident entrypoint: `$1810`
- command keywords now require a separator before arguments
- direct drive tokens now work on the resident path:
  - `A:` -> switch to logical drive `A:` without resetting `A:`'s current directory
  - `B:` -> switch to logical drive `B:` without resetting `B:`'s current directory
  - `C:` / `D:` -> explicit `DRIVE NOT PRESENT`
- bare non-keyword input now implies program launch:
  - `DEL BOOT3.PRG` -> delete `BOOT3.PRG`
  - `DELBOOT3` -> implicit launch attempt of `DELBOOT3.PRG`, then `PROGRAM NOT FOUND`
  - `BOOT3 DIR` -> implicit launch of `BOOT3.PRG` with command line `DIR`
- resident `COPY` now also supports limited wildcard expansion:
  - `*`
  - `*.*`
  - `*.EXT`
  - `NAME.*`
  - wildcard `COPY` preserves each matched source filename into the resolved destination directory
- resident `DEL` now also supports limited wildcard expansion:
  - `*`
  - `*.*`
  - `*.EXT`
  - `NAME.*`
- backend-path cache seam is now live behind the filesystem ABI:
  - mock mode synthesizes `/`, `/BIN`, `/SRC`, `/WORK`
  - hardware mode now synchronizes through Ultimate DOS `CHANGE_DIR` and queries `GET_PATH`, but remains unverified
- hardware-backed directory enumeration is now wired behind `svc_fs_enum_*`:
  - flat-image root mounts now first issue `OPEN_FILE` / repeated `FILE_SEEK` / repeated `READ_DATA`
  - tree-capable mounts still issue `OPEN_DIR` / `READ_DIR` into a small resident cache
  - current cache budget is `6` entries with names capped at `20` bytes plus terminator
  - VICE catalog input is line-streamed without a 255-byte ceiling; when the
    bounded snapshot is full, later directories take priority over cached files
  - VICE now also validates a real tree read path for `DNP` mounts through the manifest-backed backend
- hardware-backed file read is now wired behind `TYPE`:
  - flat-image hardware mode first issues raw root-directory lookup plus image `OPEN_FILE` / repeated `FILE_SEEK` / repeated `READ_DATA`
  - tree-capable hardware mode still issues `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE`
  - the current text read is bounded to the resident response buffer
  - VICE now also validates real tree reads on `DNP` mounts through the VICE backend
- hardware-backed delete is now wired behind `DEL`:
  - flat-image hardware mode now first issues raw root-directory lookup, chained sector traversal, and BAM release through image `OPEN_FILE` / repeated `FILE_SEEK` / repeated `READ_DATA` / repeated `WRITE_DATA`
  - tree-capable hardware mode still issues `DELETE_FILE`
  - VICE now also validates the tree-backed delete path through the fsdevice-backed overlay model
- hardware-backed rename is now wired behind `REN`:
  - flat-image hardware mode now first issues raw root-directory lookup plus direct directory-entry rewrite through image `OPEN_FILE` / repeated `FILE_SEEK` / repeated `READ_DATA` / repeated `WRITE_DATA`
  - tree-capable hardware mode still issues `RENAME_FILE`
  - VICE now also validates the tree-backed rename path through the fsdevice-backed overlay model
- hardware-backed copy is now wired behind `COPY`:
  - tree-only same-drive hardware mode issues `COPY_FILE`
  - tree-only cross-drive hardware mode issues source `OPEN_FILE` / `READ_DATA` and destination `OPEN_FILE` / `WRITE_DATA`
  - flat-image hardware mode now first attempts raw root-directory lookup, chained sector reads, BAM allocation, and direct directory-entry creation through image `OPEN_FILE` / repeated `FILE_SEEK` / repeated `READ_DATA` / repeated `WRITE_DATA`
  - VICE now also validates the tree-backed copy path through the fsdevice-backed overlay model
- hardware-backed fixed Tool ABI operations are now wired behind Action tools,
  native overlays, and resident directory commands:
  - `svc_file_load_sc0` resolves normal and launch-directory (`!`) paths, uses
    `FILE_STAT` for probe/size, streams the bounded prefix through repeated
    `READ_DATA`, and distinguishes OK, too-large, missing, and failed results
  - `svc_file_save_sc0` resolves tree destinations from the program snapshot,
    opens with write/create/overwrite flags, streams explicit 16-bit lengths in
    repeated `WRITE_DATA` chunks, retains the bounded zero-length text fallback
    used by `ACTWRITE`, and closes before restoring resolver state
  - `svc_file_write_begin_sc0`, `svc_file_write_chunk_sc0`, and
    `svc_file_write_close_sc0` retain one hardware stream's drive/open state in
    fixed HIRAM, write exact 16-bit chunks through repeated `WRITE_DATA`, and
    report open/write/close failures without backend fallback
  - `svc_file_stage_reu_sc0` validates the 32-bit `FILE_STAT` size against its
    24-bit destination, streams repeated `READ_DATA` chunks into REU, verifies
    the exact final count, and distinguishes missing files from failures
  - nested path resolution and enumeration use UCI `OPEN_DIR` / `READ_DIR`
  - `MD` and `svc_dir_make_sc0` probe with `FILE_STAT` and issue `CREATE_DIR`
  - `RD` and `svc_dir_remove_sc0` reject non-empty targets and issue
    `DELETE_FILE` for empty directories
  - `svc_file_copy_sc0` uses same-drive `COPY_FILE` or cross-drive
    `OPEN_FILE` / `READ_DATA` / `WRITE_DATA` / `CLOSE_FILE`
  - `svc_file_delete_sc0` probes with `FILE_STAT` and issues `DELETE_FILE`
  - `svc_file_rename_sc0` probes source and destination with `FILE_STAT`, uses
    same-directory `RENAME_FILE`, and falls back to copy/delete for moves across
    directories or drives
  - all of these hardware paths remain unvalidated on a real Ultimate target
- backend-generic Tool ABI paths select hardware from the preserved
  `TRANSPORT_SNAPSHOT` rather than calling low resident `uci_probe` code:
  - this keeps service calls valid when a large launched tool overwrites the
    resident start at `$1810`
  - focused `ACTMON.PRG CHECK` and multi-phase ACTMON mutation gates cover a
    4,095-byte tool spanning `$0900-$18FE`
- flat-image header-label import is now wired behind `VOL` for hardware `D64` / `D71` / `D81` mounts:
  - hardware mode issues `OPEN_FILE` / `FILE_SEEK` / `READ_DATA` / `CLOSE_FILE` against the mounted image path
  - current flat-image label offsets are `$00016590` for `D64` / `D71` and `$00061804` for `D81`
  - VICE still validates only the basename fallback path because no Ultimate UCI transport exists there
- implicit program launch now loads a real resident program image:
  - mock mode copies the resolved file content into a bounded resident image buffer
  - flat-image hardware mode now first attempts raw root-directory lookup plus chained-sector reads into the image buffer
  - tree-capable hardware mode still first attempts `FILE_STAT`
  - tree-capable hardware mode then attempts `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE`
  - tree-capable hardware mode can now distinguish `PROGRAM NOT FOUND` from a generic load failure before opening the file
  - VICE now validates both the loaded image length snapshots and a real tree-backed `HELLO DIR` launch path
- batch execution is now validated in VICE:
  - `ARGS ONE TWO THREE` expands to `ONE/TWO/THREE`
  - `STOP` halts after `TYPE NOFILE.TXT` and does not run the next line
  - default embedded resident `AUTOEXEC.BAT` is now retired to keep the resident image within memory
- current VICE-validated transcript:
  - `A:D64/> MOUNT B: /IMAGES/WORK.DNP`
  - `A:D64/> VOL`
  - `A:SYSTEM D64 B:WORK DNP`
  - `A:D64/> B:`
  - `B:DNP/`
  - `B:DNP/> CD SRC`
  - `B:DNP/SRC`
  - `B:DNP/SRC> COPY BOOT.ASM WORK/BOOT2.PRG`
  - `B:DNP/SRC> COPY BOOT.ASM WORK/BOOT4.ASM`
  - `COPIED`
  - `B:DNP/SRC> CD WORK`
  - `B:DNP/WORK`
  - `B:DNP/WORK> REN BOOT2.PRG BOOT3.PRG`
  - `RENAMED`
  - `B:DNP/WORK> DELBOOT3`
  - `PROGRAM NOT FOUND`
  - `B:DNP/WORK> C:`
  - `DRIVE NOT PRESENT`
  - `B:DNP/WORK> D:`
  - `DRIVE NOT PRESENT`
  - `B:DNP/WORK> DEL *.PRG`
  - `DELETED`
  - `B:DNP/WORK> DIR`
  - `B:DNP/WORK BOOT4.ASM`
- separate VICE-validated launch smoke:
  - `B:DNP/WORK> BOOT3 DIR`
  - `RUN BOOT3.PRG`
  - `ARGS DIR`
- separate VICE-validated real tree read smoke:
  - `A:D64/> MOUNT B: /IMAGES/WORK.DNP`
  - `A:D64/> VOL`
  - `A:SYSTEM D64 B:WORK DNP`
  - `A:D64/> B:`
  - `B:DNP/> DIR`
  - `B:DNP/ BIN/ SRC/ WORK/`
  - `B:DNP/> CD SRC`
  - `B:DNP/SRC> DIR`
  - `B:DNP/SRC BOOT.ASM HELLO.PRG`
  - `B:DNP/SRC> TYPE BOOT.ASM`
  - `; BOOT.ASM VICE BACKEND SOURCE`
  - `B:DNP/SRC> HELLO DIR`
  - `RUN HELLO.PRG`
  - `ARGS DIR`
- separate VICE-validated real tree write smoke:
  - `B:DNP/SRC> COPY BOOT.ASM WORK/BOOT2.ASM`
  - `B:DNP/WORK> REN BOOT2.ASM BOOT3.PRG`
  - `B:DNP/WORK> DEL BOOT3.PRG`
  - `B:DNP/WORK> TYPE BOOT3.PRG`
  - `NO SUCH FILE`
- separate VICE-validated real tree host-rename smoke:
  - `B:DNP/SRC> REN HELLO.PRG HELLO2.PRG`
  - `B:DNP/SRC> TYPE HELLO2.PRG`
  - `HELLO PROGRAM IMAGE`
  - `B:DNP/SRC> TYPE HELLO.PRG`
  - `NO SUCH FILE`
- separate VICE-validated real tree wildcard smoke:
  - `B:DNP/SRC> COPY *.* WORK`
  - `B:DNP/WORK BOOT.ASM HELLO.PRG`
  - `B:DNP/SRC> DEL *.PRG`
  - `B:DNP/SRC BOOT.ASM`
- separate VICE-validated real tree directory smoke:
  - `B:DNP/> MD NEW`
  - `CREATED`
  - `B:DNP/> CD NEW`
  - `B:DNP/NEW`
  - `B:DNP/> RD NEW`
  - `REMOVED`
- separate VICE-validated real tree remove-directory guard smoke:
  - `B:DNP/> RD SRC`
  - `DIR NOT EMPTY`
- separate VICE-validated wildcard copy smoke:
  - `B:DNP/SRC> COPY *.* WORK`
  - `B:DNP/WORK BOOT.ASM HELLO.PRG`
  - the same limited wildcard forms are now also validated on the real VICE tree backend
- separate VICE-validated reserved-drive smoke:
  - `A:D64/> C:`
  - `DRIVE NOT PRESENT`
  - `A:D64/> D:`
  - `DRIVE NOT PRESENT`
- bind snapshots:
  - `$CFE4 = $01` -> cached backend-path length for `A:` (`/`)
  - `$CFE5 = $05` -> cached backend-path length for `B:` (`/WORK`) after the smoke sequence
  - `$CFE8/$CFE9 = $01/$01` -> `A:` = `D64/flat`
  - `$CFEA/$CFEB = $04/$02` -> `B:` = `DNP/tree`
- current-drive snapshots:
  - `$CFEC = $01` -> current drive `B:`
  - `$CFEE = $02` -> current-drive flags `tree`
  - `$CFF0 = $01` -> transport mode `mock`
  - `$CFF2 = $04` -> current-drive mount kind `DNP`
  - `$CFF4 = $01` -> ABI version
- program ABI snapshots after implicit launch:
  - `$CFF6 = $02` -> program exited
  - `$CFF7 = $00` -> exit status `0`
  - `$CFF8 = $01` -> program drive `B:`
  - `$CFF9 = $03` -> program directory `WORK`
  - `$CFFA = $16` -> loaded image length low byte (`22`)
  - `$CFFB = $00` -> loaded image length high byte
- resident `MEM` now reports:
  - `RAM USED 0 FREE 65535 REU USED 47872 FREE 16729344`
- resident core code footprint: `$9235` bytes, ending at `$AA44`
- resident image end: `$AA45`, leaving `$15BB` bytes before `$C000`
- fixed tool-callable preservation begins at `$9800`; tool-callable resident
  code ends at `$9FCE`, leaving `$0032` bytes before the
  `$A000-$BFFF` Action compiler overlay window; post-return catalog rewrite code
  occupies the overlap-prone tail and is restored from REU before use
- resident-private REU state uses bank `$FF`, the temporary low-resident/tool
  swap uses `$FE`, and bounded fixed-tool file loads use `$FD`; the unused
  240-byte streamed-content mirror has been removed
- resident load window in `udos_c64.cfg`: `$A7F0`
- processor port `$36` exposes resident RAM under BASIC ROM while retaining
  KERNAL and I/O; high-RAM BSS still ends at `$CEFB`, four bytes below `$CF00`

## What Works

- standalone UDOS build and VICE validation
- native resident shell/runtime
- resident service ABI
- native UCI detection seam
- synchronous native UCI transfer primitives
- drive bind/query abstraction
- backend-path metadata query seam with hardware `CHANGE_DIR` / `GET_PATH` attempt plus mock fallback
- directory enumeration seam with flat-image raw root parsing plus tree-capable `OPEN_DIR` / `READ_DIR`, all with mock fallback
- file-read seam for `TYPE` with hardware `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE` attempt plus mock fallback
- flat-image raw file-read seam for `TYPE` with root-directory lookup plus chained sector reads
- file-delete seam for `DEL` with hardware `DELETE_FILE` attempt and explicit hardware-error reporting
- flat-image raw delete seam for `DEL` with root-directory lookup, chained sector traversal, and BAM updates
- file-rename seam for `REN` with hardware `RENAME_FILE` attempt and explicit hardware-error reporting
- flat-image raw rename seam for `REN` with root-directory lookup and direct directory-entry rewrite
- file-copy seam for `COPY` with same-drive `COPY_FILE`, cross-drive read/write streaming, and explicit hardware-error reporting
- flat-image raw file-copy seam for `COPY` with chained sector reads, BAM allocation, and direct directory-entry creation
- real `MOUNT` syntax with image-path parsing and flat-image header-label import plus basename fallback
- flat-image rejection for directory-tree semantics
- first one-level resident `TREE` scaffold with flat-image rejection, root child
  expansion, and bounded selected-directory listing
- prompt rendering from live drive/kind/path state
- direct drive-token switching for `A:` and `B:`
- resident file-oriented mock workflow:
  - `DIR`
  - `TYPE`
  - `COPY`
  - `REN`
  - `DEL`
- resident program-handoff and image-load workflow:
  - implicit program launch from a bare non-keyword line
  - `.PRG` suffix added when the target has no extension
  - flat-image raw program-image load path for `D64` / `D71` / `D81`
  - command-line separation with normal spaces
  - bounded resident image load before handoff
  - return to shell after program exit

## What Is Unverified

- no real C64 Ultimate hardware execution
- no hardware-validated UCI command/data path
- no hardware-validated mounted-image bind yet
- no hardware-validated flat-image header-label import yet
- no hardware-validated flat-image raw root-directory parsing yet
- no hardware-validated flat-image raw file reads yet
- no hardware-validated flat-image raw program-image loads yet
- no hardware-validated flat-image raw delete path yet
- no hardware-validated flat-image raw rename path yet
- no hardware-validated image-backed file delete yet
- no hardware-validated image-backed file rename yet
- no hardware-validated image-backed file copy yet
- no hardware-validated flat-image raw copy path yet
- no hardware-validated program-image loading yet behind implicit program launch
- no real-hardware validation of the UCI tree-file direct-PRG/command-overlay
  REU staging backend yet
- recursive `TREE.OVL` has no real-hardware validation yet
- recursive `XCOPY.OVL` has no real-hardware validation yet
- recursive `DELTREE.OVL` has no real-hardware validation yet

## Next Concrete Step

- keep the release boot package and root `make test` gate stable while Action
  linker/runtime changes are being prepared
- keep the all-source-backed `ACTC.PRG` object-emission matrix green and
  continue widening `ALINK.PRG` direct-PRG object/helper closure around
  remaining edge shapes
- complete bounded native constants/includes and external/fixed address
  expressions around the now-implemented ASMBLOCK/raw A/X/Y/`$A3` register
  ABI, then generalize REAL calls and returns enough to compile dependency-
  sized MATH1 modules
- preserve compiler-owned relocatable OBJ emission for REAL control flow and
  runtime condition/sequence/nested-call overlays; ALINK must remain a generic
  object linker rather than regaining body synthesis
- hardware-validate the UCI overlay stager and recursive Tool ABI operations,
  then fix any target-specific failures found by the runbook
