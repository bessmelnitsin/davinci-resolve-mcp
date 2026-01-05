"""
Fairlight (Audio) Tools for DaVinci Resolve MCP

Audio editing and mixing functionality:
- Audio track management
- Volume and pan controls
- Audio clip info
- Voice isolation
- Normalization guidance
"""
from typing import Dict, Any, List

from src.server_instance import mcp
from src.context import get_resolve
from src.api.fairlight_operations import (
    get_audio_tracks as get_tracks_impl,
    set_track_volume as set_volume_impl,
    get_audio_clip_info as get_clips_impl,
    analyze_audio_levels as analyze_impl,
    add_audio_track as add_track_impl,
    delete_audio_track as delete_track_impl,
    set_track_enabled as set_enabled_impl,
    voice_isolation as voice_isolation_impl,
    normalize_audio as normalize_impl
)


# ============================================================
# Audio Track Management
# ============================================================

@mcp.tool()
def get_audio_tracks(timeline_name: str = None) -> Dict[str, Any]:
    """Get list of audio tracks in the timeline.
    
    Args:
        timeline_name: Optional timeline name (uses current if not specified)
    """
    resolve = get_resolve()
    return get_tracks_impl(resolve, timeline_name)


@mcp.tool()
def add_audio_track_fairlight(track_type: str = "stereo") -> Dict[str, Any]:
    """Add a new audio track to the timeline.
    
    Args:
        track_type: Track type ('mono', 'stereo', '5.1', '7.1', 'adaptive')
    """
    resolve = get_resolve()
    return add_track_impl(resolve, track_type)


@mcp.tool()
def delete_audio_track_fairlight(track_index: int) -> Dict[str, Any]:
    """Delete an audio track from the timeline.
    
    Args:
        track_index: Index of track to delete (1-based)
    """
    resolve = get_resolve()
    return delete_track_impl(resolve, track_index)


@mcp.tool()
def set_audio_track_enabled(track_index: int, enabled: bool) -> Dict[str, Any]:
    """Enable or disable (mute) an audio track.
    
    Args:
        track_index: Audio track index (1-based)
        enabled: True to enable, False to mute
    """
    resolve = get_resolve()
    return set_enabled_impl(resolve, track_index, enabled)


@mcp.tool()
def set_audio_track_volume(track_index: int, volume_db: float) -> Dict[str, Any]:
    """Set volume for an audio track.
    
    Args:
        track_index: Audio track index (1-based)
        volume_db: Volume in decibels (-96 to +12)
    """
    resolve = get_resolve()
    return set_volume_impl(resolve, track_index, volume_db)


# ============================================================
# Audio Clip Analysis
# ============================================================

@mcp.tool()
def get_audio_clip_info(track_index: int = None) -> Dict[str, Any]:
    """Get information about audio clips in the timeline.
    
    Args:
        track_index: Optional specific track (all tracks if not specified)
    """
    resolve = get_resolve()
    return get_clips_impl(resolve, track_index)


@mcp.tool()
def analyze_audio_levels(clip_name: str = None) -> Dict[str, Any]:
    """Analyze audio levels for clips.
    
    Args:
        clip_name: Specific clip to analyze (analyzes timeline if not specified)
    """
    resolve = get_resolve()
    return analyze_impl(resolve, clip_name)


# ============================================================
# Audio Processing (Neural Engine)
# ============================================================

@mcp.tool()
def apply_voice_isolation(clip_name: str) -> Dict[str, Any]:
    """Apply voice isolation using DaVinci Neural Engine.
    
    Note: Requires DaVinci Resolve Studio.
    
    Args:
        clip_name: Name of the clip to process
    """
    resolve = get_resolve()
    return voice_isolation_impl(resolve, clip_name)


@mcp.tool()
def get_audio_normalization_guide(target_lufs: float = -14.0) -> Dict[str, Any]:
    """Get normalization guidance for audio clips.
    
    Standard loudness targets:
    - -14 LUFS: Streaming (YouTube, Spotify)
    - -16 LUFS: Broadcast (EBU R128)
    - -24 LUFS: Film/Cinema
    
    Args:
        target_lufs: Target loudness in LUFS
    """
    resolve = get_resolve()
    return normalize_impl(resolve, target_lufs)


