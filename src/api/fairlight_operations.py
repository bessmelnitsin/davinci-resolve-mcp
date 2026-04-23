#!/usr/bin/env python3
"""
DaVinci Resolve Fairlight (Audio) Page Operations

Provides audio editing and mixing functionality:
- Audio track management
- Volume and pan controls
- Audio effects
- Normalization and analysis
- Voice isolation (Neural Engine)
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("davinci-resolve-mcp.fairlight")


def _get_fairlight_context(resolve) -> Tuple[bool, Any, Any, str]:
    """Get Fairlight page context (project, timeline).
    
    Returns:
        Tuple of (success, project, timeline, error_message)
    """
    if not resolve:
        return False, None, None, "Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return False, None, None, "Failed to get Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return False, None, None, "No project is currently open"
    
    timeline = project.GetCurrentTimeline()
    if not timeline:
        return False, None, None, "No active timeline"
    
    return True, project, timeline, "OK"


def get_audio_tracks(resolve, timeline_name: str = None) -> Dict[str, Any]:
    """Get list of audio tracks in the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        timeline_name: Optional timeline name (uses current if None)
        
    Returns:
        Dictionary with audio track information
    """
    success, project, timeline, msg = _get_fairlight_context(resolve)
    if not success:
        return {"error": msg}
    
    # Switch to specific timeline if requested
    if timeline_name:
        found = False
        for i in range(project.GetTimelineCount()):
            t = project.GetTimelineByIndex(i + 1)
            if t and t.GetName() == timeline_name:
                timeline = t
                project.SetCurrentTimeline(timeline)
                found = True
                break
        if not found:
            return {"error": f"Timeline '{timeline_name}' not found"}
    
    try:
        audio_track_count = timeline.GetTrackCount("audio")
        tracks = []
        
        for i in range(1, audio_track_count + 1):
            track_info = {
                "index": i,
                "name": timeline.GetTrackName("audio", i),
                "enabled": True,  # Default, API may not expose this
                "items_count": 0
            }
            
            # Get items in track
            try:
                items = timeline.GetItemListInTrack("audio", i)
                if items:
                    track_info["items_count"] = len(items)
            except Exception:
                pass
            
            tracks.append(track_info)
        
        return {
            "timeline": timeline.GetName(),
            "audio_track_count": audio_track_count,
            "tracks": tracks
        }
    except Exception as e:
        logger.error(f"Error getting audio tracks: {e}")
        return {"error": f"Failed to get audio tracks: {str(e)}"}


def set_track_volume(resolve, track_index: int, volume_db: float) -> Dict[str, Any]:
    """Set volume for an audio track.
    
    Note: Direct volume control may require Fairlight page-specific API
    which is limited in the scripting API.
    
    Args:
        resolve: DaVinci Resolve instance
        track_index: Audio track index (1-based)
        volume_db: Volume in decibels (-96 to +12)
        
    Returns:
        Status dictionary
    """
    success, project, timeline, msg = _get_fairlight_context(resolve)
    if not success:
        return {"error": msg}
    
    # Switch to Fairlight page
    if resolve.GetCurrentPage() != "fairlight":
        resolve.OpenPage("fairlight")
    
    # Clamp volume to valid range
    volume_db = max(-96.0, min(12.0, volume_db))
    
    try:
        audio_track_count = timeline.GetTrackCount("audio")
        if track_index < 1 or track_index > audio_track_count:
            return {"error": f"Invalid track index. Valid range: 1-{audio_track_count}"}
        
        # Note: The Resolve API has limited audio mixing control
        # This provides the framework for when/if it becomes available
        
        # Try to set via timeline settings
        setting_name = f"audioTrack{track_index}Volume"
        result = timeline.SetSetting(setting_name, str(volume_db))
        
        if result:
            return {
                "success": True,
                "track_index": track_index,
                "volume_db": volume_db
            }
        else:
            return {
                "warning": "The scripting API may not support direct volume control",
                "suggestion": "Use the Fairlight page for manual configuration",
                "track_index": track_index,
                "requested_volume_db": volume_db
            }
    except Exception as e:
        logger.error(f"Error setting track volume: {e}")
        return {"error": f"Failed to set volume: {str(e)}"}


def get_audio_clip_info(resolve, track_index: int = None) -> Dict[str, Any]:
    """Get information about audio clips in the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        track_index: Optional specific track (all tracks if None)
        
    Returns:
        Dictionary with audio clip information
    """
    success, project, timeline, msg = _get_fairlight_context(resolve)
    if not success:
        return {"error": msg}
    
    try:
        audio_track_count = timeline.GetTrackCount("audio")
        clips_info = []
        
        tracks_to_check = [track_index] if track_index else range(1, audio_track_count + 1)
        
        for idx in tracks_to_check:
            if idx < 1 or idx > audio_track_count:
                continue
                
            items = timeline.GetItemListInTrack("audio", idx)
            if not items:
                continue
                
            for item in items:
                clip_info = {
                    "track_index": idx,
                    "name": item.GetName() if hasattr(item, 'GetName') else "Unknown"
                }
                
                # Get clip properties
                try:
                    clip_info["start_frame"] = item.GetStart()
                    clip_info["end_frame"] = item.GetEnd()
                    clip_info["duration"] = item.GetDuration()
                except Exception:
                    pass
                
                # Get source properties
                try:
                    media_pool_item = item.GetMediaPoolItem()
                    if media_pool_item:
                        clip_props = media_pool_item.GetClipProperty()
                        if clip_props:
                            clip_info["sample_rate"] = clip_props.get("Audio Sample Rate", "")
                            clip_info["channels"] = clip_props.get("Audio Channels", "")
                except Exception:
                    pass
                
                clips_info.append(clip_info)
        
        return {
            "timeline": timeline.GetName(),
            "clips": clips_info,
            "total_clips": len(clips_info)
        }
    except Exception as e:
        logger.error(f"Error getting audio clip info: {e}")
        return {"error": f"Failed to get clip information: {str(e)}"}


def analyze_audio_levels(resolve, clip_name: str = None) -> Dict[str, Any]:
    """Analyze audio levels for clips.
    
    Note: Full audio analysis requires Neural Engine features
    available in DaVinci Resolve Studio.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Specific clip to analyze (analyzes timeline if None)
        
    Returns:
        Dictionary with level analysis (if available)
    """
    success, project, timeline, msg = _get_fairlight_context(resolve)
    if not success:
        return {"error": msg}
    
    # Switch to Fairlight page for audio operations
    if resolve.GetCurrentPage() != "fairlight":
        resolve.OpenPage("fairlight")
    
    try:
        # Basic info we can gather
        frame_rate = float(timeline.GetSetting("timelineFrameRate") or 24)
        audio_tracks = timeline.GetTrackCount("audio")
        
        result = {
            "timeline": timeline.GetName(),
            "frame_rate": frame_rate,
            "audio_track_count": audio_tracks,
            "analysis": {
                "note": "Detailed level analysis requires DaVinci Resolve Studio",
                "suggestion": "Use the Fairlight page to view loudness meters"
            }
        }
        
        # Try to get track info
        tracks_analysis = []
        for i in range(1, audio_tracks + 1):
            track_info = {
                "track": i,
                "name": timeline.GetTrackName("audio", i)
            }
            
            items = timeline.GetItemListInTrack("audio", i)
            if items:
                track_info["clips_count"] = len(items)
            
            tracks_analysis.append(track_info)
        
        result["tracks"] = tracks_analysis
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing audio: {e}")
        return {"error": f"Audio analysis failed: {str(e)}"}


def add_audio_track(resolve, track_type: str = "stereo") -> Dict[str, Any]:
    """Add a new audio track to the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        track_type: Track type ('mono', 'stereo', '5.1', '7.1')
        
    Returns:
        Status dictionary
    """
    success, project, timeline, msg = _get_fairlight_context(resolve)
    if not success:
        return {"error": msg}
    
    try:
        current_count = timeline.GetTrackCount("audio")
        
        # Add audio track
        # The API uses specific type strings
        type_map = {
            "mono": "mono",
            "stereo": "stereo",
            "5.1": "5.1",
            "7.1": "7.1",
            "adaptive": "adaptive"
        }
        
        actual_type = type_map.get(track_type.lower(), "stereo")
        result = timeline.AddTrack("audio", actual_type)
        
        if result:
            new_count = timeline.GetTrackCount("audio")
            return {
                "success": True,
                "previous_count": current_count,
                "new_count": new_count,
                "track_type": actual_type
            }
        else:
            return {"error": "Failed to add audio track"}
            
    except Exception as e:
        logger.error(f"Error adding audio track: {e}")
        return {"error": f"Failed to add track: {str(e)}"}


def delete_audio_track(resolve, track_index: int) -> Dict[str, Any]:
    """Delete an audio track from the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        track_index: Index of track to delete (1-based)
        
    Returns:
        Status dictionary
    """
    success, project, timeline, msg = _get_fairlight_context(resolve)
    if not success:
        return {"error": msg}
    
    try:
        current_count = timeline.GetTrackCount("audio")
        
        if track_index < 1 or track_index > current_count:
            return {"error": f"Invalid track index. Valid range: 1-{current_count}"}
        
        result = timeline.DeleteTrack("audio", track_index)
        
        if result:
            new_count = timeline.GetTrackCount("audio")
            return {
                "success": True,
                "deleted_track": track_index,
                "previous_count": current_count,
                "new_count": new_count
            }
        else:
            return {"error": f"Failed to remove track {track_index}"}
            
    except Exception as e:
        logger.error(f"Error deleting audio track: {e}")
        return {"error": f"Failed to remove track: {str(e)}"}


def set_track_enabled(resolve, track_index: int, enabled: bool) -> Dict[str, Any]:
    """Enable or disable (mute) an audio track.
    
    Args:
        resolve: DaVinci Resolve instance
        track_index: Audio track index (1-based)
        enabled: True to enable, False to mute
        
    Returns:
        Status dictionary
    """
    success, project, timeline, msg = _get_fairlight_context(resolve)
    if not success:
        return {"error": msg}
    
    try:
        audio_track_count = timeline.GetTrackCount("audio")
        
        if track_index < 1 or track_index > audio_track_count:
            return {"error": f"Invalid track index. Valid range: 1-{audio_track_count}"}
        
        result = timeline.SetTrackEnable("audio", track_index, enabled)
        
        if result:
            return {
                "success": True,
                "track_index": track_index,
                "enabled": enabled
            }
        else:
            return {
                "warning": "SetTrackEnable may not be supported",
                "track_index": track_index,
                "requested_state": enabled
            }
            
    except Exception as e:
        logger.error(f"Error setting track enabled state: {e}")
        return {"error": f"Failed to change track state: {str(e)}"}


def voice_isolation(resolve, clip_name: str) -> Dict[str, Any]:
    """Apply voice isolation using DaVinci Neural Engine.
    
    Note: This feature requires DaVinci Resolve Studio.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip to process
        
    Returns:
        Status dictionary
    """
    success, project, timeline, msg = _get_fairlight_context(resolve)
    if not success:
        return {"error": msg}
    
    # Switch to Fairlight page
    if resolve.GetCurrentPage() != "fairlight":
        resolve.OpenPage("fairlight")
    
    try:
        # Find the clip in the timeline
        audio_tracks = timeline.GetTrackCount("audio")
        target_clip = None
        
        for i in range(1, audio_tracks + 1):
            items = timeline.GetItemListInTrack("audio", i)
            if items:
                for item in items:
                    if hasattr(item, 'GetName') and item.GetName() == clip_name:
                        target_clip = item
                        break
            if target_clip:
                break
        
        if not target_clip:
            return {"error": f"Clip '{clip_name}' not found in timeline"}
        
        # Voice isolation is typically applied through the Fairlight FX
        # The API access is limited, provide guidance
        return {
            "clip_found": True,
            "clip_name": clip_name,
            "note": "Voice Isolation requires DaVinci Resolve Studio",
            "instructions": [
                "1. Select a clip on the Fairlight page",
                "2. Open Effects Library -> Audio FX -> Fairlight FX",
                "3. Find 'Voice Isolation' or 'Dialogue Isolation'",
                "4. Drag the effect onto the clip",
                "5. Adjust parameters in the Inspector"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error with voice isolation: {e}")
        return {"error": f"Voice isolation failed: {str(e)}"}


def normalize_audio(resolve, target_lufs: float = -14.0) -> Dict[str, Any]:
    """Provide normalization guidance for audio clips.
    
    Standard loudness targets:
    - -14 LUFS: Streaming (YouTube, Spotify)
    - -16 LUFS: Broadcast (EBU R128)
    - -24 LUFS: Film/Cinema
    
    Args:
        resolve: DaVinci Resolve instance
        target_lufs: Target loudness in LUFS
        
    Returns:
        Guidance dictionary
    """
    success, project, timeline, msg = _get_fairlight_context(resolve)
    if not success:
        return {"error": msg}
    
    return {
        "target_lufs": target_lufs,
        "standard_targets": {
            "streaming": -14.0,
            "broadcast_ebu": -16.0,
            "broadcast_atsc": -24.0,
            "cinema": -24.0
        },
        "instructions": [
            f"1. Open the Fairlight page",
            f"2. Open Effects Library -> Audio FX -> Dynamics",
            f"3. Add a 'Limiter' on the master bus",
            f"4. Set target level: {target_lufs} LUFS",
            "5. Enable the Loudness meter for monitoring",
            "6. If needed, add a Compressor before the Limiter"
        ],
        "timeline": timeline.GetName()
    }
