import bpy
from bpy.props import (
    StringProperty,
    FloatProperty,
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
)
from bpy.app import timers
import os
import struct
import sqlite3
import copy
import time
from .constants import PROPERTY_NAME,VERSION_STRING,DEFAULT_PARENT_CLIP_PATH, DEFAULT_CLIP_PATH,DEFAULT_CLIP_PATH_NAME,DEFAULT_CLIP_PATH, DEFAULT_SYNC_INTERVAL, DEFAULT_WINDOW_CAPTURE_PORT, CLIP_PATH, PRODUCT_NAME, PRODUCT_NAME_UNDERSCORE, IS_DEBUG,DEFAULT_CLIP_PATH
from . import op_open_document_link
from . import op_stop_loop
from .external_storage import ExternalStorage
from .clip_tracking import ClipFileModificationTracker
from .window_capture import start_window_capture, stop_window_captures
from .window_projects import (
    fetch_active_window_projects,
    loopback_url,
    project_selected_by_default,
    resolve_selected_window_projects,
)
from .i18n import DEFAULT_LOCALE, LOCALE_ITEMS, normalize_locale, tt


_STORAGE = ExternalStorage()
_CLIP_TIMER_FUNCS = []
_CLIP_FILE_TRACKER = ClipFileModificationTracker()


def _locale(self):
    return normalize_locale(getattr(self, "language", DEFAULT_LOCALE))


def _change_language(self, context):
    # Never assign to ``self.language`` from its own update callback. Blender
    # immediately invokes the callback again, which ends in a native stack
    # overflow instead of a catchable Python exception.
    locale = normalize_locale(self.language)
    _STORAGE.set("language", locale)


def _change_sync_mode(self, context):
    if self.language_ready and self.sync_mode == "WINDOW":
        _restore_saved_window_projects(self)


def _change_active_tab(self, context):
    if self.active_tab in {"CLIP", "WINDOW"}:
        self.sync_mode = self.active_tab


def _refresh_window_projects(self, context):
    """Button-like BoolProperty callback that keeps the settings dialog open."""
    if not self.window_capture_refresh:
        return
    self.window_capture_refresh = False
    _fetch_window_projects_into(self)


class ClipSyncWindowProjectItem(bpy.types.PropertyGroup):
    project_id : StringProperty(name="Project ID")
    project_name : StringProperty(name="Project name")
    selected : BoolProperty(name="Sync", default=False)


def _selected_window_project_ids(owner):
    return list(dict.fromkeys(
        project.project_id
        for project in owner.window_capture_projects
        if project.selected and project.project_id
    ))


def _selected_window_projects(owner):
    return [
        {"id": project.project_id, "name": project.project_name.strip()}
        for project in owner.window_capture_projects
        if project.selected and project.project_id
    ]


def _stored_window_projects():
    projects = _STORAGE.get("window_capture_projects", None)
    if isinstance(projects, list):
        valid = [
            {
                "id": project["id"].strip(),
                "name": project.get("name", "").strip(),
            }
            for project in projects
            if isinstance(project, dict)
            and isinstance(project.get("id"), str)
            and project["id"].strip()
            and isinstance(project.get("name", ""), str)
        ]
        if valid:
            return list({project["id"]: project for project in valid}.values())

    # Compatibility with settings written before project names were persisted.
    return [
        {"id": project_id, "name": ""}
        for project_id in _legacy_stored_window_project_ids()
    ]


def _legacy_stored_window_project_ids():
    selected_ids = _STORAGE.get("window_capture_project_ids", None)
    if isinstance(selected_ids, list):
        return list(dict.fromkeys(
            value.strip()
            for value in selected_ids
            if isinstance(value, str) and value.strip()
        ))

    # One-shot migration from the old five free-text Project ID slots.
    return list(dict.fromkeys(
        value.strip()
        for value in (
            _STORAGE.get("window_capture_project_id", ""),
            _STORAGE.get("window_capture_project2", ""),
            _STORAGE.get("window_capture_project3", ""),
            _STORAGE.get("window_capture_project4", ""),
            _STORAGE.get("window_capture_project5", ""),
        )
        if isinstance(value, str) and value.strip()
    ))


