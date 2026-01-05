
"""
Media Pool Tools for DaVinci Resolve MCP
"""
from typing import List, Dict, Any

from src.server_instance import mcp
from src.context import get_resolve
from src.api.media_operations import (
    list_media_pool_clips as list_clips_impl,
    import_media as import_media_impl,
    create_bin as create_bin_impl,
    add_clip_to_timeline as add_clip_impl,
    list_bins as list_bins_impl,
    get_bin_contents as get_bin_contents_impl,
    
    delete_media as delete_media_impl,
    move_media_to_bin as move_media_impl,
    auto_sync_audio as auto_sync_impl,
    unlink_clips as unlink_clips_impl,
    relink_clips as relink_clips_impl,
    create_sub_clip as create_sub_clip_impl,
    get_all_media_pool_folders
)

@mcp.tool()
def export_folder(folder_name: str, export_path: str, export_type: str = "DRB") -> str:
    """Export a folder to a DRB file."""
    resolve = get_resolve()
    if not resolve: return "Error: Not connected"
    
    import os
    pm = resolve.GetProjectManager()
    if not pm: return "Error: No Project Manager"
    proj = pm.GetCurrentProject()
    if not proj: return "Error: No project open"
    mp = proj.GetMediaPool()
    
    target_folder = None
    if folder_name.lower() in ["root", "master"]:
        target_folder = mp.GetRootFolder()
    else:
        folders = get_all_media_pool_folders(mp)
        for f in folders:
            if f.GetName() == folder_name:
                target_folder = f
                break
                
    if not target_folder: return f"Error: Folder '{folder_name}' not found"
    
    export_dir = os.path.dirname(export_path)
    if not os.path.exists(export_dir) and export_dir:
        try:
            os.makedirs(export_dir)
        except Exception as e:
            return f"Error creating dir: {e}"
            
    try:
        if target_folder.Export(export_path):
            return f"Exported '{folder_name}' to '{export_path}'"
        return "Failed to export"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def transcribe_folder_audio(folder_name: str, language: str = "en-US") -> str:
    """Transcribe audio for all clips in a folder (Native)."""
    resolve = get_resolve()
    if not resolve: return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    if not pm: return "Error: No Project Manager"
    proj = pm.GetCurrentProject()
    if not proj: return "Error: No project open"
    mp = proj.GetMediaPool()
    
    target_folder = None
    if folder_name.lower() in ["root", "master"]:
        target_folder = mp.GetRootFolder()
    else:
        folders = get_all_media_pool_folders(mp)
        for f in folders:
            if f.GetName() == folder_name:
                target_folder = f
                break
                
    if not target_folder: return f"Error: Folder '{folder_name}' not found"
    
    try:
        if target_folder.TranscribeAudio(language):
            return f"Started transcription for folder '{folder_name}'"
        return "Failed to start transcription"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def delete_media(clip_name: str) -> str:
    """Delete a media clip from the media pool by name."""
    resolve = get_resolve()
    return delete_media_impl(resolve, clip_name)

@mcp.tool()
def move_media_to_bin(clip_name: str, bin_name: str) -> str:
    """Move a media clip to a specific bin."""
    resolve = get_resolve()
    return move_media_impl(resolve, clip_name, bin_name)

@mcp.tool()
def auto_sync_audio(clip_names: List[str], sync_method: str = "waveform", 
                   append_mode: bool = False, target_bin: str = None) -> str:
    """Sync audio between clips."""
    resolve = get_resolve()
    return auto_sync_impl(resolve, clip_names, sync_method, append_mode, target_bin)

@mcp.tool()
def unlink_clips(clip_names: List[str]) -> str:
    """Unlink specified clips."""
    resolve = get_resolve()
    return unlink_clips_impl(resolve, clip_names)

@mcp.tool()
def relink_clips(clip_names: List[str], media_paths: List[str] = None, 
                folder_path: str = None, recursive: bool = False) -> str:
    """Relink specified clips to their media files."""
    resolve = get_resolve()
    return relink_clips_impl(resolve, clip_names, media_paths, folder_path, recursive)

@mcp.tool()
def create_sub_clip(clip_name: str, start_frame: int, end_frame: int, 
                   sub_clip_name: str = None, bin_name: str = None) -> str:
    """Create a subclip using in and out points."""
    resolve = get_resolve()
    return create_sub_clip_impl(resolve, clip_name, start_frame, end_frame, sub_clip_name, bin_name)

