---
name: update-addon-version
description: Synchronize the ClipSync semantic version across add-on metadata, the UI version string, and release documentation. Use when preparing a ClipSync version bump, changing the release version, or verifying that version references are consistent.
---

# Update Add-on Version

Run this skill from the repository root. Keep the release name in
`constants.py` unchanged unless the user explicitly requests a new name.

| File | Version field | Update rule |
| --- | --- | --- |
| `__init__.py` | `bl_info["version"]` | Blender add-on version tuple. |
| `constants.py` | `VERSION_STRING` | UI label; preserves `VERSION_NAME`. |
| `README.md` | release heading and compatibility text | Public version reference. |
| `docs/blender-3.0-compatibility.md` | compatibility text | Public version reference. |

## Workflow

Preview the requested version bump first:

```powershell
python skills/update-addon-version/scripts/update_version.py 1.1.2 --dry-run
```

Apply it, then verify every target has the requested value:

```powershell
python skills/update-addon-version/scripts/update_version.py 1.1.2
python skills/update-addon-version/scripts/update_version.py 1.1.2 --check
```

Run the test suite after a successful update:

```powershell
python -m unittest discover -s tests
```

Build a new archive only when needed, using `build-addon-zip`. Do not commit
or publish an archive unless the user asks.
