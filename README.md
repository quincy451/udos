# UDOS

UDOS is a Commodore 64 Ultimate shell/runtime project.

The resident shell now runs as native 6502 code. Linked Action output is a
direct `.PRG`, and no separate launcher is part of that path.

This repo is intentionally separate from the existing `actionc64u/` and `cpm65-u64/`
work so the shell/runtime can move forward without continuing CP/M-65 feature work.

Current milestone:
- Phase 0 complete: pivot notes and project area established.
- Phase 1 complete.
- Phase 2 bootstrap/core slice complete.
- Phase 3 native UCI seam complete at the control/status boundary.
- Phase 4 mounted-image abstraction seam complete with flat-vs-tree policy.
- Phase 5 resident shell milestone in progress with `DIR`, `CD`, `VOL`, `MOUNT`,
  `MEM`, `TYPE`, `COPY`, `REN`, `DEL`, `MD`, `RD`, direct `A:`/`B:` drive
  switching, and implicit program launch validated under VICE.
- Phase 5 now includes real VICE tree read/write validation on the fsdevice-backed
  `DNP` path:
  - `DIR`, `CD`, `TYPE`, and implicit launch
  - exact and limited wildcard `COPY`
  - exact `REN`
  - exact and limited wildcard `DEL`
  - exact `MD`
  - exact `RD` for empty directories plus non-empty rejection
- Phase 5 now also includes a hardware-backed directory-enumeration path in code:
  - flat-image root mounts now first try raw image parsing through `OPEN_FILE` / `FILE_SEEK` / `READ_DATA`
  - tree-capable mounts still synchronize through `CHANGE_DIR`, refresh through `GET_PATH`, and enumerate through `OPEN_DIR` / `READ_DIR`
  - mock fallback retained for VICE and failure cases
- Phase 5 now also includes a hardware-backed `TYPE` read path in code:
  - flat-image mounts now first try raw image file lookup plus chained-sector reads through `OPEN_FILE` / `FILE_SEEK` / `READ_DATA`
  - tree-capable mounts still use resident path synchronization plus `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE`
  - mock fallback retained for VICE and failure cases
- Phase 5 now also includes a hardware-backed `DEL` path in code:
  - flat-image mounts now first try raw root-directory lookup plus BAM release through image `OPEN_FILE` / repeated `FILE_SEEK` / `READ_DATA` / `WRITE_DATA`
  - tree-capable mounts still use resident path synchronization plus `DELETE_FILE`
  - mock deletion is used only when hardware UCI is unavailable
  - hardware-side delete failures return an explicit shell error
- Phase 5 now also includes a hardware-backed `REN` path in code:
  - flat-image mounts now first try raw root-directory lookup plus direct directory-entry rewrite through image `OPEN_FILE` / `FILE_SEEK` / `READ_DATA` / `WRITE_DATA`
  - tree-capable mounts still use resident path synchronization plus `RENAME_FILE`
  - mock rename is used only when hardware UCI is unavailable
  - hardware-side rename failures return an explicit shell error
- Phase 5 now also includes a hardware-backed `COPY` path in code:
  - tree-only same-drive copy through `COPY_FILE`
  - tree-only cross-drive copy through source `OPEN_FILE`/`READ_DATA` and destination `OPEN_FILE`/`WRITE_DATA`
  - flat-image copies now also have a raw image path in code:
    - raw root-directory lookup
    - BAM allocation
    - chained sector streaming
    - direct directory-entry creation through image `OPEN_FILE` / `FILE_SEEK` / `READ_DATA` / `WRITE_DATA`
  - mock copy is used only when hardware UCI is unavailable
  - hardware-side copy failures return an explicit shell error
- Phase 5 now also includes a real mounted-image `MOUNT` path in code:
  - shell syntax: `MOUNT A: /path/to/system.d81` or `MOUNT B: /path/to/work.dnp`
  - image kind is inferred from the extension
  - hardware mode attempts Ultimate DOS `MOUNT_DISK`
  - flat-image hardware mounts now also try Ultimate DOS `OPEN_FILE` / `FILE_SEEK` / `READ_DATA` to import the filesystem header label for `D64` / `D71` / `D81`
  - when that header read is unavailable or fails, the resident label falls back to the mounted image basename
  - mock mode preserves the same semantics under VICE
- Phase 5 now also includes a real resident image-load path behind implicit program launch:
  - mock mode copies the resolved target into a bounded resident image buffer
  - flat-image mounts now first try raw image file lookup plus chained-sector reads
  - tree-capable hardware mode still probes with `FILE_STAT` and then attempts `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE`
  - VICE validates the loaded image length through resident snapshots
- Phase 5 now also includes resident batch support on VICE:
  - implicit `.BAT` fallback after `.PRG`
  - `%1` / `%2` / `%3`
  - `ECHO`
  - stop-on-error flow
  - default embedded resident `AUTOEXEC.BAT` is disabled so the resident image stays within memory
- Phase 5 now also includes transcript-backed VICE self-test images:
  - focused command-feed images for read, copy, rename, delete, directory, batch, stop-on-error, and implicit launch
  - checked-in expected final-screen transcripts
  - generated actual transcripts for direct `diff -u` comparison
