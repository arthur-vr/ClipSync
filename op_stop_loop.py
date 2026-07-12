import bpy
from .constants import PRODUCT_NAME_UNDERSCORE
from .window_capture import stop_window_captures
from .external_storage import ExternalStorage
from .i18n import tt

class OBJECT_OT_stop_loop(bpy.types.Operator):
    bl_idname = f"object.{PRODUCT_NAME_UNDERSCORE}_stop_loop"
    bl_label = "Stop Loop"
    def execute(self, context):
        # Import here to avoid the module-level cycle: the settings operator
        # imports this Stop operator while it defines the timer registry.
        from .op_adjust_settings import stop_clip_timers

        bpy.types.Scene.cs_is_loop = False
        stop_clip_timers()
        stop_window_captures()
        locale = ExternalStorage().get("language", "en")
        self.report({'INFO'}, tt("stopped", locale))
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(OBJECT_OT_stop_loop)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_stop_loop)
