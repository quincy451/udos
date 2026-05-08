#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

import run_action_actc_probe as rcp
import run_action_actc_alink_launch_probe_direct as launch_direct
import run_action_alink_probe as rap
import run_action_avmrun_probe as avp
import vice_prg_probe as vp

ROOT = Path(__file__).resolve().parent
ACTION_ROOT = ROOT.parent.parent / 'actionc64u'
ACTION_ALINK_BUILD = ROOT.parent.parent / 'actionc64u' / 'build' / 'udos_tools' / 'ALINK.PRG'
ACTION_AVMRUNC_BUILD = ROOT.parent.parent / 'actionc64u' / 'build' / 'udos_tools' / 'AVMRUNC.PRG'
AVM_PACK = ROOT.parent.parent / 'actionc64u' / 'tools' / 'avm_pack.py'
RUNTIME_SUPPORT_ARTIFACTS = (
    'AVMRUN_OVL1.BIN',
    'AVMRUN_OVL2.BIN',
    'AVMRUN_OVL3.BIN',
    'RT_PRINT_STD_HELPER.BIN',
    'RT_PRINT_F_HELPER.BIN',
    'RT_GFX1_HELPER.BIN',
    'RT_SIDSPR1_HELPER.BIN',
    'RT_DBF1_HELPER.BIN',
    'RT_MATH1_HELPER.BIN',
)
TOOL_ABI_HARNESS = ROOT.parent.parent / 'actionc64u' / 'build' / 'udos_tools' / 'tool_abi_harness'
UDOS_SERVICES_INC = ROOT.parent.parent / 'actionc64u' / 'build' / 'udos_tools' / 'udos_services.inc'
AVMRUNC_LABELS = ROOT.parent.parent / 'actionc64u' / 'build' / 'udos_tools' / 'avmrunc.current.labels'
UDOS_RUNTIME_MODULES = ACTION_ROOT / 'src' / 'runtime' / 'udos_modules'
ACTC_CONNECT_DELAY = rcp.CONNECT_DELAYS[0]
AVMRUN_CONNECT_DELAY = rap.CONNECT_DELAYS[0]
STAGE_ATTEMPTS = 3
STAGE_ATTEMPT_DELAY = 2.0
ACTC_PHASE_TIMEOUT = 180.0
AVMRUN_PHASE_TIMEOUT = 180.0
PHASE_TIMEOUT_MARGIN = 45.0
DEFAULT_SHAPE = "printmath"
SHELL_SANITY_NAME = "SHELLMIN"
SHELL_NONTRIV_NAME = "SHELLADD"


def work_object_text() -> str:
    return (
        'AVO1\n'
        'x w 0 13\n'
        'b s0i0r\n'
        's TOOL\n'
        'i 7\n'
        'n w\n'
    )


def realprint125_source_text() -> str:
    return (
        'MODULE MAIN\r'
        'REAL A\r'
        'REAL B\r'
        'REAL X\r'
        'PROC MAIN()\r'
        'A=REAL(1)\r'
        'B=REAL(8)\r'
        'X=A/B\r'
        'PrintRE(X)\r'
        'RETURN\r'
    )


def helper_bearing_case(shape: str) -> dict[str, object]:
    cases: dict[str, dict[str, object]] = {
        "printmath": {
            "source": rcp.source_text(),
            "object_required": [
                "AVO1",
                "x main 0 38",
                "b e0u0p0p1ap2myp3p4mp5azr",
                "u w",
                "s HELLO",
                "i 50\ni 7\ni 3\ni 60\ni 3\ni 2",
                "k 7",
                "n main",
            ],
            "expect_helper_trailer": True,
            "packed_fragments": [b"HELLO\x00TOOL\x00"],
            "done_fragment": "5459",
            "console_contains": ["HELLO", "TOOL7", "ARGS BIN/MAIN.AVM"],
            "harness_console": "HELLO\nTOOL7\n5459\n",
        },
        "realprint125": {
            "source": realprint125_source_text(),
            "object_required": ["AVO1", "x main", "n main"],
            "done_fragment": "0.125",
            "console_contains": ["0.125", "ARGS BIN/MAIN.AVM"],
            "expect_helper_trailer": True,
            "harness_console": "0.125\n",
        },
    }
    try:
        return cases[shape]
    except KeyError as exc:
        raise RuntimeError(f"unknown helper-bearing shape: {shape}") from exc


