# UDOS Milestone Handoff

## Current Milestone

UDOS is now the active native shell/runtime path for ActionC64U. The maintained
Action execution path is:

```text
ACTC.PRG -> OBJ/<MODULE>.OBJ -> ALINK.PRG -> BIN/<MODULE>.PRG
```

The final product is a direct linked 6502 `.PRG`. There is no separate runtime
runner in the maintained path; `ALINK.PRG` owns all bytes that enter the final
runnable program, including any referenced runtime helper objects.

## Completed Baseline

Resident UDOS now provides the always-present shell and service environment:

- native resident shell and live command input
- resident service ABI
- UCI transport detection seam
- logical drive state for `A:` and `B:`
- flat-vs-tree mounted-image policy
- command dispatch with built-in commands before implicit launch
- implicit `.PRG` launch and `.BAT` fallback
- resident program handoff and return path
- REU-backed resident restore after launched programs return

The resident command surface currently includes:

- `HELP`
- `VER`
- `MEM`
- `VOL`
- `MOUNT`
- `DIR`
- `CD`
- `MD`
- `RD`
- `TREE`
- `XCOPY`
- `DELTREE`
- `TYPE`
- `COPY`
- `REN`
- `DEL`
- direct `A:` and `B:` drive switching
- reserved `C:` and `D:` drive tokens that return `DRIVE NOT PRESENT`

Filesystem behavior is documented in `FILESYSTEM_BEHAVIOR.md`. User-facing
command examples are documented in `OPERATOR_GUIDE.md`.

## Current Validation State

Host and VICE validation cover the active development path:

- root `make test` runs the UDOS and ActionC64U host suites
- `make -C udos test` runs the UDOS build/test target
- `python3 -m unittest discover -v -s udos/tests -p 'test*.py'` covers UDOS host tests
- `python3 -m unittest discover -v -s actionc64u/tests -p 'test*.py'` covers ActionC64U host tests
- `make -C udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actc`
  validates `ACTC.PRG` object creation through UDOS
- `make -C udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-alink`
  validates `ALINK.PRG` direct `BIN/MAIN.PRG` output through UDOS
- `make -C udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actc-alink-launch`
  validates the helper-free `ACTC -> ALINK -> MAIN.PRG` launch path
- `make -C udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-alink-prg-matrix`
  validates the broad direct-PRG object/link matrix
- `make -C udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actc-alink-launch-object-emission-matrix`
  validates source-backed ACTC object-emission launch shapes
- `make -C udos PROOF_DEPS= RESIDENT_DEPS= RELEASE_DEPS= vice-action-actc-alink-launch-runtime-matrices`
  validates link-selected helper-family runtime paths

Current status docs report the broad ALINK direct-PRG matrix at 1356 shapes and
the non-runtime source-backed ACTC object-emission matrix at 188 shapes. Treat
those matrix counts as status facts to update whenever the probe tables change.

The latest source-backed shape compiles
`real_function_nested_postfix.act`: `MAIN` calls one nonrecursive function with
two REAL parameters and a nested straight-line REAL return expression. Pass L
emits ordinary OBJ1 exports and relocations, ALINK selects the referenced
`FAbs`/`FHypot` closure, and the direct PRG prints `5` in VICE. General call
graphs, mixed types, arbitrary signatures, and recursive frames remain compiler
work; the bounded local and control extensions are described below.

The follow-up `real_function_local_nested_postfix.act` shape adds bounded REAL
local storage to that same nonrecursive function path. Its direct PRG prints
`5`, stores binary32 `5.0` in the module result, and stores binary32 `3.0` in
the function local while retaining the same selected helper closure.

The latest `real_two_function_nested_postfix.act` shape expands that bounded
path to two independent nonrecursive two-REAL-parameter functions called by
`MAIN`. Native ACTC emits disjoint parameter/local storage and DBG1 procedure
banks; ALINK links the ordinary `length` and `shorter` exports, and VICE checks
printed values `5` and `3`, both result cells, and both function locals. The
ALINK harness ceiling is 120 million emulated instructions because this
debug-rich three-export object completes in roughly 83 million instructions.

