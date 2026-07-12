import unittest

from clip_tracking import ClipFileModificationTracker


class ClipFileModificationTrackerTests(unittest.TestCase):
    def test_tracks_each_clip_file_independently(self):
        modified_times = {"first.clip": 10, "second.clip": 20}
        tracker = ClipFileModificationTracker(modified_times.__getitem__)

        self.assertTrue(tracker.is_updated("first.clip"))
        self.assertTrue(tracker.is_updated("second.clip"))
        self.assertFalse(tracker.is_updated("first.clip"))
        self.assertFalse(tracker.is_updated("second.clip"))

        modified_times["first.clip"] = 11
        self.assertTrue(tracker.is_updated("first.clip"))
        self.assertFalse(tracker.is_updated("second.clip"))

    def test_reset_forces_the_next_check_to_update(self):
        tracker = ClipFileModificationTracker(lambda path: 10)
        self.assertTrue(tracker.is_updated("texture.clip"))
        self.assertFalse(tracker.is_updated("texture.clip"))
        tracker.reset("texture.clip")
        self.assertTrue(tracker.is_updated("texture.clip"))


if __name__ == "__main__":
    unittest.main()
