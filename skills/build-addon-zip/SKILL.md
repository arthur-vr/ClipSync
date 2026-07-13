---
name: build-addon-zip
description: Package this Blender add-on into a legacy Blender-compatible ZIP named from bl_info and VERSION_NAME as name_version-release-short-string.zip. Use when Codex needs to build, package, archive, or prepare a release ZIP for this repository.
---

# Build Add-on ZIP

Run the bundled script from the repository root to create an add-on ZIP for
Blender 3.0 and later:

```powershell
python skills/build-addon-zip/scripts/build_zip.py
```

The script reads `name` and `version` from `bl_info` in `__init__.py`, and the
release name from `VERSION_NAME` in `constants.py`. It writes the archive one
directory above the repository using
`name_version-release-short-string.zip`; the short string defaults to the
current Git commit's short SHA.

The archive contains one top-level add-on package directory named from
`bl_info["name"]`, with `__init__.py` inside it. This layout prevents Blender
from treating each Python module as a separate add-on.

To provide a release label or another suffix explicitly:

```powershell
python skills/build-addon-zip/scripts/build_zip.py --short-string beta1
```

After the command finishes, report the absolute archive path and the number of
packaged files. Do not commit the generated ZIP unless the user explicitly asks.

Development-only directories such as `docs`, `images`, `tests`, and `skills` are
excluded.