def _stored_window_project_ids():
    return [project["id"] for project in _stored_window_projects()]


def _project_display_name(name, locale):
    return name.strip() if name.strip() else tt("unnamed_project", locale)


def _restore_saved_window_projects(owner):
    owner.window_capture_projects.clear()
    for project in _stored_window_projects():
        item = owner.window_capture_projects.add()
        item.project_id = project["id"]
        item.project_name = project["name"]
        item.selected = True
    owner.window_capture_status = ""
    owner.window_capture_status_error = False


def _fetch_window_projects_into(owner, selected_ids=None):
    if selected_ids is None:
        selected_ids = set(_selected_window_project_ids(owner))
    else:
        selected_ids = set(selected_ids)
    try:
        projects = fetch_active_window_projects(loopback_url(owner.window_capture_port))
    except Exception as exc:
        # A temporary Tauri outage must not erase the user's saved set.
        if not owner.window_capture_projects:
            saved_by_id = {
                project["id"]: project["name"]
                for project in _stored_window_projects()
            }
            for project_id in selected_ids:
                item = owner.window_capture_projects.add()
                item.project_id = project_id
                item.project_name = saved_by_id.get(project_id, "")
                item.selected = True
        owner.window_capture_status = tt("fetch_failed", _locale(owner), error=exc)
        owner.window_capture_status_error = True
        return

    owner.window_capture_projects.clear()
    for project in projects:
        item = owner.window_capture_projects.add()
        item.project_id = project["id"]
        item.project_name = project["name"]
        item.selected = project_selected_by_default(project["id"], selected_ids)
    owner.window_capture_status = tt("sync_on_count", _locale(owner), count=len(projects))
    owner.window_capture_status_error = False

def SEARCH_OBJECT_OT_adjust_settings(self, context):
    self.layout.operator(OBJECT_OT_adjust_settings.bl_idname)