`real_function_call_chain_postfix.act` adds a declaration-order
`MAIN -> CHAIN -> LENGTH` edge through ordinary OBJ1 export relocations. The
follow-up `real_function_nested_local_call_postfix.act` removes the intermediate
source local and returns `FMax(LENGTH(A,B),FAbs(A))`. Its direct PRG prints `5`,
stores binary32 `5.0` in the module result and nested-call temporary, and loads
only the `FAbs`/`FHypot`/`FMax` closure. Pass 7 recognizes `LENGTH` as a local
function while traversing the intrinsic tree, so no unresolved `fmax` import is
introduced. Pass 7 is 6,678 bytes with 1,514 bytes free in its 8 KiB window.
Function-to-function calls now stack-preserve caller parameters, locals, and
live temporaries, so acyclic edges may point in either declaration direction.
Self and mutual cycles remain hard errors.

`real_function_user_call_arguments_postfix.act` extends the same bounded
declaration-order ABI with `LOWER(LOWER(A,A),LOWER(B,B))`. Pass L recognizes
that local-call temporaries feed another local call and copies each returned A/X
pointer into distinct storage before evaluating the next argument. The direct
PRG prints `3`; VICE verifies 3.0 and 4.0 in the inner spills and 3.0 in the
outer spill and module result while ALINK loads only the `FMin`, conversion, and
printing closure.

`real_function_forward_frame_postfix.act` reverses the declaration direction
with `FIRST -> SECOND` while keeping `FAbs(A)` live. Pass L saves the caller's
static cells on the 6502 stack, stages the A/X result, restores those cells, and
copies the result to an independent temporary. The rebuilt direct PRG prints
`3`, VICE verifies binary32 3.0 in the result and preserved temporaries, and
ALINK selects only the `FAbs`/`FMax`/`FMin`, conversion, and printing closure.
Pass L is 6,124 bytes with 2,068 bytes free. Recursive/reentrant frames,
unrestricted user-call argument trees, arbitrary signatures, and recursion
remain compiler work.

`real_function_if_else_postfix.act` adds one nonnested `IF`/`ELSE` in `PICK`.
Pass M (`ACTC_OVLM.BIN`, id 22) maps `A<B` through `rt_f_cmp` and emits
relocations to internal `__rf0`/`__re0` code exports. Calling `PICK` with both
operand orders executes both arms; the rebuilt direct PRG prints `34`. Pass M
is 6,998 bytes with 1,194 bytes free under its 1 KiB gate, while pass L retains
its 2 KiB reserve. Pass M intentionally retains this one-control ownership; the
separate bounded two-control extension follows.

`real_function_sequential_if_else_postfix.act` and
`real_function_nested_if_else_postfix.act` add pass N (`ACTC_OVLN.BIN`, id 23).
Pass N claims at least one second conditional and allows at most two per REAL
function, either sequentially or nested to depth two. Its independent
`__rfNN`/`__reNN` export pairs remain ordinary OBJ1 relocation targets. The
rebuilt direct PRGs print `43` and `143`; the nested case executes inner true,
inner false, and outer false paths. Pass N is 7,120 bytes with 1,072 bytes free
under its 1 KiB gate. At that pass-N checkpoint, loops, early returns, more
than two controls, deeper nesting, and recursive/reentrant frames remained.

`real_function_four_sequential_if_postfix.act` and
`real_function_four_deep_if_postfix.act` add pass O (`ACTC_OVLO.BIN`, id 24).
Pass O claims a third conditional and permits at most four controls per REAL
function, sequentially or nested to depth four. The direct PRGs print `43` and
`154`, with exact result-memory checks and reachable-only `RT_F_CMP`,
`RT_I_TO_F`, and `RT_PRINT_F` closure. Pass O is 7,123 bytes with 1,069 bytes
free under the same 1 KiB gate. Loops, early returns, controls beyond four,
deeper nesting, and recursive/reentrant frames remain compiler work.

