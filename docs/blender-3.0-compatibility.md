# Blender 3.0 compatibility

ClipSync v1.1.1-sun supports Blender 3.0 and newer.

Blender 3.0 embeds Python 3.9. The add-on source is therefore kept parseable
by Python 3.9: do not introduce Python 3.10-or-newer syntax such as `X | Y`
type unions, `match` / `case`, or parenthesized context managers. NumPy remains
optional; Window Capture falls back to its built-in Python pixel conversion
when NumPy is unavailable.

## Installation

Install ClipSync as a legacy add-on:

1. Download the ClipSync release ZIP.
2. Open **Edit > Preferences > Add-ons**.
3. Select **Install**, choose the ZIP, then enable **Object: ClipSync**.
4. Press `F3` and search for `ClipSync`.

The legacy release ZIP contains one `clipsync/` directory with
`clipsync/__init__.py` inside it. Do not extract its Python files directly into
Blender's `scripts/addons` directory: older Blender versions would otherwise
interpret files such as `window_capture.py` as separate add-ons.

The release ZIP uses the legacy add-on package layout, so it can be installed
from the Add-ons workflow in Blender 3.0 and newer.

## Compatibility safeguards

- `bl_info` specifies Blender 3.0 as the minimum version.
- The test suite parses all add-on modules using Python 3.9 grammar, so a
  newer Python syntax is caught before release.
- Window Capture works without NumPy. NumPy is used only to speed up pixel
  conversion when Blender provides it.

If Blender reports a syntax error while enabling ClipSync, make sure the ZIP
contains this version of the add-on rather than an older development build.

If a previously installed malformed ZIP produced warnings about an add-on
missing `bl_info`, remove only the loose ClipSync files it left directly under
`scripts/addons`, restart Blender, and install the current legacy ZIP again.
