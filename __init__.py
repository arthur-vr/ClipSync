from . import op_adjust_settings
from . import op_open_document_link
from . import op_stop_loop

bl_info = {
    "name": "ClipSync",
    "blender": (4, 2, 0),
    "category": "Object",
    "description": "sync canvas preview image from .clip file to .png file in blender",
    "author": "Smiley Cat",
    "version": (1, 0, 5),
    "location": "View3D > Object > ClipSync",
}

def register():
    op_adjust_settings.register()
    op_open_document_link.register()
    op_stop_loop.register()

def unregister():
    op_adjust_settings.unregister()
    op_open_document_link.unregister()
    op_stop_loop.unregister()
    
if __name__ == "__main__":
    register()