import ast
from pathlib import Path
import unittest


STORAGE_SOURCE = Path(__file__).resolve().parents[1] / "external_storage.py"
OPERATOR_SOURCE = Path(__file__).resolve().parents[1] / "op_adjust_settings.py"


class ExternalStorageSafetyTests(unittest.TestCase):
    def test_settings_file_is_replaced_atomically(self):
        source = STORAGE_SOURCE.read_text(encoding="utf-8")
        self.assertIn("tempfile.NamedTemporaryFile", source)
        self.assertIn("os.replace(temp_path, self.file_path)", source)

    def test_operator_saves_all_properties_in_one_update(self):
        tree = ast.parse(OPERATOR_SOURCE.read_text(encoding="utf-8"))
        operator = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "OBJECT_OT_adjust_settings"
        )
        save_properties = next(
            node
            for node in operator.body
            if isinstance(node, ast.FunctionDef) and node.name == "save_properties"
        )
        storage_calls = [
            node.func.attr
            for node in ast.walk(save_properties)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "_STORAGE"
        ]
        self.assertEqual(storage_calls, ["update"])


if __name__ == "__main__":
    unittest.main()
