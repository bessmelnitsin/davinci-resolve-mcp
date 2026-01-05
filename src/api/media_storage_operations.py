#!/usr/bin/env python3
"""
DaVinci Resolve MediaStorage Operations

Provides access to the media storage browser:
- Mounted volumes listing
- Folder and file browsing
- Adding items to Media Pool
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("davinci-resolve-mcp.media_storage")


def get_media_storage(resolve):
    """Get MediaStorage object from Resolve."""
    if resolve is None:
        return None
    try:
        return resolve.GetMediaStorage()
    except Exception as e:
        logger.error(f"Failed to get MediaStorage: {e}")
        return None


def get_mounted_volumes(resolve) -> Dict[str, Any]:
    """
    Get list of mounted volumes displayed in Media Storage.
    
    Args:
        resolve: DaVinci Resolve instance
        
    Returns:
        Dictionary with volume paths
    """
    storage = get_media_storage(resolve)
    if storage is None:
        return {"error": "Could not access MediaStorage"}
    
    try:
        volumes = storage.GetMountedVolumeList()
        return {
            "success": True,
            "volumes": volumes if volumes else [],
            "count": len(volumes) if volumes else 0
        }
    except Exception as e:
        logger.error(f"Failed to get mounted volumes: {e}")
        return {"error": f"Failed to get mounted volumes: {e}"}


def get_sub_folders(resolve, folder_path: str) -> Dict[str, Any]:
    """
    Get list of subfolders in a given folder path.
    
    Args:
        resolve: DaVinci Resolve instance
        folder_path: Absolute path to the folder
        
    Returns:
        Dictionary with subfolder paths
    """
    storage = get_media_storage(resolve)
    if storage is None:
        return {"error": "Could not access MediaStorage"}
    
    try:
        subfolders = storage.GetSubFolderList(folder_path)
        return {
            "success": True,
            "path": folder_path,
            "subfolders": subfolders if subfolders else [],
            "count": len(subfolders) if subfolders else 0
        }
    except Exception as e:
        logger.error(f"Failed to get subfolders for {folder_path}: {e}")
        return {"error": f"Failed to get subfolders: {e}"}


def get_files(resolve, folder_path: str) -> Dict[str, Any]:
    """
    Get list of media and file listings in a given folder path.
    
    Note: Media listings may be logically consolidated entries.
    
    Args:
        resolve: DaVinci Resolve instance
        folder_path: Absolute path to the folder
        
    Returns:
        Dictionary with file paths
    """
    storage = get_media_storage(resolve)
    if storage is None:
        return {"error": "Could not access MediaStorage"}
    
    try:
        files = storage.GetFileList(folder_path)
        return {
            "success": True,
            "path": folder_path,
            "files": files if files else [],
            "count": len(files) if files else 0
        }
    except Exception as e:
        logger.error(f"Failed to get files for {folder_path}: {e}")
        return {"error": f"Failed to get files: {e}"}


def reveal_in_storage(resolve, path: str) -> Dict[str, Any]:
    """
    Expand and display a file/folder path in Resolve's Media Storage.
    
    Args:
        resolve: DaVinci Resolve instance
        path: File or folder path to reveal
        
    Returns:
        Status dictionary
    """
    storage = get_media_storage(resolve)
    if storage is None:
        return {"error": "Could not access MediaStorage"}
    
    try:
        result = storage.RevealInStorage(path)
        if result:
            return {
                "success": True,
                "message": f"Revealed '{path}' in Media Storage"
            }
        return {
            "success": False,
            "message": f"Could not reveal '{path}' - path may not exist"
        }
    except Exception as e:
        logger.error(f"Failed to reveal in storage: {e}")
        return {"error": f"Failed to reveal in storage: {e}"}


def add_items_to_media_pool(resolve, items: List[str]) -> Dict[str, Any]:
    """
    Add file/folder paths from Media Storage into current Media Pool folder.
    
    Args:
        resolve: DaVinci Resolve instance
        items: List of file/folder paths to add
        
    Returns:
        Dictionary with created MediaPoolItem info
    """
    storage = get_media_storage(resolve)
    if storage is None:
        return {"error": "Could not access MediaStorage"}
    
    if not items:
        return {"error": "No items provided to add"}
    
    try:
        clips = storage.AddItemListToMediaPool(items)
        if clips:
            clip_info = []
            for clip in clips:
                try:
                    info = {
                        "name": clip.GetName(),
                        "id": clip.GetUniqueId() if hasattr(clip, 'GetUniqueId') else None
                    }
                    clip_info.append(info)
                except:
                    clip_info.append({"name": "Unknown"})
            
            return {
                "success": True,
                "added_count": len(clips),
                "clips": clip_info
            }
        return {
            "success": False,
            "message": "No clips were added - files may not be valid media"
        }
    except Exception as e:
        logger.error(f"Failed to add items to media pool: {e}")
        return {"error": f"Failed to add items: {e}"}


def add_items_with_info(resolve, items_info: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Add items with specific start/end frames to Media Pool.
    
    Args:
        resolve: DaVinci Resolve instance
        items_info: List of dicts with "media", "startFrame", "endFrame" keys
        
    Returns:
        Dictionary with created MediaPoolItem info
    """
    storage = get_media_storage(resolve)
    if storage is None:
        return {"error": "Could not access MediaStorage"}
    
    if not items_info:
        return {"error": "No items provided to add"}
    
    try:
        clips = storage.AddItemListToMediaPool(items_info)
        if clips:
            clip_info = []
            for clip in clips:
                try:
                    info = {
                        "name": clip.GetName(),
                        "id": clip.GetUniqueId() if hasattr(clip, 'GetUniqueId') else None
                    }
                    clip_info.append(info)
                except:
                    clip_info.append({"name": "Unknown"})
            
            return {
                "success": True,
                "added_count": len(clips),
                "clips": clip_info
            }
        return {
            "success": False,
            "message": "No clips were added"
        }
    except Exception as e:
        logger.error(f"Failed to add items with info: {e}")
        return {"error": f"Failed to add items: {e}"}


