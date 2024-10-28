import bpy
from bpy.props import StringProperty, FloatProperty
from bpy.app import timers
import os
import struct
import sqlite3
import copy
import time
from .constants import PROPERTY_NAME,VERSION_STRING, DEFAULT_CLIP_PATH,DEFAULT_CLIP_PATH_NAME,DEFAULT_CLIP_PATH, DEFAULT_SYNC_INTERVAL, CLIP_PATH, PRODUCT_NAME, PRODUCT_NAME_UNDERSCORE, IS_DEBUG,DEFAULT_CLIP_PATH
from . import op_open_document_link
from . import op_stop_loop
from .external_storage import ExternalStorage

class OBJECT_OT_adjust_settings(bpy.types.Operator):
    bl_idname = f"object.{PRODUCT_NAME_UNDERSCORE}_adjust_settings"
    bl_label = f"{PRODUCT_NAME} v{VERSION_STRING}"
    bl_options = {'REGISTER', 'UNDO'}

    clip_path1 : StringProperty(name="clip slot 1", maxlen=32767, default=DEFAULT_CLIP_PATH,subtype="FILE_PATH")
    clip_path2 : StringProperty(name="clip slot 2", maxlen=32767, default=DEFAULT_CLIP_PATH,subtype="FILE_PATH")
    clip_path3 : StringProperty(name="clip slot 3", maxlen=32767, default=DEFAULT_CLIP_PATH,subtype="FILE_PATH")
    clip_path4 : StringProperty(name="clip slot 4", maxlen=32767, default=DEFAULT_CLIP_PATH,subtype="FILE_PATH")
    clip_path5 : StringProperty(name="clip slot 5", maxlen=32767, default=DEFAULT_CLIP_PATH,subtype="FILE_PATH")
    sync_interval : FloatProperty(name="sync interval", default=DEFAULT_SYNC_INTERVAL)
    
    storage = ExternalStorage()
    
    def draw(self,context):
        layout = self.layout
        layout.prop(self, f"{CLIP_PATH[1]}")
        layout.prop(self, f"{CLIP_PATH[2]}")
        layout.prop(self, f"{CLIP_PATH[3]}")
        layout.prop(self, f"{CLIP_PATH[4]}")
        layout.prop(self, f"{CLIP_PATH[5]}")
        layout.prop(self, f"{PROPERTY_NAME['sync_interval']}")
        layout.operator(op_open_document_link.OBJECT_OT_open_document_link.bl_idname, text="Document")
        layout.operator(op_stop_loop.OBJECT_OT_stop_loop.bl_idname, text="Stop")
        
    def invoke(self, context, event):
        window_width = context.window.width
        desired_width = int(window_width * 0.4)
        self.load_properties()
        return context.window_manager.invoke_props_dialog(self, width=desired_width)
    
    def load_properties(self):
        self.clip_path1 = self.storage.get(CLIP_PATH[1], DEFAULT_CLIP_PATH)
        self.clip_path2 = self.storage.get(CLIP_PATH[2], DEFAULT_CLIP_PATH)
        self.clip_path3 = self.storage.get(CLIP_PATH[3], DEFAULT_CLIP_PATH)
        self.clip_path4 = self.storage.get(CLIP_PATH[4], DEFAULT_CLIP_PATH)
        self.clip_path5 = self.storage.get(CLIP_PATH[5], DEFAULT_CLIP_PATH)
        self.sync_interval = self.storage.get(PROPERTY_NAME["sync_interval"], DEFAULT_SYNC_INTERVAL)
    
    def save_properties(self):
        self.storage.set(CLIP_PATH[1], self.clip_path1)
        self.storage.set(CLIP_PATH[2], self.clip_path2)
        self.storage.set(CLIP_PATH[3], self.clip_path3)
        self.storage.set(CLIP_PATH[4], self.clip_path4)
        self.storage.set(CLIP_PATH[5], self.clip_path5)
        self.storage.set(PROPERTY_NAME["sync_interval"], self.sync_interval)

    def execute(self, context):
        self.save_properties()
        clip_path_list = get_clip_path_list(self.clip_path1, self.clip_path2, self.clip_path3, self.clip_path4, self.clip_path5)
        self.report({'INFO'}, f"{PRODUCT_NAME} started!: {clip_path_list}")
        sync_interval = self.sync_interval
        bpy.types.Scene.cs_is_loop = True
        start_loop(sync_interval, clip_path_list)
        return {'FINISHED'}

def check_clip_file_path(clip_path):
    if not os.path.exists(trimUnnecessaries(clip_path)):
        return False
    return True

def get_clip_path_list(clip_path_1, clip_path_2, clip_path_3, clip_path_4, clip_path_5):
    path1 = get_clip_path(clip_path_1)
    path2 = get_clip_path(clip_path_2)
    path3 = get_clip_path(clip_path_3)
    path4 = get_clip_path(clip_path_4)
    path5 = get_clip_path(clip_path_5)
    return path1, path2, path3, path4, path5


def get_clip_path(clip_path):
    root_path = trimUnnecessaries(os.path.dirname(clip_path))
    base_name = trimUnnecessaries(os.path.splitext(os.path.basename(clip_path))[0])
    output_path = trimUnnecessaries(os.path.join(root_path, f"{base_name}.png"))
    return root_path, base_name, output_path