def install_program(fs_root: Path, project_root: Path, build_path: Path, name: str) -> None:
    if not build_path.is_file():
        raise RuntimeError(f'missing built program: {build_path}')
    lowercase_workspace = rcp.detect_lowercase_workspace(fs_root)
    images_root = rcp.case_insensitive_child(fs_root, rcp.host_name('IMAGES', lowercase_workspace))
    action_root = rcp.case_insensitive_child(images_root, rcp.host_name('ACTION.DNP', lowercase_workspace))
    root_target = action_root / rcp.host_name(name, lowercase_workspace)
    shutil.copy2(build_path, root_target)
    shutil.copy2(root_target, project_root / rcp.host_name(name, lowercase_workspace))
    rap.ensure_catalog_entries(
        action_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace),
        [f'D {project_root.name.upper()}', f'F {name}'],
    )
    rap.ensure_catalog_entries(project_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace), [f'F {name}'])


def install_runtime_support_artifacts(fs_root: Path, project_root: Path | None = None) -> None:
    lowercase_workspace = rcp.detect_lowercase_workspace(fs_root)
    images_root = rcp.case_insensitive_child(fs_root, rcp.host_name('IMAGES', lowercase_workspace))
    action_root = rcp.case_insensitive_child(images_root, rcp.host_name('ACTION.DNP', lowercase_workspace))
    staged_entries: list[str] = []
    project_entries: list[str] = []
    for name in RUNTIME_SUPPORT_ARTIFACTS:
        build_path = ACTION_ROOT / 'build' / 'udos_tools' / name
        if not build_path.is_file():
            continue
        staged_target = action_root / rcp.host_name(name, lowercase_workspace)
        shutil.copy2(build_path, staged_target)
        staged_entries.append(f'F {name}')
        if project_root is not None:
            shutil.copy2(build_path, project_root / rcp.host_name(name, lowercase_workspace))
            project_entries.append(f'F {name}')
    if staged_entries:
        rap.ensure_catalog_entries(action_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace), staged_entries)
    if project_root is not None and project_entries:
        rap.ensure_catalog_entries(project_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace), project_entries)


def object_imports_from_text(text: str) -> set[str]:
    imports: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith('u '):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1]:
            imports.add(parts[1].strip().lower())
    return imports


def stage_runtime_module_closure(project_root: Path, lowercase_workspace: bool) -> None:
    obj_root = project_root / rcp.host_name('OBJ', lowercase_workspace)
    lib_root = project_root / rcp.host_name('LIB', lowercase_workspace)
    pending: list[str] = []
    seen: set[str] = set()
    copied_entries: list[str] = []

    for obj_path in sorted(obj_root.glob('*.[Oo][Bb][Jj]')):
        text = obj_path.read_text(encoding='ascii', errors='ignore')
        pending.extend(sorted(object_imports_from_text(text)))

    while pending:
        name = pending.pop(0)
        if name in seen:
            continue
        seen.add(name)
        source_path = UDOS_RUNTIME_MODULES / f'{name}.avo'
        if not source_path.is_file():
            continue
        lib_root.mkdir(parents=True, exist_ok=True)
        target_name = name.upper() + '.OBJ'
        target_path = lib_root / rcp.host_name(target_name, lowercase_workspace)
        shutil.copy2(source_path, target_path)
        copied_entries.append(f'F {target_name}')
        module_text = source_path.read_text(encoding='ascii', errors='ignore')
        for imported_name in sorted(object_imports_from_text(module_text)):
            if imported_name not in seen:
                pending.append(imported_name)

    if copied_entries:
        rap.ensure_catalog_entries(lib_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace), copied_entries)
        rap.ensure_catalog_entries(project_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace), ['D LIB'])
    else:
        shutil.rmtree(lib_root, ignore_errors=True)