- Phase 5 now also includes a release-style boot image:
  - `build/udos-release.d64`
  - boots directly to `A:D64/>` with no resident `AUTOEXEC.BAT`
  - companion VICE workspace tree staged under `build/udos-release-fs`
  - when the sibling `actionc64u` exporter is present, the release workspace
    also includes `IMAGES/ACTION.DNP`
  - `make vice-action-workspace` now builds an autoexec-backed Action test image
    that mounts the exported Action workspace, lists its root entries, and reads
    `README.TXT` from the shell
  - `make vice-action-actdir` now uses an autoexec-backed Action test image on
    top of the release workspace, launches `ACTDIR.PRG SRC`,
    enumerates a selected directory through the path-scoped external-tool
    directory ABI, and returns to the UDOS prompt
  - `make vice-action-tree-overlay` now proves the resident `TREE SRC` command
    resolves and validates `TREE.OVL`, then reaches
    `SRC/NEST/DEEP/FINAL.ACT`
  - `make vice-action-tree-overlay-invalid` corrupts the module container and
    proves UDOS uses the one-level resident fallback without entering it
  - `make vice-action-xcopy-overlay` proves `XCOPY XCSRC XCDST` loads the
    validated `XCOPY.OVL` module and recursively copies eleven files across
    three tree levels
  - `make vice-action-xcopy-overlay-invalid` proves an invalid module reports
    `OVERLAY INVALID` without entry or destination mutation
  - `make vice-action-xcopy-overlay-flat` proves recursive copy reports
    `FLAT IMAGE` on the release `D64`
  - `make vice-action-deltree-overlay` proves validated `DELTREE.OVL` removes
    eleven files and three directories in bounded post-order
  - invalid-module, flat-image, and current-directory safety are covered by
    `vice-action-deltree-overlay-invalid`, `vice-action-deltree-overlay-flat`,
    and `vice-action-deltree-overlay-busy`
  - hardware tree-file launch now uses `FILE_STAT`, `OPEN_FILE`, repeated
    `READ_DATA`, and `CLOSE_FILE` to stream direct PRGs and `UDOV` modules into
    the shared REU launch area; this path is implemented but not hardware-validated
  - hardware recursive Tool ABI paths now use nested UCI directory enumeration,
    `CREATE_DIR`, same-drive `COPY_FILE` or cross-drive read/write streaming,
    and `DELETE_FILE` for files and empty directories; these paths are
    implemented but not hardware-validated
  - fixed external-tool file load now uses `FILE_STAT`, bounded repeated
    `READ_DATA`, and `CLOSE_FILE`, including existence-only probes, `!` paths
    relative to the launched tool, and exact too-large prefix semantics; this
    path is implemented but not hardware-validated
  - `make vice-action-actadd` now uses the release image with deterministic
    typed input on top of the release workspace, seeds a project root marked
    by `ACTION.PROJ`, changes into that project, runs `ACTADD.PRG`, writes
    `SRC/HELPER.ACT` through the preserved external-tool file-save ABI, and
    proves the shell can read the created source back through `TYPE`
  - `make vice-action-actadd-persist` now uses the release image with
    deterministic typed input on top of the release workspace, seeds a project
    root marked by `ACTION.PROJ`, reruns `ACTADD.PRG HELPER` to prove
    duplicate module creation is refused with `EXISTS`, and proves the created
    `src/helper.act` persists on the host fs tree after VICE exits
  - `make vice-action-act2save` now uses the release image with deterministic
    typed input on top of the release workspace, seeds a project root marked
    by `ACTION.PROJ`, launches `ACTSAVE HELPER`, rewrites
    `SRC/HELPER.ACT` through the preserved external-tool file-save ABI, and
    proves the updated source can be read back through the shell
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
    the focused proof verifies the host-side object and `OBJ/UDOSDIR.TXT`
    catalog, then shell-reads `TYPE OBJ/MAIN.OBJ` to prove the object is visible
    through UDOS
  - `make vice-action-alink` now uses the release image with deterministic
    typed input on top of a copied Action workspace, seeds a project root
    marked by `ACTION.PROJ` plus deterministic `OBJ/*.OBJ` fixtures, launches
    `ALINK.PRG MAIN`, and proves the UDOS-native linker emits a direct
    `BIN/MAIN.PRG` final program on the host fs tree. `ALINK` owns the final
    program content and no separate runtime launcher is part of this path.
    Project objects are emitted, documented, and linked as `OBJ/*.OBJ`
    files with `OBJ1` headers.
  - `make vice-action-actc-alink-launch-printmath` is green again as the
    named higher-level direct-launch proof for the imported `printmath` shape.
    It launches `ACTC.PRG MAIN`, then `ALINK.PRG MAIN`, then direct
    `BIN/MAIN.PRG`, and proves the live screen reaches `hello`, `tool7`, and
    `5459` before returning to the UDOS prompt
  - `make vice-action-actc-alink-launch-object-emission-matrix` now covers all
    174 source-backed non-runtime, non-object-code ACTC object-emission launch
    shapes from `tools/run_action_alink_prg_probe.py`
  - `make vice-action-actc-alink-launch` is now the helper-free higher-level
    default. It uses the release image with deterministic typed input on top
    of a copied Action workspace, launches `ACTC.PRG MAIN`, then
    `ALINK.PRG MAIN`, then direct `BIN/MAIN.PRG` under VICE with no separate
    runtime launcher
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
    `ACTION.PROJ`, launches `ACTWORK.PRG`, reports current project/workspace
    state through the preserved directory and file-load ABI, and returns to
    the UDOS prompt
  - the `ACTMON` proof path is now centered on dedicated typed-input probes on
    top of the release workspace; current direct validations cover `WORK`,
    `CHECK`, `ADD EXTRA`, `REN HELPER RENAMED`, and `DEL HELPER` on seeded
    Action project states, and the nested-source delete/rename paths now
    remove or rename host-backed `SRC/<NAME>.ACT` files while updating
    `ACTION.PROJ`;
    the front-end command surface now also includes `COPY <OLD> <NEW>` for
    tracked-module duplication through the preserved file-copy ABI
  - the current `ACTMON` probe script targets that combined `WORK` /
    `ADD EXTRA` / `REN HELPER RENAMED` / `DEL HELPER` flow and is green again
    through the mounted-tree VICE launch harness, with a clean host-tree reseed
    before each phase attempt so partial mutation attempts do not poison
    later retries; `make vice-action-actmon-check` remains the narrower
    workspace-summary/integrity control proof
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
    mounted-tree probe, launches `ACTMOVE.PRG`, renames `OUT.TXT` to
    `NEXT.TXT`, and proves the renamed file persists on the host fs tree with
    `ACTION WRITE OK`
  - `make vice-action-actmove-persist` now uses the resident image with a
    retrying mounted-tree probe, launches `ACTMOVE.PRG`, and proves the rename
    persists on the host fs tree after VICE exits by requiring
    `IMAGES/ACTION.DNP/NEXT.TXT` and the absence of `OUT.TXT`
  - `make vice-action-actmkdir` now uses the release image with deterministic
    typed input, launches `ACTMKDIR.PRG`, creates `OBJ` through the preserved
    external-tool directory-mutation ABI, and proves the shell can enter
    `B:DNP/OBJ>`
  - `make vice-action-actmkdir-persist` now uses the resident image with a
    retrying mounted-tree probe, launches `ACTMKDIR.PRG`, and proves the new
    `OBJ` directory persists on the host fs tree after VICE exits
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
    preserved file-save ABI, and reads the file back through the shell
