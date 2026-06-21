#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

import run_action_actc_probe as rcp
import run_action_alink_prg_probe as rpp
import vice_prg_probe as vp


ROOT = Path(__file__).resolve().parent
ACTION_ROOT = ROOT.parent.parent / "actionc64u"
ACTC_PRG = ACTION_ROOT / "build" / "udos_tools" / "ACTC.PRG"
TOOL_ABI_HARNESS = ACTION_ROOT / "build" / "udos_tools" / "tool_abi_harness"
UDOS_SERVICES_INC = ACTION_ROOT / "build" / "udos_tools" / "udos_services.inc"
ACTC_LABELS = ACTION_ROOT / "build" / "udos_tools" / "actc.current.labels"
ACTION_ALINK_BUILD = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "ALINK.PRG"
ACTION_ALINK_LABELS = ACTION_ROOT / "build" / "udos_tools" / "alink.current.labels"
UDOS_RUNTIME_MODULES = ACTION_ROOT / "src" / "runtime" / "udos_modules"
PRG_CONNECT_DELAY = rpp.CONNECT_DELAYS[0]
DEFAULT_STAGE_ATTEMPTS = 6
DEFAULT_STAGE_ATTEMPT_DELAY = 2.0


def install_program(fs_root: Path, project_root: Path, build_path: Path, name: str) -> None:
    if not build_path.is_file():
        raise RuntimeError(f"missing built program: {build_path}")
    lowercase_workspace = rcp.detect_lowercase_workspace(fs_root)
    images_root = rcp.case_insensitive_child(fs_root, rcp.host_name("IMAGES", lowercase_workspace))
    action_root = rcp.case_insensitive_child(images_root, rcp.host_name("ACTION.DNP", lowercase_workspace))
    root_target = action_root / rcp.host_name(name, lowercase_workspace)
    shutil.copy2(build_path, root_target)
    rcp.sync_case_siblings(root_target)
    project_target = project_root / name
    shutil.copy2(root_target, project_target)
    rcp.sync_case_siblings(project_target)
    rcp.ensure_catalog_entries(
        action_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace),
        [f"D {project_root.name.upper()}", f"F {name}"],
    )
    rcp.ensure_catalog_entries(project_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), [f"F {name}"])


def object_imports_from_text(text: str) -> set[str]:
    imports: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("u "):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1]:
            imports.add(parts[1].strip().lower())
    return imports


def stage_runtime_module_closure(project_root: Path, shape: str) -> None:
    case = rpp.direct_prg_case(shape)
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    obj_root = rcp.case_insensitive_child(project_root, "OBJ")
    lib_root = rcp.case_insensitive_child(project_root, "LIB")
    pending: list[str] = []
    expanded: set[str] = set()
    copied: set[str] = set()
    copied_entries: list[str] = []

    def copy_runtime_module(name: str, *, required: bool = False) -> bool:
        source_path = UDOS_RUNTIME_MODULES / f"{name}.obj"
        if not source_path.is_file():
            if required:
                raise RuntimeError(f"missing runtime OBJ module: {source_path}")
            return False
        lib_root.mkdir(parents=True, exist_ok=True)
        target_name = name.upper() + ".OBJ"
        if name not in copied:
            target_path = lib_root / rcp.host_name(target_name, lowercase_workspace)
            shutil.copy2(source_path, target_path)
            rcp.sync_case_siblings(target_path)
            copied.add(name)
            copied_entries.append(f"F {target_name}")
        return True

    available_modules = case.get("runtime_library_objects", [])
    if isinstance(available_modules, list):
        for module_name in available_modules:
            if isinstance(module_name, str) and module_name:
                copy_runtime_module(module_name.lower(), required=True)

    for obj_path in sorted(obj_root.glob("*.[Oo][Bb][Jj]")):
        text = obj_path.read_text(encoding="ascii", errors="ignore")
        pending.extend(sorted(object_imports_from_text(text)))

    while pending:
        name = pending.pop(0)
        if name in expanded:
            continue
        expanded.add(name)
        if not copy_runtime_module(name):
            continue
        module_text = (UDOS_RUNTIME_MODULES / f"{name}.obj").read_text(encoding="ascii", errors="ignore")
        for imported_name in sorted(object_imports_from_text(module_text)):
            if imported_name not in expanded:
                pending.append(imported_name)

    if copied_entries:
        rcp.ensure_catalog_entries(lib_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), copied_entries)
        rcp.ensure_catalog_entries(project_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), ["D LIB"])


