
"""
Timeline Tools for DaVinci Resolve MCP
"""
from typing import List, Dict, Any

from src.server_instance import mcp
from src.context import get_resolve
from src.api.media_operations import append_clips_to_timeline as append_impl
from src.api.media_operations import create_timeline_from_clips as create_from_clips_impl
from src.api import timeline_operations

@mcp.resource("resolve://timelines")
def list_timelines() -> List[str]:
    """List all timelines in the current project."""
    resolve = get_resolve()
    if resolve is None: return ["Error: Not connected"]
    
    pm = resolve.GetProjectManager()
    if not pm: return ["Error: No Project Manager"]
    
    project = pm.GetCurrentProject()
    if not project: return ["Error: No project open"]
    
    count = project.GetTimelineCount()
    timelines = []
    for i in range(1, count + 1):
        tl = project.GetTimelineByIndex(i)
        if tl: timelines.append(tl.GetName())
    return timelines

@mcp.resource("resolve://current-timeline")
def get_current_timeline() -> Dict[str, Any]:
    """Get information about the current timeline."""
    resolve = get_resolve()
    if resolve is None: return {"error": "Not connected"}
    
    pm = resolve.GetProjectManager()
    if not pm: return {"error": "Failed to get Project Manager"}
    
    project = pm.GetCurrentProject()
    if not project: return {"error": "No project open"}
    
    timeline = project.GetCurrentTimeline()
    if not timeline: return {"error": "No timeline active"}
    
    return {
        "name": timeline.GetName(),
        "fps": timeline.GetSetting("timelineFrameRate"),
        "resolution": {
            "width": timeline.GetSetting("timelineResolutionWidth"),
            "height": timeline.GetSetting("timelineResolutionHeight")
        },
        "duration": timeline.GetEndFrame() - timeline.GetStartFrame() + 1
    }

@mcp.resource("resolve://timeline-tracks/{timeline_name}")
def get_timeline_tracks(timeline_name: str = None) -> Dict[str, Any]:
    """Get the track structure of a timeline."""
    resolve = get_resolve()
    return timeline_operations.get_timeline_tracks(resolve, timeline_name)

@mcp.tool()
def create_timeline(name: str) -> str:
    """Create a new timeline."""
    resolve = get_resolve()
    if resolve is None: return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    if not pm: return "Error: No Project Manager"
    
    project = pm.GetCurrentProject()
    if not project: return "Error: No project open"
    
    media_pool = project.GetMediaPool()
    if media_pool and media_pool.CreateEmptyTimeline(name):
        return f"Created timeline '{name}'"
    return f"Failed to create timeline '{name}'"

@mcp.tool()
def create_empty_timeline(name: str, 
                       frame_rate: str = None, 
                       resolution_width: int = None, 
                       resolution_height: int = None,
                       start_timecode: str = None,
                       video_tracks: int = None,
                       audio_tracks: int = None) -> str:
    """Create a new timeline with custom settings."""
    resolve = get_resolve()
    return timeline_operations.create_empty_timeline(
        resolve, name, frame_rate, resolution_width, 
        resolution_height, start_timecode, 
        video_tracks, audio_tracks
    )

@mcp.tool()
def delete_timeline(name: str) -> str:
    """Delete a timeline by name."""
    resolve = get_resolve()
    return timeline_operations.delete_timeline(resolve, name)

@mcp.tool()
def set_current_timeline(name: str) -> str:
    """Switch to a timeline by name."""
    resolve = get_resolve()
    if resolve is None: return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    if not pm: return "Error: No Project Manager"
    
    project = pm.GetCurrentProject()
    if not project: return "Error: No project open"
    
    count = project.GetTimelineCount()
    for i in range(1, count + 1):
        tl = project.GetTimelineByIndex(i)
        if tl and tl.GetName() == name:
            if project.SetCurrentTimeline(tl):
                return f"Switched to '{name}'"
    return f"Timeline '{name}' not found"

@mcp.tool()
def add_marker(frame: int = None, color: str = "Blue", note: str = "") -> str:
    """Add a marker to the timeline."""
    resolve = get_resolve()
    return timeline_operations.add_marker(resolve, frame, color, note)