The current matrix includes source-backed dynamic integer multiplication and
division, assignment/store/readback, divide-by-zero, missing-helper, and stack
underflow coverage. ACTC emits ordinary native OBJ1 machine and relocation
records for those expressions; ALINK resolves them through its generic object
path and selects the integer helper OBJ modules only when referenced.
Plain word assignments and load/store copies also use compiler-emitted native
OBJ records; the corresponding ALINK compact-body templates are retired.
Multi-procedure local calls and nested integer control flow now use
`ACTC_OVL9.BIN` machine OBJ records, and ALINK's final generic compact-body
candidate/template table has been removed. The separate seeded ALINK smoke uses
an ordinary external machine-code relocation.
Native REAL bridge, REAL-to-INT, straight-line two-literal REAL arithmetic,
unary FAbs/FSqrt print, and helper-prefixed REAL print machine OBJ generation use base-36 pass
`ACTC_OVLA.BIN`; generic `ACTC_OVL5.BIN` no longer contains that generator.
ALINK's matching REAL binary and unary compact-body compilers and fixed-address
layouts are retired. OVLA is 7,418 bytes with 774 bytes free in its 8 KiB
execution window, above its enforced 768-byte growth reserve.
Plain, ELSE, and nested REAL IF machine OBJ generation uses pass
`ACTC_OVLB.BIN`; all 36 variants now use generic ALINK closure and relocation.
All six simple REAL `DO ... UNTIL` comparisons and eight add/sub update loops
also use compiler-emitted machine OBJ from this pass. OVLB is 5,655 bytes with
2,537 bytes free, and ALINK's matching REAL IF and REAL DO/UNTIL fixed-address
strategies are retired. All 14 DO/UNTIL forms pass exact compile/link checks and
live VICE execution.
Passes `ACTC_OVLC.BIN` through `ACTC_OVLF.BIN` now emit machine OBJ for REAL
WHILE, runtime conditions, runtime sequences, and nested readbacks. All 102
seeded runtime fixtures are machine objects, 194 runtime sequences retain
static exact-byte coverage, and 298 complex compiled-runtime cases use an
independent object parser/relocator oracle. ALINK has no abstract-body compiler
or runtime synthesis queues and is now 13,806 bytes.
ALINK also stabilizes each paged object body selector before recursive import
lookups can reload the source window; an 11-import regression crosses that
boundary with the exported body beyond offset 512.
Integer `EXIT` statements in DO, WHILE, and FOR loops lower to ordinary named
machine-code relocations; live coverage includes an inner-FOR exit that leaves
the outer loop active and a plain infinite `DO ... OD` that can terminate only
through EXIT, plus pruning checks for unused integer runtime objects.
Pass 8 also owns plain and post-test DO/EXIT bodies that contain dynamic word
arithmetic. Its 6,953-byte image leaves 1,751 bytes free under the 1 KiB
reserve; exact OBJ and live VICE coverage prove `I=I+1` reaches the selected
EXIT value, stores the result, and does not pull unreferenced
print/multiply/divide objects into the final PRG. FOR debug mappings are checked
across both the `$00FF` and `$01FF` boundaries, and post-test control tokens map
to the exact post-condition machine offset.
Pass 9 also owns dynamic word arithmetic, integer printing, stack-neutral
no-argument external calls inside WHILE control, and ASMBLOCK insertion,
including nested IF and nearest-loop EXIT. Add/subtract is inline;
multiply/divide/print and external procedures use ordinary link-selected
imports. Its 8,065-byte image leaves 639 bytes free under a dedicated 128-byte
minimum reserve. Exact OBJ and live VICE
coverage verifies per-procedure transitive import markers, the helper-free result
of three, the multiply/divide result of six, a printing loop that emits `1` and
`2` before ending at four, and a `SidRst()` loop that clears prefilled SID state
and ends at one while unrelated runtime objects remain pruned.
Pass G, `ACTC_OVLG.BIN`, owns one-word byte-in-A and word-in-X/Y runtime calls
inside integer control. Its 7,110-byte image leaves 1,594 bytes free under a
512-byte minimum reserve. Source-backed `SidVol(I+10)` and
`SidCutoff(I+300)` WHILE cases prove both ABIs, loop-variable value one, and
selection of only the referenced SID closure. Core `ASMBLOCK [ ... ]` assembly
is performed in pass 4 and emitted through pass 9 as ordinary OBJ machine bytes,
block-local targets, and relocations to current globals, PROC parameters, and
locals. REAL globals and locals retain four-byte exports and can be indexed at
offsets zero through three; a live direct PRG observes `$033C-$033F` as
`$11,$44,$22,$55` without loading runtime helper objects. Pass H,
`ACTC_OVLH.BIN`, composes ASMBLOCK, runtime calls, `=*(...)`, and numeric
absolute-address declarations in one typed unit;
its 8,535-byte image leaves 169 bytes free under a 128-byte reserve. A live
direct PRG returns 42, stores trace value 41, and writes SID volume 8.
Pass J, `ACTC_OVLJ.BIN`, owns compact bodyless numeric absolute-address routine
declarations and emits direct JSR instructions through the shared register ABI.
Its 7,554-byte image leaves 1,150 bytes free; it emits no wrapper, export,
import, or runtime object. The focused `$FFD2` CHROUT case passes exact OBJ,
ALINK closure, and live VICE checks. Composed fixed-address units decline J and
fall through to pass H before any output is opened.
Forward/backward local routine aliases accept a checked signed 16-bit constant
expression on either side of the symbol and emit ordinary named OBJ1
relocations. The focused `WORKERALIAS=(1-1)+WORKER()` direct PRG prints `!`
after generic ALINK placement and selects no library object; the numeric case
uses grouped `$FFD0+2` and still emits a direct `$FFD2` call.
Local core `REAL FUNC` lowering supports direct named-storage returns with no
arguments and a constrained one-word-parameter form. The latter binds one
direct literal or an immediately initialized named module word scalar through
the scalar stack ABI, converts it with `REAL(parameter)`, returns the named REAL
storage pointer in A/X, and lets the caller copy all four bytes. Both live cases
return binary32 42.0 while ALINK selects only the ordinary reachable conversion
object.
The bounded two-REAL-parameter pass-A form now keeps its named return selector
independent from caller argument storage. A reordered shared fixture binds
`LEFT/RIGHT` to `B/A`, returns the second parameter, and writes 2.0 while VICE
checks both caller values and both reverse-bound parameter copies. Its generic
157-byte OBJ still selects only `RT_I_TO_F.OBJ`.
Pass K, `ACTC_OVLK.BIN`, adds a bounded two-REAL-parameter finite
comparison/select function. The enclosing root records the union of its
reachable conversion and comparison imports, while the function export records
only comparison. Generic ALINK closure therefore selects `RT_I_TO_F.OBJ`,
`RT_F_CMP.OBJ`, and transitive `RT_F_SPECIAL.OBJ`, prunes unrelated REAL
helpers, and launches the self-contained PRG in VICE. Native ACTC now also
captures reordered initializer, call, result, parameter-bind, comparison, and
return storage in this bounded function. Canonical and permuted shared fixtures
both return 1.0 and verify all five REAL cells. Native ACTC also
lowers bounded `FSign(A)`, `FMin(A,B)`, and `FMax(A,B)` source forms for named
REAL operands. `FSign` selects only dependency-free `RT_F_SIGN.OBJ`; min/max
select `RT_F_MIN.OBJ` or `RT_F_MAX.OBJ` plus comparison closure. Their exact
MATH1 NaN/signed-zero policy, sibling pruning, and direct VICE launches pass.
Pass K additionally emits a bounded three-initializer `FClamp` assignment and
print root. Its matcher captures the three initializer destinations, three
arguments, result destination, and printed value, so storage roles can be
permuted without changing the fixed statement skeleton. `RT_F_CLAMP.OBJ`
selects comparison, minimum, and maximum only when reachable, canonicalizes
invalid clamp inputs, and preserves valid selected operands. Pass K also emits
a bounded two-REAL-parameter function whose sole return is one selected binary
operation. The shared `RETURN(FHypot(A,B))` fixture uses a hidden non-aliasing
result cell, loads only the reachable hypotenuse closure, and returns 5.0 in
VICE. Pass K is 5,877 bytes with 2,315 bytes free. Native unary lowering now also recognizes
`FTrunc(A)`, `FFloor(A)`, `FCeil(A)`, and `FRound(A)`. Truncation imports dependency-free
`RT_F_TRUNC.OBJ`; floor imports `RT_F_FLOOR.OBJ` plus that truncation dependency
transitively. The 107-byte truncation helper preserves infinities, NaN payloads,
signed zero, and integral values. The 135-byte floor helper rounds finite
nonintegers toward negative infinity while preserving those same bit patterns.
The 42-byte `RT_F_CEIL.OBJ` helper imports floor and transitively truncation, preserves
the same bit patterns, and rounds finite nonintegers toward positive infinity.
The 152-byte `RT_F_ROUND.OBJ` helper imports only truncation, rounds nearest
with halfway cases away from zero, and preserves large integral binary32 values
without adding or subtracting 0.5.
The 93-byte `RT_F_FRAC.OBJ` helper imports truncation and subtraction, computes
the signed fractional part as `value-FTrunc(value)`, and remains safe when its
source and destination alias.
The 245-byte `RT_F_MOD.OBJ` helper imports division, truncation,
multiplication, and subtraction, computes
`value-FTrunc(value/divisor)*divisor`, and remains safe when either source
aliases its destination. Invalid inputs return canonical quiet NaN; a finite
value with an infinite divisor is preserved exactly.
The 503-byte `RT_F_HYPOT.OBJ` helper is also safe when either source aliases
its destination. Its scaled maximum/minimum calculation imports absolute
value, minimum, maximum, division, multiplication, addition, and square root,
avoids avoidable intermediate overflow and underflow, returns positive zero
for two zero inputs, and gives infinity precedence when paired with NaN.
Focused ACTC -> ALINK -> direct-PRG launches select only conversion,
truncation/floor/ceiling/rounding/fractional-part/remainder/hypotenuse dependencies, and REAL printing
while proving sibling REAL helpers remain absent. Pass 6 is
8,094 bytes with 98 bytes free under its enforced 96-byte reserve. General REAL expression
trees and the remaining 28
MATH1 routines are
still compiler work.
The complete `ACTION.DNP` includes all compiler passes, ACTEDIT, ACTDBG, and all
tools. The capacity-limited D64 retains ACTC passes 0 through H, ALINK, resident
`COPY`, and compact delete/directory/tree tools. The redundant `ACTCOPY.PRG`
wrapper, project mutation, and larger tools are workspace-only; the D64 has zero
blocks free.
Empty-return, single-call, and fanout root programs use the same native object
path; their former compact root-body templates are retired from ALINK.
Simple integer equality, inequality, and all four unsigned ordered `IF`
comparisons now use an ACTC-emitted `__if0` local export and named branch
relocation; all six former ALINK templates are rejection-only.
Simple equality `IF/ELSE` also uses compiler-emitted native code, with `__if0`
for the else entry and `__if1` for the join; its former ALINK template is
rejection-only and both branch outcomes have live VICE coverage.