@mcp.resource("resolve://media-pool-bins")
def list_media_pool_bins() -> List[Dict[str, Any]]:
    """List all bins/folders in the media pool."""
    resolve = get_resolve()
    return list_bins_impl(resolve)

@mcp.resource("resolve://media-pool-bin/{bin_name}")
def get_media_pool_bin_contents(bin_name: str) -> List[Dict[str, Any]]:
    """Get contents of a specific bin."""
    resolve = get_resolve()
    return get_bin_contents_impl(resolve, bin_name)

@mcp.tool()
def link_proxy_media(clip_name: str, proxy_file_path: str) -> str:
    """Link a proxy media file to a clip."""
    resolve = get_resolve()
    if not resolve: return "Error: Not connected"
    
    # Simple inline implementation or move to api
    # For now, inline to save time as it was inline in server
    pm = resolve.GetProjectManager()
    if not pm: return "Error: No Project Manager"
    proj = pm.GetCurrentProject()
    if not proj: return "Error: No project open"
    mp = proj.GetMediaPool()
    if not mp: return "Error: No Media Pool"
    
    clips = list_clips_impl(resolve) # This returns dicts, need objects?
    # list_clips_impl actually returns dict in resource, but we need object.
    # We need get_all_media_pool_clips
    
    from src.api.media_operations import get_all_media_pool_clips
    clip_objs = get_all_media_pool_clips(mp)
    target_clip = next((c for c in clip_objs if c.GetName() == clip_name), None)
    
    if not target_clip: return f"Error: Clip '{clip_name}' not found"
    
    try:
        if target_clip.LinkProxyMedia(proxy_file_path):
            return f"Linked proxy to '{clip_name}'"
        return "Failed to link proxy"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def unlink_proxy_media(clip_name: str) -> str:
    """Unlink proxy media from a clip."""
    resolve = get_resolve()
    if not resolve: return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    if not pm: return "Error: No Project Manager"
    proj = pm.GetCurrentProject()
    if not proj: return "Error: No project open"
    mp = proj.GetMediaPool()
    
    from src.api.media_operations import get_all_media_pool_clips
    clip_objs = get_all_media_pool_clips(mp)
    target_clip = next((c for c in clip_objs if c.GetName() == clip_name), None)
    
    if not target_clip: return f"Error: Clip '{clip_name}' not found"
    
    try:
        if target_clip.UnlinkProxyMedia():
            return f"Unlinked proxy from '{clip_name}'"
        return "Failed to unlink proxy"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def replace_clip(clip_name: str, replacement_path: str) -> str:
    """Replace a clip with another media file."""
    resolve = get_resolve()
    if not resolve: return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    if not pm: return "Error: No Project Manager"
    proj = pm.GetCurrentProject()
    if not proj: return "Error: No project open"
    mp = proj.GetMediaPool()
    
    from src.api.media_operations import get_all_media_pool_clips
    clip_objs = get_all_media_pool_clips(mp)
    target_clip = next((c for c in clip_objs if c.GetName() == clip_name), None)
    
    if not target_clip: return f"Error: Clip '{clip_name}' not found"
    
    try:
        if target_clip.ReplaceClip(replacement_path):
            return f"Replaced '{clip_name}'"
        return "Failed to replace clip"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def transcribe_audio_native(clip_name: str, language: str = "en-US") -> str:
    """Transcribe audio for a clip using DaVinci Native AI."""
    resolve = get_resolve()
    if not resolve: return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    if not pm: return "Error: No Project Manager"
    proj = pm.GetCurrentProject()
    if not proj: return "Error: No project open"
    mp = proj.GetMediaPool()
    
    from src.api.media_operations import get_all_media_pool_clips
    clip_objs = get_all_media_pool_clips(mp)
    target_clip = next((c for c in clip_objs if c.GetName() == clip_name), None)
    
    if not target_clip: return f"Error: Clip '{clip_name}' not found"
    
    try:
        if target_clip.TranscribeAudio(language):
            return f"Started transcription for '{clip_name}' ({language})"
        return "Failed to start transcription"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def clear_transcription_native(clip_name: str) -> str:
    """Clear native audio transcription for a clip."""
    resolve = get_resolve()
    if not resolve: return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    if not pm: return "Error: No Project Manager"
    proj = pm.GetCurrentProject()
    if not proj: return "Error: No project open"
    mp = proj.GetMediaPool()
    
    from src.api.media_operations import get_all_media_pool_clips
    clip_objs = get_all_media_pool_clips(mp)
    target_clip = next((c for c in clip_objs if c.GetName() == clip_name), None)
    
    if not target_clip: return f"Error: Clip '{clip_name}' not found"
    
    try:
        if target_clip.ClearTranscription():
            return f"Cleared transcription for '{clip_name}'"
        return "Failed to clear transcription"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def list_clips() -> List[Dict[str, Any]]:
    """List all clips available in the Media Pool."""
    resolve = get_resolve()
    return list_clips_impl(resolve)