# ============================================================
# Voice Isolation State (Timeline)
# ============================================================

@mcp.tool()
def get_voice_isolation_state(track_index: int = None) -> Dict[str, Any]:
    """Get Voice Isolation state for a track or timeline.
    
    Args:
        track_index: Audio track index (uses timeline if not specified)
    """
    resolve = get_resolve()
    if not resolve:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    if not pm:
        return {"error": "Failed to get Project Manager"}
    
    project = pm.GetCurrentProject()
    if not project:
        return {"error": "No project open"}
    
    timeline = project.GetCurrentTimeline()
    if not timeline:
        return {"error": "No timeline active"}
    
    try:
        if track_index:
            state = timeline.GetVoiceIsolationState(track_index)
            return {
                "track_index": track_index,
                "is_enabled": state.get("isEnabled", False) if state else False,
                "amount": state.get("amount", 0) if state else 0
            }
        else:
            # Get state for all audio tracks
            audio_tracks = timeline.GetTrackCount("audio")
            states = []
            for i in range(1, audio_tracks + 1):
                state = timeline.GetVoiceIsolationState(i)
                states.append({
                    "track_index": i,
                    "is_enabled": state.get("isEnabled", False) if state else False,
                    "amount": state.get("amount", 0) if state else 0
                })
            return {"timeline": timeline.GetName(), "tracks": states}
    except Exception as e:
        return {"error": f"Error: {e}"}


@mcp.tool()
def set_voice_isolation_state(track_index: int, enabled: bool, 
                              amount: int = 50) -> str:
    """Set Voice Isolation state for a track.
    
    Args:
        track_index: Audio track index (1-based)
        enabled: Enable/disable voice isolation
        amount: Isolation amount (0-100)
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return "Error: Failed to get Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return "Error: No project open"
    
    timeline = project.GetCurrentTimeline()
    if not timeline:
        return "Error: No timeline active"
    
    try:
        amount = max(0, min(100, amount))
        state = {"isEnabled": enabled, "amount": amount}
        
        if timeline.SetVoiceIsolationState(track_index, state):
            return f"Voice Isolation {'enabled' if enabled else 'disabled'} on track {track_index} (amount: {amount}%)"
        return "Failed to set Voice Isolation state"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Audio Mapping
# ============================================================

@mcp.tool()
def get_timeline_item_audio_mapping(clip_name: str) -> Dict[str, Any]:
    """Get audio mapping for a timeline item.
    
    Args:
        clip_name: Name of the clip in timeline
    """
    resolve = get_resolve()
    if not resolve:
        return {"error": "Not connected"}
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    timeline = project.GetCurrentTimeline() if project else None
    
    if not timeline:
        return {"error": "No timeline"}
    
    try:
        # Search in audio tracks
        audio_tracks = timeline.GetTrackCount("audio")
        for i in range(1, audio_tracks + 1):
            items = timeline.GetItemListInTrack("audio", i)
            if items:
                for item in items:
                    if item.GetName() == clip_name:
                        mapping = item.GetSourceAudioChannelMapping()
                        return {
                            "clip_name": clip_name,
                            "track_index": i,
                            "audio_mapping": mapping
                        }
        
        return {"error": f"Clip '{clip_name}' not found"}
    except Exception as e:
        return {"error": f"Error: {e}"}


# ============================================================
# Phase 2.5: Fairlight Extensions
# ============================================================

@mcp.tool()
def insert_audio_at_playhead(media_path: str, track_index: int = 1) -> str:
    """Insert audio from a file at the current playhead position.
    
    Args:
        media_path: Path to the audio file
        track_index: Audio track index to insert on (1-based, default: 1)
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return "Error: Failed to get Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return "Error: No project open"
    
    timeline = project.GetCurrentTimeline()
    if not timeline:
        return "Error: No timeline active"
    
    try:
        result = timeline.InsertAudioToCurrentTrackAtPlayhead(media_path, track_index)
        if result:
            return f"Inserted audio at playhead on track {track_index}"
        return "Failed to insert audio"
    except AttributeError:
        return "Error: InsertAudioToCurrentTrackAtPlayhead not available"
    except Exception as e:
        return f"Error inserting audio: {e}"

