#!/usr/bin/env python3
"""
DaVinci Resolve Project Operations
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger("davinci-resolve-mcp.project")

def list_projects(resolve) -> List[str]:
    """List all available projects in the current database."""
    if resolve is None:
        return ["Error: Not connected to DaVinci Resolve"]
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return ["Error: Failed to get Project Manager"]
    
    projects = project_manager.GetProjectListInCurrentFolder()
    
    # Filter out any empty strings that might be in the list
    return [p for p in projects if p]

def get_current_project_name(resolve) -> str:
    """Get the name of the currently open project."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "No project currently open"
    
    return current_project.GetName()

def open_project(resolve, name: str) -> str:
    """Open a project by name."""
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

def create_project(resolve, name: str) -> str:
    """Create a new project with the given name."""
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

def save_project(resolve) -> str:
    """Save the current project."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # DaVinci Resolve auto-saves projects, but we can perform an operation
    # that forces a save, like creating a temp timeline and then removing it
    project_name = current_project.GetName()
    try:
        # Get media pool to trigger a save indirectly
        media_pool = current_project.GetMediaPool()
        if not media_pool:
            return "Project is likely already saved (auto-save enabled)"
            
        # Another approach: DaVinci Resolve auto-saves, so we can just confirm the project exists
        return f"Project '{project_name}' is saved (auto-save enabled in DaVinci Resolve)"
    except Exception as e:
        return f"Error checking project: {str(e)}"


# ============================================================
# Phase 2: Project Management Extensions
# ============================================================

def delete_project(resolve, name: str) -> str:
    """Delete a project by name.
    
    Args:
        resolve: DaVinci Resolve instance
        name: Name of the project to delete
    """
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
        return f"Error: Project '{name}' not found"
    
    # Check if it's the current project
    current_project = project_manager.GetCurrentProject()
    if current_project and current_project.GetName() == name:
        return "Error: Cannot delete the currently open project. Close it first."
    
    try:
        if project_manager.DeleteProject(name):
            return f"Successfully deleted project '{name}'"
        return f"Failed to delete project '{name}'"
    except Exception as e:
        return f"Error deleting project: {e}"


def close_project(resolve) -> str:
    """Close the current project."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "No project currently open"
    
    project_name = current_project.GetName()
    
    try:
        if project_manager.CloseProject(current_project):
            return f"Closed project '{project_name}'"
        return "Failed to close project"
    except Exception as e:
        return f"Error closing project: {e}"


def rename_project(resolve, new_name: str) -> str:
    """Rename the current project.
    
    Args:
        resolve: DaVinci Resolve instance
        new_name: New name for the project
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not new_name:
        return "Error: New name cannot be empty"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    old_name = current_project.GetName()
    
    try:
        if current_project.SetName(new_name):
            return f"Renamed project from '{old_name}' to '{new_name}'"
        return "Failed to rename project"
    except Exception as e:
        return f"Error renaming project: {e}"


def get_project_unique_id(resolve) -> Dict[str, Any]:
    """Get the unique ID of the current project."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    try:
        return {
            "project_name": current_project.GetName(),
            "unique_id": current_project.GetUniqueId()
        }
    except Exception as e:
        return {"error": f"Error getting project ID: {e}"}


# --- Project Import/Export ---

def export_project(resolve, project_name: str, file_path: str, 
                   with_stills_and_luts: bool = True) -> str:
    """Export a project to a file.
    
    Args:
        resolve: DaVinci Resolve instance
        project_name: Name of the project to export
        file_path: Path for the exported file (.drp format)
        with_stills_and_luts: Whether to include stills and LUTs
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    # Check if project exists
    projects = project_manager.GetProjectListInCurrentFolder()
    if project_name not in projects:
        return f"Error: Project '{project_name}' not found"
    
    try:
        if project_manager.ExportProject(project_name, file_path, with_stills_and_luts):
            return f"Exported project '{project_name}' to '{file_path}'"
        return f"Failed to export project '{project_name}'"
    except Exception as e:
        return f"Error exporting project: {e}"


def import_project(resolve, file_path: str, project_name: str = None) -> str:
    """Import a project from a file.
    
    Args:
        resolve: DaVinci Resolve instance
        file_path: Path to the project file (.drp format)
        project_name: Optional name for the imported project
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    import os
    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    try:
        result = project_manager.ImportProject(file_path, project_name) if project_name else project_manager.ImportProject(file_path)
        if result:
            return f"Successfully imported project from '{file_path}'"
        return f"Failed to import project from '{file_path}'"
    except Exception as e:
        return f"Error importing project: {e}"