@mcp.resource("resolve://timeline-clips")
def list_timeline_clips() -> List[Dict[str, Any]]:
    """List all clips in the current timeline."""
    resolve = get_resolve()
    if resolve is None: return [{"error": "Not connected"}]
    
    pm = resolve.GetProjectManager()
    if not pm: return [{"error": "No Project Manager"}]
    
    project = pm.GetCurrentProject()
    if not project: return [{"error": "No project open"}]
    
    timeline = project.GetCurrentTimeline()
    if not timeline: return [{"error": "No timeline active"}]
    
    try:
        video_count = timeline.GetTrackCount("video")
        audio_count = timeline.GetTrackCount("audio")
        clips = []
        
        for i in range(1, video_count + 1):
            items = timeline.GetItemListInTrack("video", i)
            if items:
                for item in items:
                    clips.append({
                        "name": item.GetName(),
                        "type": "video",
                        "track": i,
                        "start": item.GetStart(),
                        "end": item.GetEnd(),
                        "duration": item.GetDuration()
                    })
                    
        for i in range(1, audio_count + 1):
            items = timeline.GetItemListInTrack("audio", i)
            if items:
                for item in items:
                    clips.append({
                        "name": item.GetName(),
                        "type": "audio",
                        "track": i,
                        "start": item.GetStart(),
                        "end": item.GetEnd(),
                        "duration": item.GetDuration()
                    })
        
        if not clips: return [{"info": "No clips found"}]
        return clips
    except Exception as e:
        return [{"error": f"Error listing clips: {e}"}]



@mcp.tool()
def append_clips_to_timeline(clip_names: List[str], timeline_name: str = None) -> str:
    """Append a list of clips (by name) to the timeline."""
    resolve = get_resolve()
    return append_impl(resolve, clip_names, timeline_name)

@mcp.tool()
def create_timeline_from_clips(name: str, clip_names: List[str]) -> str:
    """Create a new timeline containing the specified clips."""
    resolve = get_resolve()
    return create_from_clips_impl(resolve, name, clip_names)


@mcp.resource("resolve://timeline-items")
def get_timeline_items() -> List[Dict[str, Any]]:
    """Get all items in the current timeline."""
    resolve = get_resolve()
    return timeline_operations.get_timeline_items(resolve)

@mcp.resource("resolve://timeline-item/{item_id}")
def get_timeline_item_properties(item_id: str) -> Dict[str, Any]:
    """Get properties of a specific timeline item."""
    resolve = get_resolve()
    return timeline_operations.get_timeline_item_properties(resolve, item_id)

@mcp.tool()
def set_timeline_item_transform(item_id: str, property_name: str, value: float) -> str:
    """Set a transform property (Pan, Tilt, ZoomX, ZoomY, Rotation, Pitch, Yaw, AnchorPointX, AnchorPointY)."""
    resolve = get_resolve()
    return timeline_operations.set_timeline_item_property(resolve, item_id, property_name, value)

@mcp.tool()
def set_timeline_item_crop(item_id: str, crop_type: str, value: float) -> str:
    """Set crop property specified by type (left, right, top, bottom)."""
    resolve = get_resolve()
    prop_map = {
        "left": "CropLeft",
        "right": "CropRight", 
        "top": "CropTop",
        "bottom": "CropBottom"
    }
    key = prop_map.get(crop_type.lower())
    if not key: return "Invalid crop type. Use left, right, top, or bottom."
    return timeline_operations.set_timeline_item_property(resolve, item_id, key, value)


# --- Timeline Export/Import ---