def add_clip_mattes(resolve, media_pool_item, matte_paths: List[str], 
                    stereo_eye: str = None) -> Dict[str, Any]:
    """
    Add media files as mattes for a MediaPoolItem.
    
    Args:
        resolve: DaVinci Resolve instance
        media_pool_item: Target MediaPoolItem
        matte_paths: List of matte file paths
        stereo_eye: Optional "left" or "right" for stereo clips
        
    Returns:
        Status dictionary
    """
    storage = get_media_storage(resolve)
    if storage is None:
        return {"error": "Could not access MediaStorage"}
    
    try:
        if stereo_eye:
            result = storage.AddClipMattesToMediaPool(media_pool_item, matte_paths, stereo_eye)
        else:
            result = storage.AddClipMattesToMediaPool(media_pool_item, matte_paths)
        
        if result:
            return {
                "success": True,
                "message": f"Added {len(matte_paths)} matte(s) to clip"
            }
        return {
            "success": False,
            "message": "Failed to add mattes"
        }
    except Exception as e:
        logger.error(f"Failed to add clip mattes: {e}")
        return {"error": f"Failed to add clip mattes: {e}"}


def add_timeline_mattes(resolve, matte_paths: List[str]) -> Dict[str, Any]:
    """
    Add media files as timeline mattes in current media pool folder.
    
    Args:
        resolve: DaVinci Resolve instance
        matte_paths: List of matte file paths
        
    Returns:
        Dictionary with created MediaPoolItem info
    """
    storage = get_media_storage(resolve)
    if storage is None:
        return {"error": "Could not access MediaStorage"}
    
    try:
        items = storage.AddTimelineMattesToMediaPool(matte_paths)
        if items:
            item_info = []
            for item in items:
                try:
                    info = {
                        "name": item.GetName(),
                        "id": item.GetUniqueId() if hasattr(item, 'GetUniqueId') else None
                    }
                    item_info.append(info)
                except:
                    item_info.append({"name": "Unknown"})
            
            return {
                "success": True,
                "added_count": len(items),
                "mattes": item_info
            }
        return {
            "success": False,
            "message": "No timeline mattes were added"
        }
    except Exception as e:
        logger.error(f"Failed to add timeline mattes: {e}")
        return {"error": f"Failed to add timeline mattes: {e}"}
