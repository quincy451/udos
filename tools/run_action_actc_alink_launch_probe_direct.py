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
STAGE_ATTEMPTS = 3
STAGE_ATTEMPT_DELAY = 2.0


def install_program(fs_root: Path, project_root: Path, build_path: Path, name: str) -> None:
    if not build_path.is_file():
        raise RuntimeError(f"missing built program: {build_path}")
    lowercase_workspace = rcp.detect_lowercase_workspace(fs_root)
    images_root = rcp.case_insensitive_child(fs_root, rcp.host_name("IMAGES", lowercase_workspace))
    action_root = rcp.case_insensitive_child(images_root, rcp.host_name("ACTION.DNP", lowercase_workspace))
    root_target = action_root / rcp.host_name(name, lowercase_workspace)
    shutil.copy2(build_path, root_target)
    shutil.copy2(root_target, project_root / rcp.host_name(name, lowercase_workspace))
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


def stage_runtime_module_closure(project_root: Path) -> None:
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    obj_root = project_root / rcp.host_name("OBJ", lowercase_workspace)
    lib_root = project_root / rcp.host_name("LIB", lowercase_workspace)
    pending: list[str] = []
    seen: set[str] = set()
    copied_entries: list[str] = []

    for obj_path in sorted(obj_root.glob("*.[Oo][Bb][Jj]")):
        text = obj_path.read_text(encoding="ascii", errors="ignore")
        pending.extend(sorted(object_imports_from_text(text)))

    while pending:
        name = pending.pop(0)
        if name in seen:
            continue
        seen.add(name)
        source_path = UDOS_RUNTIME_MODULES / f"{name}.avo"
        if not source_path.is_file():
            continue
        lib_root.mkdir(parents=True, exist_ok=True)
        target_name = name.upper() + ".OBJ"
        target_path = lib_root / rcp.host_name(target_name, lowercase_workspace)
        shutil.copy2(source_path, target_path)
        copied_entries.append(f"F {target_name}")
        module_text = source_path.read_text(encoding="ascii", errors="ignore")
        for imported_name in sorted(object_imports_from_text(module_text)):
            if imported_name not in seen:
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
        obj_root = project_root / rcp.host_name("OBJ", lowercase_workspace)
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
        lib_root = project_root / rcp.host_name("LIB", lowercase_workspace)
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


def prepare_workspace(fs_root: Path, project_name: str, shape: str) -> tuple[Path, str]:
    case = rpp.direct_prg_case(shape)
    source = case.get("source")
    if not isinstance(source, str):
        raise RuntimeError(f"shape {shape} is not ACTC-compilable")

    project_root = rcp.prepare_workspace(fs_root, project_name)
    lowercase_workspace = rcp.detect_lowercase_workspace(fs_root)
    images_root = rcp.case_insensitive_child(fs_root, rcp.host_name("IMAGES", lowercase_workspace))
    action_root = rcp.case_insensitive_child(images_root, rcp.host_name("ACTION.DNP", lowercase_workspace))
    src_root = project_root / rcp.host_name("SRC", lowercase_workspace)
    bin_root = project_root / rcp.host_name("BIN", lowercase_workspace)
    obj_root = project_root / rcp.host_name("OBJ", lowercase_workspace)

    rcp.write_ascii(src_root / rcp.host_name("MAIN.ACT", lowercase_workspace), source)
    rcp.write_ascii(src_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), "F MAIN.ACT\n")
    rcp.write_ascii(bin_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), "")
    rcp.write_ascii(obj_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), "")

    for stale_name in ("MAIN.PRG", "MAIN.AVM", "main.prg", "main.avm"):
        (project_root / stale_name).unlink(missing_ok=True)
        (bin_root / stale_name).unlink(missing_ok=True)

    install_program(fs_root, project_root, ACTION_ALINK_BUILD, "ALINK.PRG")
    mount_path = f"/{images_root.name}/{action_root.name}"
    return project_root, mount_path


def run_actc_phase(image: Path, work_root: Path, project_name: str) -> None:
    lowercase_workspace = rcp.detect_lowercase_workspace(work_root)
    output_path = (
        work_root
        / rcp.host_name("IMAGES", lowercase_workspace)
        / rcp.host_name("ACTION.DNP", lowercase_workspace)
        / rcp.host_name(project_name, lowercase_workspace)
        / rcp.host_name("OBJ", lowercase_workspace)
        / rcp.host_name("MAIN.OBJ", lowercase_workspace)
    )
    cmd = [
        str(TOOL_ABI_HARNESS),
        "--prg",
        str(ACTC_PRG),
        "--workspace",
        str(
            work_root
            / rcp.host_name("IMAGES", lowercase_workspace)
            / rcp.host_name("ACTION.DNP", lowercase_workspace)
            / rcp.host_name(project_name, lowercase_workspace)
        ),
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
        raise RuntimeError(f"ACTC harness phase completed without expected host output {output_path}")


def run_alink_phase(project_root: Path) -> None:
    try:
        rpp.run_harness(ACTION_ALINK_BUILD, ACTION_ALINK_LABELS, project_root)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ALINK harness phase timed out after 120s") from exc
    except RuntimeError as exc:
        raise RuntimeError(str(exc)) from exc


def verify_link_output(project_root: Path, shape: str) -> Path:
    prg_path = rpp.verify_host_output(project_root, shape)
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    avm_path = project_root / rcp.host_name("BIN", lowercase_workspace) / rcp.host_name("MAIN.AVM", lowercase_workspace)
    if avm_path.exists():
        raise RuntimeError(f"unexpected AVM output for helper-free direct PRG probe: {avm_path}")
    return prg_path


def run_once(image: Path, fs_root: Path, project_name: str, work_root: Path, shape: str) -> None:
    shutil.rmtree(work_root, ignore_errors=True)
    shutil.copytree(fs_root, work_root, copy_function=shutil.copy)
    project_root, mount_path = prepare_workspace(work_root, project_name, shape)

    last_exc: Exception | None = None
    for attempt in range(1, STAGE_ATTEMPTS + 1):
        try:
            vp.cleanup_stale_vice(settle_seconds=STAGE_ATTEMPT_DELAY)
            run_actc_phase(image, work_root, project_name)
            stage_case_objects(project_root, shape)
            stage_runtime_module_closure(project_root)
            run_alink_phase(project_root)
            prg_path = verify_link_output(project_root, shape)
            rpp.run_prg_phase(image, work_root, project_name, mount_path, PRG_CONNECT_DELAY, prg_path, shape)
            return
        except (vp.ViceError, RuntimeError, subprocess.SubprocessError) as exc:
            last_exc = exc
            if attempt == STAGE_ATTEMPTS:
                break
            time.sleep(STAGE_ATTEMPT_DELAY)
    if last_exc is None:
        raise RuntimeError("probe failed without an exception")
    raise last_exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ACTC -> ALINK -> helper-free launch proof through direct MAIN.PRG")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--shape", default="if_else_local_call_chain_nested_do_if_else")
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()
    work_root = fs_root.parent / f"{fs_root.name}-actc-alink-launch"

    try:
        run_once(image, fs_root, project_name, work_root, args.shape)
    except Exception as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
