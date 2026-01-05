
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


# ============================================================
# Phase 2.4: Color Page Extensions
# ============================================================

@mcp.tool()
def get_color_groups_list() -> Dict[str, Any]:
    """Get list of all color groups in the project."""
    resolve = get_resolve()
    if not resolve:
        return {"error": "Not connected"}
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    
    if not project:
        return {"error": "No project open"}
    
    try:
        groups = project.GetColorGroupsList()
        if groups:
            result = []
            for group in groups:
                result.append({
                    "name": group.GetName() if hasattr(group, 'GetName') else str(group),
                    "id": group.GetID() if hasattr(group, 'GetID') else None
                })
            return {"count": len(result), "groups": result}
        return {"count": 0, "groups": []}
    except AttributeError:
        return {"error": "GetColorGroupsList not available"}
    except Exception as e:
        return {"error": f"Error: {e}"}


@mcp.tool()
def add_color_group(group_name: str) -> str:
    """Add a new color group to the project.
    
    Args:
        group_name: Name for the new color group
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    
    if not project:
        return "Error: No project open"
    
    try:
        group = project.AddColorGroup(group_name)
        if group:
            return f"Created color group: {group_name}"
        return "Failed to create color group"
    except AttributeError:
        return "Error: AddColorGroup not available"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def delete_color_group(group_name: str) -> str:
    """Delete a color group from the project.
    
    Args:
        group_name: Name of the color group to delete
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    
    if not project:
        return "Error: No project open"
    
    try:
        # Find the group by name
        groups = project.GetColorGroupsList()
        target_group = None
        if groups:
            for group in groups:
                if hasattr(group, 'GetName') and group.GetName() == group_name:
                    target_group = group
                    break
        
        if not target_group:
            return f"Color group '{group_name}' not found"
        
        if project.DeleteColorGroup(target_group):
            return f"Deleted color group: {group_name}"
        return "Failed to delete color group"
    except AttributeError:
        return "Error: DeleteColorGroup not available"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def apply_grade_from_drx(clip_name: str, drx_path: str, 
                          grade_mode: int = 0) -> str:
    """Apply a grade from a DRX file to a clip.
    
    Args:
        clip_name: Name of the clip in timeline
        drx_path: Path to the DRX file
        grade_mode: 0 = No keyframes, 1 = Source timecode, 2 = Start timecode
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    timeline = project.GetCurrentTimeline() if project else None
    
    if not timeline:
        return "Error: No timeline"
    
    try:
        # Find the clip
        target_item = None
        for i in range(1, timeline.GetTrackCount("video") + 1):
            items = timeline.GetItemListInTrack("video", i) or []
            for item in items:
                if item.GetName() == clip_name:
                    target_item = item
                    break
        
        if not target_item:
            return f"Clip '{clip_name}' not found"
        
        result = target_item.ApplyGradeFromDRX(drx_path, grade_mode, [target_item])
        if result:
            return f"Applied DRX grade to '{clip_name}'"
        return "Failed to apply DRX grade"
    except AttributeError:
        return "Error: ApplyGradeFromDRX not available"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def set_node_cache_mode(node_index: int, mode: int) -> str:
    """Set the cache mode for a color node.
    
    Args:
        node_index: Index of the node (1-based)
        mode: Cache mode (0 = None, 1 = Smart, 2 = User)
    """
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
        
        mode_names = {0: "None", 1: "Smart", 2: "User"}
        if graph.SetNodeCacheMode(node_index, mode):
            return f"Set node {node_index} cache mode to {mode_names.get(mode, mode)}"
        return "Failed to set cache mode"
    except AttributeError:
        return "Error: SetNodeCacheMode not available"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_tools_in_node(node_index: int) -> Dict[str, Any]:
    """Get the tools/effects applied in a specific node.
    
    Args:
        node_index: Index of the node (1-based)
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
        item = timeline.GetCurrentVideoItem()
        if not item:
            return {"error": "No clip selected"}
        
        graph = item.GetNodeGraph()
        if not graph:
            return {"error": "No node graph"}
        
        tools = graph.GetToolsInNode(node_index)
        return {
            "node_index": node_index,
            "tools": tools or []
        }
    except AttributeError:
        return {"error": "GetToolsInNode not available"}
    except Exception as e:
        return {"error": f"Error: {e}"}


# ============================================================
# Phase 4.7: ColorGroup Extensions
# ============================================================

from src.api.color_operations import (
    get_color_groups as get_color_groups_impl,
    get_color_group_clips_in_timeline as get_group_clips_impl,
    get_pre_clip_node_graph as get_pre_clip_graph_impl,
    get_post_clip_node_graph as get_post_clip_graph_impl,
    assign_to_color_group as assign_to_group_impl,
    remove_from_color_group as remove_from_group_impl,
    reset_all_node_colors as reset_node_colors_impl,
)


