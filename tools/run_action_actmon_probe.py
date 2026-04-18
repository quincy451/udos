#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import run_action_avmrun_probe as avm
import run_action_actc_probe as rcp
import vice_prg_probe as vp

ROOT = Path(__file__).resolve().parent
ACTION_ACTMON_BUILD = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "ACTMON.PRG"
BOOT_TIMEOUT = 15.0
BOOT_SETTLE = 0.0
POLL_INTERVAL = 0.5
INITIAL_SETTLE = 3.0
COMMAND_SETTLE = 2.0
SHELL_TIMEOUT = 20.0
PHASE_TIMEOUT = 210.0
FILESYSTEM_SETTLE = 1.0
PROJECT_SYNC_SETTLE = 2.0
CONNECT_DELAY = 10.0


class ProbeError(RuntimeError):
    pass


def debug_log(message: str) -> None:
    if not os.environ.get("ACTMON_PROBE_DEBUG"):
        return
    print(f"[actmon-probe] {message}", file=sys.stderr, flush=True)


def write_ascii(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("ascii"))


def write_project_state(project_root: Path, modules: list[tuple[str, str]], lowercase_workspace: bool) -> Path:
    lower_project_root = project_root.parent / project_root.name.lower()
    shutil.rmtree(project_root, ignore_errors=True)
    shutil.rmtree(lower_project_root, ignore_errors=True)
    src_root = project_root / rcp.host_name("SRC", lowercase_workspace)
    bin_root = project_root / rcp.host_name("BIN", lowercase_workspace)
    obj_root = project_root / rcp.host_name("OBJ", lowercase_workspace)
    src_root.mkdir(parents=True, exist_ok=True)
    bin_root.mkdir(exist_ok=True)
    obj_root.mkdir(exist_ok=True)

    write_ascii(project_root / rcp.host_name("README.TXT", lowercase_workspace), "ACTION PROJECT READY\n")
    write_ascii(
        project_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace),
        "D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF README.TXT\n",
    )
    write_ascii(bin_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), "")
    write_ascii(obj_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), "")

    manifest_lines = ["ACTION PROJECT", *[f"{module}.ACT" for module, _body in modules]]
    write_ascii(project_root / rcp.host_name("ACTION.PROJ", lowercase_workspace), "\r".join(manifest_lines) + "\r")
    write_ascii(
        src_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace),
        "".join(f"F {module}.ACT\n" for module, _body in modules),
    )

    expected = {rcp.host_name(f"{module}.ACT", lowercase_workspace) for module, _body in modules}
    for path in src_root.iterdir():
        if path.is_file() and path.name.lower().endswith(".act") and path.name not in expected:
            path.unlink()
    for module, body in modules:
        write_ascii(src_root / rcp.host_name(f"{module}.ACT", lowercase_workspace), body)
    return project_root


def default_stub_body(name: str) -> str:
    return f"PROC {name}()\rENDPROC\r"


def sync_latest_actmon_prg(fs_root: Path) -> None:
    if not ACTION_ACTMON_BUILD.is_file():
        return
    lowercase_workspace = rcp.detect_lowercase_workspace(fs_root)
    images_root = rcp.case_insensitive_child(fs_root, rcp.host_name("IMAGES", lowercase_workspace))
    action_root = rcp.case_insensitive_child(images_root, rcp.host_name("ACTION.DNP", lowercase_workspace))
    target = action_root / rcp.host_name("ACTMON.PRG", lowercase_workspace)
    if not target.parent.is_dir():
        return
    shutil.copy2(ACTION_ACTMON_BUILD, target)


def ensure_catalog_entries(path: Path, entries: list[str]) -> None:
    directory_lines: list[str] = []
    file_lines: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="ascii", errors="ignore").splitlines():
            entry = line.strip()
            if not entry:
                continue
            if entry.startswith("D "):
                directory_lines.append(entry)
            else:
                file_lines.append(entry)
    for entry in entries:
        target = directory_lines if entry.startswith("D ") else file_lines
        if entry not in target:
            target.append(entry)
    lines = directory_lines + file_lines
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="ascii")


def verify_manifest_entries(project_root: Path, required: list[str], absent: list[str]) -> None:
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    project_manifest = project_root / rcp.host_name("ACTION.PROJ", lowercase_workspace)
    if not project_manifest.is_file():
        raise ProbeError(f"expected host file {project_manifest} to exist")
    manifest_text = project_manifest.read_text(encoding="ascii", errors="ignore")
    missing = [entry for entry in required if entry not in manifest_text]
    if missing:
        raise ProbeError(f"expected host manifest {project_manifest} to contain {missing!r}")
    present = [entry for entry in absent if entry in manifest_text]
    if present:
        raise ProbeError(f"expected host manifest {project_manifest} to omit {present!r}")


