"""
DaVinci Resolve Gallery Operations
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("davinci-resolve-mcp.gallery")

def get_color_presets(resolve) -> List[Dict[str, Any]]:
    """Get all available color presets in the current project.
    
    Args:
        resolve: DaVinci Resolve object
    """
    if resolve is None:
        return [{"error": "Not connected to DaVinci Resolve"}]
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return [{"error": "Failed to get Project Manager"}]
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return [{"error": "No project currently open"}]
    
    # Switch to color page to access presets
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")
    
    try:
        # Get gallery
        gallery = current_project.GetGallery()
        if not gallery:
            return [{"error": "Failed to get gallery"}]
        
        # Get all albums
        albums = gallery.GetAlbums()
        if not albums:
            return [{"info": "No albums found in gallery"}]
        
        result = []
        for album in albums:
            # Get stills in the album
            stills = album.GetStills()
            album_info = {
                "name": album.GetName(),
                "stills": []
            }
            
            if stills:
                for still in stills:
                    still_info = {
                        "id": still.GetUniqueId(),
                        "label": still.GetLabel(),
                        "timecode": still.GetTimecode(),
                        "isGrabbed": still.IsGrabbed()
                    }
                    album_info["stills"].append(still_info)
            
            result.append(album_info)
        
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
            
        return result
    
    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return [{"error": f"Error retrieving color presets: {str(e)}"}]

def save_color_preset(resolve, clip_name: str = None, preset_name: str = None, album_name: str = "DaVinci Resolve") -> str:
    """Save a color preset from the specified clip.
    
    Args:
        resolve: DaVinci Resolve object
        clip_name: Name of the clip to save preset from (uses current clip if None)
        preset_name: Name to give the preset (uses clip name if None)
        album_name: Album to save the preset to (default: "DaVinci Resolve")
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Switch to color page
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")
    
    try:
        # Get the current timeline
        current_timeline = current_project.GetCurrentTimeline()
        if not current_timeline:
            return "Error: No timeline is currently open"
        
        # Get the specific clip or current clip
        if clip_name:
            # Find the clip by name in the timeline
            timeline_clips = current_timeline.GetItemListInTrack("video", 1)
            target_clip = None
            
            for clip in timeline_clips:
                if clip.GetName() == clip_name:
                    target_clip = clip
                    break
            
            if not target_clip:
                return f"Error: Clip '{clip_name}' not found in the timeline"
            
            # Select the clip
            current_timeline.SetCurrentSelectedItem(target_clip)
        
        # Get gallery
        gallery = current_project.GetGallery()
        if not gallery:
            return "Error: Failed to get gallery"
        
        # Get or create album
        album = None
        albums = gallery.GetAlbums()
        
        if albums:
            for a in albums:
                if a.GetName() == album_name:
                    album = a
                    break
        
        if not album:
            # Create a new album if it doesn't exist
            album = gallery.CreateAlbum(album_name)
            if not album:
                return f"Error: Failed to create album '{album_name}'"
        
        # Set preset name if specified
        final_preset_name = preset_name
        if not final_preset_name:
            if clip_name:
                final_preset_name = f"{clip_name} Preset"
            else:
                # Get current clip name if available
                current_clip = current_timeline.GetCurrentVideoItem()
                if current_clip:
                    final_preset_name = f"{current_clip.GetName()} Preset"
                else:
                    final_preset_name = f"Preset {len(album.GetStills()) + 1}"
        
        # Capture still
        result = gallery.GrabStill()
        
        if not result:
            return "Error: Failed to grab still for the preset"
        
        # Get the still that was just created
        stills = album.GetStills()
        if stills:
            latest_still = stills[-1]  # Assume the last one is the one we just grabbed
            # Set the label
            latest_still.SetLabel(final_preset_name)
        
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        
        return f"Successfully saved color preset '{final_preset_name}' to album '{album_name}'"
    
    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return f"Error saving color preset: {str(e)}"