Current command parser rule:
- shell keywords require a separator before arguments
- direct drive tokens like `A:` and `B:` switch the current logical drive and keep that drive's current directory
- direct `C:` and `D:` tokens are recognized but currently return `DRIVE NOT PRESENT`
- a non-keyword token implies program launch; if it has no extension, `.PRG` is appended
- example: `DEL BOOT3.PRG` deletes the file, while `DELBOOT3` is treated as a bare program token and returns `PROGRAM NOT FOUND`
- `DEL` now also supports limited resident wildcards:
  - `*`
  - `*.*`
  - `*.EXT`
  - `NAME.*`
- `COPY` now also supports the same limited wildcard forms
- wildcard `COPY` preserves each matched source filename and expects the destination to resolve to a directory target
- VICE tree mutations stream `UDOSDIR.TXT` line by line, so catalogs larger than
  255 bytes persist without truncating unrelated entries
- `MEM` now reports launch-capable RAM when REU is present:
  - `RAM USED` is treated as the preserved lower-RAM footprint after an aggressive spill
  - `RAM FREE` is treated as launch-available lower RAM
  - `REU USED` includes the current VICE tree cache reservation plus the spill
    reservation for the resident image and HIRAM workspace, mutation replay,
    and the streamed-write filename shadow
- the VICE backend now spills VICE tree content payloads into REU and keeps only a
  single slot cache in RAM
- UDOS-aware external launch now returns through a resident trampoline under VICE
- the current launch/return validation includes a clobber test that overwrites
  resident code and still returns to the shell through REU-backed restore
- current direct `MEM` probe:
  - `RAM USED 0 FREE 65535 REU USED 47872 FREE 16729344`
- the linked resident image ends at `$AA45`; processor-port value `$36` exposes its
  RAM under BASIC ROM while retaining KERNAL and I/O
- tool-callable resident code ends at `$9FCE`; the `$A000-$BFFF` Action overlay
  window may overwrite only post-return resident code that is restored from REU
- backend-generic Tool ABI paths use the preserved transport snapshot instead
  of low resident probe code, so large tools such as `ACTMON.PRG` may overwrite
  `$1810-$18FE` and still call resident services safely

See:
- `OPERATOR_GUIDE.md`
- `FILESYSTEM_BEHAVIOR.md`
- `PIVOT_PLAN.md`
- `ARCHITECTURE.md`
- `BUILDING.md`
- `COMMAND_MATRIX.md`
- `MILESTONE_HANDOFF.md`
- `STATUS_UDOS.md`
- `TODO_UDOS.md`