class OBJECT_OT_adjust_settings(bpy.types.Operator):
    bl_idname = f"object.{PRODUCT_NAME_UNDERSCORE}_adjust_settings"
    bl_label = f"{PRODUCT_NAME} v{VERSION_STRING}"
    bl_options = {'REGISTER', 'UNDO'}

    clip_path1 : StringProperty(name="clip slot 1", maxlen=32767, default=DEFAULT_CLIP_PATH,subtype="FILE_PATH")
    clip_path2 : StringProperty(name="clip slot 2", maxlen=32767, default=DEFAULT_CLIP_PATH,subtype="FILE_PATH")
    clip_path3 : StringProperty(name="clip slot 3", maxlen=32767, default=DEFAULT_CLIP_PATH,subtype="FILE_PATH")
    clip_path4 : StringProperty(name="clip slot 4", maxlen=32767, default=DEFAULT_CLIP_PATH,subtype="FILE_PATH")
    clip_path5 : StringProperty(name="clip slot 5", maxlen=32767, default=DEFAULT_CLIP_PATH,subtype="FILE_PATH")
    is_use_parent_folder : BoolProperty(name="use parent folder", default=False)
    parent_folder_path : StringProperty(name="parent folder", maxlen=32767, default=DEFAULT_PARENT_CLIP_PATH,subtype="DIR_PATH")
    suffix : StringProperty(name="suffix", maxlen=32767, default="")
    sync_interval : FloatProperty(name="sync interval", default=DEFAULT_SYNC_INTERVAL)
    sync_mode : EnumProperty(
        name="Sync source",
        # Keep enum strings static. Blender retains raw references to callback
        # strings and can hard-crash when a dynamic list is garbage-collected.
        # `draw()` localizes these with prop_enum(text=tt(...)).
        items=(
            ("CLIP", ".clip file", "Use the existing ClipSync .clip workflow"),
            ("WINDOW", "Window Capture", "Receive live frames from ClipSync"),
        ),
        default="CLIP",
        update=_change_sync_mode,
    )
    active_tab : EnumProperty(
        name="Tab",
        items=(
            ("CLIP", ".clip file", "Show .clip file synchronization"),
            ("WINDOW", "Window Capture", "Show Window Capture synchronization"),
            ("SETTINGS", "Settings", "Show ClipSync settings"),
        ),
        default="CLIP",
        update=_change_active_tab,
        options={'SKIP_SAVE'},
    )
    language : EnumProperty(
        name="Language",
        items=LOCALE_ITEMS,
        default=DEFAULT_LOCALE,
        update=_change_language,
    )
    window_capture_port : IntProperty(
        name="Port",
        description="Local ClipSync app port",
        default=DEFAULT_WINDOW_CAPTURE_PORT,
        min=1024,
        max=65535,
    )
    window_capture_projects : CollectionProperty(type=ClipSyncWindowProjectItem)
    window_capture_refresh : BoolProperty(
        name="Get Sync ON Projects",
        description="Refresh projects whose Sync toggle is ON in ClipSync",
        default=False,
        update=_refresh_window_projects,
    )
    window_capture_status : StringProperty(default="", options={'HIDDEN'})
    window_capture_status_error : BoolProperty(default=False, options={'HIDDEN'})
    language_ready : BoolProperty(default=False, options={'HIDDEN'})
    def draw(self,context):
        layout = self.layout
        locale = _locale(self)
        top = layout.split(factor=0.88, align=True)
        tabs = top.row(align=True)
        tabs.prop_enum(self, "active_tab", "CLIP", text=tt("clip_file", locale))
        tabs.prop_enum(self, "active_tab", "WINDOW", text=tt("window_capture", locale))
        settings_tab = top.row(align=True)
        settings_tab.alignment = 'RIGHT'
        settings_tab.prop_enum(
            self,
            "active_tab",
            "SETTINGS",
            text="",
            icon="PREFERENCES",
        )
        layout.separator(factor=0.55)
        if self.active_tab == "SETTINGS":
            settings = layout.column(align=False)
            settings.prop(self, "language", text=tt("language", locale), icon="WORLD")
            settings.separator(factor=0.8)
            settings.prop(self, "window_capture_port", text=tt("port", locale))
            return
        if self.active_tab == "WINDOW":
            layout.prop(
                self,
                "window_capture_refresh",
                text=tt("get_sync_projects", locale),
                toggle=True,
                icon="FILE_REFRESH",
            )
            box = layout.box()
            if self.window_capture_projects:
                for project in self.window_capture_projects:
                    row = box.row(align=True)
                    project_name = _project_display_name(project.project_name, locale)
                    row.prop(
                        project,
                        "selected",
                        text=f"{project_name}  —  {project.project_id}",
                    )
            else:
                box.label(text=tt("no_sync_projects", locale), icon="INFO")
            if self.window_capture_status:
                icon = "ERROR" if self.window_capture_status_error else "INFO"
                layout.label(text=self.window_capture_status, icon=icon)
            layout.operator(op_open_document_link.OBJECT_OT_open_document_link.bl_idname, text=tt("document", locale))
            layout.operator(op_stop_loop.OBJECT_OT_stop_loop.bl_idname, text=tt("stop", locale))
            return
        layout.prop(self, f"{CLIP_PATH[1]}", text=tt("clip_slot", locale, number=1))
        layout.prop(self, f"{CLIP_PATH[2]}", text=tt("clip_slot", locale, number=2))
        layout.prop(self, f"{CLIP_PATH[3]}", text=tt("clip_slot", locale, number=3))
        layout.prop(self, f"{CLIP_PATH[4]}", text=tt("clip_slot", locale, number=4))
        layout.prop(self, f"{CLIP_PATH[5]}", text=tt("clip_slot", locale, number=5))
        layout.prop(self, f"{PROPERTY_NAME['is_use_parent_folder']}", text=tt("use_parent_folder", locale))
        if self.is_use_parent_folder:
            layout.prop(self, f"{PROPERTY_NAME['parent_folder_path']}", text=tt("parent_folder", locale))
        layout.prop(self, f"{PROPERTY_NAME['suffix']}", text=tt("suffix", locale))
        layout.prop(self, f"{PROPERTY_NAME['sync_interval']}", text=tt("sync_interval", locale))
        layout.operator(op_open_document_link.OBJECT_OT_open_document_link.bl_idname, text=tt("document", locale))
        layout.operator(op_stop_loop.OBJECT_OT_stop_loop.bl_idname, text=tt("stop", locale))
        
    def invoke(self, context, event):
        window_width = context.window.width
        desired_width = int(window_width * 0.4)
        self.load_properties()
        return context.window_manager.invoke_props_dialog(self, width=desired_width)
    
    def load_properties(self):
        self.language_ready = False
        self.language = normalize_locale(_STORAGE.get("language", DEFAULT_LOCALE))
        self.clip_path1 = _STORAGE.get(CLIP_PATH[1], DEFAULT_CLIP_PATH)
        self.clip_path2 = _STORAGE.get(CLIP_PATH[2], DEFAULT_CLIP_PATH)
        self.clip_path3 = _STORAGE.get(CLIP_PATH[3], DEFAULT_CLIP_PATH)
        self.clip_path4 = _STORAGE.get(CLIP_PATH[4], DEFAULT_CLIP_PATH)
        self.clip_path5 = _STORAGE.get(CLIP_PATH[5], DEFAULT_CLIP_PATH)
        self.sync_interval = _STORAGE.get(PROPERTY_NAME["sync_interval"], DEFAULT_SYNC_INTERVAL)
        self.sync_mode = _STORAGE.get("sync_mode", "CLIP")
        self.active_tab = self.sync_mode
        self.window_capture_port = _STORAGE.get(
            "window_capture_port",
            DEFAULT_WINDOW_CAPTURE_PORT,
        )
        self.language_ready = True
        # Keep the saved Window Capture selection available even when the
        # dialog opens on the Clip or Settings tab.  save_properties() writes
        # this collection for every tab, so leaving it empty here would erase
        # the user's saved projects when unrelated settings are confirmed.
        _restore_saved_window_projects(self)

    def stored_window_project_ids(self):
        return _stored_window_project_ids()

    def restore_saved_window_projects(self):
        _restore_saved_window_projects(self)

    def selected_window_project_ids(self):
        return _selected_window_project_ids(self)

    def refresh_window_projects(self, selected_ids=None):
        _fetch_window_projects_into(self, selected_ids)
    
    def save_properties(self):
        selected_projects = _selected_window_projects(self)
        _STORAGE.update({
            CLIP_PATH[1]: self.clip_path1,
            CLIP_PATH[2]: self.clip_path2,
            CLIP_PATH[3]: self.clip_path3,
            CLIP_PATH[4]: self.clip_path4,
            CLIP_PATH[5]: self.clip_path5,
            PROPERTY_NAME["is_use_parent_folder"]: self.is_use_parent_folder,
            PROPERTY_NAME["parent_folder_path"]: self.parent_folder_path,
            PROPERTY_NAME["suffix"]: self.suffix,
            PROPERTY_NAME["sync_interval"]: self.sync_interval,
            "sync_mode": self.sync_mode,
            "window_capture_port": self.window_capture_port,
            "language": self.language,
            "window_capture_projects": selected_projects,
            "window_capture_project_ids": [
                project["id"] for project in selected_projects
            ],
        })
    def execute(self, context):
        if self.active_tab == "SETTINGS":
            self.save_properties()
            return {'FINISHED'}
        if self.sync_mode == "WINDOW":
            project_ids = _selected_window_project_ids(self)
            if not project_ids:
                self.report({'ERROR'}, tt("select_project", _locale(self)))
                return {'CANCELLED'}
            base_url = loopback_url(self.window_capture_port)
            try:
                projects, unavailable_ids = resolve_selected_window_projects(
                    fetch_active_window_projects(base_url), project_ids
                )
            except Exception as exc:
                self.report(
                    {'ERROR'},
                    tt("fetch_failed", _locale(self), error=exc),
                )
                return {'CANCELLED'}
            if not projects:
                self.report(
                    {'ERROR'},
                    tt("no_available_projects", _locale(self)),
                )
                return {'CANCELLED'}
            # Do not mutate the running synchronization until discovery and
            # selection validation have succeeded.
            self.save_properties()
            bpy.types.Scene.cs_is_loop = False
            stop_window_captures()
            stop_clip_timers()
            bpy.types.Scene.cs_is_loop = True
            try:
                for project in projects:
                    start_window_capture(base_url, project["id"], project["fps"])
            except Exception as exc:
                stop_window_captures()
                bpy.types.Scene.cs_is_loop = False
                self.report(
                    {'ERROR'},
                    tt("window_capture_start_failed", _locale(self), error=exc),
                )
                return {'CANCELLED'}
            if unavailable_ids:
                self.report(
                    {'WARNING'},
                    tt(
                        "projects_unavailable",
                        _locale(self),
                        projects=", ".join(unavailable_ids),
                    ),
                )
            self.report({'INFO'}, tt("window_capture_started", _locale(self), count=len(projects)))
            return {'FINISHED'}
        self.save_properties()
        bpy.types.Scene.cs_is_loop = False
        stop_window_captures()
        stop_clip_timers()
        bpy.types.Scene.cs_is_loop = True
        clip_path_list = get_clip_path_list(
            self.clip_path1,
            self.clip_path2,
            self.clip_path3,
            self.clip_path4,
            self.clip_path5,
            self.is_use_parent_folder,
            self.parent_folder_path,
            self.suffix,
        )
        self.report({'INFO'}, tt("clipsync_started", _locale(self), paths=clip_path_list))
        sync_interval = self.sync_interval
        start_loop(sync_interval, clip_path_list)
        return {'FINISHED'}

