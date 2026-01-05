
"""
Project Tools for DaVinci Resolve MCP
Project management, settings, properties.
"""
from typing import List, Dict, Any

from src.server_instance import mcp
from src.context import get_resolve
from src.utils.project_properties import (
    get_all_project_properties,
    get_project_property,
    set_project_property,
    get_timeline_format_settings,
    set_timeline_format,
    get_superscale_settings,
    set_superscale_settings,
    get_color_settings,
    set_color_science_mode,
    set_color_space,
    get_project_metadata,
    get_project_info
)

@mcp.resource("resolve://projects")
def list_projects() -> List[str]:
    """List all available projects in the current database."""
    resolve = get_resolve()
    if resolve is None:
        return ["Error: Not connected to DaVinci Resolve"]
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return ["Error: Failed to get Project Manager"]
    
    projects = project_manager.GetProjectListInCurrentFolder()
    
    # Filter out any empty strings that might be in the list
    return [p for p in projects if p]

@mcp.resource("resolve://current-project")
def get_current_project_name() -> str:
    """Get the name of the currently open project."""
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "No project currently open"
    
    return current_project.GetName()

@mcp.tool()
def open_project(name: str) -> str:
    """Open a project by name.
    
    Args:
        name: The name of the project to open
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not name:
        return "Error: Project name cannot be empty"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    # Check if project exists
    projects = project_manager.GetProjectListInCurrentFolder()
    if name not in projects:
        return f"Error: Project '{name}' not found. Available projects: {', '.join(projects)}"
    
    result = project_manager.LoadProject(name)
    if result:
        return f"Successfully opened project '{name}'"
    else:
        return f"Failed to open project '{name}'"

@mcp.tool()
def create_project(name: str) -> str:
    """Create a new project with the given name.
    
    Args:
        name: The name for the new project
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not name:
        return "Error: Project name cannot be empty"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    # Check if project already exists
    projects = project_manager.GetProjectListInCurrentFolder()
    if name in projects:
        return f"Error: Project '{name}' already exists"
    
    result = project_manager.CreateProject(name)
    if result:
        return f"Successfully created project '{name}'"
    else:
        return f"Failed to create project '{name}'"

@mcp.tool()
def save_project() -> str:
    """Save the current project."""
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    if project_manager.SaveProject():
         return f"Successfully saved project '{current_project.GetName()}'"
    return "Failed to save project"

# ------------------
# Project Properties Resources
# ------------------

@mcp.resource("resolve://project/properties")
def get_project_properties() -> Dict[str, Any]:
    """Get all project properties for the current project."""
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    return get_all_project_properties(current_project)

@mcp.resource("resolve://project/property/{property_name}")
def get_project_property_resource(property_name: str) -> Dict[str, Any]:
    """Get a specific project property value.
    
    Args:
        property_name: Name of the property to get
    """
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    value = get_project_property(current_project, property_name)
    return {property_name: value}

@mcp.tool()
def set_project_property_tool(property_name: str, property_value: Any) -> str:
    """Set a project property value.
    
    Args:
        property_name: Name of the property to set
        property_value: Value to set for the property
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    result = set_project_property(current_project, property_name, property_value)
    
    if result:
        return f"Successfully set project property '{property_name}' to '{property_value}'"
    else:
        return f"Failed to set project property '{property_name}'"

@mcp.resource("resolve://project/timeline-format")
def get_timeline_format() -> Dict[str, Any]:
    """Get timeline format settings for the current project."""
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    return get_timeline_format_settings(current_project)

@mcp.tool()
def set_timeline_format_tool(width: int, height: int, frame_rate: float, interlaced: bool = False) -> str:
    """Set timeline format (resolution and frame rate).
    
    Args:
        width: Timeline width in pixels
        height: Timeline height in pixels
        frame_rate: Timeline frame rate
        interlaced: Whether the timeline should use interlaced processing
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    result = set_timeline_format(current_project, width, height, frame_rate, interlaced)
    
    if result:
        interlace_status = "interlaced" if interlaced else "progressive"
        return f"Successfully set timeline format to {width}x{height} at {frame_rate} fps ({interlace_status})"
    else:
        return "Failed to set timeline format"