The focused documentation guards are:

```sh
python3 -m unittest discover -v -s udos/tests -p 'test_*docs.py'
```

## Filesystem State

Current behavior contract:

- `D64`, `D71`, and `D81` are flat images.
- `DNP` is tree-capable.
- tree commands on flat images must fail explicitly.
- `TREE` has a first one-level resident scaffold that expands root child
  directories, lists selected tree-capable directories, and rejects flat images.
- `TREE` resolves the native `TREE.OVL` module from the parsed command token and
  validates its `UDOV` header before recursive traversal, while
  preserving the resident scaffold as fallback.
- `XCOPY` resolves and validates `XCOPY.OVL`, then performs bounded recursive
  merge-copy through path-scoped directory and file-copy Tool ABI services.
- `DELTREE` resolves and validates `DELTREE.OVL`, then performs bounded
  post-order removal through nested directory-remove and file-delete Tool ABI
  services while protecting the current directory before mutation.
- `COPY` and `DEL` support only the documented limited wildcard forms.
- `REN` is same-directory behavior.
- full recursive `TREE`, bounded recursive `XCOPY`, and bounded recursive
  `DELTREE` are VICE-validated. Hardware/UCI overlay staging is implemented but
  not hardware-validated; hardware Tool ABI mutations for nested enumeration,
  directory creation, file copy/delete, and empty-directory removal are
  implemented but not hardware-validated.
