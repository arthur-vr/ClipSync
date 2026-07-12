import ast
from pathlib import Path
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "op_adjust_settings.py"


class BlenderPropertySafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(SOURCE.read_text(encoding="utf-8"))

    def test_language_update_does_not_assign_its_own_property(self):
        callback = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_change_language"
        )
        assignments = [
            target
            for node in ast.walk(callback)
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
            for target in (
                node.targets
                if isinstance(node, ast.Assign)
                else [node.target]
            )
        ]
        self.assertFalse(
            any(
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
                and target.attr == "language"
                for target in assignments
            )
        )

    def test_sync_mode_enum_uses_static_items(self):
        operator = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "OBJECT_OT_adjust_settings"
        )
        sync_mode = next(
            node
            for node in operator.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "sync_mode"
        )
        enum_call = sync_mode.annotation
        items = next(
            keyword.value for keyword in enum_call.keywords if keyword.arg == "items"
        )
        self.assertIsInstance(items, (ast.Tuple, ast.List))

    def test_operator_does_not_depend_on_plain_python_storage_attribute(self):
        self.assertNotIn("self.storage", SOURCE.read_text(encoding="utf-8"))

    def test_window_capture_fps_is_owned_by_remote_projects(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("window_capture_fps", source)
        self.assertIn('project["fps"]', source)

    def test_opening_settings_does_not_fetch_projects(self):
        operator = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "OBJECT_OT_adjust_settings"
        )
        load_properties = next(
            node
            for node in operator.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "load_properties"
        )
        called_methods = {
            node.func.attr
            for node in ast.walk(load_properties)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
        }
        self.assertNotIn("refresh_window_projects", called_methods)
        called_functions = {
            node.func.id
            for node in ast.walk(load_properties)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertIn("_restore_saved_window_projects", called_functions)

    def test_opening_clip_mode_still_restores_saved_window_projects(self):
        operator = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "OBJECT_OT_adjust_settings"
        )
        load_properties = next(
            node
            for node in operator.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "load_properties"
        )
        restore_calls = [
            node
            for node in ast.walk(load_properties)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_restore_saved_window_projects"
        ]
        self.assertEqual(len(restore_calls), 1)
        self.assertIsInstance(load_properties.body[-1], ast.Expr)
        self.assertIs(load_properties.body[-1].value, restore_calls[0])

    def test_unregister_stops_capture_and_clip_loops(self):
        unregister = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "unregister"
        )
        called_functions = {
            node.func.id
            for node in ast.walk(unregister)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertIn("stop_window_captures", called_functions)
        self.assertIn("stop_clip_timers", called_functions)
        self.assertTrue(
            any(
                isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Attribute)
                    and target.attr == "cs_is_loop"
                    for target in node.targets
                )
                and isinstance(node.value, ast.Constant)
                and node.value.value is False
                for node in ast.walk(unregister)
            )
        )

    def test_language_change_does_not_fetch_projects(self):
        callback = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_change_language"
        )
        self.assertFalse(
            any(
                isinstance(node, ast.Attribute)
                and node.attr == "refresh_window_projects"
                for node in ast.walk(callback)
            )
        )

    def test_property_update_callbacks_do_not_call_operator_methods(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("self.refresh_window_projects()", source)
        self.assertNotIn("self.restore_saved_window_projects()", source)

    def test_execute_explicitly_stops_clip_timers_without_sleeping(self):
        operator = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "OBJECT_OT_adjust_settings"
        )
        execute = next(
            node
            for node in operator.body
            if isinstance(node, ast.FunctionDef) and node.name == "execute"
        )
        called_functions = {
            node.func.id
            for node in ast.walk(execute)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertIn("stop_clip_timers", called_functions)
        self.assertNotIn("sleep", {
            node.func.attr
            for node in ast.walk(execute)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        })

    def test_window_capture_validates_before_saving_or_stopping(self):
        operator = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "OBJECT_OT_adjust_settings"
        )
        execute = next(
            node
            for node in operator.body
            if isinstance(node, ast.FunctionDef) and node.name == "execute"
        )
        window_branch = next(
            node
            for node in execute.body
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and any(
                isinstance(comparator, ast.Constant)
                and comparator.value == "WINDOW"
                for comparator in node.test.comparators
            )
        )

        def call_lines(name):
            return [
                node.lineno
                for node in ast.walk(window_branch)
                if isinstance(node, ast.Call)
                and (
                    isinstance(node.func, ast.Name) and node.func.id == name
                    or isinstance(node.func, ast.Attribute)
                    and node.func.attr == name
                )
            ]

        fetch_line = call_lines("fetch_active_window_projects")[0]
        save_line = call_lines("save_properties")[0]
        stop_line = call_lines("stop_window_captures")[0]
        self.assertLess(fetch_line, save_line)
        self.assertLess(save_line, stop_line)

    def test_window_capture_start_failure_rolls_back_started_workers(self):
        operator = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "OBJECT_OT_adjust_settings"
        )
        execute = next(
            node
            for node in operator.body
            if isinstance(node, ast.FunctionDef) and node.name == "execute"
        )
        start_try = next(
            node
            for node in ast.walk(execute)
            if isinstance(node, ast.Try)
            and any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "start_window_capture"
                for child in ast.walk(node)
            )
        )
        handler_calls = {
            node.func.id
            for handler in start_try.handlers
            for node in ast.walk(handler)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertIn("stop_window_captures", handler_calls)


if __name__ == "__main__":
    unittest.main()
