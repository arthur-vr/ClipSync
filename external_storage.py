import bpy
import glob
import json
import os
import tempfile
from .constants import CLIP_PATH, PRODUCT_NAME_UNDERSCORE, DEFAULT_PARENT_CLIP_PATH,DEFAULT_CLIP_PATH, DEFAULT_SYNC_INTERVAL, DEFAULT_WINDOW_CAPTURE_PORT, PROPERTY_NAME
from .window_projects import migrate_legacy_window_capture_port

class ExternalStorage:
    def __init__(self):
        self.storage_dir = os.path.join(bpy.utils.user_resource('SCRIPTS'), "addons")
        # Stable across addon upgrades: port, language, and selected projects
        # must not reset merely because ClipSync's version changed.
        self.file_path = os.path.join(self.storage_dir, f"{PRODUCT_NAME_UNDERSCORE}_settings.json")
        self.data = self.load_data()

    def default_data(self):
        return {
            CLIP_PATH[1]: DEFAULT_CLIP_PATH,
            CLIP_PATH[2]: DEFAULT_CLIP_PATH,
            CLIP_PATH[3]: DEFAULT_CLIP_PATH,
            CLIP_PATH[4]: DEFAULT_CLIP_PATH,
            CLIP_PATH[5]: DEFAULT_CLIP_PATH,
            PROPERTY_NAME["sync_interval"]: DEFAULT_SYNC_INTERVAL,
            PROPERTY_NAME["is_use_parent_folder"]: False,
            PROPERTY_NAME["parent_folder_path"]: DEFAULT_PARENT_CLIP_PATH,
            PROPERTY_NAME["suffix"]: "",
            "window_capture_project_ids": [],
            "window_capture_projects": [],
            "window_capture_port": DEFAULT_WINDOW_CAPTURE_PORT,
            "language": "en",
        }

    def load_data(self):
        defaults = self.default_data()
        legacy = glob.glob(os.path.join(
            self.storage_dir,
            f"{PRODUCT_NAME_UNDERSCORE}_settings_*.json",
        ))
        legacy.sort(key=lambda path: os.path.getmtime(path), reverse=True)
        for path in [self.file_path, *legacy]:
            if not os.path.exists(path):
                continue
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    loaded = migrate_legacy_window_capture_port(
                        loaded, DEFAULT_WINDOW_CAPTURE_PORT
                    )
                    defaults.update(loaded)
                    return defaults
            except (OSError, ValueError):
                continue
        return defaults

    def save_data(self):
        os.makedirs(self.storage_dir, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=self.storage_dir,
                prefix=f".{PRODUCT_NAME_UNDERSCORE}_settings_",
                suffix='.tmp',
                delete=False,
            ) as f:
                temp_path = f.name
                json.dump(self.data, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, self.file_path)
            temp_path = None
        finally:
            if temp_path is not None:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.update({key: value})

    def update(self, values):
        self.data.update(values)
        self.save_data()