@mcp.resource("resolve://project/superscale")
def get_superscale_settings() -> Dict[str, Any]:
    """Get SuperScale settings for the current project."""
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    return get_superscale_settings(current_project)

@mcp.tool()
def set_superscale_settings_tool(enabled: bool, quality: int = 0) -> str:
    """Set SuperScale settings for the current project.
    
    Args:
        enabled: Whether SuperScale is enabled
        quality: SuperScale quality (0=Auto, 1=Better Quality, 2=Smoother)
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    quality_names = {
        0: "Auto",
        1: "Better Quality",
        2: "Smoother"
    }
    
    result = set_superscale_settings(current_project, enabled, quality)
    
    if result:
        status = "enabled" if enabled else "disabled"
        quality_name = quality_names.get(quality, "Unknown")
        return f"Successfully {status} SuperScale with quality set to {quality_name}"
    else:
        return "Failed to set SuperScale settings"

@mcp.resource("resolve://project/color-settings")
def get_color_settings_resource() -> Dict[str, Any]:
    """Get color science and color space settings for the current project."""
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    return get_color_settings(current_project)

@mcp.tool()
def set_color_science_mode_tool(mode: str) -> str:
    """Set color science mode for the current project.
    
    Args:
        mode: Color science mode ('YRGB', 'YRGB Color Managed', 'ACEScct', or numeric value)
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    result = set_color_science_mode(current_project, mode)
    
    if result:
        return f"Successfully set color science mode to '{mode}'"
    else:
        return f"Failed to set color science mode to '{mode}'"