def prepare_link_workspace(fs_root: Path, project_root: Path) -> None:
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    obj_root = project_root / rcp.host_name('OBJ', lowercase_workspace)
    rap.write_ascii(obj_root / rcp.host_name('W.OBJ', lowercase_workspace), work_object_text())
    rap.ensure_catalog_entries(obj_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace), ['F W.OBJ'])
    stage_runtime_module_closure(project_root, lowercase_workspace)
    install_program(fs_root, project_root, ACTION_ALINK_BUILD, 'ALINK.PRG')
    install_program(fs_root, project_root, ACTION_AVMRUNC_BUILD, 'AVMRUNC.PRG')
    install_runtime_support_artifacts(fs_root, project_root)


def stage_shell_sanity_avm(project_root: Path) -> None:
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    bin_root = project_root / rcp.host_name('BIN', lowercase_workspace)
    samples = {
        SHELL_SANITY_NAME: (
            'entry start\n'
            'code $03\n'
            'start:\n'
            '  calln exit\n'
        ),
        SHELL_NONTRIV_NAME: (
            'entry start\n'
            'code $0A\n'
            'start:\n'
            '  push16 100\n'
            '  push16 24\n'
            '  add\n'
            '  calln exit\n'
        ),
    }
    manifest_entries: list[str] = []
    for sample_name, avm_text in samples.items():
        avt_path = bin_root / rcp.host_name(f'{sample_name}.AVT', lowercase_workspace)
        avm_path = bin_root / rcp.host_name(f'{sample_name}.AVM', lowercase_workspace)
        rcp.write_ascii(avt_path, avm_text)
        subprocess.run(
            [
                sys.executable,
                str(AVM_PACK),
                '--text',
                '--flags',
                '1',
                str(avt_path),
                '--output',
                str(avm_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        manifest_entries.extend((f'F {sample_name}.AVT', f'F {sample_name}.AVM'))
    rap.ensure_catalog_entries(
        bin_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace),
        manifest_entries,
    )


def collect_vice_debug_dump(client: vp.BinaryMonitorClient) -> str:
    parts: list[str] = []
    try:
        registers = client.registers_get()
        parts.append('registers: ' + ' '.join(f'{name}={value:#06x}' for name, value in registers.items()))
    except Exception as exc:
        parts.append(f'register_debug_error={exc!r}')
    try:
        screen, d018, dd00 = vp.read_active_screen_text(client)
        base = vp.active_screen_base(d018, dd00)
        parts.append(f'active_screen_base={base:#06x} d018={d018:#04x} dd00={dd00:#04x}')
        if screen:
            parts.append(f'screen:\n{screen}')
        raw = client.memory_get(base, base + 999, memspace=vp.MAIN_MEMSPACE, bank=vp.MAIN_BANK_RAM)
        row_dump: list[str] = []
        for row in range(25):
            row_bytes = raw[row * 40 : (row + 1) * 40]
            if any(byte != 0x20 for byte in row_bytes):
                row_dump.append(f'row{row:02d}: ' + ' '.join(f'{byte:02x}' for byte in row_bytes))
        if row_dump:
            parts.append('screen_rows:\n' + '\n'.join(row_dump))
    except Exception as exc:
        parts.append(f'screen_debug_error={exc!r}')
    try:
        stack = client.memory_get(0x01E0, 0x01FF, memspace=vp.MAIN_MEMSPACE, bank=vp.MAIN_BANK_RAM)
        parts.append('stack_01e0_01ff: ' + stack.hex())
    except Exception as exc:
        parts.append(f'stack_debug_error={exc!r}')
    try:
        zp = client.memory_get(0x00E0, 0x00F5, memspace=vp.MAIN_MEMSPACE, bank=vp.MAIN_BANK_RAM)
        parts.append('zp_00e0_00f5: ' + zp.hex())
    except Exception as exc:
        parts.append(f'zp_debug_error={exc!r}')
    try:
        interp = client.memory_get(0x3C00, 0x3C4F, memspace=vp.MAIN_MEMSPACE, bank=vp.MAIN_BANK_RAM)
        parts.append('interp_3c00_3c4f: ' + interp.hex())
    except Exception as exc:
        parts.append(f'interp_debug_error={exc!r}')
    try:
        snapshot = vp.read_debug_bytes(client, vp.UDOS_LAUNCH_DEBUG_BYTES)
        nonzero = [f'{label}={value:#04x}@{addr:#06x}' for label, addr, value in snapshot if value]
        if nonzero:
            parts.append('debug_bytes: ' + ' '.join(nonzero))
    except Exception as exc:
        parts.append(f'debug_snapshot_error={exc!r}')
    try:
        path_parts = []
        for label, addr in (
            ('tool_abi_current_path', 0xCD00),
            ('tool_abi_launch_path', 0xCD20),
            ('tool_abi_open_path', 0xCD40),
        ):
            path_parts.append(f"{label}={avp.read_c_string(client, addr)!r}")
        parts.append('tool_paths: ' + ' '.join(path_parts))
    except Exception as exc:
        parts.append(f'tool_path_debug_error={exc!r}')
    return '\n'.join(parts)


def wait_for_stable_project_prompt(
    client: vp.BinaryMonitorClient,
    prompt: str,
    timeout: float,
    *,
    settle: float = 1.0,
) -> str:
    screen = avp.wait_for_active_prompt(client, prompt, timeout, poll_interval=0.2)
    time.sleep(settle)
    return avp.wait_for_active_prompt(client, prompt, max(2.0, settle + 1.0), poll_interval=0.2)


def prepare_helper_bearing_workspace(fs_root: Path, project_name: str, shape: str) -> Path:
    project_root = rcp.prepare_workspace(fs_root, project_name)
    case = helper_bearing_case(shape)
    source = case["source"]
    if not isinstance(source, str):
        raise RuntimeError(f"missing source for helper-bearing shape: {shape}")
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    src_root = project_root / rcp.host_name('SRC', lowercase_workspace)
    bin_root = project_root / rcp.host_name('BIN', lowercase_workspace)
    obj_root = project_root / rcp.host_name('OBJ', lowercase_workspace)
    rcp.write_ascii(src_root / rcp.host_name('MAIN.ACT', lowercase_workspace), source)
    rcp.write_ascii(src_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace), 'F MAIN.ACT\n')
    rcp.write_ascii(bin_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace), '')
    rcp.write_ascii(obj_root / rcp.host_name('UDOSDIR.TXT', lowercase_workspace), '')
    for stale_name in ('MAIN.OBJ', 'MAIN.AVM', 'MAIN.PRG', 'main.obj', 'main.avm', 'main.prg'):
        (project_root / stale_name).unlink(missing_ok=True)
        (bin_root / stale_name).unlink(missing_ok=True)
        (obj_root / stale_name).unlink(missing_ok=True)
    return project_root


