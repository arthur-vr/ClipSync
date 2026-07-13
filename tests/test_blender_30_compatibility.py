"""Regression checks for Blender 3.0's embedded Python 3.9 runtime."""

import ast
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", "__pycache__", "skills", "tests"}


class Blender30CompatibilityTests(unittest.TestCase):
    def test_addon_modules_parse_with_python_39_grammar(self):
        addon_modules = [
            path
            for path in REPOSITORY_ROOT.rglob("*.py")
            if not EXCLUDED_PARTS.intersection(path.relative_to(REPOSITORY_ROOT).parts)
        ]

        for path in addon_modules:
            with self.subTest(path=path):
                ast.parse(
                    path.read_text(encoding="utf-8"),
                    filename=str(path),
                    feature_version=(3, 9),
                )

    def test_addon_metadata_declares_blender_30_minimum(self):
        source = (REPOSITORY_ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('"blender": (3, 0, 0)', source)


if __name__ == "__main__":
    unittest.main()
