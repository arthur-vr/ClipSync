#!/usr/bin/env python3
"""Synchronize ClipSync's release version across source and documentation."""

import argparse
import re
import sys
from pathlib import Path


VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
RELEASE_NAME_RE = re.compile(
    r'^VERSION_NAME\s*=\s*"(?P<name>[A-Za-z0-9._-]+)"$', re.MULTILINE
)


def read_source(path):
    """Read text without normalizing CRLF or LF line endings."""
    with path.open("r", encoding="utf-8", newline="") as source_file:
        return source_file.read()


def write_source(path, source):
    """Write text exactly as supplied, preserving the source line endings."""
    with path.open("w", encoding="utf-8", newline="") as source_file:
        source_file.write(source)


def replace_or_fail(path, pattern, replacement, version, dry_run):
    source = read_source(path)
    updated, replacements = pattern.subn(replacement, source)
    if replacements == 0:
        raise ValueError("No version reference found in {}".format(path))
    if updated == source:
        print("Unchanged: {}".format(path))
        return
    print("{}: {} reference(s)".format(path, replacements))
    if not dry_run:
        write_source(path, updated)


def version_targets(repo_root, version, release_name):
    escaped_release_name = re.escape(release_name)
    return (
        (
            repo_root / "__init__.py",
            re.compile(
                r'^(\s*"version"\s*:\s*\()\d+\s*,\s*\d+\s*,\s*\d+(\s*\),\s*)$',
                re.MULTILINE,
            ),
            r"\g<1>{}\g<2>".format(version.replace(".", ", ")),
        ),
        (
            repo_root / "constants.py",
            re.compile(
                r'^(VERSION_STRING\s*=\s*f")\d+\.\d+\.\d+( \{VERSION_NAME\}"\s*)$',
                re.MULTILINE,
            ),
            r"\g<1>{}\g<2>".format(version),
        ),
        (
            repo_root / "README.md",
            re.compile(
                r"(?<![A-Za-z0-9.])(?P<prefix>v?)\d+\.\d+\.\d+-{}".format(
                    escaped_release_name
                )
            ),
            r"\g<prefix>{}-{}".format(version, release_name),
        ),
        (
            repo_root / "docs" / "blender-3.0-compatibility.md",
            re.compile(
                r"(?<![A-Za-z0-9.])(?P<prefix>v?)\d+\.\d+\.\d+-{}".format(
                    escaped_release_name
                )
            ),
            r"\g<prefix>{}-{}".format(version, release_name),
        ),
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Target semantic version, for example 1.1.2")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Show planned changes only")
    mode.add_argument(
        "--check",
        action="store_true",
        help="Exit nonzero unless every tracked reference already has this version",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if not VERSION_RE.fullmatch(args.version):
        raise ValueError("Version must use MAJOR.MINOR.PATCH format")

    repo_root = Path(__file__).resolve().parents[3]
    constants_path = repo_root / "constants.py"
    constants = read_source(constants_path)
    release_match = RELEASE_NAME_RE.search(constants)
    if release_match is None:
        raise ValueError("Could not read VERSION_NAME from {}".format(constants_path))
    release_name = release_match.group("name")

    targets = version_targets(repo_root, args.version, release_name)
    if args.check:
        inconsistent = []
        for path, pattern, replacement in targets:
            source = read_source(path)
            updated, replacements = pattern.subn(replacement, source)
            if replacements == 0 or updated != source:
                inconsistent.append(str(path.relative_to(repo_root)))
        if inconsistent:
            print("Version references do not match {}:".format(args.version))
            for path in inconsistent:
                print("- {}".format(path))
            return 1
        print("All version references match {}-{}.".format(args.version, release_name))
        return 0

    for path, pattern, replacement in targets:
        replace_or_fail(path, pattern, replacement, args.version, args.dry_run)

    if args.dry_run:
        print("Dry run only; no files were changed.")
    else:
        print("Updated ClipSync to {}-{}.".format(args.version, release_name))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print("Error: {}".format(error), file=sys.stderr)
        raise SystemExit(2)