@mcp.resource("resolve://media-pool-clips")
def list_media_pool_clips() -> List[Dict[str, Any]]:
    """List all clips in the media pool."""
    resolve = get_resolve()
    return list_clips_impl(resolve)

@mcp.tool()
def import_media(file_path: str) -> str:
    """Import media file into the media pool."""
    resolve = get_resolve()
    return import_media_impl(resolve, file_path)

@mcp.tool()
def create_bin(name: str) -> str:
    """Create a new bin in the media pool."""
    resolve = get_resolve()
    return create_bin_impl(resolve, name)

@mcp.tool()
def add_clip_to_timeline(clip_name: str, timeline_name: str = None) -> str:
    """Append a clip to the timeline."""
    resolve = get_resolve()
    return add_clip_impl(resolve, clip_name, timeline_name)


# ============================================================
# Phase 3: MediaPoolItem Extended Tools
# ============================================================

from src.api.media_operations import (
    get_clip_metadata as get_clip_metadata_impl,
    set_clip_metadata as set_clip_metadata_impl,
    get_clip_property as get_clip_property_impl,
    set_clip_property as set_clip_property_impl,
    add_clip_marker as add_clip_marker_impl,
    get_clip_markers as get_clip_markers_impl,
    delete_clip_markers as delete_clip_markers_impl,
    delete_clip_marker_at_frame as delete_marker_at_frame_impl,
    add_clip_flag as add_clip_flag_impl,
    get_clip_flags as get_clip_flags_impl,
    clear_clip_flags as clear_clip_flags_impl,
    get_clip_color as get_clip_color_impl,
    set_clip_color as set_clip_color_impl,
    clear_clip_color as clear_clip_color_impl,
    rename_clip as rename_clip_impl,
    get_clip_unique_id as get_clip_id_impl,
    get_clip_mark_in_out as get_mark_in_out_impl,
    set_clip_mark_in_out as set_mark_in_out_impl,
    clear_clip_mark_in_out as clear_mark_in_out_impl,
)


# --- Clip Metadata Tools ---

@mcp.resource("resolve://clip-metadata/{clip_name}")
def get_clip_metadata(clip_name: str) -> Dict[str, Any]:
    """Get all metadata for a media pool clip."""
    resolve = get_resolve()
    return get_clip_metadata_impl(resolve, clip_name)


@mcp.tool()
def set_clip_metadata(clip_name: str, metadata: Dict[str, str]) -> str:
    """Set metadata for a media pool clip.
    
    Args:
        clip_name: Name of the clip
        metadata: Dictionary of metadata key-value pairs (e.g. {"Description": "My clip"})
    """
    resolve = get_resolve()
    return set_clip_metadata_impl(resolve, clip_name, metadata)


@mcp.resource("resolve://clip-properties/{clip_name}")
def get_clip_properties(clip_name: str) -> Dict[str, Any]:
    """Get all properties for a media pool clip."""
    resolve = get_resolve()
    return get_clip_property_impl(resolve, clip_name)


@mcp.tool()
def set_clip_property(clip_name: str, property_name: str, value: str) -> str:
    """Set a property for a media pool clip."""
    resolve = get_resolve()
    return set_clip_property_impl(resolve, clip_name, property_name, value)


# --- Clip Markers Tools ---