@mcp.tool()
def export_timeline(file_path: str, export_type: str = "edl", 
                    export_subtype: str = "none", timeline_name: str = None) -> str:
    """Export timeline to file (EDL, XML, AAF, FCPXML, etc).
    
    Args:
        file_path: Path where the file will be saved
        export_type: One of 'aaf', 'edl', 'xml', 'fcpxml_1_8', 'fcpxml_1_9', 'fcpxml_1_10', 
                     'drt', 'csv', 'txt', 'otio', 'ale'
        export_subtype: For AAF: 'aaf_new'/'aaf_existing'. For EDL: 'cdl'/'sdl'/'missing_clips'/'none'
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    return timeline_operations.export_timeline(resolve, file_path, export_type, export_subtype, timeline_name)


@mcp.tool()
def import_timeline_from_file(file_path: str, timeline_name: str = None,
                               import_source_clips: bool = True, 
                               source_clips_path: str = None) -> str:
    """Import timeline from file (AAF, EDL, XML, FCPXML, DRT, ADL, OTIO).
    
    Args:
        file_path: Path to the file to import
        timeline_name: Optional name for the imported timeline
        import_source_clips: Whether to import source clips into media pool
        source_clips_path: Optional path to search for source clips
    """
    resolve = get_resolve()
    return timeline_operations.import_timeline_from_file(
        resolve, file_path, timeline_name, import_source_clips, source_clips_path
    )


# --- Timeline Markers ---

@mcp.resource("resolve://timeline-markers/{timeline_name}")
def get_timeline_markers(timeline_name: str = None) -> Dict[str, Any]:
    """Get all markers from a timeline."""
    resolve = get_resolve()
    return timeline_operations.get_timeline_markers(resolve, timeline_name)


@mcp.tool()
def delete_timeline_markers(color: str = "All", timeline_name: str = None) -> str:
    """Delete markers from a timeline.
    
    Args:
        color: Marker color to delete, or 'All' to delete all markers
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    return timeline_operations.delete_timeline_markers(resolve, color, timeline_name)


# --- Timeline Duplication ---

@mcp.tool()
def duplicate_timeline(new_name: str = None, timeline_name: str = None) -> str:
    """Duplicate a timeline.
    
    Args:
        new_name: Optional name for the duplicated timeline
        timeline_name: Optional source timeline name, uses current if not specified
    """
    resolve = get_resolve()
    return timeline_operations.duplicate_timeline(resolve, new_name, timeline_name)


# ============================================================
# Phase 4.1-4.3: Timeline Track Management Tools
# ============================================================

@mcp.tool()
def add_track(track_type: str, sub_track_type: str = None, 
              timeline_name: str = None) -> str:
    """Add a new track to the timeline.
    
    Args:
        track_type: 'video', 'audio', or 'subtitle'
        sub_track_type: For audio: 'mono', 'stereo', '5.1', '7.1', 'adaptive'
        timeline_name: Optional timeline name
    """
    resolve = get_resolve()
    return timeline_operations.add_track(resolve, track_type, sub_track_type, timeline_name)


@mcp.tool()
def delete_track(track_type: str, track_index: int, timeline_name: str = None) -> str:
    """Delete a track from the timeline.
    
    Args:
        track_type: 'video', 'audio', or 'subtitle'
        track_index: 1-based track index
        timeline_name: Optional timeline name
    """
    resolve = get_resolve()
    return timeline_operations.delete_track(resolve, track_type, track_index, timeline_name)


@mcp.tool()
def get_track_name(track_type: str, track_index: int, timeline_name: str = None) -> Dict[str, Any]:
    """Get the name of a track.
    
    Args:
        track_type: 'video', 'audio', or 'subtitle'
        track_index: 1-based track index
    """
    resolve = get_resolve()
    return timeline_operations.get_track_name(resolve, track_type, int(track_index), timeline_name)


@mcp.tool()
def set_track_name(track_type: str, track_index: int, name: str, 
                   timeline_name: str = None) -> str:
    """Set the name of a track.
    
    Args:
        track_type: 'video', 'audio', or 'subtitle'
        track_index: 1-based track index
        name: New name for the track
    """
    resolve = get_resolve()
    return timeline_operations.set_track_name(resolve, track_type, track_index, name, timeline_name)


@mcp.tool()
def set_track_enabled(track_type: str, track_index: int, enabled: bool,
                      timeline_name: str = None) -> str:
    """Enable or disable a track.
    
    Args:
        track_type: 'video', 'audio', or 'subtitle'
        track_index: 1-based track index
        enabled: True to enable, False to disable
    """
    resolve = get_resolve()
    return timeline_operations.set_track_enabled(resolve, track_type, track_index, enabled, timeline_name)


@mcp.tool()
def set_track_locked(track_type: str, track_index: int, locked: bool,
                     timeline_name: str = None) -> str:
    """Lock or unlock a track.
    
    Args:
        track_type: 'video', 'audio', or 'subtitle'
        track_index: 1-based track index
        locked: True to lock, False to unlock
    """
    resolve = get_resolve()
    return timeline_operations.set_track_locked(resolve, track_type, track_index, locked, timeline_name)