def check_clip_file_path(clip_path):
    if not os.path.exists(trimUnnecessaries(clip_path)):
        return False
    return True

def get_clip_path_list(
    clip_path_1,
    clip_path_2,
    clip_path_3,
    clip_path_4,
    clip_path_5,
    is_use_parent_folder,
    parent_folder_path,
    suffix,
):
    path1 = get_clip_path(clip_path_1, is_use_parent_folder, parent_folder_path, suffix)
    path2 = get_clip_path(clip_path_2, is_use_parent_folder, parent_folder_path, suffix)
    path3 = get_clip_path(clip_path_3, is_use_parent_folder, parent_folder_path, suffix)
    path4 = get_clip_path(clip_path_4, is_use_parent_folder, parent_folder_path, suffix)
    path5 = get_clip_path(clip_path_5, is_use_parent_folder, parent_folder_path, suffix)
    return path1, path2, path3, path4, path5

def tail_suffix(base_name, suffix):
    if suffix != "":
        return f"{base_name}_{suffix}"
    return base_name

def get_clip_path(
    clip_path,
    is_use_parent_folder,
    parent_folder_path,
    suffix,
):
    root_path = trimUnnecessaries(os.path.dirname(clip_path))
    base_name = trimUnnecessaries(os.path.splitext(os.path.basename(clip_path))[0])
    output_path = trimUnnecessaries(os.path.join(root_path, f"{tail_suffix(base_name, suffix)}.png"))
    if is_use_parent_folder:
        output_path = trimUnnecessaries(os.path.join(parent_folder_path, f"{tail_suffix(base_name, suffix)}.png"))
    return root_path, base_name, output_path