@mcp.tool()
def add_clip_marker(clip_name: str, frame: int, color: str = "Blue",
                    name: str = "", note: str = "", duration: int = 1) -> str:
    """Add a marker to a media pool clip.
    
    Args:
        clip_name: Name of the clip
        frame: Frame number for the marker
        color: Marker color (Blue, Cyan, Green, Yellow, Red, Pink, Purple, etc)
        name: Marker name/title
        note: Marker note text
        duration: Duration in frames
    """
    resolve = get_resolve()
    return add_clip_marker_impl(resolve, clip_name, frame, color, name, note, duration)


@mcp.resource("resolve://clip-markers/{clip_name}")
def get_clip_markers(clip_name: str) -> Dict[str, Any]:
    """Get all markers from a media pool clip."""
    resolve = get_resolve()
    return get_clip_markers_impl(resolve, clip_name)


@mcp.tool()
def delete_clip_markers(clip_name: str, color: str = "All") -> str:
    """Delete markers from a clip by color.
    
    Args:
        clip_name: Name of the clip
        color: Marker color to delete, or 'All' for all markers
    """
    resolve = get_resolve()
    return delete_clip_markers_impl(resolve, clip_name, color)


@mcp.tool()
def delete_clip_marker_at_frame(clip_name: str, frame: int) -> str:
    """Delete a specific marker at a frame."""
    resolve = get_resolve()
    return delete_marker_at_frame_impl(resolve, clip_name, frame)


# --- Clip Flags Tools ---

@mcp.tool()
def add_clip_flag(clip_name: str, color: str) -> str:
    """Add a flag to a media pool clip.
    
    Args:
        clip_name: Name of the clip
        color: Flag color (Blue, Cyan, Green, Yellow, Red, Pink, Purple, etc)
    """
    resolve = get_resolve()
    return add_clip_flag_impl(resolve, clip_name, color)


@mcp.resource("resolve://clip-flags/{clip_name}")
def get_clip_flags(clip_name: str) -> Dict[str, Any]:
    """Get all flags from a media pool clip."""
    resolve = get_resolve()
    return get_clip_flags_impl(resolve, clip_name)


@mcp.tool()
def clear_clip_flags(clip_name: str, color: str = "All") -> str:
    """Clear flags from a clip.
    
    Args:
        clip_name: Name of the clip
        color: Flag color to clear, or 'All' for all flags
    """
    resolve = get_resolve()
    return clear_clip_flags_impl(resolve, clip_name, color)


# --- Clip Color Tools ---

@mcp.resource("resolve://clip-color/{clip_name}")
def get_clip_color(clip_name: str) -> Dict[str, Any]:
    """Get the clip color label."""
    resolve = get_resolve()
    return get_clip_color_impl(resolve, clip_name)


@mcp.tool()
def set_clip_color(clip_name: str, color: str) -> str:
    """Set the clip color label.
    
    Args:
        clip_name: Name of the clip
        color: Color name (Orange, Apricot, Yellow, Lime, Olive, Green, Teal,
               Navy, Blue, Purple, Violet, Pink, Tan, Beige, Brown, Chocolate)
    """
    resolve = get_resolve()
    return set_clip_color_impl(resolve, clip_name, color)


@mcp.tool()
def clear_clip_color(clip_name: str) -> str:
    """Clear the clip color label."""
    resolve = get_resolve()
    return clear_clip_color_impl(resolve, clip_name)


# --- Clip Rename Tool ---

@mcp.tool()
def rename_clip(clip_name: str, new_name: str) -> str:
    """Rename a media pool clip."""
    resolve = get_resolve()
    return rename_clip_impl(resolve, clip_name, new_name)


# --- Clip ID Resource ---

@mcp.resource("resolve://clip-id/{clip_name}")
def get_clip_id(clip_name: str) -> Dict[str, Any]:
    """Get the unique ID and media ID of a clip."""
    resolve = get_resolve()
    return get_clip_id_impl(resolve, clip_name)


# --- Clip Mark In/Out Tools ---

@mcp.resource("resolve://clip-mark-in-out/{clip_name}")
def get_clip_mark_in_out(clip_name: str) -> Dict[str, Any]:
    """Get mark in/out points for a clip."""
    resolve = get_resolve()
    return get_mark_in_out_impl(resolve, clip_name)


