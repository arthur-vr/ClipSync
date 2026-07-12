"""English base and final fallback. Context comments belong in this file."""

STRINGS = {
    # Tab label for the original .clip-file sync mode; keep the file extension literal.
    "clip_file": ".clip file",
    # Description of the .clip-file mode, presented as the established ClipSync workflow.
    "clip_file_desc": "Use the existing ClipSync .clip workflow",
    # Tab label for live capture from the companion app; use title case as a feature name.
    "window_capture": "Window Capture",
    # Description of live capture, emphasizing that frames come from the local companion app.
    "window_capture_desc": "Receive live frames from the local ClipSync app",
    # Label for the configuration tab; use a neutral noun rather than an action.
    "settings": "Settings",
    # Field label for choosing the UI language in the Settings tab.
    "language": "Language",
    # Field label for the editable loopback port; the host itself is fixed.
    "port": "Port",
    # Tooltip describing the port as belonging to the local ClipSync companion app.
    "port_desc": "Local ClipSync app port",
    # Refresh-button label using the companion app's exact “Sync ON” terminology.
    "get_sync_projects": "Get Sync ON Projects",
    # Tooltip for refreshing only projects whose Sync toggle is currently enabled.
    "get_sync_projects_desc": "Refresh projects whose Sync toggle is ON in ClipSync",
    # Empty-state message shown when the companion app has no Sync-enabled projects.
    "no_sync_projects": "No projects have Sync enabled",
    # Concise fetch error status; {error} is the underlying connection or parsing message.
    "fetch_failed": "Fetch failed: {error}",
    # Informational project count; {count} is numeric and “project(s)” avoids plural rules.
    "sync_on_count": "Sync ON: {count} project(s)",
    # Fallback display name for a project whose supplied name is blank.
    "unnamed_project": "Unnamed",
    # Validation error instructing the user to choose at least one eligible project.
    "select_project": "Select at least one project with Sync enabled",
    # Error shown when every saved selection is currently absent or Sync OFF.
    "no_available_projects": "None of the selected projects currently have Sync enabled",
    # Warning when valid projects start but stale selections are skipped.
    "projects_unavailable": "Unavailable projects were skipped: {projects}",
    # Success report after live capture starts; {count} is the number of selected projects.
    "window_capture_started": "ClipSync Window Capture started: {count} projects",
    # Error shown when local worker/timer setup fails after validation.
    "window_capture_start_failed": "Window Capture failed to start: {error}",
    # Numbered label for each .clip path field; {number} identifies the slot.
    "clip_slot": "clip slot {number}",
    # Checkbox label for sourcing files from one containing directory; phrase as an action.
    "use_parent_folder": "use parent folder",
    # Directory-picker label shown when parent-folder mode is enabled.
    "parent_folder": "parent folder",
    # Field label for the filename suffix appended by the .clip workflow.
    "suffix": "suffix",
    # Field label for the delay between .clip-file checks.
    "sync_interval": "sync interval",
    # Success report after .clip sync starts; {paths} contains the selected path list.
    "clipsync_started": "ClipSync started: {paths}",
    # Button label that opens online documentation; use a short noun.
    "document": "Document",
    # Button label that stops active synchronization; use a direct action verb.
    "stop": "Stop",
    # Confirmation report after synchronization has stopped.
    "stopped": "ClipSync stopped",
    # Confirmation report after the external documentation URL opens successfully.
    "web_link_opened": "Web link opened.",
}