def apply_color_preset(resolve, preset_id: str = None, preset_name: str = None, 
                     clip_name: str = None, album_name: str = "DaVinci Resolve") -> str:
    """Apply a color preset to the specified clip.
    
    Args:
        resolve: DaVinci Resolve object
        preset_id: ID of the preset to apply (if known)
        preset_name: Name of the preset to apply (searches in album)
        clip_name: Name of the clip to apply preset to (uses current clip if None)
        album_name: Album containing the preset (default: "DaVinci Resolve")
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not preset_id and not preset_name:
        return "Error: Must provide either preset_id or preset_name"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Switch to color page
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")
    
    try:
        # Get the current timeline
        current_timeline = current_project.GetCurrentTimeline()
        if not current_timeline:
            return "Error: No timeline is currently open"
        
        # Get the specific clip or current clip
        if clip_name:
            # Find the clip by name in the timeline
            timeline_clips = current_timeline.GetItemListInTrack("video", 1)
            target_clip = None
            
            for clip in timeline_clips:
                if clip.GetName() == clip_name:
                    target_clip = clip
                    break
            
            if not target_clip:
                return f"Error: Clip '{clip_name}' not found in the timeline"
            
            # Select the clip
            current_timeline.SetCurrentSelectedItem(target_clip)
        
        # Get gallery
        gallery = current_project.GetGallery()
        if not gallery:
            return "Error: Failed to get gallery"
        
        # Find the album
        album = None
        albums = gallery.GetAlbums()
        
        if albums:
            for a in albums:
                if a.GetName() == album_name:
                    album = a
                    break
        
        if not album:
            return f"Error: Album '{album_name}' not found"
        
        # Find the still to apply
        stills = album.GetStills()
        if not stills:
            return f"Error: No presets found in album '{album_name}'"
        
        target_still = None
        
        if preset_id:
            # Find by ID
            for still in stills:
                if still.GetUniqueId() == preset_id:
                    target_still = still
                    break
        elif preset_name:
            # Find by name
            for still in stills:
                if still.GetLabel() == preset_name:
                    target_still = still
                    break
        
        if not target_still:
            search_term = preset_id if preset_id else preset_name
            return f"Error: Preset '{search_term}' not found in album '{album_name}'"
        
        # Apply the preset
        result = target_still.ApplyToClip()
        
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        
        if result:
            return f"Successfully applied color preset to {'specified clip' if clip_name else 'current clip'}"
        else:
            return f"Failed to apply color preset"
    
    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return f"Error applying color preset: {str(e)}"

def delete_color_preset(resolve, preset_id: str = None, preset_name: str = None, 
                       album_name: str = "DaVinci Resolve") -> str:
    """Delete a color preset.
    
    Args:
        resolve: DaVinci Resolve object
        preset_id: ID of the preset to delete (if known)
        preset_name: Name of the preset to delete (searches in album)
        album_name: Album containing the preset (default: "DaVinci Resolve")
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not preset_id and not preset_name:
        return "Error: Must provide either preset_id or preset_name"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Switch to color page
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")
    
    try:
        # Get gallery
        gallery = current_project.GetGallery()
        if not gallery:
            return "Error: Failed to get gallery"
        
        # Find the album
        album = None
        albums = gallery.GetAlbums()
        
        if albums:
            for a in albums:
                if a.GetName() == album_name:
                    album = a
                    break
        
        if not album:
            return f"Error: Album '{album_name}' not found"
        
        # Find the still to delete
        stills = album.GetStills()
        if not stills:
            return f"Error: No presets found in album '{album_name}'"
        
        target_still = None
        
        if preset_id:
            # Find by ID
            for still in stills:
                if still.GetUniqueId() == preset_id:
                    target_still = still
                    break
        elif preset_name:
            # Find by name
            for still in stills:
                if still.GetLabel() == preset_name:
                    target_still = still
                    break
        
        if not target_still:
            search_term = preset_id if preset_id else preset_name
            return f"Error: Preset '{search_term}' not found in album '{album_name}'"
        
        # Delete the preset
        result = album.DeleteStill(target_still)
        
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        
        if result:
            return f"Successfully deleted color preset from album '{album_name}'"
        else:
            return f"Failed to delete color preset"
    
    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return f"Error deleting color preset: {str(e)}"

def create_color_preset_album(resolve, album_name: str) -> str:
    """Create a new album for color presets.
    
    Args:
        resolve: DaVinci Resolve object
        album_name: Name for the new album
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Switch to color page
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")
    
    try:
        # Get gallery
        gallery = current_project.GetGallery()
        if not gallery:
            return "Error: Failed to get gallery"
        
        # Check if album already exists
        albums = gallery.GetAlbums()
        
        if albums:
            for a in albums:
                if a.GetName() == album_name:
                    # Return to the original page if we switched
                    if current_page != "color":
                        resolve.OpenPage(current_page)
                    return f"Album '{album_name}' already exists"
        
        # Create a new album
        album = gallery.CreateAlbum(album_name)
        
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        
        if album:
            return f"Successfully created album '{album_name}'"
        else:
            return f"Failed to create album '{album_name}'"
    
    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return f"Error creating album: {str(e)}"

def delete_color_preset_album(resolve, album_name: str) -> str:
    """Delete a color preset album.
    
    Args:
        resolve: DaVinci Resolve object
        album_name: Name of the album to delete
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Switch to color page
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")
    
    try:
        # Get gallery
        gallery = current_project.GetGallery()
        if not gallery:
            return "Error: Failed to get gallery"
        
        # Find the album
        album = None
        albums = gallery.GetAlbums()
        
        if albums:
            for a in albums:
                if a.GetName() == album_name:
                    album = a
                    break
        
        if not album:
            # Return to the original page if we switched
            if current_page != "color":
                resolve.OpenPage(current_page)
            return f"Error: Album '{album_name}' not found"
        
        # Delete the album
        result = gallery.DeleteAlbum(album)
        
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        
        if result:
            return f"Successfully deleted album '{album_name}'"
        else:
            return f"Failed to delete album '{album_name}'"
    
    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return f"Error deleting album: {str(e)}"