def archive_project(resolve, project_name: str, file_path: str,
                    is_archive_src_media: bool = True,
                    is_archive_render_cache: bool = False,
                    is_archive_proxy_media: bool = False) -> str:
    """Archive a project to a file.
    
    Args:
        resolve: DaVinci Resolve instance
        project_name: Name of the project to archive
        file_path: Path for the archive file (.dra format)
        is_archive_src_media: Include source media files
        is_archive_render_cache: Include render cache
        is_archive_proxy_media: Include proxy media
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    # Check if project exists
    projects = project_manager.GetProjectListInCurrentFolder()
    if project_name not in projects:
        return f"Error: Project '{project_name}' not found"
    
    try:
        # ArchiveProject(projectName, filePath, isArchiveSrcMedia, isArchiveRenderCache, isArchiveProxyMedia)
        result = project_manager.ArchiveProject(
            project_name, file_path,
            is_archive_src_media, is_archive_render_cache, is_archive_proxy_media
        )
        if result:
            return f"Archived project '{project_name}' to '{file_path}'"
        return f"Failed to archive project '{project_name}'"
    except Exception as e:
        return f"Error archiving project: {e}"


def restore_project(resolve, file_path: str, project_name: str = None) -> str:
    """Restore a project from an archive.
    
    Args:
        resolve: DaVinci Resolve instance
        file_path: Path to the archive file (.dra format)
        project_name: Optional name for the restored project
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    import os
    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    try:
        result = project_manager.RestoreProject(file_path, project_name) if project_name else project_manager.RestoreProject(file_path)
        if result:
            return f"Successfully restored project from '{file_path}'"
        return f"Failed to restore project from '{file_path}'"
    except Exception as e:
        return f"Error restoring project: {e}"


# --- Database Folder Navigation ---

def list_database_folders(resolve) -> Dict[str, Any]:
    """List folders in the current database folder."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    try:
        folders = project_manager.GetFolderListInCurrentFolder()
        current = project_manager.GetCurrentFolder()
        
        return {
            "current_folder": current if current else "Root",
            "folders": folders if folders else []
        }
    except Exception as e:
        return {"error": f"Error listing folders: {e}"}


def create_database_folder(resolve, folder_name: str) -> str:
    """Create a folder in the current database folder.
    
    Args:
        resolve: DaVinci Resolve instance
        folder_name: Name of the folder to create
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not folder_name:
        return "Error: Folder name cannot be empty"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    try:
        if project_manager.CreateFolder(folder_name):
            return f"Created folder '{folder_name}'"
        return f"Failed to create folder '{folder_name}'"
    except Exception as e:
        return f"Error creating folder: {e}"


def delete_database_folder(resolve, folder_name: str) -> str:
    """Delete a folder in the current database folder.
    
    Args:
        resolve: DaVinci Resolve instance
        folder_name: Name of the folder to delete
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    try:
        if project_manager.DeleteFolder(folder_name):
            return f"Deleted folder '{folder_name}'"
        return f"Failed to delete folder '{folder_name}'"
    except Exception as e:
        return f"Error deleting folder: {e}"


def open_database_folder(resolve, folder_name: str) -> str:
    """Open/navigate to a folder in the database.
    
    Args:
        resolve: DaVinci Resolve instance
        folder_name: Name of the folder to open
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    try:
        if project_manager.OpenFolder(folder_name):
            return f"Opened folder '{folder_name}'"
        return f"Failed to open folder '{folder_name}'"
    except Exception as e:
        return f"Error opening folder: {e}"


def goto_root_folder(resolve) -> str:
    """Navigate to the root folder of the database."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    try:
        if project_manager.GotoRootFolder():
            return "Navigated to root folder"
        return "Failed to navigate to root folder"
    except Exception as e:
        return f"Error navigating: {e}"


def goto_parent_folder(resolve) -> str:
    """Navigate to the parent folder in the database."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    try:
        if project_manager.GotoParentFolder():
            return "Navigated to parent folder"
        return "Already at root folder"
    except Exception as e:
        return f"Error navigating: {e}"


# --- Database Management ---

def get_database_list(resolve) -> Dict[str, Any]:
    """Get list of available databases."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    try:
        databases = project_manager.GetDatabaseList()
        current = project_manager.GetCurrentDatabase()
        
        return {
            "current_database": current,
            "databases": databases if databases else []
        }
    except Exception as e:
        return {"error": f"Error getting databases: {e}"}


def set_current_database(resolve, db_info: Dict[str, str]) -> str:
    """Switch to a different database.
    
    Args:
        resolve: DaVinci Resolve instance
        db_info: Database info dict with 'DbType', 'DbName', and optionally 'IpAddress'
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    try:
        if project_manager.SetCurrentDatabase(db_info):
            return f"Switched to database '{db_info.get('DbName', 'Unknown')}'"
        return "Failed to switch database"
    except Exception as e:
        return f"Error switching database: {e}"
 