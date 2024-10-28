import bpy
from .constants import PRODUCT_NAME_UNDERSCORE

class OBJECT_OT_stop_loop(bpy.types.Operator):
    bl_idname = f"object.{PRODUCT_NAME_UNDERSCORE}_stop_loop"
    bl_label = "Stop Loop"
    def execute(self, context):
        bpy.types.Scene.cs_is_loop = False
        self.report({'INFO'}, "ClipSync stopped")
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(OBJECT_OT_stop_loop)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_stop_loop)