@mcp.tool()
def get_color_groups() -> Dict[str, Any]:
    """Get all color groups in the current timeline."""
    resolve = get_resolve()
    return get_color_groups_impl(resolve)


@mcp.tool()
def get_color_group_clips_in_timeline(group_index: int,
                                       timeline_name: str = None) -> Dict[str, Any]:
    """Get clips belonging to a specific color group.
    
    Args:
        group_index: Index of the color group (0-based)
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    return get_group_clips_impl(resolve, group_index, timeline_name)


@mcp.tool()
def get_pre_clip_node_graph(group_index: int) -> Dict[str, Any]:
    """Get the pre-clip node graph for a color group.
    
    Pre-clip grades are applied before individual clip grades.
    
    Args:
        group_index: Index of the color group (0-based)
    """
    resolve = get_resolve()
    return get_pre_clip_graph_impl(resolve, group_index)


@mcp.tool()
def get_post_clip_node_graph(group_index: int) -> Dict[str, Any]:
    """Get the post-clip node graph for a color group.
    
    Post-clip grades are applied after individual clip grades.
    
    Args:
        group_index: Index of the color group (0-based)
    """
    resolve = get_resolve()
    return get_post_clip_graph_impl(resolve, group_index)


@mcp.tool()
def assign_to_color_group(clip_name: str, group_index: int,
                          timeline_name: str = None) -> str:
    """Assign a timeline clip to a color group.
    
    Args:
        clip_name: Name of the clip in timeline
        group_index: Index of the color group (0-based)
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    return assign_to_group_impl(resolve, clip_name, group_index, timeline_name)


@mcp.tool()
def remove_from_color_group(clip_name: str, timeline_name: str = None) -> str:
    """Remove a clip from its color group.
    
    Args:
        clip_name: Name of the clip in timeline
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    return remove_from_group_impl(resolve, clip_name, timeline_name)


@mcp.tool()
def reset_all_node_colors(clip_name: str, timeline_name: str = None) -> str:
    """Reset all node colors for a timeline clip.
    
    This resets the color corrections on all nodes to their default values.
    
    Args:
        clip_name: Name of the clip in timeline
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    return reset_node_colors_impl(resolve, clip_name, timeline_name)


# ============================================================
# Phase 4.8: Gallery Extensions
# ============================================================

from src.api.gallery_operations import (
    delete_stills_from_album as delete_stills_impl,
    get_still_label as get_still_label_impl,
    set_still_label as set_still_label_impl,
)


@mcp.tool()
def delete_stills_from_album(album_name: str = None,
                              still_labels: List[str] = None) -> str:
    """Delete stills from a gallery album.
    
    Args:
        album_name: Album name, uses current album if not specified
        still_labels: Optional list of labels to delete; if None, deletes all stills
    """
    resolve = get_resolve()
    return delete_stills_impl(resolve, album_name, still_labels)


@mcp.tool()
def get_still_label(album_name: str = None, still_index: int = 0) -> Dict[str, Any]:
    """Get the label of a still in an album.
    
    Args:
        album_name: Album name, uses current album if not specified
        still_index: Index of the still (0-based)
    """
    resolve = get_resolve()
    return get_still_label_impl(resolve, album_name, still_index)


@mcp.tool()
def set_still_label(label: str, album_name: str = None,
                    still_index: int = 0) -> str:
    """Set the label of a still in an album.
    
    Args:
        label: New label for the still
        album_name: Album name, uses current album if not specified
        still_index: Index of the still (0-based)
    """
    resolve = get_resolve()
    return set_still_label_impl(resolve, label, album_name, still_index)


# ============================================================
# Full Coverage: PowerGrade Albums
# ============================================================

from src.api.gallery_operations import (
    get_gallery_powergrade_albums as get_powergrade_albums_impl,
    create_gallery_powergrade_album as create_powergrade_album_impl,
)


@mcp.tool()
def get_gallery_powergrade_albums() -> List[Dict[str, Any]]:
    """Get all PowerGrade albums in the gallery.
    
    PowerGrade albums contain saved color grades that can be shared across projects.
    """
    resolve = get_resolve()
    return get_powergrade_albums_impl(resolve)


@mcp.tool()
def create_gallery_powergrade_album() -> Dict[str, Any]:
    """Create a new PowerGrade album in the gallery.
    
    PowerGrade albums are used to store and share color grades across projects.
    """
    resolve = get_resolve()
    return create_powergrade_album_impl(resolve)


# ============================================================
# Full Coverage: Graph Node Cache Functions
# ============================================================