def verify_host_object(project_root: Path, shape: str) -> None:
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    output_path = project_root / rcp.host_name('OBJ', lowercase_workspace) / rcp.host_name('MAIN.OBJ', lowercase_workspace)
    if not output_path.is_file():
        raise RuntimeError(f'expected host file {output_path} to exist')
    text = output_path.read_text(encoding='ascii', errors='ignore')
    case = helper_bearing_case(shape)
    required = case.get("object_required", [])
    if isinstance(required, list):
        missing = [fragment for fragment in required if fragment not in text]
        if missing:
            raise RuntimeError(f"expected host object {output_path} to contain {missing!r}")


def verify_link_output(project_root: Path, shape: str) -> None:
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    avm_path = project_root / rcp.host_name('BIN', lowercase_workspace) / rcp.host_name('MAIN.AVM', lowercase_workspace)
    if not avm_path.is_file():
        raise RuntimeError(f'expected host file {avm_path} to exist')
    case = helper_bearing_case(shape)
    packed = avm_path.read_bytes()
    if not packed.startswith(b"AVM1"):
        raise RuntimeError(f"expected AVM output {avm_path} to start with AVM1")
    if case.get("expect_helper_trailer") and b"AVH1" not in packed:
        raise RuntimeError(f"expected helper trailer in {avm_path}")
    packed_fragments = case.get("packed_fragments", [])
    if isinstance(packed_fragments, list):
        missing = []
        for fragment in packed_fragments:
            fragment_bytes = fragment.encode("ascii") if isinstance(fragment, str) else fragment
            if not isinstance(fragment_bytes, (bytes, bytearray)) or bytes(fragment_bytes) not in packed:
                missing.append(fragment)
        if missing:
            raise RuntimeError(f"expected packed AVM {avm_path} to contain {missing!r}")