@mcp.tool()
def set_clip_mark_in_out(clip_name: str, mark_in: int = None, mark_out: int = None) -> str:
    """Set mark in/out points for a clip.
    
    Args:
        clip_name: Name of the clip
        mark_in: Mark in frame number
        mark_out: Mark out frame number
    """
    resolve = get_resolve()
    return set_mark_in_out_impl(resolve, clip_name, mark_in, mark_out)


@mcp.tool()
def clear_clip_mark_in_out(clip_name: str) -> str:
    """Clear mark in/out points for a clip."""
    resolve = get_resolve()
    return clear_mark_in_out_impl(resolve, clip_name)


# ============================================================
# Phase 2.1: MediaPool Extensions
# ============================================================

def _get_media_pool_clip(resolve, clip_name: str):
    """Helper to get a MediaPoolItem by name."""
    pm = resolve.GetProjectManager()
    if not pm:
        return None, "No Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return None, "No project open"
    
    mp = project.GetMediaPool()
    if not mp:
        return None, "No Media Pool"
    
    from src.api.media_operations import get_all_media_pool_clips
    clips = get_all_media_pool_clips(mp)
    for clip in clips:
        if clip.GetName() == clip_name:
            return clip, None
    
    return None, f"Clip '{clip_name}' not found"


@mcp.tool()
def get_selected_clips() -> Dict[str, Any]:
    """Get list of currently selected clips in the media pool."""
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    if not pm:
        return {"error": "No Project Manager"}
    
    project = pm.GetCurrentProject()
    if not project:
        return {"error": "No project open"}
    
    mp = project.GetMediaPool()
    if not mp:
        return {"error": "No Media Pool"}
    
    try:
        selected = mp.GetSelectedClips()
        if selected:
            clips_info = []
            for clip in selected:
                clips_info.append({
                    "name": clip.GetName(),
                    "id": clip.GetUniqueId() if hasattr(clip, 'GetUniqueId') else None
                })
            return {
                "selected_count": len(clips_info),
                "clips": clips_info
            }
        return {"selected_count": 0, "clips": []}
    except AttributeError:
        return {"error": "GetSelectedClips not available (requires DaVinci Resolve 18+)"}
    except Exception as e:
        return {"error": f"Error getting selected clips: {e}"}


@mcp.tool()
def set_selected_clip(clip_name: str) -> str:
    """Select a clip in the media pool by name.
    
    Args:
        clip_name: Name of the clip to select
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    clip, error = _get_media_pool_clip(resolve, clip_name)
    if error:
        return f"Error: {error}"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject()
    mp = project.GetMediaPool()
    
    try:
        result = mp.SetSelectedClip(clip)
        if result:
            return f"Selected clip '{clip_name}'"
        return f"Failed to select clip '{clip_name}'"
    except AttributeError:
        return "Error: SetSelectedClip not available (requires DaVinci Resolve 18+)"
    except Exception as e:
        return f"Error selecting clip: {e}"


@mcp.tool()
def export_metadata_csv(file_path: str) -> str:
    """Export metadata for all clips in the media pool to a CSV file.
    
    Args:
        file_path: Path for the exported CSV file
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
    
    mp = project.GetMediaPool()
    if not mp:
        return "Error: No Media Pool"
    
    try:
        result = mp.ExportMetadata(file_path)
        if result:
            return f"Exported metadata to: {file_path}"
        return "Failed to export metadata"
    except AttributeError:
        return "Error: ExportMetadata not available (requires DaVinci Resolve 18+)"
    except Exception as e:
        return f"Error exporting metadata: {e}"


@mcp.tool()
def get_clip_audio_mapping(clip_name: str) -> Dict[str, Any]:
    """Get the audio channel mapping for a media pool clip.
    
    Args:
        clip_name: Name of the clip
    """
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    clip, error = _get_media_pool_clip(resolve, clip_name)
    if error:
        return {"error": error}
    
    try:
        mapping = clip.GetAudioMapping()
        if mapping:
            return {
                "clip_name": clip_name,
                "audio_mapping": mapping
            }
        return {"clip_name": clip_name, "audio_mapping": None}
    except AttributeError:
        return {"error": "GetAudioMapping not available"}
    except Exception as e:
        return {"error": f"Error getting audio mapping: {e}"}


