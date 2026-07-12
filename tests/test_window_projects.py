import unittest

from window_projects import (
    active_window_projects,
    loopback_url,
    migrate_legacy_window_capture_port,
    port_from_legacy_url,
    project_selected_by_default,
    resolve_selected_window_projects,
)


class ActiveWindowProjectsTests(unittest.TestCase):
    def test_keeps_only_sync_on_non_archived_projects(self):
        payload = [
            {"id": "main-1", "name": "Main texture", "fps": 20, "active": True, "archived": False},
            {"id": "new-2", "name": "New Window", "fps": 60, "active": True},
            {"id": "off-3", "name": "Off", "fps": 30, "active": False},
            {"id": "old-4", "name": "Archived", "fps": 30, "active": True, "archived": True},
        ]
        self.assertEqual(
            active_window_projects(payload),
            [
                {"id": "main-1", "name": "Main texture", "fps": 20},
                {"id": "new-2", "name": "New Window", "fps": 60},
            ],
        )

    def test_deduplicates_ids_and_preserves_blank_name(self):
        payload = [
            {"id": "p_1", "name": "", "fps": 35, "active": True},
            {"id": "p_1", "name": "duplicate", "fps": 35, "active": True},
            {"id": "bad/id", "name": "unsafe", "fps": 35, "active": True},
        ]
        self.assertEqual(
            active_window_projects(payload),
            [{"id": "p_1", "name": "", "fps": 35}],
        )

    def test_rejects_projects_without_a_valid_remote_fps(self):
        payload = [
            {"id": "missing", "name": "Missing", "active": True},
            {"id": "zero", "name": "Zero", "fps": 0, "active": True},
            {"id": "bool", "name": "Bool", "fps": True, "active": True},
        ]
        self.assertEqual(active_window_projects(payload), [])

    def test_rejects_non_array_contract(self):
        with self.assertRaises(ValueError):
            active_window_projects({"projects": []})

    def test_first_discovery_selects_every_active_project(self):
        self.assertTrue(project_selected_by_default("main", []))
        self.assertTrue(project_selected_by_default("new-window", set()))

    def test_saved_subset_is_preserved(self):
        selected = {"main"}
        self.assertTrue(project_selected_by_default("main", selected))
        self.assertFalse(project_selected_by_default("new-window", selected))

    def test_stale_selection_does_not_block_available_projects(self):
        projects = [
            {"id": "main", "name": "Main", "fps": 30},
            {"id": "detail", "name": "Detail", "fps": 20},
        ]
        available, unavailable = resolve_selected_window_projects(
            projects, ["missing", "main"]
        )
        self.assertEqual(available, [projects[0]])
        self.assertEqual(unavailable, ["missing"])

    def test_all_stale_selections_resolve_to_no_projects(self):
        available, unavailable = resolve_selected_window_projects(
            [{"id": "main", "name": "Main", "fps": 30}],
            ["missing"],
        )
        self.assertEqual(available, [])
        self.assertEqual(unavailable, ["missing"])

    def test_port_only_builds_a_loopback_url(self):
        self.assertEqual(loopback_url(48123), "http://127.0.0.1:48123")
        with self.assertRaises(ValueError):
            loopback_url(80)

    def test_migrates_port_from_the_legacy_url(self):
        self.assertEqual(port_from_legacy_url("http://127.0.0.1:54321"), 54321)
        self.assertEqual(port_from_legacy_url("not a URL", 48123), 48123)

    def test_migrates_legacy_url_before_default_port_is_merged(self):
        settings = {
            "window_capture_url": "http://127.0.0.1:54321",
            "language": "ja",
        }
        self.assertEqual(
            migrate_legacy_window_capture_port(settings)["window_capture_port"],
            54321,
        )
        self.assertNotIn("window_capture_port", settings)

    def test_explicit_port_wins_over_legacy_url(self):
        settings = {
            "window_capture_port": 50000,
            "window_capture_url": "http://127.0.0.1:54321",
        }
        self.assertEqual(
            migrate_legacy_window_capture_port(settings)["window_capture_port"],
            50000,
        )


if __name__ == "__main__":
    unittest.main()