def stage_case_objects(project_root: Path, shape: str) -> None:
    case = rpp.direct_prg_case(shape)
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    staged_any = False

    extra_project_objects = case.get("extra_objects", {})
    if isinstance(extra_project_objects, dict) and extra_project_objects:
        obj_root = rcp.case_insensitive_child(project_root, "OBJ")
        entries: list[str] = []
        for name, text in extra_project_objects.items():
            if not isinstance(name, str) or not name:
                continue
            if not isinstance(text, str):
                continue
            target = obj_root / rcp.host_name(name, lowercase_workspace)
            rcp.write_ascii(target, text)
            entries.append(f"F {name.upper()}")
        if entries:
            rcp.ensure_catalog_entries(obj_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), entries)
            staged_any = True

    extra_library_objects = case.get("extra_library_objects", {})
    if isinstance(extra_library_objects, dict) and extra_library_objects:
        lib_root = rcp.case_insensitive_child(project_root, "LIB")
        lib_root.mkdir(parents=True, exist_ok=True)
        entries = []
        for name, text in extra_library_objects.items():
            if not isinstance(name, str) or not name:
                continue
            if not isinstance(text, str):
                continue
            target = lib_root / rcp.host_name(name, lowercase_workspace)
            rcp.write_ascii(target, text)
            entries.append(f"F {name.upper()}")
        if entries:
            rcp.ensure_catalog_entries(lib_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), entries)
            rcp.ensure_catalog_entries(project_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), ["D LIB"])
            staged_any = True

    if not staged_any:
        return


def read_source_override(fs_root: Path, source_from: str) -> str:
    source_path = fs_root / source_from.lstrip("/")
    if not source_path.is_file():
        raise RuntimeError(f"missing source override: {source_path}")
    return source_path.read_text(encoding="ascii").replace("\r\n", "\n").replace("\n", "\r")


def prepare_workspace(
    fs_root: Path,
    project_name: str,
    shape: str,
    *,
    source_from: str | None = None,
) -> tuple[Path, str]:
    case = rpp.direct_prg_case(shape)
    source = read_source_override(fs_root, source_from) if source_from else case.get("source")
    if not isinstance(source, str):
        raise RuntimeError(f"shape {shape} is not ACTC-compilable")
    if source and not source.endswith("\r"):
        source += "\r"

    project_root = rcp.prepare_workspace(fs_root, project_name)
    lowercase_workspace = rcp.detect_lowercase_workspace(fs_root)
    images_root = rcp.case_insensitive_child(fs_root, rcp.host_name("IMAGES", lowercase_workspace))
    action_root = rcp.case_insensitive_child(images_root, rcp.host_name("ACTION.DNP", lowercase_workspace))
    src_root = rcp.case_insensitive_child(project_root, "SRC")
    bin_root = rcp.case_insensitive_child(project_root, "BIN")
    obj_root = rcp.case_insensitive_child(project_root, "OBJ")

    rcp.write_ascii(src_root / rcp.host_name("MAIN.ACT", lowercase_workspace), source)
    rcp.write_ascii(src_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), "F MAIN.ACT\n")
    rcp.write_ascii(bin_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), "")
    rcp.write_ascii(obj_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), "")

    for stale_name in ("MAIN.PRG", "main.prg"):
        (project_root / stale_name).unlink(missing_ok=True)
        (bin_root / stale_name).unlink(missing_ok=True)

    install_program(fs_root, project_root, ACTION_ALINK_BUILD, "ALINK.PRG")
    rcp.add_case_aliases(project_root)
    mount_path = f"/{images_root.name}/{action_root.name}"
    return project_root, mount_path