@mcp.tool()
def get_track_status(track_type: str, track_index: int, timeline_name: str = None) -> Dict[str, Any]:
    """Get track enabled/locked status.
    
    Args:
        track_type: 'video', 'audio', or 'subtitle'
        track_index: 1-based track index
    """
    resolve = get_resolve()
    return timeline_operations.get_track_status(resolve, track_type, int(track_index), timeline_name)


# --- Timecode Tools ---

@mcp.tool()
def get_current_timecode(timeline_name: str = None) -> Dict[str, Any]:
    """Get current playhead timecode."""
    resolve = get_resolve()
    return timeline_operations.get_current_timecode(resolve, timeline_name)


@mcp.tool()
def set_current_timecode(timecode: str, timeline_name: str = None) -> str:
    """Set playhead to timecode.
    
    Args:
        timecode: Timecode string (e.g., '01:00:00:00')
    """
    resolve = get_resolve()
    return timeline_operations.set_current_timecode(resolve, timecode, timeline_name)


# --- Generator and Title Tools ---

@mcp.tool()
def insert_generator(generator_name: str, duration: int = None, 
                     timeline_name: str = None) -> str:
    """Insert a generator into the timeline.
    
    Args:
        generator_name: Name of the generator (e.g., 'Solid Color', '10 Point Grid')
        duration: Optional duration in frames
    """
    resolve = get_resolve()
    return timeline_operations.insert_generator(resolve, generator_name, duration, timeline_name)


@mcp.tool()
def insert_title(title_name: str, duration: int = None, 
                 timeline_name: str = None) -> str:
    """Insert a title into the timeline.
    
    Args:
        title_name: Name of the title template (e.g., 'Text+', 'Scroll')
        duration: Optional duration in frames
    """
    resolve = get_resolve()
    return timeline_operations.insert_title(resolve, title_name, duration, timeline_name)


@mcp.tool()
def insert_fusion_title(title_name: str, duration: int = None,
                        timeline_name: str = None) -> str:
    """Insert a Fusion title into the timeline."""
    resolve = get_resolve()
    return timeline_operations.insert_fusion_title(resolve, title_name, duration, timeline_name)


# --- Special Timeline Operations ---

@mcp.tool()
def create_compound_clip(clip_info: Dict[str, Any] = None,
                         timeline_name: str = None) -> str:
    """Create a compound clip from selected items."""
    resolve = get_resolve()
    return timeline_operations.create_compound_clip(resolve, clip_info, timeline_name)


@mcp.tool()
def create_fusion_clip(timeline_name: str = None) -> str:
    """Create a Fusion clip from selected items."""
    resolve = get_resolve()
    return timeline_operations.create_fusion_clip(resolve, timeline_name)


@mcp.tool()
def detect_scene_cuts(timeline_name: str = None) -> str:
    """Detect scene cuts in the timeline."""
    resolve = get_resolve()
    return timeline_operations.detect_scene_cuts(resolve, timeline_name)


@mcp.tool()
def rename_timeline(new_name: str, timeline_name: str = None) -> str:
    """Rename a timeline.
    
    Args:
        new_name: New name for the timeline
        timeline_name: Optional current name, uses current if not specified
    """
    resolve = get_resolve()
    return timeline_operations.rename_timeline(resolve, new_name, timeline_name)


@mcp.tool()
def get_timeline_id(timeline_name: str = None) -> Dict[str, Any]:
    """Get the unique ID of a timeline."""
    resolve = get_resolve()
    return timeline_operations.get_timeline_unique_id(resolve, timeline_name)


# ============================================================
# Phase 5: TimelineItem Extended Tools
# ============================================================

@mcp.tool()
def get_timeline_item_property(clip_name: str, property_key: str = None,
                               timeline_name: str = None) -> Dict[str, Any]:
    """Get TimelineItem property or all properties.
    
    Args:
        clip_name: Name of the clip in timeline
        property_key: Optional specific property (returns all if not specified)
    """
    resolve = get_resolve()
    return timeline_operations.get_timeline_item_property(resolve, clip_name, property_key, timeline_name)