@mcp.tool()
def set_color_space_tool(color_space: str, gamma: str = None) -> str:
    """Set timeline color space and gamma.
    
    Args:
        color_space: Timeline color space (e.g., 'Rec.709', 'DCI-P3 D65', 'Rec.2020')
        gamma: Timeline gamma (e.g., 'Rec.709 Gamma', 'Gamma 2.4')
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    result = set_color_space(current_project, color_space, gamma)
    
    if result:
        if gamma:
            return f"Successfully set timeline color space to '{color_space}' with gamma '{gamma}'"
        else:
            return f"Successfully set timeline color space to '{color_space}'"
    else:
        return "Failed to set timeline color space"

@mcp.resource("resolve://project/metadata")
def get_project_metadata_resource() -> Dict[str, Any]:
    """Get metadata for the current project."""
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    return get_project_metadata(current_project)

@mcp.resource("resolve://project/info")
def get_project_info_resource() -> Dict[str, Any]:
    """Get comprehensive information about the current project."""
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    return get_project_info(current_project)
@mcp.resource('resolve://cache/settings')
def get_cache_settings() -> Dict[str, Any]:
    resolve = get_resolve()
    if resolve is None: return {'error': 'Not connected'}
    pm = resolve.GetProjectManager()
    if not pm: return {'error': 'No PM'}
    proj = pm.GetCurrentProject()
    if not proj: return {'error': 'No project'}
    settings = {}
    for key in ['CacheMode', 'CacheClipMode', 'OptimizedMediaMode', 'ProxyMode', 'ProxyQuality', 'TimelineCacheMode', 'LocalCachePath', 'NetworkCachePath']:
        settings[key] = proj.GetSetting(key)
    return settings

@mcp.tool()
def set_cache_mode(mode: str) -> str:
    resolve = get_resolve()
    if not resolve: return 'Error'
    mode_map = {'auto': '0', 'on': '1', 'off': '2'}
    if mode.lower() not in mode_map: return 'Invalid mode'
    proj = resolve.GetProjectManager().GetCurrentProject()
    if proj.SetSetting('CacheMode', mode_map[mode.lower()]): return f'Set cache mode to {mode}'
    return 'Failed'

@mcp.tool()
def set_optimized_media_mode(mode: str) -> str:
    resolve = get_resolve()
    if not resolve: return 'Error'
    mode_map = {'auto': '0', 'on': '1', 'off': '2'}
    if mode.lower() not in mode_map: return 'Invalid mode'
    proj = resolve.GetProjectManager().GetCurrentProject()
    if proj.SetSetting('OptimizedMediaMode', mode_map[mode.lower()]): return f'Set optimized media mode to {mode}'
    return 'Failed'

@mcp.tool()
def set_proxy_mode(mode: str) -> str:
    resolve = get_resolve()
    if not resolve: return 'Error'
    mode_map = {'auto': '0', 'on': '1', 'off': '2'}
    if mode.lower() not in mode_map: return 'Invalid mode'
    proj = resolve.GetProjectManager().GetCurrentProject()
    if proj.SetSetting('ProxyMode', mode_map[mode.lower()]): return f'Set proxy mode to {mode}'
    return 'Failed'


@mcp.tool()
def set_proxy_quality(quality: str) -> str:
    """Set proxy media quality."""
    resolve = get_resolve()
    if not resolve: return "Error"
    quality_map = {"quarter": "0", "half": "1", "threeQuarter": "2", "full": "3"}
    if quality not in quality_map: return "Invalid quality"
    proj = resolve.GetProjectManager().GetCurrentProject()
    if proj.SetSetting("ProxyQuality", quality_map[quality]): return f"Set proxy quality to {quality}"
    return "Failed"

@mcp.tool()
def set_cache_path(path_type: str, path: str) -> str:
    """Set cache file path."""
    resolve = get_resolve()
    if not resolve: return "Error"
    import os
    if not os.path.exists(path): return f"Path {path} not found"
    proj = resolve.GetProjectManager().GetCurrentProject()
    key = "LocalCachePath" if path_type.lower() == "local" else "NetworkCachePath"
    if proj.SetSetting(key, path): return f"Set {key} to {path}"
    return "Failed"

@mcp.tool()
def generate_optimized_media(clip_names: List[str] = None) -> str:
    """Generate optimized media."""
    resolve = get_resolve()
    if not resolve: return "Error"
    proj = resolve.GetProjectManager().GetCurrentProject()
    mp = proj.GetMediaPool()
    
    from src.api.media_operations import get_all_media_pool_clips
    all_clips = get_all_media_pool_clips(mp)
    targets = []
    
    if clip_names:
        for name in clip_names:
            found = next((c for c in all_clips if c.GetName() == name), None)
            if found: targets.append(found)
    else:
        targets = all_clips
        
    if not targets: return "No clips found"
    
    try:
        mp.SetCurrentFolder(mp.GetRootFolder())
        resolve.OpenPage("media")
        mp.SetClipSelection(targets)
        if proj.GenerateOptimizedMedia(): return f"Started generation for {len(targets)} clips"
        return "Failed to start"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def delete_optimized_media(clip_names: List[str] = None) -> str:
    """Delete optimized media."""
    resolve = get_resolve()
    if not resolve: return "Error"
    proj = resolve.GetProjectManager().GetCurrentProject()
    mp = proj.GetMediaPool()
    
    from src.api.media_operations import get_all_media_pool_clips
    all_clips = get_all_media_pool_clips(mp)
    targets = []
    
    if clip_names:
        for name in clip_names:
            found = next((c for c in all_clips if c.GetName() == name), None)
            if found: targets.append(found)
    else:
        targets = all_clips
        
    if not targets: return "No clips found"
    
    try:
        mp.SetCurrentFolder(mp.GetRootFolder())
        resolve.OpenPage("media")
        mp.SetClipSelection(targets)
        if proj.DeleteOptimizedMedia(): return f"Deleted optimized media for {len(targets)} clips"
        return "Failed to delete"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Phase 2: Project Management Extensions
# ============================================================

from src.api.project_operations import (
    delete_project as delete_project_impl,
    close_project as close_project_impl,
    rename_project as rename_project_impl,
    get_project_unique_id as get_project_id_impl,
    export_project as export_project_impl,
    import_project as import_project_impl,
    archive_project as archive_project_impl,
    restore_project as restore_project_impl,
    list_database_folders as list_db_folders_impl,
    create_database_folder as create_db_folder_impl,
    delete_database_folder as delete_db_folder_impl,
    open_database_folder as open_db_folder_impl,
    goto_root_folder as goto_root_impl,
    goto_parent_folder as goto_parent_impl,
    get_database_list as get_db_list_impl,
    set_current_database as set_db_impl,
)


# --- Project Lifecycle ---

@mcp.tool()
def delete_project(name: str) -> str:
    """Delete a project by name.
    
    Args:
        name: Name of the project to delete (cannot be current project)
    """
    resolve = get_resolve()
    return delete_project_impl(resolve, name)


@mcp.tool()
def close_project() -> str:
    """Close the current project."""
    resolve = get_resolve()
    return close_project_impl(resolve)


@mcp.tool()
def rename_project(new_name: str) -> str:
    """Rename the current project.
    
    Args:
        new_name: New name for the project
    """
    resolve = get_resolve()
    return rename_project_impl(resolve, new_name)


@mcp.resource("resolve://project-id")
def get_project_id() -> Dict[str, Any]:
    """Get the unique ID of the current project."""
    resolve = get_resolve()
    return get_project_id_impl(resolve)


# --- Project Import/Export ---

@mcp.tool()
def export_project(project_name: str, file_path: str, 
                   with_stills_and_luts: bool = True) -> str:
    """Export a project to a .drp file.
    
    Args:
        project_name: Name of the project to export
        file_path: Path for the exported file (.drp format)
        with_stills_and_luts: Whether to include stills and LUTs
    """
    resolve = get_resolve()
    return export_project_impl(resolve, project_name, file_path, with_stills_and_luts)


@mcp.tool()
def import_project(file_path: str, project_name: str = None) -> str:
    """Import a project from a .drp file.
    
    Args:
        file_path: Path to the project file (.drp format)
        project_name: Optional name for the imported project
    """
    resolve = get_resolve()
    return import_project_impl(resolve, file_path, project_name)


@mcp.tool()
def archive_project(project_name: str, file_path: str,
                    is_archive_src_media: bool = True,
                    is_archive_render_cache: bool = False,
                    is_archive_proxy_media: bool = False) -> str:
    """Archive a project to a .dra file with media.
    
    Args:
        project_name: Name of the project to archive
        file_path: Path for the archive file (.dra format)
        is_archive_src_media: Include source media files
        is_archive_render_cache: Include render cache
        is_archive_proxy_media: Include proxy media
    """
    resolve = get_resolve()
    return archive_project_impl(resolve, project_name, file_path,
                                is_archive_src_media, is_archive_render_cache, is_archive_proxy_media)


@mcp.tool()
def restore_project(file_path: str, project_name: str = None) -> str:
    """Restore a project from a .dra archive.
    
    Args:
        file_path: Path to the archive file (.dra format)
        project_name: Optional name for the restored project
    """
    resolve = get_resolve()
    return restore_project_impl(resolve, file_path, project_name)


# --- Database Folder Navigation ---

@mcp.resource("resolve://database-folders")
def list_database_folders() -> Dict[str, Any]:
    """List folders in the current database folder."""
    resolve = get_resolve()
    return list_db_folders_impl(resolve)


@mcp.tool()
def create_database_folder(folder_name: str) -> str:
    """Create a folder in the current database folder."""
    resolve = get_resolve()
    return create_db_folder_impl(resolve, folder_name)


@mcp.tool()
def delete_database_folder(folder_name: str) -> str:
    """Delete a folder in the current database folder."""
    resolve = get_resolve()
    return delete_db_folder_impl(resolve, folder_name)


@mcp.tool()
def open_database_folder(folder_name: str) -> str:
    """Navigate to a folder in the database."""
    resolve = get_resolve()
    return open_db_folder_impl(resolve, folder_name)


@mcp.tool()
def goto_root_folder() -> str:
    """Navigate to the root folder of the database."""
    resolve = get_resolve()
    return goto_root_impl(resolve)


@mcp.tool()
def goto_parent_folder() -> str:
    """Navigate to the parent folder in the database."""
    resolve = get_resolve()
    return goto_parent_impl(resolve)


# --- Database Management ---

@mcp.resource("resolve://databases")
def get_database_list() -> Dict[str, Any]:
    """Get list of available databases."""
    resolve = get_resolve()
    return get_db_list_impl(resolve)


@mcp.tool()
def set_current_database(db_info: Dict[str, str]) -> str:
    """Switch to a different database.
    
    Args:
        db_info: Database info dict with 'DbType', 'DbName', and optionally 'IpAddress'
    """
    resolve = get_resolve()
    return set_db_impl(resolve, db_info)