def trimUnnecessaries(path):
    path = replaceDoubleQuote(path)
    return path

def replaceDoubleQuote(path):
    return path.replace("\"", "")

def is_clip_file_updated(clip_file_path):
    return _CLIP_FILE_TRACKER.is_updated(clip_file_path)

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

def get_image_binary(connect):
    query_results = exec_sqlite_query(
        connect,
        "SELECT ImageData FROM CanvasPreview;",
    )
    return query_results[0][0] if query_results else None

def extract_canvas_preview_image_binary(
    sqlite_binary_data,
    tmp_db_path,
):
    connect = sqlite3.connect(':memory:')
    if hasattr(connect, 'deserialize'):
        connect.deserialize(sqlite_binary_data)
        connect.commit()
        image_binary = get_image_binary(connect)
    else:
        with open(tmp_db_path, mode="wb") as f:
            f.write(sqlite_binary_data)
        connect = sqlite3.connect(tmp_db_path)
        image_binary = get_image_binary(connect)
    connect.close()
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
        if DEFAULT_CLIP_PATH_NAME in base_name:
            continue
        clip_file_path = os.path.join(root_path, f"{base_name}.clip")
        if not check_clip_file_path(clip_file_path):
            continue
        _CLIP_FILE_TRACKER.reset(clip_file_path)
        update_image_on_timer(root_path, base_name, output_path, sync_interval)
        check_image_on_timer(output_path, sync_interval)