def run_avmrun_harness_phase(project_root: Path, shape: str) -> None:
    case = helper_bearing_case(shape)
    expected_console = case.get("harness_console")
    if not isinstance(expected_console, str):
        raise RuntimeError(f"missing harness console for helper-bearing shape: {shape}")
    if not TOOL_ABI_HARNESS.is_file():
        raise RuntimeError(f"missing tool_abi_harness: {TOOL_ABI_HARNESS}")
    cmd = [
        str(TOOL_ABI_HARNESS),
        '--prg',
        str(ACTION_AVMRUNC_BUILD),
        '--workspace',
        str(project_root),
        '--cmdline',
        'BIN/MAIN.AVM',
        '--services-inc',
        str(UDOS_SERVICES_INC),
        '--labels',
        str(AVMRUNC_LABELS),
        '--max-steps',
        '12000000',
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120.0,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('AVMRUN harness phase timed out after 120s') from exc
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or 'AVMRUN harness phase failed'
        raise RuntimeError(details)
    try:
        summary = __import__('json').loads(result.stdout)
    except Exception as exc:  # pragma: no cover - defensive probe parsing
        raise RuntimeError(f'failed to parse AVMRUN harness JSON: {exc}') from exc
    console = summary.get('console', '')
    if console != expected_console:
        raise RuntimeError(
            f"expected AVMRUN harness console {expected_console!r}, got {console!r}"
        )


def run_actc_phase(image: Path, work_root: Path, project_name: str, project_root: Path) -> None:
    cmd = [
        sys.executable,
        str(ROOT / 'run_action_actc_probe.py'),
        '--disk',
        str(image),
        '--fs-root',
        str(work_root),
        '--project',
        project_name,
        '--attempts',
        '1',
        '--connect-delay',
        str(ACTC_CONNECT_DELAY),
        '--command-timeout',
        str(ACTC_PHASE_TIMEOUT),
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=ACTC_PHASE_TIMEOUT + PHASE_TIMEOUT_MARGIN,
        )
    except subprocess.TimeoutExpired as exc:
        raise vp.ViceError(f'ACTC phase timed out after {ACTC_PHASE_TIMEOUT:.0f}s') from exc
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or 'ACTC phase failed'
        raise vp.ViceError(details)

    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    avo_path = project_root / rcp.host_name('OBJ', lowercase_workspace) / rcp.host_name('MAIN.OBJ', lowercase_workspace)
    if not avo_path.is_file():
        raise vp.ViceError(f'ACTC phase completed without expected host output {avo_path}')


def run_alink_phase(project_root: Path) -> None:
    try:
        launch_direct.run_alink_phase(project_root)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ALINK harness phase timed out after 120s") from exc
    except RuntimeError as exc:
        raise RuntimeError(str(exc)) from exc


def run_avmrun_phase(image: Path, work_root: Path, project_name: str, shape: str) -> None:
    case = helper_bearing_case(shape)
    done_fragment = case.get("done_fragment")
    if not isinstance(done_fragment, str):
        raise RuntimeError(f"missing done fragment for helper-bearing shape: {shape}")
    console_contains = case.get("console_contains", [])
    if not isinstance(console_contains, list):
        raise RuntimeError(f"invalid console fragments for helper-bearing shape: {shape}")
    last_error: Exception | None = None
    last_screen = ""
    last_debug = ""
    for attempt in range(1, STAGE_ATTEMPTS + 1):
        vp.cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, STAGE_ATTEMPT_DELAY)))
        port = vp.reserve_tcp_port()
        process = vp.launch_vice(
            image,
            port,
            extra_args=["-iecdevice9", "-fs9", str(work_root), "-fslongnames"],
        )
        client = vp.BinaryMonitorClient("127.0.0.1", port, timeout=5.0)
        try:
            if AVMRUN_CONNECT_DELAY > 0.0:
                time.sleep(AVMRUN_CONNECT_DELAY)
            client.connect(time.monotonic() + 20.0)
            client.ping()
            client.resume()

            avp.wait_for_screen_fragment(client, "A:D64/>", 60.0, poll_interval=0.2)
            time.sleep(3.0)

            avp.type_command(client, "MOUNT B: /IMAGES/ACTION.DNP", 30.0)
            avp.wait_for_mount_completion(
                client,
                30.0,
                retry_echo="MOUNT B: /IMAGES/ACTION.DNP",
                poll_interval=0.2,
            )

            avp.type_command(client, "B:", 30.0)
            avp.wait_for_screen_fragment(client, "B:DNP/>", 30.0, retry_echo="B:", poll_interval=0.2)

            avp.type_command(client, f"CD {project_name}", 30.0)
            project_prompt = f"B:DNP/{project_name}>"
            avp.wait_for_screen_fragment(client, project_prompt, 30.0, retry_echo=f"CD {project_name}", poll_interval=0.2)

            avp.type_command(client, f"AVMRUNC BIN/{SHELL_SANITY_NAME}.AVM", 30.0)
            avp.wait_for_screen_fragment(
                client,
                "RUN AVMRUNC.PRG",
                30.0,
                retry_echo=f"AVMRUNC BIN/{SHELL_SANITY_NAME}.AVM",
                poll_interval=0.2,
            )
            try:
                wait_for_stable_project_prompt(client, project_prompt, 12.0)
            except Exception as exc:
                raise vp.ViceError(
                    "generic shell-launched AVMRUNC path is blocked before shape-specific replay; "
                    "minimal nested launch did not return to the project prompt"
                ) from exc

            avp.type_command(client, f"AVMRUNC BIN/{SHELL_NONTRIV_NAME}.AVM", 30.0)
            avp.wait_for_screen_fragment(
                client,
                "RUN AVMRUNC.PRG",
                30.0,
                retry_echo=f"AVMRUNC BIN/{SHELL_NONTRIV_NAME}.AVM",
                poll_interval=0.2,
            )
            try:
                wait_for_stable_project_prompt(client, project_prompt, 20.0)
            except Exception as exc:
                raise vp.ViceError(
                    "generic nontrivial shell-launched AVMRUNC path is blocked before shape-specific replay; "
                    "a no-output add/exit AVM did not return to the project prompt"
                ) from exc

            avp.type_command(client, "AVMRUNC BIN/MAIN.AVM", 30.0)
            avp.wait_for_screen_fragment(
                client,
                "RUN AVMRUNC.PRG",
                30.0,
                retry_echo="AVMRUNC BIN/MAIN.AVM",
                poll_interval=0.2,
            )
            screen = avp.wait_for_active_prompt(
                client,
                project_prompt,
                20.0,
                poll_interval=0.2,
            )
            expected_fragments = [project_prompt, done_fragment]
            for fragment in console_contains:
                if isinstance(fragment, str) and fragment not in expected_fragments:
                    expected_fragments.append(fragment)
            for fragment in expected_fragments:
                if not vp.screen_contains(screen, fragment):
                    raise vp.ViceError(
                        f"expected screen fragment {fragment!r} was not present after helper-bearing replay:\n{screen}"
                    )
            for fragment in ("NEEDS AVMRUN COMPAT", "BAD AVM", "UNSUPPORTED AVM", "HARNESS NO ACHERON"):
                if vp.screen_contains(screen, fragment):
                    raise vp.ViceError(f"unexpected screen fragment {fragment!r} was present:\n{screen}")
            return
        except Exception as exc:
            last_error = exc
            try:
                last_screen = avp.screen_text(client)
            except Exception:
                last_screen = ""
            try:
                last_debug = collect_vice_debug_dump(client)
            except Exception:
                last_debug = ""
        finally:
            try:
                client.quit_emulator()
            except Exception:
                pass
            client.close()
            vp.terminate_process_tree(process)
        if attempt < STAGE_ATTEMPTS:
            time.sleep(STAGE_ATTEMPT_DELAY)
    message = str(last_error) if last_error is not None else "AVMRUNC phase failed"
    if last_screen:
        message += f"\nlast screen:\n{last_screen}"
    if last_debug:
        message += f"\ndebug:\n{last_debug}"
    raise vp.ViceError(message)


