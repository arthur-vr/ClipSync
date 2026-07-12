import bpy
import webbrowser
from .constants import DOCUMENT_URL, PRODUCT_NAME_UNDERSCORE
from .external_storage import ExternalStorage
from .i18n import tt

class OBJECT_OT_open_document_link(bpy.types.Operator):
    bl_idname = f"object.{PRODUCT_NAME_UNDERSCORE}_open_document_link"
    bl_label = "Open Document Link"
    def execute(self, context):
        url = DOCUMENT_URL
        webbrowser.open(url)
        locale = ExternalStorage().get("language", "en")
        self.report({'INFO'}, tt("web_link_opened", locale))
        return {'FINISHED'}
      
def register():
    bpy.utils.register_class(OBJECT_OT_open_document_link)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_open_document_link)