@mcp.tool()
def set_node_cache_mode(clip_name: str, node_index: int, cache_value: str,
                         timeline_name: str = None) -> str:
    """Set cache mode for a node in a clip's node graph.
    
    Args:
        clip_name: Name of the clip in timeline
        node_index: Index of the node (1-based)
        cache_value: 'auto', 'on', or 'off'
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    if not project:
        return "Error: No project open"
    
    timeline = project.GetCurrentTimeline() if not timeline_name else None
    if timeline_name:
        for i in range(1, project.GetTimelineCount() + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    
    if not timeline:
        return "Error: No timeline found"
    
    # Find clip
    for track_idx in range(1, timeline.GetTrackCount("video") + 1):
        for item in timeline.GetItemListInTrack("video", track_idx) or []:
            if item.GetName() == clip_name:
                try:
                    graph = item.GetNodeGraph()
                    if graph:
                        result = graph.SetNodeCacheMode(node_index, cache_value)
                        if result:
                            return f"Set node {node_index} cache to '{cache_value}'"
                        return "Failed to set node cache mode"
                    return "Error: No node graph for clip"
                except Exception as e:
                    return f"Error: {e}"
    
    return f"Error: Clip not found: {clip_name}"


@mcp.tool()
def get_node_cache_mode(clip_name: str, node_index: int,
                         timeline_name: str = None) -> Dict[str, Any]:
    """Get cache mode for a node in a clip's node graph.
    
    Args:
        clip_name: Name of the clip in timeline
        node_index: Index of the node (1-based)
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    if not resolve:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    if not project:
        return {"error": "No project open"}
    
    timeline = project.GetCurrentTimeline() if not timeline_name else None
    if timeline_name:
        for i in range(1, project.GetTimelineCount() + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    
    if not timeline:
        return {"error": "No timeline found"}
    
    # Find clip
    for track_idx in range(1, timeline.GetTrackCount("video") + 1):
        for item in timeline.GetItemListInTrack("video", track_idx) or []:
            if item.GetName() == clip_name:
                try:
                    graph = item.GetNodeGraph()
                    if graph:
                        cache_mode = graph.GetNodeCacheMode(node_index)
                        return {
                            "clip_name": clip_name,
                            "node_index": node_index,
                            "cache_mode": cache_mode
                        }
                    return {"error": "No node graph for clip"}
                except Exception as e:
                    return {"error": f"Error: {e}"}
    
    return {"error": f"Clip not found: {clip_name}"}


@mcp.tool()
def apply_arri_cdl_lut(clip_name: str, timeline_name: str = None) -> str:
    """Apply ARRI CDL and LUT to a clip's node graph.
    
    Args:
        clip_name: Name of the clip in timeline
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    if not project:
        return "Error: No project open"
    
    timeline = project.GetCurrentTimeline() if not timeline_name else None
    if timeline_name:
        for i in range(1, project.GetTimelineCount() + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    
    if not timeline:
        return "Error: No timeline found"
    
    # Find clip
    for track_idx in range(1, timeline.GetTrackCount("video") + 1):
        for item in timeline.GetItemListInTrack("video", track_idx) or []:
            if item.GetName() == clip_name:
                try:
                    graph = item.GetNodeGraph()
                    if graph:
                        result = graph.ApplyArriCdlLut()
                        if result:
                            return f"Applied ARRI CDL LUT to '{clip_name}'"
                        return "Failed to apply ARRI CDL LUT"
                    return "Error: No node graph for clip"
                except Exception as e:
                    return f"Error: {e}"
    
    return f"Error: Clip not found: {clip_name}"


@mcp.tool()
def reset_all_grades(clip_name: str, timeline_name: str = None) -> str:
    """Reset all grades in a clip's node graph.
    
    Args:
        clip_name: Name of the clip in timeline
        timeline_name: Optional timeline name, uses current if not specified
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    if not project:
        return "Error: No project open"
    
    timeline = project.GetCurrentTimeline() if not timeline_name else None
    if timeline_name:
        for i in range(1, project.GetTimelineCount() + 1):
            tl = project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                timeline = tl
                break
    
    if not timeline:
        return "Error: No timeline found"
    
    # Find clip
    for track_idx in range(1, timeline.GetTrackCount("video") + 1):
        for item in timeline.GetItemListInTrack("video", track_idx) or []:
            if item.GetName() == clip_name:
                try:
                    graph = item.GetNodeGraph()
                    if graph:
                        result = graph.ResetAllGrades()
                        if result:
                            return f"Reset all grades for '{clip_name}'"
                        return "Failed to reset grades"
                    return "Error: No node graph for clip"
                except Exception as e:
                    return f"Error: {e}"
    
    return f"Error: Clip not found: {clip_name}"
