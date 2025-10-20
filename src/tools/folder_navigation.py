"""
DaVinci Resolve MCP - MediaPool Folder Navigation

Implements MediaPool folder navigation operations including:
- Root and parent folder navigation
- Current folder tracking
- Folder opening by name

MEDIUM PRIORITY: Useful for bin organization and navigation workflows
"""

from typing import Dict, Any, List, Optional
import json
import logging

logger = logging.getLogger("davinci-resolve-mcp.tools.folder_navigation")

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
# Folder Navigation Operations (MEDIUM PRIORITY)
# ============================================================================

def goto_root_folder() -> Dict[str, Any]:
    """
    Navigate to the root folder in the Media Pool.

    Sets the current folder context to the root/master folder.

    Returns:
        Navigation result

    Example:
        >>> goto_root_folder()
        {
            "success": True,
            "folder_name": "Master",
            "message": "Navigated to root folder"
        }
    """
    try:
        media_pool = get_media_pool()

        # GotoRootFolder()
        result = media_pool.GotoRootFolder()

        # Get root folder to confirm
        root = media_pool.GetRootFolder()
        folder_name = root.GetName() if root else "Master"

        return {
            "success": bool(result),
            "folder_name": folder_name,
            "message": f"Navigated to root folder" if result else "Navigation failed"
        }

    except Exception as e:
        logger.error(f"Error navigating to root folder: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def goto_parent_folder() -> Dict[str, Any]:
    """
    Navigate to the parent folder of the current folder.

    Moves up one level in the folder hierarchy.

    Returns:
        Navigation result

    Example:
        >>> goto_parent_folder()
        {
            "success": True,
            "message": "Navigated to parent folder"
        }
    """
    try:
        media_pool = get_media_pool()

        # GotoParentFolder()
        result = media_pool.GotoParentFolder()

        return {
            "success": bool(result),
            "message": f"Navigated to parent folder" if result else "Navigation failed (may be at root)"
        }

    except Exception as e:
        logger.error(f"Error navigating to parent folder: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_current_folder() -> Dict[str, Any]:
    """
    Get the name of the current folder in the Media Pool.

    Returns:
        Current folder information

    Example:
        >>> get_current_folder()
        {
            "success": True,
            "folder_name": "Interview Clips",
            "is_root": False
        }
    """
    try:
        media_pool = get_media_pool()

        # GetCurrentFolder() - returns folder name as string
        folder_name = media_pool.GetCurrentFolder()

        if not folder_name:
            return {
                "success": False,
                "error": "Unable to get current folder"
            }

        # Check if it's the root folder
        root = media_pool.GetRootFolder()
        is_root = (folder_name == root.GetName()) if root else False

        return {
            "success": True,
            "folder_name": folder_name,
            "is_root": is_root
        }

    except Exception as e:
        logger.error(f"Error getting current folder: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def open_folder(folder_name: str) -> Dict[str, Any]:
    """
    Open a folder by name in the Media Pool.

    Navigates to the specified folder, making it the current folder.

    Args:
        folder_name: Name of the folder to open

    Returns:
        Open result

    Example:
        >>> open_folder("Interview Clips")
        {
            "success": True,
            "folder_name": "Interview Clips",
            "message": "Folder opened"
        }
    """
    try:
        media_pool = get_media_pool()

        # OpenFolder(folderName)
        result = media_pool.OpenFolder(folder_name)

        return {
            "success": bool(result),
            "folder_name": folder_name,
            "message": f"Folder {'opened' if result else 'open failed - folder may not exist'}"
        }

    except Exception as e:
        logger.error(f"Error opening folder '{folder_name}': {e}")
        return {
            "success": False,
            "error": str(e),
            "folder_name": folder_name
        }


def refresh_folders() -> Dict[str, Any]:
    """
    Refresh the folder list in the Media Pool.

    Useful in collaborative environments where other users may have
    created or modified folders.

    Returns:
        Refresh result

    Example:
        >>> refresh_folders()
        {
            "success": True,
            "message": "Folders refreshed"
        }
    """
    try:
        media_pool = get_media_pool()

        # RefreshFolders()
        result = media_pool.RefreshFolders()

        return {
            "success": bool(result),
            "message": f"Folders {'refreshed' if result else 'refresh failed'}"
        }

    except Exception as e:
        logger.error(f"Error refreshing folders: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# Tool Registration
# ============================================================================

def register_tools(mcp):
    """
    Register MediaPool Folder Navigation tools with the MCP server.

    Args:
        mcp: FastMCP server instance

    Returns:
        Number of tools registered
    """
    from ..proxy import get_proxy

    proxy = get_proxy()

    # Register MEDIUM priority folder navigation tools
    proxy.register_tool(
        "goto_root_folder",
        goto_root_folder,
        "media",
        "Navigate to the root folder in the Media Pool",
        {}
    )

    proxy.register_tool(
        "goto_parent_folder",
        goto_parent_folder,
        "media",
        "Navigate to the parent folder of the current folder",
        {}
    )

    proxy.register_tool(
        "get_current_folder",
        get_current_folder,
        "media",
        "Get the name of the current folder in the Media Pool",
        {}
    )

    proxy.register_tool(
        "open_folder",
        open_folder,
        "media",
        "Open a folder by name in the Media Pool",
        {"folder_name": {"type": "string", "description": "Name of the folder to open"}}
    )

    proxy.register_tool(
        "refresh_folders",
        refresh_folders,
        "media",
        "Refresh the folder list (useful in collaborative environments)",
        {}
    )

    logger.info("Registered 5 MediaPool Folder Navigation tools")
    return 5


# For standalone testing
if __name__ == "__main__":
    print("MediaPool Folder Navigation Tools - Testing")
    print("=" * 60)

    try:
        current = get_current_folder()
        print(f"\nCurrent folder: {current}")
    except Exception as e:
        print(f"Error: {e}")