def stop_clip_timers():
    """Unregister every .clip update/reload timer owned by this module."""
    while _CLIP_TIMER_FUNCS:
        timer_func = _CLIP_TIMER_FUNCS.pop()
        if timers.is_registered(timer_func):
            timers.unregister(timer_func)

def update_image_on_timer(root_path, base_name, output_path, sync_interval):
    clip_timer_func = update_image(root_path, base_name, output_path, sync_interval)
    if not timers.is_registered(clip_timer_func):
        timers.register(clip_timer_func, first_interval=sync_interval, persistent=True)
        _CLIP_TIMER_FUNCS.append(clip_timer_func)

def check_image_on_timer(output_path, sync_interval):
    image_timer_func = check_and_reload_textures(output_path, sync_interval)
    if not timers.is_registered(image_timer_func):
        timers.register(image_timer_func, first_interval=sync_interval, persistent=True)
        _CLIP_TIMER_FUNCS.append(image_timer_func)

def update_image(root_path, base_name, output_path, sync_interval):
    def timer_func():
        try:
            if IS_DEBUG:
                current_time = time.strftime("%M:%S", time.localtime())
                print(f"${PRODUCT_NAME}--------------------------------------")
                print(f"loop update clip to png... {current_time}")
            clip_file_path = os.path.join(root_path, f"{base_name}.clip")
            if not is_clip_file_updated(clip_file_path):
                if IS_DEBUG:
                    print(f"clip file is not updated: {clip_file_path}")
                return sync_interval
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

def check_and_reload_textures(output_path, sync_interval):
    def timer_func():
        try:
            if IS_DEBUG:
                current_time = time.strftime("%M:%S", time.localtime())
                print(f"loop update texture... {current_time}")
            if os.path.exists(output_path):
                file_mtime = os.path.getmtime(output_path)
                for image in bpy.data.images:
                    image_path = bpy.path.abspath(image.filepath)
                    if os.path.abspath(image_path) == os.path.abspath(output_path):
                        if "last_check_time" not in image:
                            image["last_check_time"] = 0
                        if file_mtime > image["last_check_time"]:
                            image.reload()
                            image["last_check_time"] = file_mtime
                        else:
                            if IS_DEBUG:
                                print(f"No need to reload texture: {image.name}")
            else:
                if IS_DEBUG:
                    print(f"File does not exist: {output_path}")
            if bpy.types.Scene.cs_is_loop:
                return sync_interval
            else:
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    return timer_func

def register():
    bpy.utils.register_class(ClipSyncWindowProjectItem)
    bpy.utils.register_class(OBJECT_OT_adjust_settings)
    bpy.types.VIEW3D_MT_object.append(SEARCH_OBJECT_OT_adjust_settings)

def unregister():
    stop_window_captures()
    bpy.types.Scene.cs_is_loop = False
    stop_clip_timers()
    bpy.types.VIEW3D_MT_object.remove(SEARCH_OBJECT_OT_adjust_settings)
    bpy.utils.unregister_class(OBJECT_OT_adjust_settings)
    bpy.utils.unregister_class(ClipSyncWindowProjectItem)