def trimUnnecessaries(path):
    path = replaceDoubleQuote(path)
    return path

def replaceDoubleQuote(path):
    return path.replace("\"", "")

def get_sqlite_binary_data_from_clip_file(filepath):
    chunk_data_list = []
    binary_data = None
    sqlite_binary_data = None
    baseOffset = 8
    with open(filepath, mode='rb') as binary_file:
        binary_data = binary_file.read()
        data_size = len(binary_data)
        offset = 0
        csf_magic_number = struct.unpack_from(f'{baseOffset}s', binary_data, offset)[0]
        csf_magic_number = csf_magic_number.decode()
        offset += baseOffset*3
        while offset < data_size:
            chunk_start_position = offset
            chunk_type = struct.unpack_from(f'{baseOffset}s', binary_data, offset)[0]
            chunk_type = chunk_type.decode()
            offset += baseOffset
            chunk_size = struct.unpack_from('>Q', binary_data, offset)[0]
            offset += baseOffset
            offset += chunk_size
            chunk_end_position = offset
            chunk_data = {
                'type': chunk_type,
                'size': chunk_size,
                'chunk_start_position': chunk_start_position,
                'chunk_end_position': chunk_end_position,
            }
            chunk_data_list.append(chunk_data)
        sqlite_chunk_start_position = 0
        for chunk_info in chunk_data_list:
            if chunk_info['type'] == 'CHNKSQLi':
                sqlite_chunk_start_position = chunk_info[
                    'chunk_start_position']
        sqlite_offset = sqlite_chunk_start_position + baseOffset*2
        sqlite_binary_data = copy.deepcopy(binary_data[sqlite_offset:])
    return sqlite_binary_data

def exec_sqlite_query(
    connect,
    query,
):
    cursor = connect.cursor()
    cursor.execute(query)
    query_results = cursor.fetchall()
    cursor.close()
    return query_results

def extract_canvas_preview_image_binary(
    sqlite_binary_data,
    temp_db_path,
):
    with open(temp_db_path, mode="wb") as f:
        f.write(sqlite_binary_data)
    connect = sqlite3.connect(temp_db_path)
    query_results = exec_sqlite_query(
        connect,
        "SELECT ImageData FROM CanvasPreview;",
    )
    if query_results:
        image_binary = query_results[0][0]
    else:
        image_binary = None
    connect.close()
    os.remove(temp_db_path)
    return image_binary

def get_canvas_preview(
    clip_file_path,
    tmp_db_path,
):
    sqlite_binary_data = get_sqlite_binary_data_from_clip_file(clip_file_path)
    image_binary = extract_canvas_preview_image_binary(
        sqlite_binary_data,
        tmp_db_path,
    )
    return image_binary

def start_loop(sync_interval, clip_path_list):
    for root_path, base_name, output_path in clip_path_list:
        if(base_name == DEFAULT_CLIP_PATH_NAME):
            continue
        if not check_clip_file_path(root_path):
            continue
        update_image_on_timer(root_path, base_name, output_path, sync_interval)
        start_image_on_timer(output_path, sync_interval)

def update_image_on_timer(root_path, base_name, output_path, sync_interval):
    clip_timer_func = update_image(root_path, base_name, output_path, sync_interval)
    if not timers.is_registered(clip_timer_func):
        timers.register(clip_timer_func, first_interval=sync_interval, persistent=True)

def start_image_on_timer(output_path, sync_interval):
    image_timer_func = check_and_reload_textures(output_path, sync_interval)
    if not timers.is_registered(image_timer_func):
        timers.register(image_timer_func, first_interval=sync_interval, persistent=True)

def update_image(root_path, base_name, output_path, sync_interval):
    def timer_func():
        try:
            if IS_DEBUG:
                current_time = time.strftime("%M:%S", time.localtime())
                print(f"${PRODUCT_NAME}--------------------------------------")
                print(f"loop update clip to png... {current_time}")
            clip_file_path = os.path.join(root_path, f"{base_name}.clip")
            tmp_db_path = os.path.join(root_path, f"{base_name}.db")
            image_binary = get_canvas_preview(clip_file_path, tmp_db_path)
            with open(output_path, 'wb') as f:
                f.write(image_binary)
            if bpy.types.Scene.cs_is_loop:
                return sync_interval
            else:
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    return timer_func

def check_and_reload_textures(watched_file_path, sync_interval):
    def timer_func():
        try:
            if IS_DEBUG:
                current_time = time.strftime("%M:%S", time.localtime())
                print(f"loop update texture... {current_time}")
            if os.path.exists(watched_file_path):
                file_mtime = os.path.getmtime(watched_file_path)
                for image in bpy.data.images:
                    image_path = bpy.path.abspath(image.filepath)
                    if os.path.abspath(image_path) == os.path.abspath(watched_file_path):
                        if "last_check_time" not in image:
                            image["last_check_time"] = 0
                        if file_mtime > image["last_check_time"]:
                            image.reload()
                            image["last_check_time"] = file_mtime
                        else:
                            print(f"No need to reload texture: {image.name}")
            else:
                print(f"File does not exist: {watched_file_path}")
            if bpy.types.Scene.cs_is_loop:
                return sync_interval
            else:
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    return timer_func

def register():
    bpy.utils.register_class(OBJECT_OT_adjust_settings)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_adjust_settings)