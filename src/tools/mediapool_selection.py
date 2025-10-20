"""
DaVinci Resolve MCP - MediaPool Selection and Metadata

Implements MediaPool selection and metadata operations including:
- Clip selection management
- Metadata export to CSV
- Timeline deletion
- Folder management

MEDIUM PRIORITY: Useful for batch operations and metadata workflows
"""

from typing import Dict, Any, List, Optional
import json
import logging

logger = logging.getLogger("davinci-resolve-mcp.tools.mediapool_selection")

# Import from the shared resolve connection module
try:
    from ..resolve_mcp_server import (
        get_resolve,
        get_project_manager,
        get_current_project,
        get_current_timeline,
    )
except ImportError:
    # Fallback for direct execution
    def get_resolve():
        raise NotImplementedError("Resolve connection not available")
    def get_project_manager():
        raise NotImplementedError("Project manager not available")
    def get_current_project():
        raise NotImplementedError("Current project not available")
    def get_current_timeline():
        raise NotImplementedError("Current timeline not available")


def get_media_pool():
    """Helper to get MediaPool from current project."""
    project = get_current_project()
    if not project:
        raise ValueError("No project is currently open")

    media_pool = project.GetMediaPool()
    if not media_pool:
        raise ValueError("Could not access Media Pool")

    return media_pool


# ============================================================================
# Clip Selection Operations (MEDIUM PRIORITY)
# ============================================================================

def get_selected_clips() -> List[Dict[str, Any]]:
    """
    Get list of currently selected clips in the Media Pool.

    Returns:
        List of selected clip information

    Example:
        >>> get_selected_clips()
        [
            {"name": "A001_C002.mov", "duration": 500, "fps": "24"},
            {"name": "A001_C003.mov", "duration": 600, "fps": "24"}
        ]
    """
    try:
        media_pool = get_media_pool()

        # GetSelectedClips()
        clips = media_pool.GetSelectedClips()

        if not clips:
            return []

        result = []
        for clip in clips:
            try:
                result.append({
                    "name": clip.GetName(),
                    "clip_property": clip.GetClipProperty() if hasattr(clip, 'GetClipProperty') else {}
                })
            except:
                result.append({"name": str(clip)})

        return result

    except Exception as e:
        logger.error(f"Error getting selected clips: {e}")
        return []


def set_selected_clip(clip_name: str) -> Dict[str, Any]:
    """
    Set a clip as selected in the Media Pool.

    Args:
        clip_name: Name of the clip to select

    Returns:
        Selection result

    Example:
        >>> set_selected_clip("A001_C002.mov")
        {
            "success": True,
            "clip_name": "A001_C002.mov",
            "message": "Clip selected"
        }
    """
    try:
        media_pool = get_media_pool()
        root = media_pool.GetRootFolder()

        # Find clip by name
        clip = _find_clip_by_name(root, clip_name)

        if not clip:
            return {
                "success": False,
                "error": f"Clip '{clip_name}' not found",
                "clip_name": clip_name
            }

        # SetSelectedClip(MediaPoolItem)
        result = media_pool.SetSelectedClip(clip)

        return {
            "success": bool(result),
            "clip_name": clip_name,
            "message": f"Clip {'selected' if result else 'selection failed'}"
        }

    except Exception as e:
        logger.error(f"Error setting selected clip: {e}")
        return {
            "success": False,
            "error": str(e),
            "clip_name": clip_name
        }


# ============================================================================
# Metadata Export Operations (MEDIUM PRIORITY)
# ============================================================================

