# Translation specification

English in `i18n/locales/en.py` is the source text and final fallback. Japanese,
Simplified Chinese, and Korean dictionaries must contain exactly the same keys.

## English context comments

Every entry in `en.py` must have one single-line comment immediately above it.
The comment should explain where the text appears, its intended tone or nuance,
and the meaning of any format placeholders. Keep comments in English and do not
combine one comment across multiple entries.

## Translation rules

- Preserve dictionary keys and placeholders such as `{count}`, `{error}`, and
  `{number}` exactly.
- Preserve product names, file extensions, and technical abbreviations unless a
  language has an established localized form.
- Translate for the UI context described in `en.py`, not word for word.
- Keep labels short, instructions direct, and status messages clear.
- Add a new key to every locale in the same change.
- Use `tt(key, locale, **variables)` for localized UI text. Missing locales and
  missing translations fall back to English.

## Supported locales

| Code | Language |
| --- | --- |
| `en` | English |
| `ja` | Japanese |
| `zh` | Simplified Chinese |
| `ko` | Korean |

Run `python -m unittest tests.test_i18n` after changing translations.
