"""
MediaStorage Operations for DaVinci Resolve MCP

This module implements MediaStorage operations from the DaVinci Resolve API.
MediaStorage allows browsing and accessing media files on mounted volumes.

API Coverage:
- GetMountedVolumeList() - List all mounted volumes
- GetSubFolderList(folderPath) - List subfolders in a folder
- GetFileList(folderPath) - List files in a folder
- RevealInStorage(path) - Reveal and expand path in Media Storage
- AddItemListToMediaPool() - Import media from storage to media pool
- AddClipMattesToMediaPool() - Add matte files to a clip
- AddTimelineMattesToMediaPool() - Add timeline mattes
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("davinci-resolve-mcp.media_storage")

# Global resolve object (set by main server)
resolve = None


def set_resolve(resolve_instance):
    """Set the global resolve instance."""
    global resolve
    resolve = resolve_instance


def get_media_storage():
    """Get the MediaStorage object."""
    if resolve is None:
        raise RuntimeError("Not connected to DaVinci Resolve")
    return resolve.GetMediaStorage()


# ------------------
# MediaStorage Tools
# ------------------

def get_mounted_volumes() -> List[str]:
    """
    Get list of all mounted volumes visible in DaVinci Resolve Media Storage.

    Returns:
        List of volume paths (e.g., ["/Volumes/MyDrive", "/Users/username"])

    Example:
        >>> get_mounted_volumes()
        ["/Volumes/SSD1", "/Volumes/SSD2", "/Users/john"]
    """
    try:
        media_storage = get_media_storage()
        volumes = media_storage.GetMountedVolumeList()

        if volumes:
            logger.info(f"Found {len(volumes)} mounted volumes")
            return volumes
        else:
            logger.warning("No mounted volumes found")
            return []

    except Exception as e:
        logger.error(f"Error getting mounted volumes: {e}")
        raise


def get_sub_folders(folder_path: str) -> List[str]:
    """
    Get list of subfolders in the specified folder.

    Args:
        folder_path: Absolute path to folder (e.g., "/Users/username/Videos")

    Returns:
        List of subfolder paths

    Example:
        >>> get_sub_folders("/Users/john/Videos")
        ["/Users/john/Videos/Project1", "/Users/john/Videos/Project2"]
    """
    try:
        media_storage = get_media_storage()
        subfolders = media_storage.GetSubFolderList(folder_path)

        if subfolders:
            logger.info(f"Found {len(subfolders)} subfolders in {folder_path}")
            return subfolders
        else:
            logger.info(f"No subfolders found in {folder_path}")
            return []

    except Exception as e:
        logger.error(f"Error getting subfolders from {folder_path}: {e}")
        raise


def get_file_list(folder_path: str) -> List[str]:
    """
    Get list of media files and folders in the specified folder.

    Note: Media listings may be logically consolidated entries.
    For example, image sequences may appear as a single entry.

    Args:
        folder_path: Absolute path to folder

    Returns:
        List of file/folder paths

    Example:
        >>> get_file_list("/Users/john/Videos/Footage")
        [
            "/Users/john/Videos/Footage/clip001.mov",
            "/Users/john/Videos/Footage/clip002.mov",
            "/Users/john/Videos/Footage/sequence_[001-100].dpx"
        ]
    """
    try:
        media_storage = get_media_storage()
        files = media_storage.GetFileList(folder_path)

        if files:
            logger.info(f"Found {len(files)} items in {folder_path}")
            return files
        else:
            logger.info(f"No files found in {folder_path}")
            return []

    except Exception as e:
        logger.error(f"Error getting file list from {folder_path}: {e}")
        raise


def reveal_in_storage(path: str) -> bool:
    """
    Reveal and expand the specified path in DaVinci Resolve's Media Storage panel.

    This is useful for navigating to a specific folder or file in the Media Storage.

    Args:
        path: Absolute path to file or folder to reveal

    Returns:
        True if successful, False otherwise

    Example:
        >>> reveal_in_storage("/Users/john/Videos/Project1")
        True
    """
    try:
        media_storage = get_media_storage()
        success = media_storage.RevealInStorage(path)

        if success:
            logger.info(f"Successfully revealed path in Media Storage: {path}")
        else:
            logger.warning(f"Failed to reveal path in Media Storage: {path}")

        return success

    except Exception as e:
        logger.error(f"Error revealing path {path}: {e}")
        return False


def add_items_to_media_pool(
    file_paths: List[str]
) -> List[str]:
    """
    Add specified file/folder paths from Media Storage to current Media Pool folder.

    Args:
        file_paths: List of absolute file/folder paths to import

    Returns:
        List of MediaPoolItem IDs that were created

    Example:
        >>> add_items_to_media_pool([
        ...     "/Users/john/Videos/clip1.mov",
        ...     "/Users/john/Videos/clip2.mov"
        ... ])
        ["mediapool_item_1", "mediapool_item_2"]
    """
    try:
        media_storage = get_media_storage()
        clips = media_storage.AddItemListToMediaPool(file_paths)

        if clips:
            logger.info(f"Successfully imported {len(clips)} items to media pool")
            # Return clip names/IDs
            return [clip.GetName() if hasattr(clip, 'GetName') else str(clip) for clip in clips]
        else:
            logger.warning("No items were imported to media pool")
            return []

    except Exception as e:
        logger.error(f"Error adding items to media pool: {e}")
        raise


def add_items_to_media_pool_with_range(
    items_info: List[Dict[str, Any]]
) -> List[str]:
    """
    Add media files with specific in/out points to the media pool.

    Each item can specify start and end frames for clip subranges.

    Args:
        items_info: List of dicts with keys:
                   - "media": File path (string)
                   - "startFrame": Start frame (int, optional)
                   - "endFrame": End frame (int, optional)

    Returns:
        List of created MediaPoolItem names

    Example:
        >>> add_items_to_media_pool_with_range([
        ...     {
        ...         "media": "/path/to/clip.mov",
        ...         "startFrame": 100,
        ...         "endFrame": 500
        ...     }
        ... ])
    """
    try:
        media_storage = get_media_storage()
        clips = media_storage.AddItemListToMediaPool(items_info)

        if clips:
            logger.info(f"Successfully imported {len(clips)} items with ranges")
            return [clip.GetName() if hasattr(clip, 'GetName') else str(clip) for clip in clips]
        else:
            logger.warning("No items were imported")
            return []

    except Exception as e:
        logger.error(f"Error adding items with ranges: {e}")
        raise


def add_clip_mattes_to_media_pool(
    media_pool_item_name: str,
    matte_paths: List[str],
    stereo_eye: Optional[str] = None
) -> bool:
    """
    Add matte files to a specific MediaPoolItem.

    Mattes are alpha channel or transparency files that can be composited with clips.

    Args:
        media_pool_item_name: Name of the MediaPoolItem to add mattes to
        matte_paths: List of absolute paths to matte files
        stereo_eye: Optional stereo eye ("left" or "right") for stereo clips

    Returns:
        True if successful, False otherwise

    Example:
        >>> add_clip_mattes_to_media_pool(
        ...     "clip001.mov",
        ...     ["/path/to/matte001.png", "/path/to/matte002.png"],
        ...     stereo_eye="left"
        ... )
    """
    try:
        # Get media pool item
        project = resolve.GetProjectManager().GetCurrentProject()
        media_pool = project.GetMediaPool()

        # Find the media pool item
        media_pool_item = None
        for folder in media_pool.GetRootFolder().GetClipList():
            if folder.GetName() == media_pool_item_name:
                media_pool_item = folder
                break

        if not media_pool_item:
            logger.error(f"MediaPoolItem not found: {media_pool_item_name}")
            return False

        # Add mattes
        media_storage = get_media_storage()

        if stereo_eye:
            success = media_storage.AddClipMattesToMediaPool(
                media_pool_item, matte_paths, stereo_eye
            )
        else:
            success = media_storage.AddClipMattesToMediaPool(
                media_pool_item, matte_paths
            )

        if success:
            logger.info(f"Successfully added {len(matte_paths)} mattes to {media_pool_item_name}")
        else:
            logger.warning(f"Failed to add mattes to {media_pool_item_name}")

        return success

    except Exception as e:
        logger.error(f"Error adding clip mattes: {e}")
        return False


def add_timeline_mattes_to_media_pool(matte_paths: List[str]) -> List[str]:
    """
    Add timeline matte files to the current media pool folder.

    Timeline mattes are special matte clips that can be used on timeline tracks.

    Args:
        matte_paths: List of absolute paths to matte files

    Returns:
        List of created MediaPoolItem names

    Example:
        >>> add_timeline_mattes_to_media_pool([
        ...     "/path/to/timeline_matte1.png",
        ...     "/path/to/timeline_matte2.png"
        ... ])
        ["timeline_matte1", "timeline_matte2"]
    """
    try:
        media_storage = get_media_storage()
        mattes = media_storage.AddTimelineMattesToMediaPool(matte_paths)

        if mattes:
            logger.info(f"Successfully added {len(mattes)} timeline mattes")
            return [matte.GetName() if hasattr(matte, 'GetName') else str(matte) for matte in mattes]
        else:
            logger.warning("No timeline mattes were added")
            return []

    except Exception as e:
        logger.error(f"Error adding timeline mattes: {e}")
        raise


def browse_media_storage(
    start_path: Optional[str] = None,
    max_depth: int = 2
) -> Dict[str, Any]:
    """
    Browse media storage starting from a path and return folder structure.

    This is a helper function that recursively explores folders.

    Args:
        start_path: Starting path (uses mounted volumes if None)
        max_depth: Maximum folder depth to explore (default: 2)

    Returns:
        Dictionary with folder structure:
        {
            "path": "/Users/john",
            "subfolders": [...],
            "files": [...]
        }

    Example:
        >>> browse_media_storage("/Users/john/Videos", max_depth=1)
        {
            "path": "/Users/john/Videos",
            "subfolders": [
                {"path": "/Users/john/Videos/Project1", "files": [...]}
            ],
            "files": ["clip1.mov", "clip2.mov"]
        }
    """
    try:
        media_storage = get_media_storage()

        # Start from mounted volumes if no path specified
        if start_path is None:
            volumes = media_storage.GetMountedVolumeList()
            return {
                "volumes": [
                    browse_media_storage(vol, max_depth - 1) if max_depth > 0 else {"path": vol}
                    for vol in volumes
                ]
            }

        # Get subfolders and files
        subfolders = media_storage.GetSubFolderList(start_path) if max_depth > 0 else []
        files = media_storage.GetFileList(start_path)

        result = {
            "path": start_path,
            "files": files
        }

        if max_depth > 0 and subfolders:
            result["subfolders"] = [
                browse_media_storage(subfolder, max_depth - 1)
                for subfolder in subfolders
            ]

        return result

    except Exception as e:
        logger.error(f"Error browsing media storage at {start_path}: {e}")
        return {"path": start_path, "error": str(e)}


# ------------------
# Register Tools
# ------------------

def register_tools(mcp):
    """
    Register MediaStorage tools with the MCP server.

    Args:
        mcp: FastMCP server instance

    Returns:
        Number of tools registered
    """
    from ..proxy import get_proxy

    proxy = get_proxy()

    # Register all tools with proxy for search/execute
    proxy.register_tool(
        "get_mounted_volumes",
        get_mounted_volumes,
        "media_storage",
        "Get list of all mounted volumes in Media Storage",
        {}
    )

    proxy.register_tool(
        "get_sub_folders",
        get_sub_folders,
        "media_storage",
        "Get list of subfolders in a folder",
        {"folder_path": {"type": "string", "description": "Absolute path to folder"}}
    )

    proxy.register_tool(
        "get_file_list",
        get_file_list,
        "media_storage",
        "Get list of files in a folder",
        {"folder_path": {"type": "string", "description": "Absolute path to folder"}}
    )

    proxy.register_tool(
        "reveal_in_storage",
        reveal_in_storage,
        "media_storage",
        "Reveal path in Media Storage panel",
        {"path": {"type": "string", "description": "Path to reveal"}}
    )

    proxy.register_tool(
        "add_items_to_media_pool",
        add_items_to_media_pool,
        "media_storage",
        "Import files from Media Storage to Media Pool",
        {"file_paths": {"type": "array", "description": "List of file paths to import"}}
    )

    proxy.register_tool(
        "add_items_to_media_pool_with_range",
        add_items_to_media_pool_with_range,
        "media_storage",
        "Import files with specific in/out points",
        {"items_info": {"type": "array", "description": "List of items with media path and frame range"}}
    )

    proxy.register_tool(
        "add_clip_mattes_to_media_pool",
        add_clip_mattes_to_media_pool,
        "media_storage",
        "Add matte files to a MediaPoolItem",
        {
            "media_pool_item_name": {"type": "string", "description": "Name of clip"},
            "matte_paths": {"type": "array", "description": "List of matte file paths"},
            "stereo_eye": {"type": "string", "description": "left or right (optional)"}
        }
    )

    proxy.register_tool(
        "add_timeline_mattes_to_media_pool",
        add_timeline_mattes_to_media_pool,
        "media_storage",
        "Add timeline matte files to Media Pool",
        {"matte_paths": {"type": "array", "description": "List of timeline matte paths"}}
    )

    proxy.register_tool(
        "browse_media_storage",
        browse_media_storage,
        "media_storage",
        "Browse folder structure in Media Storage",
        {
            "start_path": {"type": "string", "description": "Starting path (optional)"},
            "max_depth": {"type": "integer", "description": "Maximum depth to explore"}
        }
    )

    logger.info("Registered 9 MediaStorage tools")
    return 9
