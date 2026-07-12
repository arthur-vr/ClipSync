"""Per-file modification tracking for the original .clip workflow."""

import os


class ClipFileModificationTracker:
    def __init__(self, getmtime=os.path.getmtime):
        self._getmtime = getmtime
        self._modified_times = {}

    @staticmethod
    def _key(path):
        return os.path.normcase(os.path.abspath(path))

    def is_updated(self, path):
        key = self._key(path)
        modified_time = self._getmtime(path)
        previous = self._modified_times.get(key)
        self._modified_times[key] = modified_time
        return previous is None or previous != modified_time

    def reset(self, path):
        self._modified_times.pop(self._key(path), None)