def export_metadata(
    file_name: str,
    clip_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Export clip metadata to CSV file.

    Exports metadata fields (name, duration, fps, resolution, etc.) for
    specified clips or all clips in the Media Pool.

    Args:
        file_name: Destination CSV file path
        clip_names: Optional list of clip names (exports all if None)

    Returns:
        Export result

    Example:
        >>> export_metadata(
        ...     file_name="/exports/metadata.csv",
        ...     clip_names=["A001_C002.mov", "A001_C003.mov"]
        ... )
        {
            "success": True,
            "file_name": "/exports/metadata.csv",
            "clip_count": 2
        }
    """
    try:
        media_pool = get_media_pool()
        root = media_pool.GetRootFolder()

        # Get clips
        if clip_names:
            clips = []
            for clip_name in clip_names:
                clip = _find_clip_by_name(root, clip_name)
                if clip:
                    clips.append(clip)

            if not clips:
                return {
                    "success": False,
                    "error": "No clips found with specified names",
                    "clip_names": clip_names
                }
        else:
            # Export all clips - pass empty list
            clips = []

        # ExportMetadata(fileName, [clips])
        result = media_pool.ExportMetadata(file_name, clips)

        return {
            "success": bool(result),
            "file_name": file_name,
            "clip_count": len(clips) if clips else "all",
            "message": f"Metadata {'exported' if result else 'export failed'}"
        }

    except Exception as e:
        logger.error(f"Error exporting metadata: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_name": file_name
        }


# ============================================================================
# Timeline Management Operations (MEDIUM PRIORITY)
# ============================================================================

def delete_timelines(timeline_names: List[str]) -> Dict[str, Any]:
    """
    Delete one or more timelines from the project.

    Args:
        timeline_names: List of timeline names to delete

    Returns:
        Deletion result

    Example:
        >>> delete_timelines(["Unused Timeline 1", "Test Timeline"])
        {
            "success": True,
            "deleted_count": 2,
            "attempted_count": 2
        }
    """
    try:
        media_pool = get_media_pool()
        project = get_current_project()

        # Find timelines by name
        timelines = []
        timeline_count = project.GetTimelineCount()

        for name in timeline_names:
            for i in range(1, timeline_count + 1):
                tl = project.GetTimelineByIndex(i)
                if tl and tl.GetName() == name:
                    timelines.append(tl)
                    break

        if not timelines:
            return {
                "success": False,
                "error": "No timelines found with specified names",
                "timeline_names": timeline_names
            }

        # DeleteTimelines([timeline])
        result = media_pool.DeleteTimelines(timelines)

        if isinstance(result, bool):
            return {
                "success": result,
                "attempted_count": len(timelines),
                "message": f"Timeline deletion {'succeeded' if result else 'failed'}"
            }
        elif isinstance(result, int):
            return {
                "success": result > 0,
                "deleted_count": result,
                "failed_count": len(timelines) - result,
                "attempted_count": len(timelines)
            }
        else:
            return {
                "success": True,
                "message": "Timelines deleted",
                "result": result
            }

    except Exception as e:
        logger.error(f"Error deleting timelines: {e}")
        return {
            "success": False,
            "error": str(e),
            "timeline_names": timeline_names
        }


def delete_folders(folder_names: List[str]) -> Dict[str, Any]:
    """
    Delete one or more folders from the Media Pool.

    Args:
        folder_names: List of folder names to delete

    Returns:
        Deletion result

    Example:
        >>> delete_folders(["Old Footage", "Temp Bin"])
        {
            "success": True,
            "deleted_count": 2
        }
    """
    try:
        media_pool = get_media_pool()
        root = media_pool.GetRootFolder()

        # Find folders by name
        folders = []
        for folder_name in folder_names:
            folder = _find_folder_by_name(root, folder_name)
            if folder:
                folders.append(folder)

        if not folders:
            return {
                "success": False,
                "error": "No folders found with specified names",
                "folder_names": folder_names
            }

        # DeleteFolders([subfolders])
        result = media_pool.DeleteFolders(folders)

        if isinstance(result, bool):
            return {
                "success": result,
                "attempted_count": len(folders),
                "message": f"Folder deletion {'succeeded' if result else 'failed'}"
            }
        elif isinstance(result, int):
            return {
                "success": result > 0,
                "deleted_count": result,
                "failed_count": len(folders) - result
            }
        else:
            return {
                "success": True,
                "message": "Folders deleted",
                "result": result
            }

    except Exception as e:
        logger.error(f"Error deleting folders: {e}")
        return {
            "success": False,
            "error": str(e),
            "folder_names": folder_names
        }


def move_folders(
    folder_names: List[str],
    target_folder_name: str
) -> Dict[str, Any]:
    """
    Move folders to a target folder in the Media Pool.

    Args:
        folder_names: List of folder names to move
        target_folder_name: Name of the destination folder

    Returns:
        Move result

    Example:
        >>> move_folders(
        ...     folder_names=["Day 1", "Day 2"],
        ...     target_folder_name="Production Footage"
        ... )
        {
            "success": True,
            "moved_count": 2,
            "target_folder": "Production Footage"
        }
    """
    try:
        media_pool = get_media_pool()
        root = media_pool.GetRootFolder()

        # Find folders to move
        folders = []
        for folder_name in folder_names:
            folder = _find_folder_by_name(root, folder_name)
            if folder:
                folders.append(folder)

        if not folders:
            return {
                "success": False,
                "error": "No folders found with specified names",
                "folder_names": folder_names
            }

        # Find target folder
        target_folder = _find_folder_by_name(root, target_folder_name)
        if not target_folder:
            return {
                "success": False,
                "error": f"Target folder '{target_folder_name}' not found"
            }

        # MoveFolders([folders], targetFolder)
        result = media_pool.MoveFolders(folders, target_folder)

        return {
            "success": bool(result),
            "moved_count": len(folders) if result else 0,
            "target_folder": target_folder_name,
            "message": f"Moved {len(folders) if result else 0} folders"
        }

    except Exception as e:
        logger.error(f"Error moving folders: {e}")
        return {
            "success": False,
            "error": str(e),
            "folder_names": folder_names
        }


# ============================================================================
# Helper Functions
# ============================================================================

def _find_folder_by_name(root_folder, folder_name: str):
    """Recursively search for a folder by name."""
    if root_folder.GetName() == folder_name:
        return root_folder

    subfolders = root_folder.GetSubFolderList()
    if subfolders:
        for subfolder in subfolders:
            result = _find_folder_by_name(subfolder, folder_name)
            if result:
                return result

    return None


def _find_clip_by_name(folder, clip_name: str):
    """Recursively search for a clip by name."""
    clips = folder.GetClipList()
    if clips:
        for clip in clips:
            if clip.GetName() == clip_name:
                return clip

    # Search subfolders
    subfolders = folder.GetSubFolderList()
    if subfolders:
        for subfolder in subfolders:
            result = _find_clip_by_name(subfolder, clip_name)
            if result:
                return result

    return None


# ============================================================================
# Tool Registration
# ============================================================================

def register_tools(mcp):
    """
    Register MediaPool Selection and Metadata tools with the MCP server.

    Args:
        mcp: FastMCP server instance

    Returns:
        Number of tools registered
    """
    from ..proxy import get_proxy

    proxy = get_proxy()

    # Register MEDIUM priority clip selection tools
    proxy.register_tool(
        "get_selected_clips",
        get_selected_clips,
        "media",
        "Get list of currently selected clips in the Media Pool",
        {}
    )

    proxy.register_tool(
        "set_selected_clip",
        set_selected_clip,
        "media",
        "Set a clip as selected in the Media Pool",
        {"clip_name": {"type": "string", "description": "Name of the clip to select"}}
    )

    # Register MEDIUM priority metadata tool
    proxy.register_tool(
        "export_metadata",
        export_metadata,
        "media",
        "Export clip metadata to CSV file",
        {
            "file_name": {"type": "string", "description": "Destination CSV file path"},
            "clip_names": {"type": "array", "description": "Optional list of clip names (exports all if None)", "optional": True}
        }
    )

    # Register MEDIUM priority timeline management tools
    proxy.register_tool(
        "delete_timelines",
        delete_timelines,
        "timeline",
        "Delete one or more timelines from the project",
        {"timeline_names": {"type": "array", "description": "List of timeline names to delete"}}
    )

    proxy.register_tool(
        "delete_folders",
        delete_folders,
        "media",
        "Delete one or more folders from the Media Pool",
        {"folder_names": {"type": "array", "description": "List of folder names to delete"}}
    )

    proxy.register_tool(
        "move_folders",
        move_folders,
        "media",
        "Move folders to a target folder in the Media Pool",
        {
            "folder_names": {"type": "array", "description": "List of folder names to move"},
            "target_folder_name": {"type": "string", "description": "Name of the destination folder"}
        }
    )

    logger.info("Registered 6 MediaPool Selection and Metadata tools")
    return 6


# For standalone testing
if __name__ == "__main__":
    print("MediaPool Selection and Metadata Tools - Testing")
    print("=" * 60)

    try:
        selected = get_selected_clips()
        print(f"\nSelected clips: {len(selected)}")
        for clip in selected:
            print(f"  - {clip.get('name')}")
    except Exception as e:
        print(f"Error: {e}")