- fixed external-tool file load/probe is implemented for hardware/UCI tree
  files with bounded too-large semantics, but is not hardware-validated.
- fixed external-tool file save is implemented for hardware/UCI tree files with
  exact explicit-length writes and the bounded null-terminated compatibility
  path used by `ACTWRITE`, but is not hardware-validated.
- external-tool streamed write begin/chunk/close is implemented for
  hardware/UCI tree files with exact binary lengths and persistent target-drive
  state, but is not hardware-validated.
- fixed external-tool file stage-to-REU is implemented for hardware/UCI tree
  files with 24-bit capacity checks and exact final-count validation, but is
  not hardware-validated.
- VICE catalog enumeration streams the complete `UDOSDIR.TXT` rather than a
  255-byte prefix while retaining a bounded six-entry snapshot; later
  directories displace cached files so recursive traversal remains possible.
- VICE-created data paths are lowercase physical host artifacts while logical
  catalog records remain uppercase; catalog metadata is physically
  `UDOSDIR.TXT`.

Current linked memory boundary facts:

- resident image end: `$AA45`
- fixed Tool ABI preservation start: `$9800`
- exclusive tool-callable safe end: `$9FCE`, leaving 50 bytes before `$A000`
- resident-private REU bank: `$FF`
- temporary low-resident/tool swap bank: `$FE`
- bounded fixed-tool file-load bank: `$FD`
- current `MEM` result: `REU USED 47872 FREE 16729344`

