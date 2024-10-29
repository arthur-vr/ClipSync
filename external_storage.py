import bpy
import json
import os
from .constants import VERSION_STRING, CLIP_PATH, PRODUCT_NAME_UNDERSCORE, DEFAULT_CLIP_PATH, DEFAULT_SYNC_INTERVAL, PROPERTY_NAME

class ExternalStorage:
    def __init__(self):
        self.file_path = os.path.join(bpy.utils.user_resource('SCRIPTS'), "addons", f"{PRODUCT_NAME_UNDERSCORE}_settings_{VERSION_STRING}.json")
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            CLIP_PATH[1]: DEFAULT_CLIP_PATH,
            CLIP_PATH[2]: DEFAULT_CLIP_PATH,
            CLIP_PATH[3]: DEFAULT_CLIP_PATH,
            CLIP_PATH[4]: DEFAULT_CLIP_PATH,
            CLIP_PATH[5]: DEFAULT_CLIP_PATH,
            PROPERTY_NAME["sync_interval"]: DEFAULT_SYNC_INTERVAL
        }

    def save_data(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save_data()