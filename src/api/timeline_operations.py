#!/usr/bin/env python3
"""
DaVinci Resolve Timeline Operations
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("davinci-resolve-mcp.timeline")

def list_timelines(resolve) -> List[str]:
    """List all timelines in the current project."""
    if resolve is None:
        return ["Error: Not connected to DaVinci Resolve"]
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return ["Error: Failed to get Project Manager"]
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return ["Error: No project currently open"]
    
    timeline_count = current_project.GetTimelineCount()
    timelines = []
    
    for i in range(1, timeline_count + 1):
        timeline = current_project.GetTimelineByIndex(i)
        if timeline:
            timelines.append(timeline.GetName())
    
    return timelines if timelines else ["No timelines found in the current project"]

def get_current_timeline_info(resolve) -> Dict[str, Any]:
    """Get information about the current timeline."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return {"error": "No timeline currently active"}
    
    # Get basic timeline info
    info = {
        "name": current_timeline.GetName(),
        "framerate": current_timeline.GetSetting("timelineFrameRate"),
        "resolution": {
            "width": current_timeline.GetSetting("timelineResolutionWidth"),
            "height": current_timeline.GetSetting("timelineResolutionHeight")
        },
        "start_timecode": current_timeline.GetStartTimecode()
    }
    
    return info

def create_timeline(resolve, name: str) -> str:
    """Create a new timeline with the given name."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not name:
        return "Error: Timeline name cannot be empty"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Check if timeline already exists to avoid duplicates
    existing_timelines = list_timelines(resolve)
    if name in existing_timelines:
        return f"Error: Timeline '{name}' already exists"
    
    # Create the timeline
    timeline = media_pool.CreateEmptyTimeline(name)
    if timeline:
        return f"Successfully created timeline '{name}'"
    else:
        return f"Failed to create timeline '{name}'"

def create_empty_timeline(resolve, name: str, 
                       frame_rate: str = None, 
                       resolution_width: int = None, 
                       resolution_height: int = None,
                       start_timecode: str = None,
                       video_tracks: int = None,
                       audio_tracks: int = None) -> str:
    """Create a new timeline with the given name and custom settings.
    
    Args:
        resolve: The DaVinci Resolve instance
        name: The name for the new timeline
        frame_rate: Optional frame rate (e.g. "24", "29.97", "30", "60")
        resolution_width: Optional width in pixels (e.g. 1920)
        resolution_height: Optional height in pixels (e.g. 1080)
        start_timecode: Optional start timecode (e.g. "01:00:00:00")
        video_tracks: Optional number of video tracks (Default is project setting)
        audio_tracks: Optional number of audio tracks (Default is project setting)
        
    Returns:
        String indicating success or failure with detailed error message
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not name:
        return "Error: Timeline name cannot be empty"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Check if timeline already exists to avoid duplicates
    existing_timelines = list_timelines(resolve)
    if name in existing_timelines:
        return f"Error: Timeline '{name}' already exists"
    
    # Store original settings to restore later if needed
    original_settings = {}
    settings_to_modify = {}
    
    # Prepare settings modifications
    if frame_rate is not None:
        setting_name = "timelineFrameRate"
        original_settings[setting_name] = current_project.GetSetting(setting_name)
        settings_to_modify[setting_name] = frame_rate
    
    if resolution_width is not None:
        setting_name = "timelineResolutionWidth"
        original_settings[setting_name] = current_project.GetSetting(setting_name)
        settings_to_modify[setting_name] = str(resolution_width)
    
    if resolution_height is not None:
        setting_name = "timelineResolutionHeight"
        original_settings[setting_name] = current_project.GetSetting(setting_name)
        settings_to_modify[setting_name] = str(resolution_height)
    
    # Apply settings before creating timeline
    for setting_name, setting_value in settings_to_modify.items():
        logger.info(f"Setting project setting {setting_name} to {setting_value}")
        current_project.SetSetting(setting_name, setting_value)
    
    # Create the timeline
    timeline = media_pool.CreateEmptyTimeline(name)
    
    if not timeline:
        # Timeline creation failed, restore original settings
        for setting_name, setting_value in original_settings.items():
            current_project.SetSetting(setting_name, setting_value)
        return f"Failed to create timeline '{name}'"
    
    # Set the timeline as current to modify it
    current_project.SetCurrentTimeline(timeline)
    
    # Setup timecode if specified
    if start_timecode is not None:
        try:
            success = timeline.SetStartTimecode(start_timecode)
            if not success:
                logger.warning(f"Failed to set start timecode to {start_timecode}")
        except Exception as e:
            logger.error(f"Error setting start timecode: {str(e)}")
    
    # Add video tracks if specified
    if video_tracks is not None and video_tracks > 1:  # Timeline comes with 1 video track by default
        # Resolve does not have a direct API for adding tracks
        # This would need to be implemented using UI automation or future API versions
        logger.info(f"Custom video track count ({video_tracks}) will need to be set manually")
    
    # Add audio tracks if specified
    if audio_tracks is not None and audio_tracks > 1:  # Timeline comes with 1 audio track by default
        # Resolve does not have a direct API for adding tracks
        logger.info(f"Custom audio track count ({audio_tracks}) will need to be set manually")
    
    # Restore original settings if needed
    if original_settings:
        for setting_name, setting_value in original_settings.items():
            current_project.SetSetting(setting_name, setting_value)
    
    return f"Successfully created timeline '{name}' with custom settings"