# ============================================================
# Phase 4.8: Gallery Extensions
# ============================================================

def delete_stills_from_album(resolve, album_name: str = None,
                              still_labels: List[str] = None) -> str:
    """Delete stills from a gallery album.
    
    Args:
        resolve: DaVinci Resolve instance
        album_name: Album name, uses current album if not specified
        still_labels: List of still labels to delete; if None, deletes all
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
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
            return "No stills in album to delete"
        
        # Filter stills to delete
        stills_to_delete = []
        if still_labels:
            for still in stills:
                label = target_album.GetLabel(still)
                if label in still_labels:
                    stills_to_delete.append(still)
        else:
            stills_to_delete = list(stills)
        
        if not stills_to_delete:
            return "No matching stills found to delete"
        
        # Delete stills
        result = target_album.DeleteStills(stills_to_delete)
        if result:
            return f"Deleted {len(stills_to_delete)} stills from album"
        return "Failed to delete stills"
    except Exception as e:
        return f"Error: {e}"


def get_still_label(resolve, album_name: str = None,
                    still_index: int = 0) -> Dict[str, Any]:
    """Get the label of a still in an album.
    
    Args:
        resolve: DaVinci Resolve instance
        album_name: Album name, uses current album if not specified
        still_index: Index of the still (0-based)
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
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
        if still_index >= len(stills):
            return {"error": f"Still index {still_index} out of range (album has {len(stills)} stills)"}
        
        still = stills[still_index]
        label = target_album.GetLabel(still)
        return {
            "album": gallery.GetAlbumName(target_album),
            "still_index": still_index,
            "label": label
        }
    except Exception as e:
        return {"error": f"Error: {e}"}


def set_still_label(resolve, label: str, album_name: str = None,
                    still_index: int = 0) -> str:
    """Set the label of a still in an album.
    
    Args:
        resolve: DaVinci Resolve instance
        label: New label for the still
        album_name: Album name, uses current album if not specified
        still_index: Index of the still (0-based)
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
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
        if still_index >= len(stills):
            return f"Error: Still index {still_index} out of range"
        
        still = stills[still_index]
        result = target_album.SetLabel(still, label)
        if result:
            return f"Set label to '{label}' for still at index {still_index}"
        return "Failed to set label"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Full Coverage: PowerGrade Albums
# ============================================================

def get_gallery_powergrade_albums(resolve) -> List[Dict[str, Any]]:
    """Get all PowerGrade albums in the gallery.
    
    Args:
        resolve: DaVinci Resolve instance
    """
    if not resolve:
        return [{"error": "Not connected to DaVinci Resolve"}]
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    if not project:
        return [{"error": "No project open"}]
    
    try:
        gallery = project.GetGallery()
        if not gallery:
            return [{"error": "Failed to get gallery"}]
        
        albums = gallery.GetGalleryPowerGradeAlbums() or []
        result = []
        
        for album in albums:
            album_info = {
                "name": gallery.GetAlbumName(album),
                "stills": []
            }
            
            stills = album.GetStills() or []
            for still in stills:
                album_info["stills"].append({
                    "label": album.GetLabel(still)
                })
            
            result.append(album_info)
        
        return result if result else [{"info": "No PowerGrade albums found"}]
    except Exception as e:
        return [{"error": f"Error: {e}"}]


def create_gallery_powergrade_album(resolve) -> Dict[str, Any]:
    """Create a new PowerGrade album in the gallery.
    
    Args:
        resolve: DaVinci Resolve instance
    """
    if not resolve:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    if not project:
        return {"error": "No project open"}
    
    try:
        gallery = project.GetGallery()
        if not gallery:
            return {"error": "Failed to get gallery"}
        
        album = gallery.CreateGalleryPowerGradeAlbum()
        if album:
            return {
                "success": True,
                "album_name": gallery.GetAlbumName(album)
            }
        return {"error": "Failed to create PowerGrade album"}
    except Exception as e:
        return {"error": f"Error: {e}"}
