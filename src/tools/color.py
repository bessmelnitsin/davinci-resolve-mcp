
"""
Color Page Tools for DaVinci Resolve MCP
Extended with Gallery and Node Graph operations.
"""
from typing import Dict, Any, List

from src.server_instance import mcp
from src.context import get_resolve
from src.api.color_operations import (
    get_current_node as get_node_impl,
    get_color_wheels as get_wheels_impl,
    apply_lut as apply_lut_impl,
    set_color_wheel_param as set_param_impl,
    add_node as add_node_impl,
    copy_grade as copy_grade_impl
)


# ============================================================
# Core Color Tools
# ============================================================

@mcp.tool()
def get_current_color_node() -> Dict[str, Any]:
    """Get information about the current node in the color page."""
    resolve = get_resolve()
    return get_node_impl(resolve)


@mcp.tool()
def get_color_wheel_params(node_index: int = None) -> Dict[str, Any]:
    """Get color wheel parameters for a specific node."""
    resolve = get_resolve()
    return get_wheels_impl(resolve, node_index)


@mcp.tool()
def apply_lut(lut_path: str, node_index: int = None) -> str:
    """Apply a LUT to a node."""
    resolve = get_resolve()
    return apply_lut_impl(resolve, lut_path, node_index)


@mcp.tool()
def set_color_wheel_param(wheel: str, param: str, value: float, node_index: int = None) -> str:
    """Set a color wheel parameter for a node.
    
    Args:
        wheel: 'lift', 'gamma', 'gain', or 'offset'
        param: 'red', 'green', 'blue', or 'master'
        value: Value to set (typically -1.0 to 1.0)
        node_index: Optional node index (uses current if not specified)
    """
    resolve = get_resolve()
    return set_param_impl(resolve, wheel, param, value, node_index)


@mcp.tool()
def add_node(node_type: str = "serial", label: str = None) -> str:
    """Add a new node to the current grade ('serial', 'parallel', or 'layer')."""
    resolve = get_resolve()
    return add_node_impl(resolve, node_type, label)


@mcp.tool()
def copy_grade_tool(source_clip_name: str = None, target_clip_name: str = None, 
                    mode: str = "full") -> str:
    """Copy a grade from one clip to another."""
    resolve = get_resolve()
    return copy_grade_impl(resolve, source_clip_name, target_clip_name, mode)


# ============================================================
# Phase 6: Extended Node Graph Operations
# ============================================================

