"""Discovery helpers for ClipSync Window Capture projects.

This module intentionally has no Blender dependency so the HTTP contract and
filtering can be tested with a regular Python interpreter.
"""

import json
import re
import urllib.parse
import urllib.request


_SAFE_PROJECT_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
# JSON discovery payload limit only. This is not a frame width/height limit;
# frame dimensions come from the canvas-bridge RGBA endpoint.
_MAX_PROJECT_RESPONSE_BYTES = 1_048_576


def project_selected_by_default(project_id, selected_ids):
    """Select every discovered project until a saved subset exists."""
    selected_ids = set(selected_ids)
    return not selected_ids or project_id in selected_ids


def loopback_url(port):
    """Build the fixed localhost URL from a user-configurable port only."""
    port = int(port)
    if port < 1024 or port > 65535:
        raise ValueError("ClipSync port must be between 1024 and 65535")
    return f"http://127.0.0.1:{port}"


def port_from_legacy_url(value, fallback=48123):
    """Migrate the previous free-form URL setting without exposing it again."""
    try:
        parsed = urllib.parse.urlsplit(str(value))
        return parsed.port or fallback
    except (TypeError, ValueError):
        return fallback


def migrate_legacy_window_capture_port(settings, fallback=48123):
    """Copy settings and migrate the old URL key before defaults are merged."""
    migrated = dict(settings)
    if "window_capture_port" not in migrated and "window_capture_url" in migrated:
        migrated["window_capture_port"] = port_from_legacy_url(
            migrated["window_capture_url"], fallback
        )
    return migrated


def active_window_projects(payload):
    """Return active projects with the FPS configured by canvas-bridge."""
    if not isinstance(payload, list):
        raise ValueError("ClipSync /projects response must be a JSON array")

    projects = []
    seen = set()
    for project in payload:
        if not isinstance(project, dict):
            continue
        project_id = project.get("id")
        fps = project.get("fps")
        if (
            project.get("active") is not True
            or project.get("archived") is True
            or not isinstance(project_id, str)
            or not _SAFE_PROJECT_ID.fullmatch(project_id)
            or isinstance(fps, bool)
            or not isinstance(fps, int)
            or fps < 1
            or project_id in seen
        ):
            continue
        name = project.get("name")
        if not isinstance(name, str):
            name = ""
        seen.add(project_id)
        projects.append({"id": project_id, "name": name.strip(), "fps": fps})
    return projects


def resolve_selected_window_projects(projects, selected_ids):
    """Split saved selections into currently available projects and stale IDs."""
    projects_by_id = {project["id"]: project for project in projects}
    available = []
    unavailable_ids = []
    for project_id in dict.fromkeys(selected_ids):
        project = projects_by_id.get(project_id)
        if project is None:
            unavailable_ids.append(project_id)
        else:
            available.append(project)
    return available, unavailable_ids


def fetch_active_window_projects(base_url, timeout=1.5):
    """Fetch the projects whose Sync toggle is ON in ClipSync."""
    parsed = urllib.parse.urlsplit(base_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("invalid local ClipSync endpoint")

    projects_url = urllib.parse.urljoin(base_url.rstrip("/") + "/", "projects")
    request = urllib.request.Request(
        projects_url,
        headers={"Accept": "application/json", "Connection": "close"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read(_MAX_PROJECT_RESPONSE_BYTES + 1)
        if len(payload) > _MAX_PROJECT_RESPONSE_BYTES:
            raise ValueError("ClipSync /projects response is too large")
    return active_window_projects(json.loads(payload.decode("utf-8")))
