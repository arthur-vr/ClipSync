#!/usr/bin/env python3
"""Build a versioned Blender add-on ZIP in the repository's parent directory."""

from __future__ import annotations

import argparse
import re
import subprocess
import tomllib
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
    manifest_path = repo_root / "blender_manifest.toml"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Blender manifest not found: {manifest_path}")

    with manifest_path.open("rb") as manifest_file:
        manifest = tomllib.load(manifest_file)

    name = safe_component(str(manifest["name"]), "manifest name")
    version = safe_component(str(manifest["version"]), "manifest version")
    suffix = safe_component(args.short_string or git_short_sha(repo_root), "short string")
    output_dir = (args.output_dir or repo_root.parent).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"{name}_{version}-{suffix}.zip"

    files = package_files(repo_root)
    if not files:
        raise RuntimeError(f"No files found to package under {repo_root}")

    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in files:
            archive.write(path, path.relative_to(repo_root).as_posix())

    print(f"Archive: {archive_path}")
    print(f"Files: {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
