import os

VERSION_NAME = "house"
VERSION_STRING = f"1.0.5 ({VERSION_NAME})"
IS_DEBUG = False
PRODUCT_NAME = "ClipSync"
PRODUCT_NAME_UNDERSCORE = "clipsync"
DOCUMENT_URL = "https://github.com/arthur-vr/ClipSync"
USER_NAME = os.getlogin()
DEFAULT_CLIP_PATH_NAME = "YOUR CLIP PATH"
DEFAULT_CLIP_PATH = rf"C:\Users\{USER_NAME}\{DEFAULT_CLIP_PATH_NAME}.clip"
DEFAULT_SYNC_INTERVAL = 1.0
CLIP_PATH = {
    1: "clip_path1",
    2: "clip_path2",
    3: "clip_path3",
    4: "clip_path4",
    5: "clip_path5",
}
PROPERTY_NAME = {
    "sync_interval": "sync_interval",
}