def run_once_helper_bearing(image: Path, fs_root: Path, project_name: str, work_root: Path, shape: str) -> None:
    shutil.rmtree(work_root, ignore_errors=True)
    shutil.copytree(fs_root, work_root, copy_function=shutil.copy)
    project_root = prepare_helper_bearing_workspace(work_root, project_name, shape)

    last_exc: Exception | None = None
    for attempt in range(1, STAGE_ATTEMPTS + 1):
        try:
            vp.cleanup_stale_vice(settle_seconds=4.0)
            launch_direct.run_actc_phase(image, work_root, project_name)
            last_exc = None
            break
        except (vp.ViceError, RuntimeError) as exc:
            last_exc = exc
            if attempt == STAGE_ATTEMPTS:
                raise
            time.sleep(STAGE_ATTEMPT_DELAY)
    if last_exc is not None:
        raise last_exc
    verify_host_object(project_root, shape)

    prepare_link_workspace(work_root, project_root)

    last_exc: Exception | None = None
    for attempt in range(1, STAGE_ATTEMPTS + 1):
        try:
            vp.cleanup_stale_vice(settle_seconds=4.0)
            run_alink_phase(project_root)
            last_exc = None
            break
        except (vp.ViceError, RuntimeError) as exc:
            last_exc = exc
            if attempt == STAGE_ATTEMPTS:
                raise
            time.sleep(STAGE_ATTEMPT_DELAY)
    if last_exc is not None:
        raise last_exc
    verify_link_output(project_root, shape)
    run_avmrun_harness_phase(project_root, shape)
    stage_shell_sanity_avm(project_root)

    last_exc = None
    for attempt in range(1, STAGE_ATTEMPTS + 1):
        try:
            vp.cleanup_stale_vice(settle_seconds=4.0)
            run_avmrun_phase(image, work_root, project_name, shape)
            last_exc = None
            break
        except vp.ViceError as exc:
            last_exc = exc
            if attempt == STAGE_ATTEMPTS:
                raise
            time.sleep(STAGE_ATTEMPT_DELAY)
    if last_exc is not None:
        raise last_exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Run the helper-bearing ACTC -> ALINK -> AVMRUNC probe, validating compat AVMRUNC and then attempting the live nested replay'
    )
    parser.add_argument('--disk', required=True)
    parser.add_argument('--fs-root', required=True)
    parser.add_argument('--project', default='PROJ3')
    parser.add_argument('--shape', default=DEFAULT_SHAPE)
    parser.add_argument('--attempts', type=int, default=2)
    parser.add_argument('--attempt-delay', type=float, default=4.0)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()
    work_root = fs_root.parent / f'{fs_root.name}-actc-alink-avmrunc-direct'

    for attempt in range(1, args.attempts + 1):
        try:
            run_once_helper_bearing(image, fs_root, project_name, work_root, args.shape)
            return 0
        except (vp.ViceError, RuntimeError) as exc:
            if attempt == args.attempts:
                print(exc, file=sys.stderr)
                return 1
            time.sleep(args.attempt_delay)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