VICE validates the tree-capable `DNP` path used by the current release workspace.
Flat-image code paths exist for raw directory/file handling, but real hardware
validation remains a separate requirement.

## Hardware Boundary

No real C64 Ultimate hardware validation has been completed from this
environment. VICE validation is necessary, but it does not prove the
`Hardware/UCI` column in `COMMAND_MATRIX.md` because VICE does not provide the
Ultimate UCI block.

Before changing any `Hardware/UCI` command status to `Yes`, run and record the
matching sequence in `HARDWARE_VALIDATION.md` on real hardware.

Known hardware-facing areas that remain unverified on target:

- `MOUNT_DISK` image binding
- `CHANGE_DIR` / `GET_PATH` synchronization
- `OPEN_DIR` / `READ_DIR` tree enumeration
- `OPEN_FILE` / `READ_DATA` / `CLOSE_FILE` file reads
- fixed external-tool `svc_file_load_sc0` probe and bounded file loads
- fixed external-tool `svc_file_save_sc0` create/overwrite and chunked writes
- fixed external-tool streamed binary write begin/chunk/close
- fixed external-tool `svc_file_stage_reu_sc0` UCI read-to-REU transfers
- raw flat-image `FILE_SEEK` / `READ_DATA` traversal
- raw flat-image `WRITE_DATA` mutation paths
- `DELETE_FILE`, `RENAME_FILE`, and `COPY_FILE` tree mutation paths
- implicit program-image loads through the hardware backend
- direct-PRG and native `UDOV` tree-file staging through repeated `READ_DATA`
  transfers into REU
- recursive overlay Tool ABI behavior and return to the resident shell

## ActionC64U Resume Point

Resume ActionC64U work in the sibling repo:

- [actionc64u](../actionc64u)

The active Action direction is not VM/interpreter execution. Continue widening
the direct object/link path:

- keep `ACTC.PRG` emitting `.OBJ` records for `ALINK.PRG`
- keep `ALINK.PRG` producing direct `BIN/<MODULE>.PRG` output
- keep optional library/runtime helper families selected only when referenced
- keep final linked programs runnable without any separate runtime runner
- keep the direct-PRG matrix green as new object-code and helper-family cases are added

High-value next Action work:

- widen ACTC source coverage and object emission
- continue ALINK object closure and helper selection edge cases
- keep large ACTC and ALINK lookup payloads moving into REU-backed storage
- add remaining library/runtime helper families through link-selected `.OBJ` modules
- keep root `make test` and the focused UDOS VICE gates green after each slice

## Safe Handoff Checklist

Before moving to a new machine or handing off to another session:

1. Run `make clean` from the workspace root.
2. Confirm no generated `build`, `__pycache__`, or `.pytest_cache` trees remain.
3. Check `git -C actionc64u status --short` and `git -C udos status --short`.
4. Run cached and unstaged whitespace checks:

```sh
git -C actionc64u diff --check --cached
git -C udos diff --check --cached
git -C actionc64u diff --check
git -C udos diff --check
```

5. Archive the whole `~/action` tree, including hidden files and nested `.git`
   directories, if preserving staged work without committing.