def set_current_timeline(resolve, name: str) -> str:
    """Switch to a timeline by name."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not name:
        return "Error: Timeline name cannot be empty"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # First get a list of all timelines
    timeline_count = current_project.GetTimelineCount()
    
    for i in range(1, timeline_count + 1):
        timeline = current_project.GetTimelineByIndex(i)
        if timeline and timeline.GetName() == name:
            # Found the timeline, set it as current
            current_project.SetCurrentTimeline(timeline)
            # Verify it was set
            current_timeline = current_project.GetCurrentTimeline()
            if current_timeline and current_timeline.GetName() == name:
                return f"Successfully switched to timeline '{name}'"
            else:
                return f"Error: Failed to switch to timeline '{name}'"
    
    return f"Error: Timeline '{name}' not found"

def add_marker(resolve, frame: Optional[int] = None, color: str = "Blue", note: str = "") -> str:
    """Add a marker at the specified frame in the current timeline.
    
    Args:
        resolve: The DaVinci Resolve instance
        frame: The frame number to add the marker at (defaults to auto-selection if None)
        color: The marker color (Blue, Cyan, Green, Yellow, Red, Pink, Purple, Fuchsia, 
               Rose, Lavender, Sky, Mint, Lemon, Sand, Cocoa, Cream)
        note: Text note to add to the marker
    
    Returns:
        String indicating success or failure with detailed error message
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return "Error: No timeline currently active"
    
    # Get timeline information
    try:
        timeline_start = current_timeline.GetStartFrame()
        timeline_end = current_timeline.GetEndFrame()
        timeline_name = current_timeline.GetName()
        print(f"Timeline '{timeline_name}' frame range: {timeline_start}-{timeline_end}")
    except Exception as e:
        return f"Error: Failed to get timeline information: {str(e)}"
    
    # Validate marker color
    valid_colors = [
        "Blue", "Cyan", "Green", "Yellow", "Red", "Pink", 
        "Purple", "Fuchsia", "Rose", "Lavender", "Sky", 
        "Mint", "Lemon", "Sand", "Cocoa", "Cream"
    ]
    
    if color not in valid_colors:
        return f"Error: Invalid marker color. Valid colors are: {', '.join(valid_colors)}"
    
    try:
        # Get information about clips in the timeline
        clips = []
        for track_idx in range(1, 5):  # Check first 4 video tracks
            try:
                track_clips = current_timeline.GetItemListInTrack("video", track_idx)
                if track_clips and len(track_clips) > 0:
                    clips.extend(track_clips)
            except:
                continue
        
        if not clips:
            return "Error: No clips found in timeline. Add media to the timeline first."
        
        # Get existing markers to avoid conflicts
        existing_markers = current_timeline.GetMarkers() or {}
        
        # If no frame specified, find a good position
        if frame is None:
            # Try to find a frame in the middle of a clip that doesn't have a marker
            for clip in clips:
                clip_start = clip.GetStart()
                clip_end = clip.GetEnd()
                
                # Try middle of clip
                mid_frame = clip_start + ((clip_end - clip_start) // 2)
                if mid_frame not in existing_markers:
                    frame = mid_frame
                    break
                
                # Try middle + 1
                if (mid_frame + 1) not in existing_markers:
                    frame = mid_frame + 1
                    break
                
                # Try other positions in the clip
                for offset in [10, 20, 30, 40, 50]:
                    test_frame = clip_start + offset
                    if clip_start <= test_frame <= clip_end and test_frame not in existing_markers:
                        frame = test_frame
                        break
            
            # If we still don't have a frame, use the first valid position we can find
            if frame is None:
                for f in range(timeline_start, timeline_end, 10):
                    if f not in existing_markers:
                        # Check if this frame is within a clip
                        for clip in clips:
                            if clip.GetStart() <= f <= clip.GetEnd():
                                frame = f
                                break
                    if frame is not None:
                        break
            
            # If we still don't have a frame, report error
            if frame is None:
                return "Error: Could not find a valid frame position for marker. Try specifying a frame number."
        
        # Frame specified - validate it
        else:
            # Check if frame is within timeline bounds
            if frame < timeline_start or frame > timeline_end:
                return f"Error: Frame {frame} is out of timeline bounds ({timeline_start}-{timeline_end})"
            
            # Check if frame already has a marker
            if frame in existing_markers:
                # Suggest an alternate frame
                alternate_found = False
                alternates = [frame + 1, frame - 1, frame + 2, frame + 5, frame + 10]
                
                for alt_frame in alternates:
                    if timeline_start <= alt_frame <= timeline_end and alt_frame not in existing_markers:
                        # Check if frame is within a clip
                        for clip in clips:
                            if clip.GetStart() <= alt_frame <= clip.GetEnd():
                                return f"Error: A marker already exists at frame {frame}. Try frame {alt_frame} instead."
                
                return f"Error: A marker already exists at frame {frame}. Try a different frame position."
            
            # Verify frame is within a clip
            frame_in_clip = False
            for clip in clips:
                if clip.GetStart() <= frame <= clip.GetEnd():
                    frame_in_clip = True
                    break
            
            if not frame_in_clip:
                return f"Error: Frame {frame} is not within any media in the timeline. Markers must be on actual clips."
        
        # Add the marker
        print(f"Adding marker at frame {frame} with color {color}")
        marker_result = current_timeline.AddMarker(
            frame,  # frameId
            color,  # color
            note,   # name - we'll use the note for this
            note,   # note
            1,      # duration - default to 1 frame
            ""      # customData - not used for now
        )
        
        if marker_result:
            return f"Successfully added {color} marker at frame {frame} with note: {note}"
        else:
            return f"Failed to add marker at frame {frame}"
            
    except Exception as e:
        return f"Error adding marker: {str(e)}"

def delete_timeline(resolve, name: str) -> str:
    """Delete a timeline by name.
    
    Args:
        resolve: The DaVinci Resolve instance
        name: The name of the timeline to delete
    
    Returns:
        String indicating success or failure with detailed error message
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # First check if the timeline exists
    timeline_count = current_project.GetTimelineCount()
    target_timeline = None
    
    # Find the timeline by name
    for i in range(1, timeline_count + 1):
        timeline = current_project.GetTimelineByIndex(i)
        if timeline and timeline.GetName() == name:
            target_timeline = timeline
            break
    
    if not target_timeline:
        return f"Error: Timeline '{name}' not found"
    
    # Check if it's the current timeline
    current_timeline = current_project.GetCurrentTimeline()
    if current_timeline and current_timeline.GetName() == name:
        # We shouldn't delete the current timeline - need to switch to another one first
        # Find another timeline to switch to
        another_timeline = None
        for i in range(1, timeline_count + 1):
            timeline = current_project.GetTimelineByIndex(i)
            if timeline and timeline.GetName() != name:
                another_timeline = timeline
                break
        
        if another_timeline:
            # Switch to this timeline first
            current_project.SetCurrentTimeline(another_timeline)
        else:
            return f"Error: Cannot delete the only timeline in the project. Create a new timeline first."
    
    # Now delete the timeline
    try:
        # The DeleteTimelines method takes a list of timelines
        result = current_project.DeleteTimelines([target_timeline])
        
        if result:
            return f"Successfully deleted timeline '{name}'"
        else:
            return f"Failed to delete timeline '{name}'"
    except Exception as e:
        return f"Error deleting timeline: {str(e)}"

def get_timeline_tracks(resolve, timeline_name: str = None) -> Dict[str, Any]:
    """Get the track structure of a timeline.
    
    Args:
        resolve: The DaVinci Resolve instance
        timeline_name: Optional name of the timeline to get tracks from. Uses current timeline if None.
    
    Returns:
        Dictionary with track information
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    # Determine which timeline to use
    timeline = None
    if timeline_name:
        # Find the timeline by name
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        
        if not timeline:
            return {"error": f"Timeline '{timeline_name}' not found"}
    else:
        # Use current timeline
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return {"error": "No timeline currently active"}
    
    timeline_name = timeline.GetName()
    
    try:
        # Get track counts
        video_track_count = timeline.GetTrackCount("video")
        audio_track_count = timeline.GetTrackCount("audio")
        subtitle_track_count = timeline.GetTrackCount("subtitle")
        
        # Get track information
        tracks = {
            "name": timeline_name,
            "video": {
                "count": video_track_count,
                "tracks": []
            },
            "audio": {
                "count": audio_track_count,
                "tracks": []
            },
            "subtitle": {
                "count": subtitle_track_count,
                "tracks": []
            }
        }
        
        # Get information about video tracks
        for i in range(1, video_track_count + 1):
            track_info = {
                "index": i,
                "name": f"V{i}",  # Default name format
                "enabled": timeline.GetIsTrackEnabled("video", i),
                "clip_count": 0,
            }
            
            # Get clips in this track
            clips = timeline.GetItemListInTrack("video", i)
            track_info["clip_count"] = len(clips) if clips else 0
            
            tracks["video"]["tracks"].append(track_info)
        
        # Get information about audio tracks
        for i in range(1, audio_track_count + 1):
            track_info = {
                "index": i,
                "name": f"A{i}",  # Default name format
                "enabled": timeline.GetIsTrackEnabled("audio", i),
                "clip_count": 0,
            }
            
            # Get clips in this track
            clips = timeline.GetItemListInTrack("audio", i)
            track_info["clip_count"] = len(clips) if clips else 0
            
            tracks["audio"]["tracks"].append(track_info)
        
        # Get information about subtitle tracks
        for i in range(1, subtitle_track_count + 1):
            track_info = {
                "index": i,
                "name": f"S{i}",  # Default name format
                "enabled": timeline.GetIsTrackEnabled("subtitle", i),
                "clip_count": 0,
            }
            
            # Get clips in this track
            clips = timeline.GetItemListInTrack("subtitle", i)
            track_info["clip_count"] = len(clips) if clips else 0
            
            tracks["subtitle"]["tracks"].append(track_info)
        
        return tracks
    
    except Exception as e:
        return {"error": f"Error getting timeline tracks: {str(e)}"} 
def get_timeline_items(resolve) -> List[Dict[str, Any]]:
    """Get all items in the current timeline with their IDs and basic properties."""
    if resolve is None: return [{"error": "Not connected"}]
    
    project_manager = resolve.GetProjectManager()
    if not project_manager: return [{"error": "No Project Manager"}]
    
    current_project = project_manager.GetCurrentProject()
    if not current_project: return [{"error": "No project open"}]
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline: return [{"error": "No timeline active"}]
    
    try:
        video_track_count = current_timeline.GetTrackCount("video")
        audio_track_count = current_timeline.GetTrackCount("audio")
        items = []
        
        for track_index in range(1, video_track_count + 1):
            track_items = current_timeline.GetItemListInTrack("video", track_index)
            if track_items:
                for item in track_items:
                    items.append({
                        "id": str(item.GetUniqueId()),
                        "name": item.GetName(),
                        "type": "video",
                        "track": track_index,
                        "start": item.GetStart(),
                        "end": item.GetEnd(),
                        "duration": item.GetDuration()
                    })
        
        for track_index in range(1, audio_track_count + 1):
            track_items = current_timeline.GetItemListInTrack("audio", track_index)
            if track_items:
                for item in track_items:
                    items.append({
                        "id": str(item.GetUniqueId()),
                        "name": item.GetName(),
                        "type": "audio",
                        "track": track_index,
                        "start": item.GetStart(),
                        "end": item.GetEnd(),
                        "duration": item.GetDuration()
                    })
        
        return items if items else [{"info": "No items found"}]
    except Exception as e:
        return [{"error": f"Error: {e}"}]

def get_timeline_item(resolve, item_id: str):
    """Helper to find an item by ID."""
    if not resolve: return None
    pm = resolve.GetProjectManager()
    if not pm: return None
    proj = pm.GetCurrentProject()
    if not proj: return None
    tl = proj.GetCurrentTimeline()
    if not tl: return None
    
    # naive search across all tracks
    v_tracks = tl.GetTrackCount("video")
    a_tracks = tl.GetTrackCount("audio")
    
    for i in range(1, v_tracks + 1):
        items = tl.GetItemListInTrack("video", i)
        if items:
            for item in items:
                if str(item.GetUniqueId()) == item_id:
                    return item
    
    for i in range(1, a_tracks + 1):
        items = tl.GetItemListInTrack("audio", i)
        if items:
            for item in items:
                if str(item.GetUniqueId()) == item_id:
                    return item
    return None

def get_timeline_item_properties(resolve, item_id: str) -> Dict[str, Any]:
    """Get properties of a specific timeline item by ID."""
    item = get_timeline_item(resolve, item_id)
    if not item: return {"error": f"Item {item_id} not found or no active timeline"}
    
    try:
        props = {
            "id": item_id,
            "name": item.GetName(),
            "type": item.GetType(),
            "start": item.GetStart(),
            "end": item.GetEnd(),
            "duration": item.GetDuration()
        }
        
        if item.GetType() == "Video":
            props["transform"] = {
                "zoom_x": item.GetProperty("ZoomX"),
                "zoom_y": item.GetProperty("ZoomY"),
                "pan": item.GetProperty("Pan"),
                "tilt": item.GetProperty("Tilt"),
                "rotation": item.GetProperty("Rotation"),
                "pitch": item.GetProperty("Pitch"),
                "yaw": item.GetProperty("Yaw"),
                "anchor_x": item.GetProperty("AnchorPointX"),
                "anchor_y": item.GetProperty("AnchorPointY")
            }
            props["crop"] = {
                "left": item.GetProperty("CropLeft"),
                "right": item.GetProperty("CropRight"),
                "top": item.GetProperty("CropTop"),
                "bottom": item.GetProperty("CropBottom")
            }
            props["composite"] = {
                "mode": item.GetProperty("CompositeMode"),
                "opacity": item.GetProperty("Opacity")
            }
        
        if item.GetType() == "Audio" or item.GetMediaType() == "Audio":
             props["audio"] = {
                "volume": item.GetProperty("Volume")
             }
             
        return props
    except Exception as e:
        return {"error": f"Error getting props: {e}"}

def set_timeline_item_property(resolve, item_id: str, property_name: str, value: Any) -> str:
    """Set a property for a timeline item."""
    item = get_timeline_item(resolve, item_id)
    if not item: return f"Error: Item {item_id} not found"
    
    try:
        if item.SetProperty(property_name, value):
            return f"Set {property_name} to {value}"
        return f"Failed to set {property_name}"
    except Exception as e:
        return f"Error: {e}"


# Timeline Export Constants
EXPORT_TYPES = {
    "aaf": "EXPORT_AAF",
    "edl": "EXPORT_EDL", 
    "xml": "EXPORT_FCP_7_XML",
    "fcpxml_1_8": "EXPORT_FCPXML_1_8",
    "fcpxml_1_9": "EXPORT_FCPXML_1_9",
    "fcpxml_1_10": "EXPORT_FCPXML_1_10",
    "drt": "EXPORT_DRT",
    "csv": "EXPORT_TEXT_CSV",
    "txt": "EXPORT_TEXT_TAB",
    "otio": "EXPORT_OTIO",
    "ale": "EXPORT_ALE",
    "ale_cdl": "EXPORT_ALE_CDL",
    "hdr10_a": "EXPORT_HDR_10_PROFILE_A",
    "hdr10_b": "EXPORT_HDR_10_PROFILE_B",
    "dolby_2_9": "EXPORT_DOLBY_VISION_VER_2_9",
    "dolby_4_0": "EXPORT_DOLBY_VISION_VER_4_0",
    "dolby_5_1": "EXPORT_DOLBY_VISION_VER_5_1",
}

EXPORT_SUBTYPES = {
    "none": "EXPORT_NONE",
    "aaf_new": "EXPORT_AAF_NEW",
    "aaf_existing": "EXPORT_AAF_EXISTING",
    "cdl": "EXPORT_CDL",
    "sdl": "EXPORT_SDL",
    "missing_clips": "EXPORT_MISSING_CLIPS",
}


def export_timeline(resolve, file_path: str, export_type: str = "edl", 
                    export_subtype: str = "none", timeline_name: str = None) -> str:
    """Export timeline to file (EDL, XML, AAF, FCPXML, etc).
    
    Args:
        resolve: The DaVinci Resolve instance
        file_path: Path where the file will be saved
        export_type: One of 'aaf', 'edl', 'xml', 'fcpxml_1_8', 'fcpxml_1_9', 'fcpxml_1_10', 
                     'drt', 'csv', 'txt', 'otio', 'ale', 'ale_cdl', 'hdr10_a', 'hdr10_b',
                     'dolby_2_9', 'dolby_4_0', 'dolby_5_1'
        export_subtype: For AAF: 'aaf_new' or 'aaf_existing'. For EDL: 'cdl', 'sdl', 'missing_clips', or 'none'
        timeline_name: Optional timeline name, uses current if not specified
    
    Returns:
        String indicating success or failure
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Get timeline
    timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        if not timeline:
            return f"Error: Timeline '{timeline_name}' not found"
    else:
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return "Error: No timeline currently active"
    
    # Validate export type
    export_type_lower = export_type.lower()
    if export_type_lower not in EXPORT_TYPES:
        valid_types = ", ".join(EXPORT_TYPES.keys())
        return f"Error: Invalid export type '{export_type}'. Valid types: {valid_types}"
    
    # Validate export subtype
    export_subtype_lower = export_subtype.lower()
    if export_subtype_lower not in EXPORT_SUBTYPES:
        valid_subtypes = ", ".join(EXPORT_SUBTYPES.keys())
        return f"Error: Invalid export subtype '{export_subtype}'. Valid subtypes: {valid_subtypes}"
    
    try:
        # Get the actual enum values from resolve
        export_type_enum = getattr(resolve, EXPORT_TYPES[export_type_lower], None)
        export_subtype_enum = getattr(resolve, EXPORT_SUBTYPES[export_subtype_lower], None)
        
        if export_type_enum is None:
            return f"Error: Export type '{export_type}' not supported in this version of Resolve"
        
        if export_subtype_enum is None:
            export_subtype_enum = getattr(resolve, "EXPORT_NONE", 0)
        
        result = timeline.Export(file_path, export_type_enum, export_subtype_enum)
        
        if result:
            return f"Successfully exported timeline '{timeline.GetName()}' to '{file_path}'"
        else:
            return f"Failed to export timeline to '{file_path}'"
    except Exception as e:
        return f"Error exporting timeline: {e}"


def import_timeline_from_file(resolve, file_path: str, timeline_name: str = None,
                               import_source_clips: bool = True, 
                               source_clips_path: str = None) -> str:
    """Import timeline from file (AAF, EDL, XML, FCPXML, DRT, ADL, OTIO).
    
    Args:
        resolve: The DaVinci Resolve instance
        file_path: Path to the file to import
        timeline_name: Optional name for the imported timeline
        import_source_clips: Whether to import source clips into media pool
        source_clips_path: Optional path to search for source clips
    
    Returns:
        String indicating success or failure
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    import os
    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"
    
    try:
        import_options = {
            "importSourceClips": import_source_clips
        }
        
        if timeline_name:
            import_options["timelineName"] = timeline_name
        
        if source_clips_path:
            import_options["sourceClipsPath"] = source_clips_path
        
        timeline = media_pool.ImportTimelineFromFile(file_path, import_options)
        
        if timeline:
            return f"Successfully imported timeline '{timeline.GetName()}' from '{file_path}'"
        else:
            return f"Failed to import timeline from '{file_path}'"
    except Exception as e:
        return f"Error importing timeline: {e}"


def get_timeline_markers(resolve, timeline_name: str = None) -> Dict[str, Any]:
    """Get all markers from a timeline.
    
    Args:
        resolve: The DaVinci Resolve instance
        timeline_name: Optional timeline name, uses current if not specified
    
    Returns:
        Dictionary with marker information
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    # Get timeline
    timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        if not timeline:
            return {"error": f"Timeline '{timeline_name}' not found"}
    else:
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return {"error": "No timeline currently active"}
    
    try:
        markers = timeline.GetMarkers()
        
        # Convert to more readable format
        marker_list = []
        if markers:
            for frame_id, info in markers.items():
                marker_list.append({
                    "frame": frame_id,
                    "color": info.get("color", ""),
                    "name": info.get("name", ""),
                    "note": info.get("note", ""),
                    "duration": info.get("duration", 1),
                    "custom_data": info.get("customData", "")
                })
        
        return {
            "timeline": timeline.GetName(),
            "count": len(marker_list),
            "markers": marker_list
        }
    except Exception as e:
        return {"error": f"Error getting markers: {e}"}


def delete_timeline_markers(resolve, color: str = "All", timeline_name: str = None) -> str:
    """Delete markers from a timeline.
    
    Args:
        resolve: The DaVinci Resolve instance
        color: Marker color to delete, or 'All' to delete all markers
        timeline_name: Optional timeline name, uses current if not specified
    
    Returns:
        String indicating success or failure
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Get timeline
    timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        if not timeline:
            return f"Error: Timeline '{timeline_name}' not found"
    else:
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return "Error: No timeline currently active"
    
    try:
        result = timeline.DeleteMarkersByColor(color)
        if result:
            return f"Deleted {color} markers from timeline '{timeline.GetName()}'"
        else:
            return f"Failed to delete markers or no {color} markers found"
    except Exception as e:
        return f"Error deleting markers: {e}"


def duplicate_timeline(resolve, new_name: str = None, timeline_name: str = None) -> str:
    """Duplicate a timeline.
    
    Args:
        resolve: The DaVinci Resolve instance
        new_name: Optional name for the duplicated timeline
        timeline_name: Optional source timeline name, uses current if not specified
    
    Returns:
        String indicating success or failure
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Get source timeline
    timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        if not timeline:
            return f"Error: Timeline '{timeline_name}' not found"
    else:
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return "Error: No timeline currently active"
    
    try:
        duplicated = timeline.DuplicateTimeline(new_name) if new_name else timeline.DuplicateTimeline()
        if duplicated:
            return f"Successfully duplicated timeline to '{duplicated.GetName()}'"
        else:
            return "Failed to duplicate timeline"
    except Exception as e:
        return f"Error duplicating timeline: {e}"


# ============================================================
# Phase 4.1-4.3: Timeline Track Management
# ============================================================

def _get_timeline(resolve, timeline_name: str = None):
    """Helper to get timeline by name or current."""
    if not resolve:
        return None, "Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return None, "Failed to get Project Manager"
    
    proj = pm.GetCurrentProject()
    if not proj:
        return None, "No project currently open"
    
    if timeline_name:
        count = proj.GetTimelineCount()
        for i in range(1, count + 1):
            t = proj.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                return t, None
        return None, f"Timeline '{timeline_name}' not found"
    else:
        t = proj.GetCurrentTimeline()
        if not t:
            return None, "No timeline currently active"
        return t, None


def add_track(resolve, track_type: str, sub_track_type: str = None, 
              timeline_name: str = None) -> str:
    """Add a new track to the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        track_type: 'video', 'audio', or 'subtitle'
        sub_track_type: For audio: 'mono', 'stereo', '5.1', '7.1', 'adaptive'
        timeline_name: Optional timeline name
    """
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if sub_track_type:
            result = timeline.AddTrack(track_type, sub_track_type)
        else:
            result = timeline.AddTrack(track_type)
        
        if result:
            return f"Added {track_type} track to '{timeline.GetName()}'"
        return f"Failed to add {track_type} track"
    except Exception as e:
        return f"Error adding track: {e}"


def delete_track(resolve, track_type: str, track_index: int,
                 timeline_name: str = None) -> str:
    """Delete a track from the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        track_type: 'video', 'audio', or 'subtitle'
        track_index: 1-based track index
        timeline_name: Optional timeline name
    """
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = timeline.DeleteTrack(track_type, track_index)
        if result:
            return f"Deleted {track_type} track {track_index}"
        return f"Failed to delete track (it may contain clips or be the only track)"
    except Exception as e:
        return f"Error deleting track: {e}"


def get_track_name(resolve, track_type: str, track_index: int,
                   timeline_name: str = None) -> Dict[str, Any]:
    """Get the name of a track.
    
    Args:
        resolve: DaVinci Resolve instance
        track_type: 'video', 'audio', or 'subtitle'
        track_index: 1-based track index
        timeline_name: Optional timeline name
    """
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return {"error": error}
    
    try:
        name = timeline.GetTrackName(track_type, track_index)
        return {
            "timeline": timeline.GetName(),
            "track_type": track_type,
            "track_index": track_index,
            "name": name if name else f"{track_type[0].upper()}{track_index}"
        }
    except Exception as e:
        return {"error": f"Error getting track name: {e}"}


def set_track_name(resolve, track_type: str, track_index: int, name: str,
                   timeline_name: str = None) -> str:
    """Set the name of a track.
    
    Args:
        resolve: DaVinci Resolve instance
        track_type: 'video', 'audio', or 'subtitle'
        track_index: 1-based track index
        name: New name for the track
        timeline_name: Optional timeline name
    """
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = timeline.SetTrackName(track_type, track_index, name)
        if result:
            return f"Set {track_type} track {track_index} name to '{name}'"
        return "Failed to set track name"
    except Exception as e:
        return f"Error setting track name: {e}"


def set_track_enabled(resolve, track_type: str, track_index: int, enabled: bool,
                      timeline_name: str = None) -> str:
    """Enable or disable a track.
    
    Args:
        resolve: DaVinci Resolve instance
        track_type: 'video', 'audio', or 'subtitle'
        track_index: 1-based track index
        enabled: True to enable, False to disable
        timeline_name: Optional timeline name
    """
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = timeline.SetTrackEnable(track_type, track_index, enabled)
        state = "enabled" if enabled else "disabled"
        if result:
            return f"{track_type.capitalize()} track {track_index} {state}"
        return f"Failed to {state[:-1]} track"
    except Exception as e:
        return f"Error: {e}"


def set_track_locked(resolve, track_type: str, track_index: int, locked: bool,
                     timeline_name: str = None) -> str:
    """Lock or unlock a track.
    
    Args:
        resolve: DaVinci Resolve instance
        track_type: 'video', 'audio', or 'subtitle'
        track_index: 1-based track index
        locked: True to lock, False to unlock
        timeline_name: Optional timeline name
    """
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = timeline.SetTrackLock(track_type, track_index, locked)
        state = "locked" if locked else "unlocked"
        if result:
            return f"{track_type.capitalize()} track {track_index} {state}"
        return f"Failed to {state[:-2]} track"
    except Exception as e:
        return f"Error: {e}"


def get_track_status(resolve, track_type: str, track_index: int,
                     timeline_name: str = None) -> Dict[str, Any]:
    """Get track enabled/locked status.
    
    Args:
        resolve: DaVinci Resolve instance
        track_type: 'video', 'audio', or 'subtitle'
        track_index: 1-based track index
        timeline_name: Optional timeline name
    """
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return {"error": error}
    
    try:
        return {
            "timeline": timeline.GetName(),
            "track_type": track_type,
            "track_index": track_index,
            "enabled": timeline.GetIsTrackEnabled(track_type, track_index),
            "locked": timeline.GetIsTrackLocked(track_type, track_index)
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


# --- Timecode Operations ---

def get_current_timecode(resolve, timeline_name: str = None) -> Dict[str, Any]:
    """Get current playhead timecode."""
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return {"error": error}
    
    try:
        return {
            "timeline": timeline.GetName(),
            "current_timecode": timeline.GetCurrentTimecode(),
            "start_timecode": timeline.GetStartTimecode()
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def set_current_timecode(resolve, timecode: str, timeline_name: str = None) -> str:
    """Set playhead to timecode.
    
    Args:
        resolve: DaVinci Resolve instance
        timecode: Timecode string (e.g., '01:00:00:00')
        timeline_name: Optional timeline name
    """
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = timeline.SetCurrentTimecode(timecode)
        if result:
            return f"Set playhead to {timecode}"
        return "Failed to set timecode"
    except Exception as e:
        return f"Error: {e}"


# --- Insert Generators and Titles ---

def insert_generator(resolve, generator_name: str, duration: int = None,
                     timeline_name: str = None) -> str:
    """Insert a generator into the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        generator_name: Name of the generator (e.g., 'Solid Color', '10 Point Grid')
        duration: Optional duration in frames
        timeline_name: Optional timeline name
    """
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if duration:
            result = timeline.InsertGeneratorIntoTimeline(generator_name, {"duration": duration})
        else:
            result = timeline.InsertGeneratorIntoTimeline(generator_name)
        
        if result:
            return f"Inserted generator '{generator_name}'"
        return f"Failed to insert generator '{generator_name}'"
    except Exception as e:
        return f"Error: {e}"


def insert_title(resolve, title_name: str, duration: int = None,
                 timeline_name: str = None) -> str:
    """Insert a title into the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        title_name: Name of the title template (e.g., 'Text+', 'Scroll')
        duration: Optional duration in frames
        timeline_name: Optional timeline name
    """
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if duration:
            result = timeline.InsertTitleIntoTimeline(title_name, {"duration": duration})
        else:
            result = timeline.InsertTitleIntoTimeline(title_name)
        
        if result:
            return f"Inserted title '{title_name}'"
        return f"Failed to insert title '{title_name}'"
    except Exception as e:
        return f"Error: {e}"


def insert_fusion_title(resolve, title_name: str, duration: int = None,
                        timeline_name: str = None) -> str:
    """Insert a Fusion title into the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        title_name: Name of the Fusion title template
        duration: Optional duration in frames
        timeline_name: Optional timeline name
    """
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if duration:
            result = timeline.InsertFusionTitleIntoTimeline(title_name, {"duration": duration})
        else:
            result = timeline.InsertFusionTitleIntoTimeline(title_name)
        
        if result:
            return f"Inserted Fusion title '{title_name}'"
        return f"Failed to insert Fusion title"
    except Exception as e:
        return f"Error: {e}"


# --- Special Timeline Operations ---

def create_compound_clip(resolve, clip_info: Dict[str, Any] = None,
                         timeline_name: str = None) -> str:
    """Create a compound clip from selected items.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_info: Optional dict with 'startTimecode' and compound clip info
        timeline_name: Optional timeline name
    """
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = timeline.CreateCompoundClip(clip_info) if clip_info else timeline.CreateCompoundClip({})
        if result:
            return "Created compound clip"
        return "Failed to create compound clip (select clips first)"
    except Exception as e:
        return f"Error: {e}"


def create_fusion_clip(resolve, timeline_name: str = None) -> str:
    """Create a Fusion clip from selected items."""
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = timeline.CreateFusionClip([])
        if result:
            return "Created Fusion clip"
        return "Failed to create Fusion clip (select clips first)"
    except Exception as e:
        return f"Error: {e}"


def detect_scene_cuts(resolve, timeline_name: str = None) -> str:
    """Detect scene cuts in the timeline."""
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = timeline.DetectSceneCuts()
        if result:
            return "Scene cut detection started"
        return "Failed to start scene cut detection"
    except Exception as e:
        return f"Error: {e}"


def rename_timeline(resolve, new_name: str, timeline_name: str = None) -> str:
    """Rename a timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        new_name: New name for the timeline
        timeline_name: Optional current name, uses current timeline if not specified
    """
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return f"Error: {error}"
    
    old_name = timeline.GetName()
    
    try:
        if timeline.SetName(new_name):
            return f"Renamed timeline from '{old_name}' to '{new_name}'"
        return "Failed to rename timeline"
    except Exception as e:
        return f"Error: {e}"


def get_timeline_unique_id(resolve, timeline_name: str = None) -> Dict[str, Any]:
    """Get the unique ID of a timeline."""
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return {"error": error}
    
    try:
        return {
            "timeline": timeline.GetName(),
            "unique_id": timeline.GetUniqueId()
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


# ============================================================
# Phase 5: TimelineItem Extended Operations
# ============================================================

def _find_timeline_item(resolve, clip_name: str, track_type: str = "video", 
                        track_index: int = None, timeline_name: str = None):
    """Helper to find a timeline item by name."""
    timeline, error = _get_timeline(resolve, timeline_name)
    if error:
        return None, error
    
    # Search in all tracks if track_index not specified
    if track_type == "video":
        track_count = timeline.GetTrackCount("video")
        tracks_to_search = range(1, track_count + 1) if track_index is None else [track_index]
        
        for idx in tracks_to_search:
            items = timeline.GetItemListInTrack("video", idx)
            if items:
                for item in items:
                    if item.GetName() == clip_name:
                        return item, None
    
    elif track_type == "audio":
        track_count = timeline.GetTrackCount("audio")
        tracks_to_search = range(1, track_count + 1) if track_index is None else [track_index]
        
        for idx in tracks_to_search:
            items = timeline.GetItemListInTrack("audio", idx)
            if items:
                for item in items:
                    if item.GetName() == clip_name:
                        return item, None
    
    return None, f"Clip '{clip_name}' not found in {track_type} tracks"


def get_timeline_item_property(resolve, clip_name: str, property_key: str = None,
                               timeline_name: str = None) -> Dict[str, Any]:
    """Get TimelineItem property or all properties.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip in timeline
        property_key: Optional specific property key (returns all if not specified)
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        if property_key:
            value = item.GetProperty(property_key)
            return {"clip_name": clip_name, property_key: value}
        else:
            properties = item.GetProperty()
            return {"clip_name": clip_name, "properties": properties if properties else {}}
    except Exception as e:
        return {"error": f"Error: {e}"}


def set_timeline_item_property(resolve, clip_name: str, property_key: str, 
                               property_value, timeline_name: str = None) -> str:
    """Set a TimelineItem property.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip in timeline
        property_key: Property key (e.g., 'Pan', 'Tilt', 'ZoomX', 'ZoomY', 'CropLeft', etc.)
        property_value: Value to set
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.SetProperty(property_key, property_value):
            return f"Set '{property_key}' to '{property_value}' for '{clip_name}'"
        return f"Failed to set '{property_key}' for '{clip_name}'"
    except Exception as e:
        return f"Error: {e}"


def get_timeline_item_info(resolve, clip_name: str, timeline_name: str = None) -> Dict[str, Any]:
    """Get detailed info about a timeline item."""
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        track_info = item.GetTrackTypeAndIndex()
        return {
            "name": item.GetName(),
            "duration": item.GetDuration(),
            "start": item.GetStart(),
            "end": item.GetEnd(),
            "source_start": item.GetSourceStartFrame(),
            "source_end": item.GetSourceEndFrame(),
            "track_type": track_info[0] if track_info else None,
            "track_index": track_info[1] if track_info else None,
            "enabled": item.GetClipEnabled(),
            "color": item.GetClipColor(),
            "unique_id": item.GetUniqueId()
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def set_timeline_item_enabled(resolve, clip_name: str, enabled: bool,
                              timeline_name: str = None) -> str:
    """Enable or disable a timeline item."""
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = item.SetClipEnabled(enabled)
        state = "enabled" if enabled else "disabled"
        if result:
            return f"Clip '{clip_name}' {state}"
        return f"Failed to {state[:-1]} clip"
    except Exception as e:
        return f"Error: {e}"


# --- Timeline Item Color Versions ---

def add_color_version(resolve, clip_name: str, version_name: str, 
                      version_type: int = 0, timeline_name: str = None) -> str:
    """Add a new color version to a timeline item.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        version_name: Name for the new version
        version_type: 0 = local, 1 = remote
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.AddVersion(version_name, version_type):
            vtype = "local" if version_type == 0 else "remote"
            return f"Added {vtype} version '{version_name}' to '{clip_name}'"
        return "Failed to add version"
    except Exception as e:
        return f"Error: {e}"


def get_color_versions(resolve, clip_name: str, version_type: int = 0,
                       timeline_name: str = None) -> Dict[str, Any]:
    """Get list of color versions for a timeline item.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        version_type: 0 = local, 1 = remote
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        versions = item.GetVersionNameList(version_type)
        current = item.GetCurrentVersion()
        
        return {
            "clip_name": clip_name,
            "version_type": "local" if version_type == 0 else "remote",
            "versions": versions if versions else [],
            "current_version": current
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def load_color_version(resolve, clip_name: str, version_name: str,
                       version_type: int = 0, timeline_name: str = None) -> str:
    """Load a color version by name."""
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.LoadVersionByName(version_name, version_type):
            return f"Loaded version '{version_name}'"
        return f"Failed to load version '{version_name}'"
    except Exception as e:
        return f"Error: {e}"


# --- Timeline Item Effects/Processing ---

def stabilize_clip(resolve, clip_name: str, timeline_name: str = None) -> str:
    """Stabilize a timeline clip."""
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.Stabilize():
            return f"Stabilization started for '{clip_name}'"
        return "Failed to start stabilization"
    except Exception as e:
        return f"Error: {e}"


def smart_reframe_clip(resolve, clip_name: str, timeline_name: str = None) -> str:
    """Apply Smart Reframe to a timeline clip."""
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.SmartReframe():
            return f"Smart Reframe applied to '{clip_name}'"
        return "Failed to apply Smart Reframe"
    except Exception as e:
        return f"Error: {e}"


def create_magic_mask(resolve, clip_name: str, mode: str = "F",
                      timeline_name: str = None) -> str:
    """Create Magic Mask on a clip.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        mode: 'F' (forward), 'B' (backward), or 'BI' (bidirectional)
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.CreateMagicMask(mode):
            return f"Magic Mask created on '{clip_name}' (mode: {mode})"
        return "Failed to create Magic Mask"
    except Exception as e:
        return f"Error: {e}"


# --- Timeline Item Markers/Flags/Color ---

def add_timeline_item_marker(resolve, clip_name: str, frame: int, color: str = "Blue",
                             name: str = "", note: str = "", duration: int = 1,
                             timeline_name: str = None) -> str:
    """Add a marker to a timeline item."""
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.AddMarker(frame, color, name, note, duration, ""):
            return f"Added {color} marker at frame {frame} on '{clip_name}'"
        return "Failed to add marker"
    except Exception as e:
        return f"Error: {e}"


def get_timeline_item_markers(resolve, clip_name: str, 
                              timeline_name: str = None) -> Dict[str, Any]:
    """Get markers from a timeline item."""
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        markers = item.GetMarkers()
        marker_list = []
        if markers:
            for frame_id, info in markers.items():
                marker_list.append({
                    "frame": frame_id,
                    "color": info.get("color", ""),
                    "name": info.get("name", ""),
                    "note": info.get("note", ""),
                    "duration": info.get("duration", 1)
                })
        return {"clip_name": clip_name, "count": len(marker_list), "markers": marker_list}
    except Exception as e:
        return {"error": f"Error: {e}"}


def set_timeline_item_color(resolve, clip_name: str, color: str,
                            timeline_name: str = None) -> str:
    """Set the color label of a timeline item."""
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.SetClipColor(color):
            return f"Set color to '{color}' for '{clip_name}'"
        return "Failed to set color"
    except Exception as e:
        return f"Error: {e}"


def add_timeline_item_flag(resolve, clip_name: str, color: str,
                           timeline_name: str = None) -> str:
    """Add a flag to a timeline item."""
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.AddFlag(color):
            return f"Added {color} flag to '{clip_name}'"
        return "Failed to add flag"
    except Exception as e:
        return f"Error: {e}"


# --- Timeline Item Cache Control ---

def set_color_output_cache(resolve, clip_name: str, enabled: bool,
                           timeline_name: str = None) -> str:
    """Enable/disable color output cache for a clip."""
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        cache_value = 1 if enabled else 0
        if item.SetColorOutputCache(cache_value):
            state = "enabled" if enabled else "disabled"
            return f"Color output cache {state} for '{clip_name}'"
        return "Failed to set cache"
    except Exception as e:
        return f"Error: {e}"


def set_fusion_output_cache(resolve, clip_name: str, cache_mode: int,
                            timeline_name: str = None) -> str:
    """Set Fusion output cache mode for a clip.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        cache_mode: -1 = auto, 0 = disabled, 1 = enabled
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.SetFusionOutputCache(cache_mode):
            modes = {-1: "auto", 0: "disabled", 1: "enabled"}
            return f"Fusion cache set to '{modes.get(cache_mode, cache_mode)}' for '{clip_name}'"
        return "Failed to set Fusion cache"
    except Exception as e:
        return f"Error: {e}"


def copy_grades(resolve, source_clip: str, target_clips: List[str],
                timeline_name: str = None) -> str:
    """Copy grades from source clip to target clips.
    
    Args:
        resolve: DaVinci Resolve instance
        source_clip: Source clip name
        target_clips: List of target clip names
    """
    source_item, error = _find_timeline_item(resolve, source_clip, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    target_items = []
    for name in target_clips:
        item, err = _find_timeline_item(resolve, name, timeline_name=timeline_name)
        if item:
            target_items.append(item)
    
    if not target_items:
        return "Error: No valid target clips found"
    
    try:
        if source_item.CopyGrades(target_items):
            return f"Copied grades from '{source_clip}' to {len(target_items)} clips"
        return "Failed to copy grades"
    except Exception as e:
        return f"Error: {e}"


def get_linked_items(resolve, clip_name: str, timeline_name: str = None) -> Dict[str, Any]:
    """Get linked items for a timeline item."""
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        linked = item.GetLinkedItems()
        linked_names = [i.GetName() for i in linked] if linked else []
        return {"clip_name": clip_name, "linked_items": linked_names}
    except Exception as e:
        return {"error": f"Error: {e}"}


# ============================================================
# Phase 4.1: Timeline Marker CustomData Operations
# ============================================================

def add_marker_with_custom_data(resolve, frame: int, color: str = "Blue", 
                                 name: str = "", note: str = "", 
                                 duration: int = 1, custom_data: str = "",
                                 timeline_name: str = None) -> str:
    """Add a marker with custom data to the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        frame: Frame number for the marker
        color: Marker color
        name: Marker name
        note: Marker note
        duration: Duration in frames
        custom_data: Custom data string (for scripting/automation)
        timeline_name: Optional timeline name
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Get timeline
    timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        if not timeline:
            return f"Error: Timeline '{timeline_name}' not found"
    else:
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return "Error: No timeline currently active"
    
    try:
        if timeline.AddMarker(frame, color, name, note, duration, custom_data):
            return f"Added {color} marker at frame {frame} with customData"
        return "Failed to add marker"
    except Exception as e:
        return f"Error: {e}"


def get_timeline_marker_by_custom_data(resolve, custom_data: str, 
                                        timeline_name: str = None) -> Dict[str, Any]:
    """Find a timeline marker by its custom data.
    
    Args:
        resolve: DaVinci Resolve instance
        custom_data: Custom data string to search for
        timeline_name: Optional timeline name
    
    Returns:
        Dict with marker information or error
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    # Get timeline
    timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        if not timeline:
            return {"error": f"Timeline '{timeline_name}' not found"}
    else:
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return {"error": "No timeline currently active"}
    
    try:
        marker = timeline.GetMarkerByCustomData(custom_data)
        if marker:
            return {
                "found": True,
                "marker": marker,
                "custom_data": custom_data
            }
        return {"found": False, "custom_data": custom_data}
    except Exception as e:
        return {"error": f"Error: {e}"}


def update_timeline_marker_custom_data(resolve, frame: int, custom_data: str,
                                         timeline_name: str = None) -> str:
    """Update custom data for a timeline marker at a specific frame.
    
    Args:
        resolve: DaVinci Resolve instance
        frame: Frame number of the marker
        custom_data: New custom data string
        timeline_name: Optional timeline name
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Get timeline
    timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        if not timeline:
            return f"Error: Timeline '{timeline_name}' not found"
    else:
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return "Error: No timeline currently active"
    
    try:
        if timeline.UpdateMarkerCustomData(frame, custom_data):
            return f"Updated customData at frame {frame}"
        return f"Failed to update customData at frame {frame}"
    except Exception as e:
        return f"Error: {e}"


def get_timeline_marker_custom_data(resolve, frame: int, 
                                     timeline_name: str = None) -> Dict[str, Any]:
    """Get custom data for a timeline marker at a specific frame.
    
    Args:
        resolve: DaVinci Resolve instance
        frame: Frame number of the marker
        timeline_name: Optional timeline name
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    # Get timeline
    timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        if not timeline:
            return {"error": f"Timeline '{timeline_name}' not found"}
    else:
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return {"error": "No timeline currently active"}
    
    try:
        custom_data = timeline.GetMarkerCustomData(frame)
        return {
            "frame": frame,
            "custom_data": custom_data if custom_data else ""
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def delete_timeline_marker_by_custom_data(resolve, custom_data: str,
                                           timeline_name: str = None) -> str:
    """Delete a timeline marker by its custom data.
    
    Args:
        resolve: DaVinci Resolve instance
        custom_data: Custom data string of the marker to delete
        timeline_name: Optional timeline name
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Get timeline
    timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        if not timeline:
            return f"Error: Timeline '{timeline_name}' not found"
    else:
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return "Error: No timeline currently active"
    
    try:
        if timeline.DeleteMarkerByCustomData(custom_data):
            return f"Deleted marker with customData '{custom_data}'"
        return f"Failed to delete marker with customData '{custom_data}'"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Phase 4.1: Timeline Clip Linking
# ============================================================

def set_clips_linked(resolve, clip_names: List[str], linked: bool,
                     timeline_name: str = None) -> str:
    """Link or unlink timeline clips.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_names: List of clip names to link/unlink
        linked: True to link, False to unlink
        timeline_name: Optional timeline name
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not clip_names:
        return "Error: No clip names provided"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Get timeline
    timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        if not timeline:
            return f"Error: Timeline '{timeline_name}' not found"
    else:
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return "Error: No timeline currently active"
    
    # Find all timeline items by name
    items = []
    video_count = timeline.GetTrackCount("video")
    audio_count = timeline.GetTrackCount("audio")
    
    for track_idx in range(1, video_count + 1):
        track_items = timeline.GetItemListInTrack("video", track_idx)
        if track_items:
            for item in track_items:
                if item.GetName() in clip_names:
                    items.append(item)
    
    for track_idx in range(1, audio_count + 1):
        track_items = timeline.GetItemListInTrack("audio", track_idx)
        if track_items:
            for item in track_items:
                if item.GetName() in clip_names:
                    items.append(item)
    
    if not items:
        return f"Error: No clips found matching: {', '.join(clip_names)}"
    
    try:
        if timeline.SetClipsLinked(items, linked):
            action = "linked" if linked else "unlinked"
            return f"Successfully {action} {len(items)} clips"
        return "Failed to set clips linked state"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Phase 4.1: Timeline Stills
# ============================================================

def grab_timeline_still(resolve, timeline_name: str = None) -> Dict[str, Any]:
    """Grab a still from the current playhead position in the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        timeline_name: Optional timeline name
    
    Returns:
        Dict with still information or error
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    # Get timeline
    timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        if not timeline:
            return {"error": f"Timeline '{timeline_name}' not found"}
    else:
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return {"error": "No timeline currently active"}
    
    try:
        still = timeline.GrabStill()
        if still:
            return {
                "success": True,
                "message": "Still grabbed successfully",
                "timeline": timeline.GetName()
            }
        return {"success": False, "message": "Failed to grab still"}
    except Exception as e:
        return {"error": f"Error: {e}"}


def grab_all_timeline_stills(resolve, still_frame_source: int = 1,
                              timeline_name: str = None) -> Dict[str, Any]:
    """Grab stills from all clips in the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        still_frame_source: 1 = First frame, 2 = Middle frame
        timeline_name: Optional timeline name
    
    Returns:
        Dict with stills information or error
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    if still_frame_source not in [1, 2]:
        return {"error": "still_frame_source must be 1 (First frame) or 2 (Middle frame)"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    # Get timeline
    timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        if not timeline:
            return {"error": f"Timeline '{timeline_name}' not found"}
    else:
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return {"error": "No timeline currently active"}
    
    try:
        stills = timeline.GrabAllStills(still_frame_source)
        if stills:
            source_name = "first frame" if still_frame_source == 1 else "middle frame"
            return {
                "success": True,
                "count": len(stills),
                "source": source_name,
                "timeline": timeline.GetName()
            }
        return {"success": False, "message": "Failed to grab stills"}
    except Exception as e:
        return {"error": f"Error: {e}"}


# ============================================================
# Phase 4.1: Timeline Stereo Conversion
# ============================================================

def convert_timeline_to_stereo(resolve, timeline_name: str = None) -> str:
    """Convert a timeline to stereo format.
    
    Args:
        resolve: DaVinci Resolve instance
        timeline_name: Optional timeline name
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Get timeline
    timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            t = current_project.GetTimelineByIndex(i)
            if t and t.GetName() == timeline_name:
                timeline = t
                break
        if not timeline:
            return f"Error: Timeline '{timeline_name}' not found"
    else:
        timeline = current_project.GetCurrentTimeline()
        if not timeline:
            return "Error: No timeline currently active"
    
    try:
        if timeline.ConvertTimelineToStereo():
            return f"Timeline '{timeline.GetName()}' converted to stereo"
        return "Failed to convert timeline to stereo"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Phase 4.2: TimelineItem Offset Operations
# ============================================================

def get_timeline_item_left_offset(resolve, clip_name: str, 
                                   timeline_name: str = None) -> Dict[str, Any]:
    """Get the left offset (handle) of a timeline item in frames.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        offset = item.GetLeftOffset()
        return {
            "clip_name": clip_name,
            "left_offset": offset
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def get_timeline_item_right_offset(resolve, clip_name: str, 
                                    timeline_name: str = None) -> Dict[str, Any]:
    """Get the right offset (handle) of a timeline item in frames.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        offset = item.GetRightOffset()
        return {
            "clip_name": clip_name,
            "right_offset": offset
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


# ============================================================
# Phase 4.2: TimelineItem Take Management
# ============================================================

def add_take(resolve, clip_name: str, media_pool_item_name: str,
             start_frame: int = None, end_frame: int = None,
             timeline_name: str = None) -> str:
    """Add a take to a timeline item's take selector.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the timeline item
        media_pool_item_name: Name of the media pool item to add as take
        start_frame: Optional start frame within the media
        end_frame: Optional end frame within the media  
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    # Find the media pool item
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    if not project:
        return "Error: No project open"
    
    media_pool = project.GetMediaPool()
    if not media_pool:
        return "Error: No media pool"
    
    # Search for media pool item
    mp_item = None
    def find_in_folder(folder):
        clips = folder.GetClipList()
        for clip in clips:
            if clip.GetName() == media_pool_item_name:
                return clip
        for subfolder in folder.GetSubFolderList():
            result = find_in_folder(subfolder)
            if result:
                return result
        return None
    
    root_folder = media_pool.GetRootFolder()
    mp_item = find_in_folder(root_folder)
    
    if not mp_item:
        return f"Error: MediaPoolItem '{media_pool_item_name}' not found"
    
    try:
        if start_frame is not None and end_frame is not None:
            result = item.AddTake(mp_item, start_frame, end_frame)
        else:
            result = item.AddTake(mp_item)
        
        if result:
            return f"Added take from '{media_pool_item_name}' to '{clip_name}'"
        return "Failed to add take"
    except Exception as e:
        return f"Error: {e}"


def get_takes_count(resolve, clip_name: str, 
                    timeline_name: str = None) -> Dict[str, Any]:
    """Get the number of takes for a timeline item.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        count = item.GetTakesCount()
        return {
            "clip_name": clip_name,
            "takes_count": count
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def get_take_by_index(resolve, clip_name: str, take_index: int,
                      timeline_name: str = None) -> Dict[str, Any]:
    """Get take information by index.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        take_index: 1-based index of the take
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        take = item.GetTakeByIndex(take_index)
        if take:
            return {
                "clip_name": clip_name,
                "take_index": take_index,
                "take": {
                    "startFrame": take.get("startFrame"),
                    "endFrame": take.get("endFrame"),
                    "mediaPoolItem": take.get("mediaPoolItem").GetName() if take.get("mediaPoolItem") else None
                }
            }
        return {"error": f"Take at index {take_index} not found"}
    except Exception as e:
        return {"error": f"Error: {e}"}


def select_take_by_index(resolve, clip_name: str, take_index: int,
                         timeline_name: str = None) -> str:
    """Select a take by index in the timeline item.
    
    Args:
        resolve: DaVinci Resolve instance  
        clip_name: Name of the clip
        take_index: 1-based index of the take to select
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.SelectTakeByIndex(take_index):
            return f"Selected take {take_index} for '{clip_name}'"
        return f"Failed to select take {take_index}"
    except Exception as e:
        return f"Error: {e}"


def get_selected_take_index(resolve, clip_name: str, 
                            timeline_name: str = None) -> Dict[str, Any]:
    """Get the currently selected take index.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        index = item.GetSelectedTakeIndex()
        return {
            "clip_name": clip_name,
            "selected_take_index": index
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def finalize_take(resolve, clip_name: str, 
                  timeline_name: str = None) -> str:
    """Finalize the current take, removing all other takes.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.FinalizeTake():
            return f"Finalized take for '{clip_name}'"
        return "Failed to finalize take"
    except Exception as e:
        return f"Error: {e}"


def delete_take_by_index(resolve, clip_name: str, take_index: int,
                         timeline_name: str = None) -> str:
    """Delete a take by index.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        take_index: 1-based index of the take to delete
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.DeleteTakeByIndex(take_index):
            return f"Deleted take {take_index} from '{clip_name}'"
        return f"Failed to delete take {take_index}"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Phase 4.2: TimelineItem Magic Mask and Sidecar
# ============================================================

def regenerate_magic_mask(resolve, clip_name: str,
                          timeline_name: str = None) -> str:
    """Regenerate Magic Mask for a timeline item.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.RegenerateMagicMask():
            return f"Regenerated Magic Mask for '{clip_name}'"
        return "Failed to regenerate Magic Mask (mask must already exist)"
    except Exception as e:
        return f"Error: {e}"


def update_sidecar(resolve, clip_name: str,
                   timeline_name: str = None) -> str:
    """Update sidecar file for BRAW/R3D clips.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        if item.UpdateSidecar():
            return f"Updated sidecar for '{clip_name}'"
        return "Failed to update sidecar (clip may not be BRAW/R3D)"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Phase 4.2: TimelineItem Stereo Operations (Optional)
# ============================================================

def get_stereo_convergence_values(resolve, clip_name: str,
                                   timeline_name: str = None) -> Dict[str, Any]:
    """Get stereo convergence values for a timeline item.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        values = item.GetStereoConvergenceValues()
        return {
            "clip_name": clip_name,
            "stereo_convergence": values
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def get_stereo_left_floating_window_params(resolve, clip_name: str,
                                            timeline_name: str = None) -> Dict[str, Any]:
    """Get stereo left eye floating window parameters.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        params = item.GetStereoLeftFloatingWindowParams()
        return {
            "clip_name": clip_name,
            "left_floating_window": params
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def get_stereo_right_floating_window_params(resolve, clip_name: str,
                                             timeline_name: str = None) -> Dict[str, Any]:
    """Get stereo right eye floating window parameters.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        params = item.GetStereoRightFloatingWindowParams()
        return {
            "clip_name": clip_name,
            "right_floating_window": params
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


# ============================================================
# Full Coverage: Remaining Timeline Functions
# ============================================================

def get_current_clip_thumbnail(resolve, timeline_name: str = None) -> Dict[str, Any]:
    """Get thumbnail image data for the current clip in Color page.
    
    Returns dict with width, height, format and base64-encoded RGB data.
    """
    if not resolve:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    if not project:
        return {"error": "No project open"}
    
    timeline = None
    if timeline_name:
        count = project.GetTimelineCount()
        for i in range(1, count + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    else:
        timeline = project.GetCurrentTimeline()
    
    if not timeline:
        return {"error": "No timeline found"}
    
    try:
        data = timeline.GetCurrentClipThumbnailImage()
        if data:
            return {
                "width": data.get("width"),
                "height": data.get("height"),
                "format": data.get("format"),
                "has_data": bool(data.get("data"))
            }
        return {"error": "No thumbnail available"}
    except Exception as e:
        return {"error": f"Error: {e}"}


def analyze_dolby_vision(resolve, timeline_name: str = None,
                          clip_names: List[str] = None,
                          blend_shots: bool = False) -> str:
    """Analyze Dolby Vision on timeline clips.
    
    Args:
        resolve: DaVinci Resolve instance
        timeline_name: Optional timeline name
        clip_names: Optional list of clip names to analyze (all if empty)
        blend_shots: Use blend shots analysis mode
    """
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    if not project:
        return "Error: No project open"
    
    timeline = None
    if timeline_name:
        count = project.GetTimelineCount()
        for i in range(1, count + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    else:
        timeline = project.GetCurrentTimeline()
    
    if not timeline:
        return "Error: No timeline found"
    
    try:
        items = []
        if clip_names:
            for track_idx in range(1, timeline.GetTrackCount("video") + 1):
                for item in timeline.GetItemListInTrack("video", track_idx) or []:
                    if item.GetName() in clip_names:
                        items.append(item)
        
        # Note: analysisType would need resolve.DLB_BLEND_SHOTS for blend mode
        if items:
            result = timeline.AnalyzeDolbyVision(items)
        else:
            result = timeline.AnalyzeDolbyVision()
        
        if result:
            return "Dolby Vision analysis started"
        return "Failed to start Dolby Vision analysis"
    except AttributeError:
        return "Error: AnalyzeDolbyVision not available (requires DaVinci Resolve Studio)"
    except Exception as e:
        return f"Error: {e}"


def get_timeline_mediapool_item(resolve, timeline_name: str = None) -> Dict[str, Any]:
    """Get the MediaPoolItem corresponding to the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        timeline_name: Optional timeline name
    """
    if not resolve:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    if not project:
        return {"error": "No project open"}
    
    timeline = None
    if timeline_name:
        count = project.GetTimelineCount()
        for i in range(1, count + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    else:
        timeline = project.GetCurrentTimeline()
    
    if not timeline:
        return {"error": "No timeline found"}
    
    try:
        mpi = timeline.GetMediaPoolItem()
        if mpi:
            return {
                "timeline": timeline.GetName(),
                "media_pool_item_name": mpi.GetName(),
                "media_id": mpi.GetMediaId()
            }
        return {"error": "No MediaPoolItem for timeline"}
    except Exception as e:
        return {"error": f"Error: {e}"}


# ============================================================
# Full Coverage: Remaining TimelineItem Functions
# ============================================================

def stabilize_clip(resolve, clip_name: str, timeline_name: str = None) -> str:
    """Stabilize a timeline clip.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = item.Stabilize()
        if result:
            return f"Stabilized clip '{clip_name}'"
        return "Failed to stabilize clip"
    except AttributeError:
        return "Error: Stabilize not available"
    except Exception as e:
        return f"Error: {e}"


def smart_reframe_clip(resolve, clip_name: str, timeline_name: str = None) -> str:
    """Apply Smart Reframe to a timeline clip.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = item.SmartReframe()
        if result:
            return f"Applied Smart Reframe to '{clip_name}'"
        return "Failed to apply Smart Reframe"
    except AttributeError:
        return "Error: SmartReframe not available"
    except Exception as e:
        return f"Error: {e}"


def export_lut_from_clip(resolve, clip_name: str, export_path: str,
                          export_type: int = 0,
                          timeline_name: str = None) -> str:
    """Export LUT from a timeline clip.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        export_path: Path for the exported LUT file
        export_type: LUT size type (0=17pt, 1=33pt, 2=65pt)
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = item.ExportLUT(export_type, export_path)
        if result:
            return f"Exported LUT from '{clip_name}' to: {export_path}"
        return "Failed to export LUT"
    except Exception as e:
        return f"Error: {e}"


def get_linked_items(resolve, clip_name: str, timeline_name: str = None) -> Dict[str, Any]:
    """Get linked timeline items for a clip.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        linked = item.GetLinkedItems() or []
        return {
            "clip_name": clip_name,
            "linked_items": [li.GetName() for li in linked],
            "count": len(linked)
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def get_track_type_and_index(resolve, clip_name: str, timeline_name: str = None) -> Dict[str, Any]:
    """Get the track type and index for a timeline item.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        result = item.GetTrackTypeAndIndex()
        if result and len(result) >= 2:
            return {
                "clip_name": clip_name,
                "track_type": result[0],
                "track_index": result[1]
            }
        return {"error": "Could not get track info"}
    except Exception as e:
        return {"error": f"Error: {e}"}


def get_source_audio_channel_mapping(resolve, clip_name: str, timeline_name: str = None) -> Dict[str, Any]:
    """Get source audio channel mapping for a timeline item.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        mapping = item.GetSourceAudioChannelMapping()
        return {
            "clip_name": clip_name,
            "audio_mapping": mapping
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def set_color_output_cache(resolve, clip_name: str, enabled: bool,
                            timeline_name: str = None) -> str:
    """Set color output cache for a timeline item.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        enabled: Enable or disable caching
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = item.SetColorOutputCache(enabled)
        status = "enabled" if enabled else "disabled"
        if result:
            return f"Color output cache {status} for '{clip_name}'"
        return "Failed to set color output cache"
    except Exception as e:
        return f"Error: {e}"


def get_color_output_cache_enabled(resolve, clip_name: str, timeline_name: str = None) -> Dict[str, Any]:
    """Check if color output cache is enabled for a timeline item.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        result = item.GetIsColorOutputCacheEnabled()
        return {
            "clip_name": clip_name,
            "color_cache_enabled": result
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def set_fusion_output_cache(resolve, clip_name: str, cache_value: str,
                             timeline_name: str = None) -> str:
    """Set Fusion output cache for a timeline item.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        cache_value: 'auto', 'on', or 'off'
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = item.SetFusionOutputCache(cache_value)
        if result:
            return f"Fusion output cache set to '{cache_value}' for '{clip_name}'"
        return "Failed to set Fusion output cache"
    except Exception as e:
        return f"Error: {e}"


def get_fusion_output_cache_enabled(resolve, clip_name: str, timeline_name: str = None) -> Dict[str, Any]:
    """Check if Fusion output cache is enabled for a timeline item.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        result = item.GetIsFusionOutputCacheEnabled()
        return {
            "clip_name": clip_name,
            "fusion_cache_enabled": result
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def get_clip_mediapool_item(resolve, clip_name: str, timeline_name: str = None) -> Dict[str, Any]:
    """Get MediaPoolItem for a timeline clip.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip
        timeline_name: Optional timeline name
    """
    item, error = _find_timeline_item(resolve, clip_name, timeline_name=timeline_name)
    if error:
        return {"error": error}
    
    try:
        mpi = item.GetMediaPoolItem()
        if mpi:
            return {
                "clip_name": clip_name,
                "media_pool_item": mpi.GetName(),
                "media_id": mpi.GetMediaId()
            }
        return {"error": "No MediaPoolItem for clip"}
    except Exception as e:
        return {"error": f"Error: {e}"}