@mcp.tool()
def get_marker_by_custom_data(clip_name: str, custom_data: str) -> Dict[str, Any]:
    """Find a marker by its custom data string.
    
    Args:
        clip_name: Name of the clip
        custom_data: Custom data string to search for
    """
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    clip, error = _get_media_pool_clip(resolve, clip_name)
    if error:
        return {"error": error}
    
    try:
        marker = clip.GetMarkerByCustomData(custom_data)
        if marker:
            return {
                "clip_name": clip_name,
                "custom_data": custom_data,
                "marker": marker
            }
        return {"info": f"No marker found with custom data: {custom_data}"}
    except AttributeError:
        return {"error": "GetMarkerByCustomData not available"}
    except Exception as e:
        return {"error": f"Error finding marker: {e}"}


@mcp.tool()
def update_marker_custom_data(clip_name: str, frame: int, custom_data: str) -> str:
    """Update the custom data for a marker at a specific frame.
    
    Args:
        clip_name: Name of the clip
        frame: Frame number of the marker
        custom_data: New custom data string
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    clip, error = _get_media_pool_clip(resolve, clip_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = clip.UpdateMarkerCustomData(frame, custom_data)
        if result:
            return f"Updated marker custom data at frame {frame}"
        return f"Failed to update marker at frame {frame}"
    except AttributeError:
        return "Error: UpdateMarkerCustomData not available"
    except Exception as e:
        return f"Error updating marker: {e}"


@mcp.tool()
def get_marker_custom_data(clip_name: str, frame: int) -> Dict[str, Any]:
    """Get the custom data for a marker at a specific frame.
    
    Args:
        clip_name: Name of the clip
        frame: Frame number of the marker
    """
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    clip, error = _get_media_pool_clip(resolve, clip_name)
    if error:
        return {"error": error}
    
    try:
        custom_data = clip.GetMarkerCustomData(frame)
        return {
            "clip_name": clip_name,
            "frame": frame,
            "custom_data": custom_data
        }
    except AttributeError:
        return {"error": "GetMarkerCustomData not available"}
    except Exception as e:
        return {"error": f"Error getting marker data: {e}"}


@mcp.tool()
def delete_marker_by_custom_data(clip_name: str, custom_data: str) -> str:
    """Delete a marker by its custom data string.
    
    Args:
        clip_name: Name of the clip
        custom_data: Custom data string of the marker to delete
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    clip, error = _get_media_pool_clip(resolve, clip_name)
    if error:
        return f"Error: {error}"
    
    try:
        result = clip.DeleteMarkerByCustomData(custom_data)
        if result:
            return f"Deleted marker with custom data: {custom_data}"
        return f"Failed to delete marker"
    except AttributeError:
        return "Error: DeleteMarkerByCustomData not available"
    except Exception as e:
        return f"Error deleting marker: {e}"


# ============================================================
# Phase 4.3: MediaPoolItem Third Party Metadata Tools
# ============================================================

from src.api.media_operations import (
    get_third_party_metadata as get_third_party_metadata_impl,
    set_third_party_metadata as set_third_party_metadata_impl,
    link_full_resolution_media as link_full_res_impl,
    replace_clip_preserve_sub_clip as replace_preserve_impl,
    monitor_growing_file as monitor_growing_impl,
)


@mcp.tool()
def get_third_party_metadata(clip_name: str) -> Dict[str, Any]:
    """Get third-party metadata for a media pool clip.
    
    Third-party metadata is custom metadata added by external applications.
    
    Args:
        clip_name: Name of the clip
    """
    resolve = get_resolve()
    return get_third_party_metadata_impl(resolve, clip_name)


@mcp.tool()
def set_third_party_metadata(clip_name: str, metadata: Dict[str, str]) -> str:
    """Set third-party metadata for a media pool clip.
    
    Args:
        clip_name: Name of the clip
        metadata: Dictionary of metadata key-value pairs
    """
    resolve = get_resolve()
    return set_third_party_metadata_impl(resolve, clip_name, metadata)


@mcp.tool()
def link_full_resolution_media(clip_name: str, media_file_path: str) -> str:
    """Link full resolution media to a proxy or optimized media clip.
    
    Use this to reconnect high-res media after editing with proxies.
    
    Args:
        clip_name: Name of the clip
        media_file_path: Absolute path to the full resolution media file
    """
    resolve = get_resolve()
    return link_full_res_impl(resolve, clip_name, media_file_path)


