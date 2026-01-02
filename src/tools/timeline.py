
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