@mcp.tool()
def set_timeline_item_property(clip_name: str, property_key: str, 
                               property_value: float, timeline_name: str = None) -> str:
    """Set a TimelineItem property (Pan, Tilt, ZoomX, ZoomY, CropLeft, etc.)."""
    resolve = get_resolve()
    return timeline_operations.set_timeline_item_property(resolve, clip_name, property_key, property_value, timeline_name)


@mcp.tool()
def get_timeline_item_info(clip_name: str, timeline_name: str = None) -> Dict[str, Any]:
    """Get detailed info about a timeline item."""
    resolve = get_resolve()
    return timeline_operations.get_timeline_item_info(resolve, clip_name, timeline_name)


@mcp.tool()
def set_timeline_item_enabled(clip_name: str, enabled: bool, 
                              timeline_name: str = None) -> str:
    """Enable or disable a timeline item."""
    resolve = get_resolve()
    return timeline_operations.set_timeline_item_enabled(resolve, clip_name, enabled, timeline_name)


# --- Color Versions ---

@mcp.tool()
def add_color_version(clip_name: str, version_name: str, 
                      version_type: int = 0, timeline_name: str = None) -> str:
    """Add a new color version to a clip (0=local, 1=remote)."""
    resolve = get_resolve()
    return timeline_operations.add_color_version(resolve, clip_name, version_name, version_type, timeline_name)


@mcp.tool()
def get_color_versions(clip_name: str, version_type: int = 0, 
                       timeline_name: str = None) -> Dict[str, Any]:
    """Get list of color versions for a clip."""
    resolve = get_resolve()
    return timeline_operations.get_color_versions(resolve, clip_name, version_type, timeline_name)


@mcp.tool()
def load_color_version(clip_name: str, version_name: str,
                       version_type: int = 0, timeline_name: str = None) -> str:
    """Load a color version by name."""
    resolve = get_resolve()
    return timeline_operations.load_color_version(resolve, clip_name, version_name, version_type, timeline_name)


# --- Effects/Processing ---

@mcp.tool()
def stabilize_clip(clip_name: str, timeline_name: str = None) -> str:
    """Stabilize a timeline clip."""
    resolve = get_resolve()
    return timeline_operations.stabilize_clip(resolve, clip_name, timeline_name)


@mcp.tool()
def smart_reframe_clip(clip_name: str, timeline_name: str = None) -> str:
    """Apply Smart Reframe to a clip."""
    resolve = get_resolve()
    return timeline_operations.smart_reframe_clip(resolve, clip_name, timeline_name)


@mcp.tool()
def create_magic_mask(clip_name: str, mode: str = "F", 
                      timeline_name: str = None) -> str:
    """Create Magic Mask on a clip (mode: F/B/BI)."""
    resolve = get_resolve()
    return timeline_operations.create_magic_mask(resolve, clip_name, mode, timeline_name)


# --- Markers/Flags/Color ---

@mcp.tool()
def add_timeline_item_marker(clip_name: str, frame: int, color: str = "Blue",
                             name: str = "", note: str = "", 
                             timeline_name: str = None) -> str:
    """Add a marker to a timeline item."""
    resolve = get_resolve()
    return timeline_operations.add_timeline_item_marker(resolve, clip_name, frame, color, name, note, 1, timeline_name)


@mcp.tool()
def get_timeline_item_markers(clip_name: str, timeline_name: str = None) -> Dict[str, Any]:
    """Get markers from a timeline item."""
    resolve = get_resolve()
    return timeline_operations.get_timeline_item_markers(resolve, clip_name, timeline_name)


@mcp.tool()
def set_timeline_item_color(clip_name: str, color: str, 
                            timeline_name: str = None) -> str:
    """Set the color label of a timeline item."""
    resolve = get_resolve()
    return timeline_operations.set_timeline_item_color(resolve, clip_name, color, timeline_name)


@mcp.tool()
def add_timeline_item_flag(clip_name: str, color: str, 
                           timeline_name: str = None) -> str:
    """Add a flag to a timeline item."""
    resolve = get_resolve()
    return timeline_operations.add_timeline_item_flag(resolve, clip_name, color, timeline_name)


# --- Cache/Grades ---

@mcp.tool()
def set_color_output_cache(clip_name: str, enabled: bool, 
                           timeline_name: str = None) -> str:
    """Enable/disable color output cache for a clip."""
    resolve = get_resolve()
    return timeline_operations.set_color_output_cache(resolve, clip_name, enabled, timeline_name)