def run_actc_phase(image: Path, work_root: Path, project_name: str, project_root: Path) -> None:
    output_path = rcp.project_output_path(project_root, "OBJ", "MAIN.OBJ")
    cmd = [
        str(TOOL_ABI_HARNESS),
        "--prg",
        str(ACTC_PRG),
        "--workspace",
        str(project_root),
        "--cmdline",
        "MAIN",
        "--services-inc",
        str(UDOS_SERVICES_INC),
        "--labels",
        str(ACTC_LABELS),
        "--max-steps",
        "12000000",
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ACTC harness phase timed out after 120s") from exc
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or "ACTC harness phase failed"
        raise RuntimeError(details)
    if not output_path.is_file() or output_path.stat().st_size == 0:
        actual_output_path = rcp.project_output_path(project_root, "OBJ", "MAIN.OBJ")
        if not actual_output_path.is_file() or actual_output_path.stat().st_size == 0:
            raise RuntimeError(f"ACTC harness phase completed without expected host output {actual_output_path}")


def run_alink_phase(project_root: Path) -> dict[str, object]:
    try:
        return rpp.run_harness(ACTION_ALINK_BUILD, ACTION_ALINK_LABELS, project_root)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ALINK harness phase timed out after 120s") from exc
    except RuntimeError as exc:
        raise RuntimeError(str(exc)) from exc


def verify_alink_dependency_loads(summary: dict[str, object], shape: str) -> None:
    case = rpp.direct_prg_case(shape)
    expected_loads = case.get("expected_alink_loads", [])
    unexpected_loads = case.get("unexpected_alink_loads", [])
    if (
        (not isinstance(expected_loads, list) or not expected_loads)
        and (not isinstance(unexpected_loads, list) or not unexpected_loads)
    ):
        return
    ops = summary.get("ops", [])
    if not isinstance(ops, list):
        raise RuntimeError("ALINK harness summary did not include file operations")
    loaded_paths: set[str] = set()
    for op in ops:
        if not isinstance(op, dict):
            continue
        path = op.get("path")
        if isinstance(path, str):
            loaded_paths.add(path.upper())
    missing = [
        path
        for path in expected_loads
        if isinstance(path, str) and path.upper() not in loaded_paths
    ]
    if missing:
        raise RuntimeError(f"ALINK did not load expected dependency objects: {missing}")
    unexpected = [
        path
        for path in unexpected_loads
        if isinstance(path, str) and path.upper() in loaded_paths
    ]
    if unexpected:
        raise RuntimeError(f"ALINK loaded unexpected dependency objects: {unexpected}")


def verify_link_output(project_root: Path, shape: str) -> Path:
    prg_path = rpp.verify_host_output(project_root, shape)
    return prg_path


def run_once(
    image: Path,
    fs_root: Path,
    project_name: str,
    work_root: Path,
    shape: str,
    *,
    source_from: str | None = None,
    attempts: int = DEFAULT_STAGE_ATTEMPTS,
    attempt_delay: float = DEFAULT_STAGE_ATTEMPT_DELAY,
) -> None:
    shutil.rmtree(work_root, ignore_errors=True)
    shutil.copytree(fs_root, work_root, symlinks=True, copy_function=shutil.copy)
    project_root, mount_path = prepare_workspace(work_root, project_name, shape, source_from=source_from)
    rpp.stage_case_files(project_root, shape)
    rcp.add_case_aliases(project_root)

    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            vp.cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, attempt_delay)))
            run_actc_phase(image, work_root, project_name, project_root)
            rcp.add_case_aliases(project_root)
            rpp.verify_actc_object_output(project_root, shape)
            stage_case_objects(project_root, shape)
            stage_runtime_module_closure(project_root, shape)
            rcp.add_case_aliases(project_root)
            alink_summary = run_alink_phase(project_root)
            verify_alink_dependency_loads(alink_summary, shape)
            prg_path = verify_link_output(project_root, shape)
            rpp.ensure_host_prg_catalog(project_root)
            if bool(rpp.direct_prg_case(shape).get("spin_after_marker_for_live", False)):
                rpp.patch_prg_to_spin_after_marker(prg_path)
            rpp.run_prg_phase(image, work_root, project_name, mount_path, PRG_CONNECT_DELAY, prg_path, shape)
            return
        except (vp.ViceError, RuntimeError, subprocess.SubprocessError) as exc:
            last_exc = exc
            if attempt == attempts:
                break
            time.sleep(max(0.0, attempt_delay))
    if last_exc is None:
        raise RuntimeError("probe failed without an exception")
    raise last_exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ACTC -> ALINK launch proof through direct MAIN.PRG")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--shape", default="if_else_local_call_chain_nested_do_if_else")
    parser.add_argument("--source-from", help="read MAIN.ACT source from this path inside the copied fs root")
    parser.add_argument("--attempts", type=int, default=DEFAULT_STAGE_ATTEMPTS)
    parser.add_argument("--attempt-delay", type=float, default=DEFAULT_STAGE_ATTEMPT_DELAY)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()
    work_root = fs_root.parent / f"{fs_root.name}-actc-alink-launch"

    try:
        run_once(
            image,
            fs_root,
            project_name,
            work_root,
            args.shape,
            source_from=args.source_from,
            attempts=max(1, args.attempts),
            attempt_delay=args.attempt_delay,
        )
    except Exception as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