def verify_source_contains(project_root: Path, module: str, fragment: str) -> None:
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    source_path = (
        project_root
        / rcp.host_name("SRC", lowercase_workspace)
        / rcp.host_name(f"{module}.ACT", lowercase_workspace)
    )
    if not source_path.is_file():
        raise ProbeError(f"expected host file {source_path} to exist")
    source_text = source_path.read_text(encoding="ascii", errors="ignore")
    if fragment not in source_text:
        raise ProbeError(f"expected host file {source_path} to contain {fragment!r}")


def verify_source_missing(project_root: Path, module: str) -> None:
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    source_path = (
        project_root
        / rcp.host_name("SRC", lowercase_workspace)
        / rcp.host_name(f"{module}.ACT", lowercase_workspace)
    )
    if source_path.exists():
        raise ProbeError(f"expected host path {source_path} to be absent")


def verify_host_state_after_ren(project_root: Path, add_module: str, old_module: str, new_module: str) -> None:
    verify_source_contains(project_root, new_module, "ENDPROC")
    verify_source_missing(project_root, old_module)
    verify_manifest_entries(
        project_root,
        ["ACTION PROJECT", "MAIN.ACT", f"{add_module}.ACT", f"{new_module}.ACT"],
        [f"{old_module}.ACT"],
    )


def verify_host_state_after_del(
    project_root: Path, renamed_module: str, copied_module: str, deleted_module: str, old_module: str
) -> None:
    verify_source_contains(project_root, renamed_module, "ENDPROC")
    verify_source_contains(project_root, copied_module, "ENDPROC")
    verify_source_missing(project_root, deleted_module)
    verify_manifest_entries(
        project_root,
        ["ACTION PROJECT", "MAIN.ACT", f"{renamed_module}.ACT", f"{copied_module}.ACT"],
        [f"{deleted_module}.ACT", f"{old_module}.ACT"],
    )


def cleanup_stale_vice() -> None:
    settle_seconds = 5.0
    debug_log(f"cleanup_stale_vice settle={settle_seconds}")
    vp.cleanup_stale_vice(settle_seconds=settle_seconds)


def copytree_workspace(src_root: Path, dst_root: Path) -> None:
    debug_log(f"copytree {src_root} -> {dst_root}")
    shutil.rmtree(dst_root, ignore_errors=True)
    shutil.copytree(src_root, dst_root)


def restore_clean_workspace(baseline_root: Path, fs_root: Path) -> None:
    debug_log(f"restore_clean_workspace baseline={baseline_root} fs_root={fs_root}")
    copytree_workspace(baseline_root, fs_root)


def prepare_workspace(fs_root: Path, project_name: str, modules: list[tuple[str, str]]) -> Path:
    debug_log(f"prepare_workspace fs_root={fs_root} project={project_name} modules={len(modules)}")
    lowercase_workspace = rcp.detect_lowercase_workspace(fs_root)
    images_root = rcp.case_insensitive_child(fs_root, rcp.host_name("IMAGES", lowercase_workspace))
    action_root = rcp.case_insensitive_child(images_root, rcp.host_name("ACTION.DNP", lowercase_workspace))
    project_root = write_project_state(
        action_root / rcp.host_name(project_name.upper(), lowercase_workspace),
        modules,
        lowercase_workspace,
    )
    sync_latest_actmon_prg(fs_root)
    root_actmon = action_root / rcp.host_name("ACTMON.PRG", lowercase_workspace)
    if root_actmon.is_file():
        shutil.copy2(root_actmon, project_root / rcp.host_name("ACTMON.PRG", lowercase_workspace))
        ensure_catalog_entries(project_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace), ["F ACTMON.PRG"])
    ensure_catalog_entries(
        action_root / rcp.host_name("UDOSDIR.TXT", lowercase_workspace),
        [f"D {project_name.upper()}", "F ACTMON.PRG"],
    )
    debug_log(f"prepare_workspace done project_root={project_root}")
    return project_root


