import unittest

from i18n import tt
from i18n.locales.en import STRINGS as EN
from i18n.locales.ja import STRINGS as JA
from i18n.locales.zh import STRINGS as ZH
from i18n.locales.ko import STRINGS as KO


class I18nTests(unittest.TestCase):
    def test_every_locale_mirrors_the_english_base(self):
        for locale in (JA, ZH, KO):
            self.assertEqual(set(locale), set(EN))

    def test_unknown_locale_and_missing_key_fall_back_to_english(self):
        self.assertEqual(tt("port", "unknown"), "Port")
        self.assertEqual(tt("missing.key", "ja"), "missing.key")

    def test_interpolation(self):
        self.assertEqual(tt("sync_on_count", "en", count=3), "Sync ON: 3 project(s)")


if __name__ == "__main__":
    unittest.main()