@mcp.tool()
def copy_grades(source_clip: str, target_clips: List[str], 
                timeline_name: str = None) -> str:
    """Copy grades from source clip to target clips."""
    resolve = get_resolve()
    return timeline_operations.copy_grades(resolve, source_clip, target_clips, timeline_name)


@mcp.tool()
def get_linked_items(clip_name: str, timeline_name: str = None) -> Dict[str, Any]:
    """Get linked items for a timeline item."""
    resolve = get_resolve()
    return timeline_operations.get_linked_items(resolve, clip_name, timeline_name)


# ============================================================
# Phase 1.3: Critical Timeline Extensions
# ============================================================

@mcp.tool()
def delete_timeline_clips(clip_names: List[str], ripple: bool = False,
                          timeline_name: str = None) -> str:
    """Delete clips from the timeline.
    
    Args:
        clip_names: List of clip names to delete
        ripple: If True, perform ripple delete (close gaps)
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return "Error: No Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return "Error: No project open"
    
    timeline = project.GetCurrentTimeline()
    if timeline_name:
        count = project.GetTimelineCount()
        for i in range(1, count + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    
    if not timeline:
        return "Error: No timeline found"
    
    try:
        # Find timeline items by name
        items_to_delete = []
        for track_type in ["video", "audio"]:
            track_count = timeline.GetTrackCount(track_type)
            for i in range(1, track_count + 1):
                items = timeline.GetItemListInTrack(track_type, i)
                if items:
                    for item in items:
                        if item.GetName() in clip_names:
                            items_to_delete.append(item)
        
        if not items_to_delete:
            return f"No clips found matching: {', '.join(clip_names)}"
        
        result = timeline.DeleteClips(items_to_delete, ripple)
        if result:
            return f"Deleted {len(items_to_delete)} clip(s)" + (" with ripple" if ripple else "")
        return "Failed to delete clips"
    except Exception as e:
        return f"Error deleting clips: {e}"


@mcp.tool()
def get_timeline_setting(setting_name: str, timeline_name: str = None) -> str:
    """Get a timeline setting value.
    
    Args:
        setting_name: Name of the setting (e.g., 'timelineFrameRate', 'timelineResolutionWidth')
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return "Error: No Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return "Error: No project open"
    
    timeline = project.GetCurrentTimeline()
    if timeline_name:
        count = project.GetTimelineCount()
        for i in range(1, count + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    
    if not timeline:
        return "Error: No timeline found"
    
    try:
        if setting_name:
            value = timeline.GetSetting(setting_name)
            return f"{setting_name}: {value}"
        else:
            # Return all settings
            all_settings = timeline.GetSetting("")
            return str(all_settings)
    except Exception as e:
        return f"Error getting setting: {e}"


@mcp.tool()
def set_timeline_setting(setting_name: str, setting_value: str, 
                         timeline_name: str = None) -> str:
    """Set a timeline setting value.
    
    Args:
        setting_name: Name of the setting
        setting_value: Value to set
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return "Error: No Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return "Error: No project open"
    
    timeline = project.GetCurrentTimeline()
    if timeline_name:
        count = project.GetTimelineCount()
        for i in range(1, count + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    
    if not timeline:
        return "Error: No timeline found"
    
    try:
        result = timeline.SetSetting(setting_name, setting_value)
        if result:
            return f"Set {setting_name} to '{setting_value}'"
        return f"Failed to set {setting_name}"
    except Exception as e:
        return f"Error setting value: {e}"


@mcp.tool()
def get_current_video_item(timeline_name: str = None) -> Dict[str, Any]:
    """Get the current video item at playhead position.
    
    Args:
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    if not pm:
        return {"error": "No Project Manager"}
    
    project = pm.GetCurrentProject()
    if not project:
        return {"error": "No project open"}
    
    timeline = project.GetCurrentTimeline()
    if timeline_name:
        count = project.GetTimelineCount()
        for i in range(1, count + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    
    if not timeline:
        return {"error": "No timeline found"}
    
    try:
        item = timeline.GetCurrentVideoItem()
        if item:
            return {
                "name": item.GetName(),
                "start": item.GetStart(),
                "end": item.GetEnd(),
                "duration": item.GetDuration(),
                "enabled": item.GetClipEnabled() if hasattr(item, 'GetClipEnabled') else None
            }
        return {"info": "No video item at current position"}
    except Exception as e:
        return {"error": f"Error getting current item: {e}"}


@mcp.tool()
def create_subtitles_from_audio(language: str = "auto",
                                preset: str = "default",
                                chars_per_line: int = 42,
                                line_break: str = "single",
                                gap: int = 0,
                                timeline_name: str = None) -> str:
    """Create subtitles from audio using DaVinci Neural Engine.
    
    Requires DaVinci Resolve Studio with Neural Engine support.
    
    Args:
        language: Language code or 'auto' for automatic detection
        preset: 'default', 'teletext', or 'netflix'
        chars_per_line: Max characters per line (1-60, default: 42)
        line_break: 'single' or 'double'
        gap: Gap in frames between captions (0-10)
        timeline_name: Optional timeline name
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return "Error: No Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return "Error: No project open"
    
    timeline = project.GetCurrentTimeline()
    if timeline_name:
        count = project.GetTimelineCount()
        for i in range(1, count + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    
    if not timeline:
        return "Error: No timeline found"
    
    try:
        # Build settings dict using Resolve constants if available
        settings = {}
        
        # Map language string to constant
        lang_map = {
            "auto": "AUTO_CAPTION_AUTO",
            "english": "AUTO_CAPTION_ENGLISH",
            "spanish": "AUTO_CAPTION_SPANISH",
            "french": "AUTO_CAPTION_FRENCH",
            "german": "AUTO_CAPTION_GERMAN",
            "italian": "AUTO_CAPTION_ITALIAN",
            "portuguese": "AUTO_CAPTION_PORTUGUESE",
            "russian": "AUTO_CAPTION_RUSSIAN",
            "japanese": "AUTO_CAPTION_JAPANESE",
            "korean": "AUTO_CAPTION_KOREAN",
            "mandarin": "AUTO_CAPTION_MANDARIN_SIMPLIFIED",
        }
        
        # Call CreateSubtitlesFromAudio
        result = timeline.CreateSubtitlesFromAudio(settings if settings else None)
        if result:
            return f"Started subtitle generation for timeline '{timeline.GetName()}'"
        return "Failed to start subtitle generation (requires Studio version)"
    except AttributeError:
        return "Error: CreateSubtitlesFromAudio not available (requires DaVinci Resolve 18.5+)"
    except Exception as e:
        return f"Error creating subtitles: {e}"


@mcp.tool()
def get_timeline_bounds(timeline_name: str = None) -> Dict[str, Any]:
    """Get start and end frames of the timeline.
    
    Args:
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    if not pm:
        return {"error": "No Project Manager"}
    
    project = pm.GetCurrentProject()
    if not project:
        return {"error": "No project open"}
    
    timeline = project.GetCurrentTimeline()
    if timeline_name:
        count = project.GetTimelineCount()
        for i in range(1, count + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    
    if not timeline:
        return {"error": "No timeline found"}
    
    try:
        start_frame = timeline.GetStartFrame()
        end_frame = timeline.GetEndFrame()
        start_tc = timeline.GetStartTimecode() if hasattr(timeline, 'GetStartTimecode') else None
        
        return {
            "timeline_name": timeline.GetName(),
            "start_frame": start_frame,
            "end_frame": end_frame,
            "duration_frames": end_frame - start_frame + 1,
            "start_timecode": start_tc
        }
    except Exception as e:
        return {"error": f"Error getting timeline bounds: {e}"}


@mcp.tool()
def set_timeline_start_timecode(timecode: str, timeline_name: str = None) -> str:
    """Set the start timecode of the timeline.
    
    Args:
        timecode: Start timecode string (e.g., '01:00:00:00')
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return "Error: No Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return "Error: No project open"
    
    timeline = project.GetCurrentTimeline()
    if timeline_name:
        count = project.GetTimelineCount()
        for i in range(1, count + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    
    if not timeline:
        return "Error: No timeline found"
    
    try:
        result = timeline.SetStartTimecode(timecode)
        if result:
            return f"Set start timecode to '{timecode}'"
        return "Failed to set start timecode"
    except Exception as e:
        return f"Error setting timecode: {e}"
