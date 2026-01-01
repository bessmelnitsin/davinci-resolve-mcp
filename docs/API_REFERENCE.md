# DaVinci Resolve MCP Server API Reference

This document provides a comprehensive reference for the tools and resources available in the DaVinci Resolve MCP Server.

## 📁 Project Operations
*Module: `src/api/project_operations.py`*

### Tools

#### `list_projects`
List all available projects in the current database.
- **Returns**: `List[str]` - Names of available projects.

#### `get_current_project_name`
Get the name of the currently open project.
- **Returns**: `str` - Name of the current project.

#### `open_project`
Open a project by name.
- **Args**:
  - `name` (str): Name of the project to open.
- **Returns**: `str` - Success or error message.

#### `create_project`
Create a new project with the given name.
- **Args**:
  - `name` (str): Name for the new project.
- **Returns**: `str` - Success or error message.

#### `save_project`
Save the current project.
- **Returns**: `str` - Success or error message.

---

## 🎬 Timeline Operations
*Module: `src/api/timeline_operations.py`*

### Tools

#### `list_timelines`
List all timelines in the current project.
- **Returns**: `List[str]` - Names of timelines.

#### `get_current_timeline_info`
Get information about the current timeline.
- **Returns**: `Dict[str, Any]` - Timeline properties (name, framerate, resolution, etc.).

#### `create_timeline`
Create a new timeline with the given name.
- **Args**:
  - `name` (str): Name for the timeline.
- **Returns**: `str` - Success or error message.

#### `set_current_timeline`
Switch to a timeline by name.
- **Args**:
  - `name` (str): Name of the timeline to activate.
- **Returns**: `str` - Success or error message.

#### `add_marker`
Add a marker at the specified frame in the current timeline.
- **Args**:
  - `frame` (int, optional): Frame number (defaults to auto-selection).
  - `color` (str): Marker color (e.g., "Blue", "Red").
  - `note` (str): Text note for the marker.
- **Returns**: `str` - Success or error message.

---

## 🖼️ Gallery Operations
*Module: `src/api/gallery_operations.py`*

### Tools

#### `get_color_presets`
List available color presets (stills) from the gallery.
- **Returns**: `List[Dict]` - List of presets with 'album' and 'name'.

#### `save_color_preset`
Save the current grade as a preset (still) in the gallery.
- **Args**:
  - `name` (str): Name for the new preset.
  - `album_name` (str, optional): Target album name (defaults to current).
- **Returns**: `str` - Success or error message.

#### `apply_color_preset`
Apply a color preset to the current clip.
- **Args**:
  - `name` (str): Name of the preset to apply.
  - `album_name` (str, optional): Source album name.
- **Returns**: `str` - Success or error message.

#### `delete_color_preset`
Delete a color preset from the gallery.
- **Args**:
  - `name` (str): Name of the preset to delete.
  - `album_name` (str, optional): Album name.
- **Returns**: `str` - Success or error message.

#### `create_color_preset_album`
Create a new gallery album.
- **Args**:
  - `album_name` (str): Name for the new album.
- **Returns**: `str` - Success or error message.

#### `delete_color_preset_album`
Delete a gallery album.
- **Args**:
  - `album_name` (str): Name of the album to delete.
- **Returns**: `str` - Success or error message.

---

## 📤 Export Operations
*Module: `src/api/export_operations.py`*

### Tools

#### `export_lut`
Export the current grade as a LUT.
- **Args**:
  - `file_name` (str): Name for the LUT file (without extension).
- **Returns**: `str` - Success or error message.

#### `get_lut_formats`
Get a list of supported LUT export formats.
- **Returns**: `List[str]` - Supported formats (e.g., "DaVinci Cube", "Panasonic V35").

#### `export_all_powergrade_luts`
Export all PowerGrades as `.cube` files to a directory.
- **Args**:
  - `export_dir` (str): Absolute path to the export directory.
- **Returns**: `str` - Summary of export results.

---

## 🔑 Keyframe Operations
*Module: `src/api/keyframe_operations.py`*

### Resources
- `resolve://timeline-item/{timeline_item_id}/keyframes/{property_name}`: Get keyframes for a specific property.

### Tools

#### `add_keyframe`
Add a keyframe to a timeline item property.
- **Args**:
  - `timeline_item_id` (str): The timeline item ID.
  - `property_name` (str): Property to animate (e.g., "Pan", "ZoomX").
  - `frame` (int): Frame number.
  - `value` (float): Value to set.
- **Returns**: `str` - Success or error message.

#### `modify_keyframe`
Modify an existing keyframe's value.
- **Args**:
  - `timeline_item_id` (str): The timeline item ID.
  - `property_name` (str): Property name.
  - `frame` (int): Frame number of the existing keyframe.
  - `value` (float): New value.
- **Returns**: `str` - Success or error message.

#### `delete_keyframe`
Delete a keyframe.
- **Args**:
  - `timeline_item_id` (str): The timeline item ID.
  - `property_name` (str): Property name.
  - `frame` (int): Frame number of the keyframe to delete.
- **Returns**: `str` - Success or error message.

---

## 📝 Transcription Operations
*Module: `src/api/transcription_operations.py`*

### Tools

#### `transcribe_clip_to_cache`
Run Whisper transcription on a clip and cache the result.
- **Args**:
  - `clip_name` (str): Name of the clip.
  - `model_size` (str): Whisper model size (default "large-v3").
  - `force_retranscribe` (bool): Ignore existing cache if True.
- **Returns**: `str` - Path to cached transcription or error.

#### `get_cached_transcription`
Retrieve cached transcription for a clip.
- **Args**:
  - `clip_name` (str): Name of the clip.
- **Returns**: `Dict` or `str` - Transcription data or error.

#### `clear_folder_transcription`
Clear internal DaVinci Resolve transcription for all clips in a folder.
- **Args**:
  - `folder_name` (str): Name of the bin/folder.
- **Returns**: `str` - Success or error message.
