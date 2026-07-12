"""ClipSync Blender UI localization with English as the final fallback."""

from .locales.en import STRINGS as EN
from .locales.ja import STRINGS as JA
from .locales.zh import STRINGS as ZH
from .locales.ko import STRINGS as KO


DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ("en", "ja", "zh", "ko")
LOCALE_ITEMS = (
    ("en", "English", "English"),
    ("ja", "日本語", "Japanese"),
    ("zh", "简体中文", "Simplified Chinese"),
    ("ko", "한국어", "Korean"),
)
_DICTIONARIES = {"en": EN, "ja": JA, "zh": ZH, "ko": KO}


def normalize_locale(locale):
    return locale if locale in SUPPORTED_LOCALES else DEFAULT_LOCALE


def tt(key, locale=DEFAULT_LOCALE, **variables):
    """Translate one key, falling back to the authored English dictionary."""
    dictionary = _DICTIONARIES.get(normalize_locale(locale), EN)
    template = dictionary.get(key, EN.get(key, key))
    try:
        return template.format(**variables)
    except (KeyError, ValueError):
        return template
