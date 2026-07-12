---
name: build-addon-zip
description: Package this Blender add-on into a distributable ZIP named from blender_manifest.toml as name_version-short-string.zip. Use when Codex needs to build, package, archive, or prepare a release ZIP for this repository.
---

# Build Add-on ZIP

Run the bundled script from the repository root:

```powershell
python skills/build-addon-zip/scripts/build_zip.py
```

The script reads `name` and `version` from `blender_manifest.toml` and writes the archive one directory above the repository. It uses the current Git commit's short SHA as the suffix.

To provide a release label or another suffix explicitly:

```powershell
python skills/build-addon-zip/scripts/build_zip.py --short-string beta1
```

After the command finishes, report the absolute archive path and the number of packaged files. Do not commit the generated ZIP unless the user explicitly asks.

The archive keeps add-on files at its root so `blender_manifest.toml` is a top-level entry. Development-only directories such as `docs`, `images`, `tests`, and `skills` are excluded.
