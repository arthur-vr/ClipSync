#!/usr/bin/env python3
"""Build a versioned Blender add-on ZIP in the repository's parent directory."""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import zipfile
from pathlib import Path


EXCLUDED_DIRS = {
    ".agent",
    ".git",
    ".github",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "docs",
    "images",
    "skills",
    "tests",
}
EXCLUDED_FILES = {".gitignore", "AGENTS.md", "CLAUDE.md"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}


def safe_component(value: str, label: str) -> str:
    """Return a filename-safe component while keeping common release punctuation."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip(".-_")
    if not cleaned:
        raise ValueError(f"{label} does not contain any filename-safe characters")
    return cleaned


def git_short_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def package_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        relative = path.relative_to(repo_root)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if (
            path.is_file()
            and path.name not in EXCLUDED_FILES
            and path.suffix.lower() not in EXCLUDED_SUFFIXES
        ):
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(repo_root).as_posix())


def addon_metadata(init_path: Path) -> tuple[str, str, str]:
    """Read the add-on name and version from the legacy ``bl_info`` dictionary."""
    tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
    bl_info = None
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "bl_info" for target in node.targets)
        ):
            bl_info = ast.literal_eval(node.value)
            break
    if not isinstance(bl_info, dict):
        raise ValueError("Could not read bl_info from {}".format(init_path))

    name = safe_component(str(bl_info["name"]), "bl_info name")
    version_tuple = bl_info["version"]
    if (
        not isinstance(version_tuple, tuple)
        or len(version_tuple) != 3
        or not all(isinstance(part, int) and part >= 0 for part in version_tuple)
    ):
        raise ValueError("bl_info version must be a three-part integer tuple")
    version = ".".join(str(part) for part in version_tuple)
    return name, version, name.lower()


def release_name(constants_path: Path) -> str:
    """Read the human-readable release name used in archive filenames."""
    tree = ast.parse(
        constants_path.read_text(encoding="utf-8"), filename=str(constants_path)
    )
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "VERSION_NAME"
                for target in node.targets
            )
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, str):
                return safe_component(value, "VERSION_NAME")
    raise ValueError("Could not read VERSION_NAME from {}".format(constants_path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--short-string",
        help="Filename suffix; defaults to the current Git commit's short SHA.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory; defaults to one level above the repository.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    name, version, addon_directory = addon_metadata(repo_root / "__init__.py")
    release = release_name(repo_root / "constants.py")
    suffix = safe_component(args.short_string or git_short_sha(repo_root), "short string")
    output_dir = (args.output_dir or repo_root.parent).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_suffix = f"{name}_{version}-{release}-{suffix}"
    archive_path = output_dir / f"{archive_suffix}.zip"

    files = package_files(repo_root)
    if not files:
        raise RuntimeError(f"No files found to package under {repo_root}")

    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in files:
            relative_path = path.relative_to(repo_root).as_posix()
            # Legacy Blender installs extract the ZIP into scripts/addons.
            # A single package directory prevents each module from being
            # registered as an independent, fake add-on.
            relative_path = f"{addon_directory}/{relative_path}"
            archive.write(path, relative_path)

    print(f"Archive: {archive_path}")
    print(f"Files: {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
