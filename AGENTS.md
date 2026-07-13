## covenant

- The add-on must remain compatible with Blender 3.0.

## structure

```text
./
├── *.py                  # Blender add-on source
├── docs/                 # Project documentation
├── i18n/                 # Translations
├── images/               # Documentation images
├── skills/               # Repository-specific Codex skills
├── tests/                # Tests
├── README.md             # Project overview
└── LICENSE.md            # License
```

## ./docs/*

| Path | Description |
| --- | --- |
| `blender-3.0-compatibility.md` | Blender 3.0 support, legacy installation, and Python 3.9 compatibility rules. |
| `translations.md` | Translation context, fallback behavior, and update rules. |

## ./skills/*

| Path | Description |
| --- | --- |
| `build-addon-zip/` | Build a versioned Blender add-on ZIP in the parent directory. |
| `commit-with-emoji/` | Create focused Git commits with emoji-prefixed Conventional Commit messages. |
| `update-addon-version/` | Synchronize the add-on version across metadata, UI text, and release documentation. |
