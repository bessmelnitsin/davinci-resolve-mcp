"""
MediaStorage Tools for DaVinci Resolve MCP

Browse mounted volumes, folders, and files in Media Storage.
Add items directly to Media Pool from storage locations.
"""
from typing import List, Dict, Any

from src.server_instance import mcp
from src.context import get_resolve
from src.api.media_storage_operations import (
    get_mounted_volumes as get_volumes_impl,
    get_sub_folders as get_folders_impl,
    get_files as get_files_impl,
    reveal_in_storage as reveal_impl,
    add_items_to_media_pool as add_items_impl,
    add_items_with_info as add_items_info_impl,
    add_timeline_mattes as add_mattes_impl,
)


# ============================================================
# MediaStorage Browse Tools
# ============================================================

@mcp.tool()
def list_mounted_volumes() -> str:
    """List all mounted volumes displayed in DaVinci Resolve's Media Storage.
    
    Returns paths to all drives and network locations visible in Media Storage.
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = get_volumes_impl(resolve)
    if "error" in result:
        return f"Error: {result['error']}"
    
    volumes = result.get("volumes", [])
    if not volumes:
        return "No mounted volumes found in Media Storage"
    
    lines = [f"Mounted volumes ({result['count']}):"]
    for vol in volumes:
        lines.append(f"  • {vol}")
    return "\n".join(lines)


@mcp.tool()
def list_storage_folders(folder_path: str) -> str:
    """List subfolders in a Media Storage folder.
    
    Args:
        folder_path: Absolute path to the folder to browse
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = get_folders_impl(resolve, folder_path)
    if "error" in result:
        return f"Error: {result['error']}"
    
    folders = result.get("subfolders", [])
    if not folders:
        return f"No subfolders found in: {folder_path}"
    
    lines = [f"Subfolders in '{folder_path}' ({result['count']}):"]
    for folder in folders:
        lines.append(f"  📁 {folder}")
    return "\n".join(lines)


@mcp.tool()
def list_storage_files(folder_path: str) -> str:
    """List media files in a Media Storage folder.
    
    Note: Media listings may be consolidated (e.g., image sequences).
    
    Args:
        folder_path: Absolute path to the folder to browse
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = get_files_impl(resolve, folder_path)
    if "error" in result:
        return f"Error: {result['error']}"
    
    files = result.get("files", [])
    if not files:
        return f"No media files found in: {folder_path}"
    
    lines = [f"Media files in '{folder_path}' ({result['count']}):"]
    for f in files[:50]:  # Limit display to 50 items
        lines.append(f"  📄 {f}")
    
    if len(files) > 50:
        lines.append(f"  ... and {len(files) - 50} more files")
    
    return "\n".join(lines)


@mcp.tool()
def reveal_in_storage(path: str) -> str:
    """Reveal a file or folder in DaVinci Resolve's Media Storage browser.
    
    Expands the path and highlights it in the Media Storage panel.
    
    Args:
        path: Absolute path to the file or folder to reveal
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = reveal_impl(resolve, path)
    if "error" in result:
        return f"Error: {result['error']}"
    
    if result.get("success"):
        return result.get("message", f"Revealed: {path}")
    return result.get("message", "Failed to reveal path")


# ============================================================
# Add to Media Pool Tools
# ============================================================

@mcp.tool()
def add_from_storage(file_paths: List[str]) -> str:
    """Add files from Media Storage to current Media Pool folder.
    
    Imports the specified files/folders into the currently selected
    Media Pool folder.
    
    Args:
        file_paths: List of absolute file or folder paths to add
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not file_paths:
        return "Error: No file paths provided"
    
    result = add_items_impl(resolve, file_paths)
    if "error" in result:
        return f"Error: {result['error']}"
    
    if result.get("success"):
        clips = result.get("clips", [])
        count = result.get("added_count", 0)
        
        lines = [f"Added {count} item(s) to Media Pool:"]
        for clip in clips[:10]:
            lines.append(f"  ✓ {clip.get('name', 'Unknown')}")
        
        if len(clips) > 10:
            lines.append(f"  ... and {len(clips) - 10} more")
        
        return "\n".join(lines)
    
    return result.get("message", "Failed to add items")


@mcp.tool()
def add_from_storage_with_range(media_path: str, start_frame: int, 
                                 end_frame: int) -> str:
    """Add a media file with specific in/out points to Media Pool.
    
    Useful for adding only a portion of a longer clip.
    
    Args:
        media_path: Absolute path to the media file
        start_frame: Start frame number
        end_frame: End frame number
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    items_info = [{
        "media": media_path,
        "startFrame": start_frame,
        "endFrame": end_frame
    }]
    
    result = add_items_info_impl(resolve, items_info)
    if "error" in result:
        return f"Error: {result['error']}"
    
    if result.get("success"):
        clips = result.get("clips", [])
        if clips:
            return f"Added '{clips[0].get('name', media_path)}' (frames {start_frame}-{end_frame})"
        return "Added clip with specified range"
    
    return result.get("message", "Failed to add item")


@mcp.tool()
def add_timeline_mattes(matte_paths: List[str]) -> str:
    """Add media files as timeline mattes to current Media Pool folder.
    
    Args:
        matte_paths: List of absolute paths to matte files
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not matte_paths:
        return "Error: No matte paths provided"
    
    result = add_mattes_impl(resolve, matte_paths)
    if "error" in result:
        return f"Error: {result['error']}"
    
    if result.get("success"):
        count = result.get("added_count", 0)
        return f"Added {count} timeline matte(s) to Media Pool"
    
    return result.get("message", "Failed to add timeline mattes")


# ============================================================
# Resources
# ============================================================

@mcp.resource("resolve://media-storage/volumes")
def get_volumes_resource() -> Dict[str, Any]:
    """Get all mounted volumes in Media Storage."""
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    return get_volumes_impl(resolve)
