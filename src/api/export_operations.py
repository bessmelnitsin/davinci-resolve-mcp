"""
DaVinci Resolve Export Operations
"""

import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger("davinci-resolve-mcp.export")

def export_lut(resolve, clip_name: str = None, 
              export_path: str = None, 
              lut_format: str = "Cube", 
              lut_size: str = "33Point") -> str:
    """Export a LUT from the current clip's grade.
    
    Args:
        resolve: DaVinci Resolve object
        clip_name: Name of the clip to export grade from (uses current clip if None)
        export_path: Path to save the LUT file (generated if None)
        lut_format: Format of the LUT. Options: 'Cube', 'Davinci', '3dl', 'Panasonic'
        lut_size: Size of the LUT. Options: '17Point', '33Point', '65Point'
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
        
        # Generate export path if not provided
        if not export_path:
            import tempfile
            clip_name_safe = clip_name if clip_name else "current_clip"
            clip_name_safe = clip_name_safe.replace(' ', '_').replace(':', '-')
            
            extension = ".cube"
            if lut_format.lower() == "davinci":
                extension = ".ilut"
            elif lut_format.lower() == "3dl":
                extension = ".3dl"
            elif lut_format.lower() == "panasonic":
                extension = ".vlut"
                
            export_path = os.path.join(tempfile.gettempdir(), f"{clip_name_safe}_lut{extension}")
        
        # Validate LUT format
        valid_formats = ['Cube', 'Davinci', '3dl', 'Panasonic']
        if lut_format not in valid_formats:
            return f"Error: Invalid LUT format. Must be one of: {', '.join(valid_formats)}"
        
        # Validate LUT size
        valid_sizes = ['17Point', '33Point', '65Point']
        if lut_size not in valid_sizes:
            return f"Error: Invalid LUT size. Must be one of: {', '.join(valid_sizes)}"
        
        # Map format string to numeric value expected by DaVinci Resolve API
        format_map = {
            'Cube': 0,
            'Davinci': 1,
            '3dl': 2,
            'Panasonic': 3
        }
        
        # Map size string to numeric value
        size_map = {
            '17Point': 0,
            '33Point': 1,
            '65Point': 2
        }
        
        # Get current clip
        current_clip = current_timeline.GetCurrentVideoItem()
        if not current_clip:
            return "Error: No clip is currently selected"
        
        # Create a directory for the export path if it doesn't exist
        export_dir = os.path.dirname(export_path)
        if export_dir and not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
        
        # Export the LUT
        colorpage = resolve.GetCurrentPage() == "color"
        if not colorpage:
            resolve.OpenPage("color")
        
        # Access Color page functionality 
        result = current_project.ExportCurrentGradeAsLUT(
            format_map[lut_format], 
            size_map[lut_size], 
            export_path
        )
        
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        
        if result:
            return f"Successfully exported LUT to '{export_path}' in {lut_format} format with {lut_size} size"
        else:
            return f"Failed to export LUT"
    
    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return f"Error exporting LUT: {str(e)}"

def get_lut_formats(resolve) -> Dict[str, Any]:
    """Get available LUT export formats and sizes.
    
    Args:
        resolve: DaVinci Resolve object
    """
    formats = {
        "formats": [
            {
                "name": "Cube",
                "extension": ".cube",
                "description": "Industry standard LUT format supported by most applications"
            },
            {
                "name": "Davinci",
                "extension": ".ilut",
                "description": "DaVinci Resolve's native LUT format"
            },
            {
                "name": "3dl",
                "extension": ".3dl",
                "description": "ASSIMILATE SCRATCH and some Autodesk applications"
            },
            {
                "name": "Panasonic",
                "extension": ".vlut",
                "description": "Panasonic VariCam and other Panasonic cameras"
            }
        ],
        "sizes": [
            {
                "name": "17Point",
                "description": "Smaller file size, less precision (17x17x17)"
            },
            {
                "name": "33Point",
                "description": "Standard size with good balance of precision and file size (33x33x33)"
            },
            {
                "name": "65Point",
                "description": "Highest precision but larger file size (65x65x65)"
            }
        ]
    }
    return formats

def export_all_powergrade_luts(resolve, export_dir: str) -> str:
    """Export all PowerGrade presets as LUT files.
    
    Args:
        resolve: DaVinci Resolve object
        export_dir: Directory to save the exported LUTs
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
        
        # Get PowerGrade album
        powergrade_album = None
        albums = gallery.GetAlbums()
        
        if albums:
            for album in albums:
                if album.GetName() == "PowerGrade":
                    powergrade_album = album
                    break
        
        if not powergrade_album:
            return "Error: PowerGrade album not found"
        
        # Get all stills in the PowerGrade album
        stills = powergrade_album.GetStills()
        if not stills:
            return "Error: No stills found in PowerGrade album"
        
        # Create export directory if it doesn't exist
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
        
        # Export each still as a LUT
        exported_count = 0
        failed_stills = []
        
        for still in stills:
            still_name = still.GetLabel()
            if not still_name:
                still_name = f"PowerGrade_{still.GetUniqueId()}"
            
            # Create safe filename
            safe_name = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in still_name)
            lut_path = os.path.join(export_dir, f"{safe_name}.cube")
            
            # Apply the still to the current clip
            current_timeline = current_project.GetCurrentTimeline()
            current_clip = current_timeline.GetCurrentVideoItem()
            if not current_clip:
                failed_stills.append(f"{still_name} (no clip selected)")
                continue
            
            # Apply the grade from the still
            applied = still.ApplyToClip()
            if not applied:
                failed_stills.append(f"{still_name} (could not apply grade)")
                continue
            
            # Export as LUT
            result = current_project.ExportCurrentGradeAsLUT(0, 1, lut_path)  # Cube format, 33-point
            
            if result:
                exported_count += 1
            else:
                failed_stills.append(f"{still_name} (export failed)")
        
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        
        if failed_stills:
            return f"Exported {exported_count} LUTs to '{export_dir}'. Failed to export: {', '.join(failed_stills)}"
        else:
            return f"Successfully exported all {exported_count} PowerGrade LUTs to '{export_dir}'"
    
    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return f"Error exporting PowerGrade LUTs: {str(e)}"