@mcp.tool()
def get_node_graph_info(clip_name: str = None) -> Dict[str, Any]:
    """Get node graph information for a clip."""
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
    
    # Switch to Color page if needed
    if resolve.GetCurrentPage() != "color":
        resolve.OpenPage("color")
    
    try:
        item = timeline.GetCurrentVideoItem()
        if clip_name:
            # Find clip by name
            for i in range(1, timeline.GetTrackCount("video") + 1):
                for clip in timeline.GetItemListInTrack("video", i) or []:
                    if clip.GetName() == clip_name:
                        item = clip
                        break
        
        if not item:
            return {"error": "No clip found"}
        
        graph = item.GetNodeGraph()
        if not graph:
            return {"error": "Failed to get node graph"}
        
        node_count = graph.GetNumNodes()
        nodes = []
        
        for i in range(1, node_count + 1):
            nodes.append({
                "index": i,
                "label": graph.GetNodeLabel(i),
                "lut": graph.GetLUT(i),
                "tools": graph.GetToolsInNode(i)
            })
        
        return {
            "clip_name": item.GetName(),
            "node_count": node_count,
            "nodes": nodes
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


@mcp.tool()
def set_node_lut(node_index: int, lut_path: str) -> str:
    """Set LUT on a specific node by index."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    timeline = project.GetCurrentTimeline() if project else None
    
    if not timeline:
        return "Error: No timeline"
    
    try:
        item = timeline.GetCurrentVideoItem()
        if not item:
            return "Error: No clip selected"
        
        graph = item.GetNodeGraph()
        if not graph:
            return "Error: No node graph"
        
        if graph.SetLUT(node_index, lut_path):
            return f"Applied LUT to node {node_index}"
        return "Failed to apply LUT"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def set_node_enabled(node_index: int, enabled: bool) -> str:
    """Enable or disable a node by index."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    timeline = project.GetCurrentTimeline() if project else None
    
    if not timeline:
        return "Error: No timeline"
    
    try:
        item = timeline.GetCurrentVideoItem()
        if not item:
            return "Error: No clip selected"
        
        graph = item.GetNodeGraph()
        if not graph:
            return "Error: No node graph"
        
        if graph.SetNodeEnabled(node_index, enabled):
            state = "enabled" if enabled else "disabled"
            return f"Node {node_index} {state}"
        return "Failed to set node state"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def reset_all_grades() -> str:
    """Reset all grades on the current clip."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    timeline = project.GetCurrentTimeline() if project else None
    
    if not timeline:
        return "Error: No timeline"
    
    try:
        item = timeline.GetCurrentVideoItem()
        if not item:
            return "Error: No clip selected"
        
        graph = item.GetNodeGraph()
        if graph and graph.ResetAllGrades():
            return "All grades reset"
        return "Failed to reset grades"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Phase 6: Gallery Operations
# ============================================================

@mcp.tool()
def grab_still() -> str:
    """Grab a still from the current clip."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    timeline = project.GetCurrentTimeline() if project else None
    
    if not timeline:
        return "Error: No timeline"
    
    try:
        still = timeline.GrabStill()
        if still:
            return "Still grabbed successfully"
        return "Failed to grab still"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_gallery_albums() -> Dict[str, Any]:
    """Get all gallery albums (stills and power grades)."""
    resolve = get_resolve()
    if not resolve:
        return {"error": "Not connected"}
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    
    if not project:
        return {"error": "No project open"}
    
    try:
        gallery = project.GetGallery()
        if not gallery:
            return {"error": "Failed to get gallery"}
        
        still_albums = gallery.GetGalleryStillAlbums() or []
        power_grade_albums = gallery.GetGalleryPowerGradeAlbums() or []
        
        result = {
            "still_albums": [gallery.GetAlbumName(a) for a in still_albums],
            "power_grade_albums": [gallery.GetAlbumName(a) for a in power_grade_albums]
        }
        
        # Get current album
        current = gallery.GetCurrentStillAlbum()
        if current:
            result["current_album"] = gallery.GetAlbumName(current)
        
        return result
    except Exception as e:
        return {"error": f"Error: {e}"}


@mcp.tool()
def create_still_album(album_name: str = None) -> str:
    """Create a new still album in the gallery."""
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    
    if not project:
        return "Error: No project open"
    
    try:
        gallery = project.GetGallery()
        if not gallery:
            return "Error: Failed to get gallery"
        
        album = gallery.CreateGalleryStillAlbum()
        if album:
            if album_name:
                gallery.SetAlbumName(album, album_name)
            return f"Created still album: {album_name or 'Untitled'}"
        return "Failed to create album"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_stills_in_album(album_name: str = None) -> Dict[str, Any]:
    """Get stills in a gallery album."""
    resolve = get_resolve()
    if not resolve:
        return {"error": "Not connected"}
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    
    if not project:
        return {"error": "No project open"}
    
    try:
        gallery = project.GetGallery()
        if not gallery:
            return {"error": "Failed to get gallery"}
        
        # Get target album
        target_album = None
        if album_name:
            for album in gallery.GetGalleryStillAlbums() or []:
                if gallery.GetAlbumName(album) == album_name:
                    target_album = album
                    break
        else:
            target_album = gallery.GetCurrentStillAlbum()
        
        if not target_album:
            return {"error": f"Album not found: {album_name or 'current'}"}
        
        stills = target_album.GetStills() or []
        still_list = []
        
        for still in stills:
            label = target_album.GetLabel(still)
            still_list.append({"label": label or "Untitled"})
        
        return {
            "album": gallery.GetAlbumName(target_album),
            "count": len(still_list),
            "stills": still_list
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


@mcp.tool()
def export_stills(folder_path: str, file_prefix: str = "still", 
                  format: str = "dpx", album_name: str = None) -> str:
    """Export stills from an album.
    
    Args:
        folder_path: Directory to export to
        file_prefix: Filename prefix
        format: Export format (dpx, cin, tif, jpg, png, ppm, bmp, xpm, drx)
        album_name: Optional album name (uses current if not specified)
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    
    if not project:
        return "Error: No project open"
    
    try:
        gallery = project.GetGallery()
        if not gallery:
            return "Error: Failed to get gallery"
        
        # Get target album
        target_album = None
        if album_name:
            for album in gallery.GetGalleryStillAlbums() or []:
                if gallery.GetAlbumName(album) == album_name:
                    target_album = album
                    break
        else:
            target_album = gallery.GetCurrentStillAlbum()
        
        if not target_album:
            return f"Error: Album not found: {album_name or 'current'}"
        
        stills = target_album.GetStills() or []
        if not stills:
            return "No stills in album to export"
        
        if target_album.ExportStills(stills, folder_path, file_prefix, format):
            return f"Exported {len(stills)} stills to {folder_path}"
        return "Failed to export stills"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def import_stills(file_paths: List[str], album_name: str = None) -> str:
    """Import stills into an album.
    
    Args:
        file_paths: List of file paths to import
        album_name: Optional album name (uses current if not specified)
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    
    if not project:
        return "Error: No project open"
    
    try:
        gallery = project.GetGallery()
        if not gallery:
            return "Error: Failed to get gallery"
        
        # Get target album
        target_album = None
        if album_name:
            for album in gallery.GetGalleryStillAlbums() or []:
                if gallery.GetAlbumName(album) == album_name:
                    target_album = album
                    break
        else:
            target_album = gallery.GetCurrentStillAlbum()
        
        if not target_album:
            return f"Error: Album not found: {album_name or 'current'}"
        
        if target_album.ImportStills(file_paths):
            return f"Imported {len(file_paths)} stills"
        return "Failed to import stills"
    except Exception as e:
        return f"Error: {e}"

