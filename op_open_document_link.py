import bpy
import webbrowser
from .constants import DOCUMENT_URL, PRODUCT_NAME_UNDERSCORE

class OBJECT_OT_open_document_link(bpy.types.Operator):
    bl_idname = f"object.{PRODUCT_NAME_UNDERSCORE}_open_document_link"
    bl_label = "Open Document Link"
    def execute(self, context):
        url = DOCUMENT_URL
        webbrowser.open(url)
        self.report({'INFO'}, "Web link opened.")
        return {'FINISHED'}
      
def register():
    bpy.utils.register_class(OBJECT_OT_open_document_link)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_open_document_link)