@mcp.tool()
def replace_clip_preserve_sub_clip(clip_name: str, new_media_file_path: str) -> str:
    """Replace a clip while preserving sub-clip information.
    
    Useful when replacing media with a different version while keeping in/out points.
    
    Args:
        clip_name: Name of the clip to replace
        new_media_file_path: Absolute path to the new media file
    """
    resolve = get_resolve()
    return replace_preserve_impl(resolve, clip_name, new_media_file_path)


@mcp.tool()
def monitor_growing_file(clip_name: str, enable: bool = True) -> str:
    """Enable or disable monitoring of a growing file.
    
    Used for live recording workflows where media is still being captured.
    
    Args:
        clip_name: Name of the clip
        enable: True to start monitoring, False to stop
    """
    resolve = get_resolve()
    return monitor_growing_impl(resolve, clip_name, enable)


# ============================================================
# Phase 4.4: MediaPool Matte Tools
# ============================================================

from src.api.media_operations import (
    create_stereo_clip as create_stereo_impl,
    get_clip_matte_list as get_clip_mattes_impl,
    get_timeline_matte_list as get_timeline_mattes_impl,
    delete_clip_mattes as delete_mattes_impl,
)


@mcp.tool()
def create_stereo_clip(left_clip_name: str, right_clip_name: str) -> str:
    """Create a stereo 3D clip from left and right eye clips.
    
    Args:
        left_clip_name: Name of the left eye clip
        right_clip_name: Name of the right eye clip
    """
    resolve = get_resolve()
    return create_stereo_impl(resolve, left_clip_name, right_clip_name)


@mcp.resource("resolve://clip-mattes/{clip_name}")
def get_clip_mattes(clip_name: str) -> Dict[str, Any]:
    """Get list of mattes associated with a clip."""
    resolve = get_resolve()
    return get_clip_mattes_impl(resolve, clip_name)


@mcp.tool()
def get_clip_matte_list(clip_name: str) -> Dict[str, Any]:
    """Get list of mattes associated with a clip.
    
    Args:
        clip_name: Name of the clip
    """
    resolve = get_resolve()
    return get_clip_mattes_impl(resolve, clip_name)


@mcp.tool()
def get_timeline_matte_list(timeline_name: str = None) -> Dict[str, Any]:
    """Get list of mattes in a timeline.
    
    Args:
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    return get_timeline_mattes_impl(resolve, timeline_name)


@mcp.tool()
def delete_clip_mattes(clip_name: str, matte_paths: List[str] = None) -> str:
    """Delete mattes associated with a clip.
    
    Args:
        clip_name: Name of the clip
        matte_paths: Optional list of specific matte paths to delete; if None, deletes all
    """
    resolve = get_resolve()
    return delete_mattes_impl(resolve, clip_name, matte_paths)


# ============================================================
# Phase 4.6: Folder Operations Tools
# ============================================================

from src.api.media_operations import (
    get_folder_is_stale as get_folder_stale_impl,
    get_folder_unique_id as get_folder_id_impl,
    export_folder as export_folder_impl,
)


@mcp.tool()
def get_folder_is_stale(folder_name: str = None) -> Dict[str, Any]:
    """Check if a folder's contents are stale and need refresh.
    
    Args:
        folder_name: Folder name, uses current folder if not specified
    """
    resolve = get_resolve()
    return get_folder_stale_impl(resolve, folder_name)


@mcp.tool()
def get_folder_unique_id(folder_name: str = None) -> Dict[str, Any]:
    """Get the unique ID of a media pool folder.
    
    Args:
        folder_name: Folder name, uses current folder if not specified
    """
    resolve = get_resolve()
    return get_folder_id_impl(resolve, folder_name)


@mcp.tool()
def export_folder_to_drb(folder_name: str, output_path: str) -> str:
    """Export a folder as a DRB (DaVinci Resolve Bin) file.
    
    DRB files can be imported into other projects to share bins and clips.
    
    Args:
        folder_name: Name of the folder to export
        output_path: Output file path with .drb extension
    """
    resolve = get_resolve()
    return export_folder_impl(resolve, folder_name, output_path)