def run_phase(
    *,
    image: Path,
    baseline_root: Path,
    fs_root: Path,
    project_name: str,
    modules: list[tuple[str, str]],
    command: str,
    run_marker: str,
    fragments: list[str],
    post_command: str | None = None,
    post_done_fragment: str | None = None,
    attempts: int,
    attempt_delay: float,
) -> tuple[str, Path]:
    project_prompt = f"B:DNP/{project_name.upper()}>"
    runner = ROOT / "run_action_avmrun_probe.py"
    last_error: str | None = None
    for attempt in range(1, attempts + 1):
        debug_log(f"phase start command={command!r} attempt={attempt}/{attempts}")
        cleanup_stale_vice()
        restore_clean_workspace(baseline_root, fs_root)
        time.sleep(FILESYSTEM_SETTLE)
        project_root = prepare_workspace(fs_root, project_name, modules)
        time.sleep(PROJECT_SYNC_SETTLE)

        phase_args = [
            sys.executable,
            str(runner),
            "--disk",
            str(image),
            "--fs-root",
            str(fs_root),
            "--command",
            command,
            "--run-marker",
            run_marker,
            "--done-fragment",
            "",
            "--b-prompt",
            "B:DNP/>",
            "--final-prompt",
            project_prompt,
            "--attempts",
            "1",
            "--attempt-delay",
            "0",
            "--connect-delay",
            str(CONNECT_DELAY),
            "--boot-timeout",
            str(max(30.0, BOOT_TIMEOUT)),
            "--initial-settle",
            str(INITIAL_SETTLE),
            "--command-settle",
            str(COMMAND_SETTLE),
            "--shell-timeout",
            str(SHELL_TIMEOUT),
            "--pre-command",
            f"CD {project_name.upper()}",
            "--pre-prompt",
            project_prompt,
        ]
        for fragment in fragments:
            phase_args.extend(["--contains", fragment])
        if post_command:
            phase_args.extend(["--post-command", post_command])
        if post_done_fragment is not None:
            phase_args.extend(["--post-done-fragment", post_done_fragment])

        debug_log(f"phase launch command={command!r} cwd={ROOT}")
        result = subprocess.run(
            phase_args,
            capture_output=True,
            text=True,
            timeout=PHASE_TIMEOUT,
            check=False,
            cwd=ROOT,
        )
        debug_log(
            f"phase done command={command!r} rc={result.returncode} "
            f"stdout_len={len(result.stdout)} stderr_len={len(result.stderr)}"
        )
        if result.returncode == 0:
            screen = result.stdout.rstrip()
            if not screen:
                raise ProbeError(f"phase {command!r} returned no screen output")
            cleanup_stale_vice()
            return screen, project_root
        last_error = result.stderr.strip() or result.stdout.strip() or f"phase {command!r} failed with exit {result.returncode}"
        if attempt < attempts:
            time.sleep(max(0.0, attempt_delay))
    raise ProbeError(last_error or f"phase {command!r} failed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a focused ACTMON proof through sequenced VICE sessions")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--add-module", default="EXTRA")
    parser.add_argument("--rename-source", default="HELPER")
    parser.add_argument("--rename-module", default="NEW")
    parser.add_argument("--copy-module", default="CLONE")
    parser.add_argument("--delete-module", default="EXTRA")
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--attempt-delay", type=float, default=1.0)
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    source_fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()
    add_module = args.add_module.upper()
    rename_source = args.rename_source.upper()
    rename_module = args.rename_module.upper()
    copy_module = args.copy_module.upper()
    delete_module = args.delete_module.upper()

    last_error: Exception | None = None
    try:
        debug_log(f"main start disk={image} source_fs_root={source_fs_root} project={project_name}")
        cleanup_stale_vice()
        baseline_root = source_fs_root.parent / f"{source_fs_root.name}-actmon-baseline"
        shutil.rmtree(baseline_root, ignore_errors=True)
        copytree_workspace(source_fs_root, baseline_root)
        fs_root = source_fs_root.parent / f"{source_fs_root.name}-actmon-work"
        debug_log(f"main baseline prepared baseline_root={baseline_root} fs_root={fs_root}")

        initial_modules = [
            ("MAIN", default_stub_body("MAIN")),
            ("HELPER", "PROC OLDHELPER()\rENDPROC\r"),
        ]
        after_rename_modules = [
            ("MAIN", default_stub_body("MAIN")),
            (rename_module, "PROC OLDHELPER()\rENDPROC\r"),
            (add_module, default_stub_body(add_module)),
        ]

        _screen, project_root = run_phase(
            image=image,
            baseline_root=baseline_root,
            fs_root=fs_root,
            project_name=project_name,
            modules=initial_modules,
            command=f"ACTMON.PRG ADD {add_module}",
            run_marker="",
            fragments=["CREATED", "ACTMON OK"],
            post_command=f"ACTMON.PRG REN {rename_source} {rename_module}",
            post_done_fragment="RENAMED",
            attempts=args.attempts,
            attempt_delay=args.attempt_delay,
        )
        verify_host_state_after_ren(project_root, add_module, rename_source, rename_module)

        _screen, project_root = run_phase(
            image=image,
            baseline_root=baseline_root,
            fs_root=fs_root,
            project_name=project_name,
            modules=after_rename_modules,
            command=f"ACTMON.PRG COPY {rename_module} {copy_module}",
            run_marker="",
            fragments=["COPIED", "ACTMON OK"],
            post_command=f"ACTMON.PRG DEL {delete_module}",
            post_done_fragment="REMOVED",
            attempts=args.attempts,
            attempt_delay=args.attempt_delay,
        )
        verify_host_state_after_del(project_root, rename_module, copy_module, delete_module, rename_source)
        shutil.rmtree(baseline_root, ignore_errors=True)
        cleanup_stale_vice()
        debug_log("main success")
        return 0
    except Exception as exc:
        last_error = exc
        debug_log(f"main failure: {exc}")
    cleanup_stale_vice()
    print(str(last_error), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
