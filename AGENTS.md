## structure

```text
clipSyncPublic/
├── *.py                  # Blender add-on source
├── docs/                 # Project documentation
├── i18n/                 # Translations
├── images/               # Documentation images
├── skills/               # Repository-specific Codex skills
├── tests/                # Tests
├── blender_manifest.toml # Add-on manifest
├── README.md             # Project overview
└── LICENSE.md            # License
```

## ./docs/*

| Path | Description |
| --- | --- |
| `translations.md` | Translation context, fallback behavior, and update rules. |

## ./skills/*

| Path | Description |
| --- | --- |
| `build-addon-zip/` | Build a versioned Blender add-on ZIP in the parent directory. |
| `commit-with-emoji/` | Create focused Git commits with emoji-prefixed Conventional Commit messages. |
