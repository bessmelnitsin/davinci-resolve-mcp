
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

