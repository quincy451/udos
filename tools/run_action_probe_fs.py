#!/usr/bin/env python3
from __future__ import annotations

import itertools
import shutil
from pathlib import Path


def case_insensitive_child(parent: Path, name: str) -> Path:
    exact = parent / name
    if exact.exists():
        return exact
    target_name = name.lower()
    for child in parent.iterdir():
        if child.name.lower() == target_name:
            return child
    return parent / name


def detect_lowercase_workspace(fs_root: Path) -> bool:
    images = fs_root / "images"
    if not images.exists():
        images = case_insensitive_child(fs_root, "IMAGES")
    action_dnp = images / "action.dnp"
    if not action_dnp.exists():
        action_dnp = case_insensitive_child(images, "ACTION.DNP")
    return images.name.islower() or action_dnp.name.islower()


def host_name(name: str, lowercase_workspace: bool) -> str:
    return name.lower() if lowercase_workspace else name


def ensure_relative_symlink(alias: Path, target_name: str, *, is_dir: bool = False) -> None:
    if alias.exists() or alias.is_symlink():
        try:
            if alias.is_symlink() and alias.readlink() == Path(target_name):
                return
        except OSError:
            pass
        if alias.is_dir() and not alias.is_symlink():
            shutil.rmtree(alias)
        else:
            alias.unlink()
    alias.symlink_to(target_name, target_is_directory=is_dir)


def case_name_variants(name: str) -> list[str]:
    variants: list[str] = []
    for candidate in (name, name.lower(), name.upper()):
        if candidate not in variants:
            variants.append(candidate)
    return variants


def copy_file_alias(source: Path, alias: Path) -> None:
    if alias == source:
        return
    if alias.exists() and source.exists():
        try:
            if alias.samefile(source):
                return
        except OSError:
            pass
    if alias.is_dir():
        return
    if alias.exists() or alias.is_symlink():
        alias.unlink()
    alias.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, alias)


def sync_case_siblings(path: Path) -> None:
    if not path.is_file():
        return
    for alias_name in case_name_variants(path.name):
        copy_file_alias(path, path.with_name(alias_name))


def sync_case_path_variants(root: Path, path: Path) -> None:
    """Copy one authoritative file across every path-component case variant."""
    if not path.is_file():
        return
    rel_parts = path.relative_to(root).parts
    for variant_parts in itertools.product(
        *(case_name_variants(part) for part in rel_parts)
    ):
        copy_file_alias(path, root.joinpath(*variant_parts))


def add_case_aliases(root: Path) -> None:
    """Materialize upper/lower path variants for VICE fsdevice on Linux."""
    paths = [path for path in root.rglob("*") if not path.is_symlink()]
    dirs = sorted((path for path in paths if path.is_dir()), key=lambda item: len(item.parts))
    files = sorted((path for path in paths if path.is_file()), key=lambda item: len(item.parts))
    for directory in dirs:
        rel_parts = directory.relative_to(root).parts
        for variant_parts in itertools.product(*(case_name_variants(part) for part in rel_parts)):
            alias_dir = root.joinpath(*variant_parts)
            if alias_dir.exists() and not alias_dir.is_dir():
                alias_dir.unlink()
            alias_dir.mkdir(parents=True, exist_ok=True)
    for file_path in files:
        sync_case_path_variants(root, file_path)


def write_ascii(path: Path, text: str, *, sync_case: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("ascii"))
    if sync_case:
        sync_case_siblings(path)


def ensure_catalog_entries(path: Path, entries: list[str], *, sync_case: bool = True) -> None:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="ascii")
    if sync_case:
        sync_case_siblings(path)


def project_output_path(project_root: Path, directory: str, filename: str) -> Path:
    directory_name = directory.lower()
    filename_name = filename.lower()
    if project_root.exists():
        for candidate_dir in project_root.iterdir():
            if not candidate_dir.is_dir() or candidate_dir.name.lower() != directory_name:
                continue
            for candidate_file in candidate_dir.iterdir():
                if candidate_file.name.lower() == filename_name:
                    return candidate_file
    output_dir = case_insensitive_child(project_root, directory)
    return output_dir / filename
