#!/usr/bin/env python3
"""
DaVinci Resolve MCP Server
A server that connects to DaVinci Resolve via the Model Context Protocol (MCP)

Version: 1.3.8 - Improved Cursor Integration, Entry Point Standardization
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Union

# Add project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import platform utilities
from src.utils.platform import setup_environment, get_platform, get_resolve_paths

# Setup platform-specific paths and environment variables
paths = get_resolve_paths()
RESOLVE_API_PATH = paths["api_path"]
RESOLVE_LIB_PATH = paths["lib_path"]
RESOLVE_MODULES_PATH = paths["modules_path"]

os.environ["RESOLVE_SCRIPT_API"] = RESOLVE_API_PATH
os.environ["RESOLVE_SCRIPT_LIB"] = RESOLVE_LIB_PATH

# DLL directory fix for Python 3.8+ on Windows
if sys.platform.startswith("win") and hasattr(os, "add_dll_directory"):
    resolve_dir = os.path.dirname(RESOLVE_LIB_PATH)
    if os.path.exists(resolve_dir):
        os.add_dll_directory(resolve_dir)

# Add the module path to Python's path if it's not already there
if RESOLVE_MODULES_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULES_PATH)

# Import MCP
from mcp.server.fastmcp import FastMCP

# Import our utility functions
from src.utils.platform import setup_environment, get_platform, get_resolve_paths
from src.utils.object_inspection import (
    inspect_object,
    get_object_methods,
    get_object_properties,
    print_object_help,
    convert_lua_to_python
)
from src.utils.layout_presets import (
    list_layout_presets,
    save_layout_preset,
    load_layout_preset,
    export_layout_preset,
    import_layout_preset,
    delete_layout_preset
)
from src.utils.app_control import (
    quit_resolve_app,
    get_app_state,
    restart_resolve_app,
    open_project_settings,
    open_preferences
)
from src.utils.cloud_operations import (
    create_cloud_project,
    import_cloud_project,
    restore_cloud_project,
    get_cloud_project_list,
    export_project_to_cloud,
    add_user_to_cloud_project,
    remove_user_from_cloud_project
)
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("davinci-resolve-mcp")

# Log server version and platform
VERSION = "1.3.8"
logger.info(f"Starting DaVinci Resolve MCP Server v{VERSION}")
logger.info(f"Detected platform: {get_platform()}")
logger.info(f"Using Resolve API path: {RESOLVE_API_PATH}")
logger.info(f"Using Resolve library path: {RESOLVE_LIB_PATH}")

# Create MCP server instance
mcp = FastMCP("DaVinciResolveMCP")

# Initialize connection to DaVinci Resolve
try:
    # Direct import from the Modules directory
    sys.path.insert(0, RESOLVE_MODULES_PATH)
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
    if resolve:
        logger.info(f"Connected to DaVinci Resolve: {resolve.GetProductName()} {resolve.GetVersionString()}")
    else:
        logger.error("Failed to get Resolve object. Is DaVinci Resolve running?")
except ImportError as e:
    logger.error(f"Failed to import DaVinciResolveScript: {str(e)}")
    logger.error("Check that DaVinci Resolve is installed and running.")
    logger.error(f"RESOLVE_SCRIPT_API: {RESOLVE_API_PATH}")
    logger.error(f"RESOLVE_SCRIPT_LIB: {RESOLVE_LIB_PATH}")
    logger.error(f"RESOLVE_MODULES_PATH: {RESOLVE_MODULES_PATH}")
    logger.error(f"sys.path: {sys.path}")
    resolve = None
except Exception as e:
    logger.error(f"Unexpected error initializing Resolve: {str(e)}")
    resolve = None

# New Modules for v2 Workflow
from src.api.whisper_node import transcribe_with_whisper_node
from src.api.jump_cut import generate_jump_cut_edits
from src.api.smart_editing import create_vertical_timeline, create_trendy_timeline as create_trendy_impl
from src.api.ai_director import prepare_transcription_for_ai
from src.api import (
    transcription_operations,
    keyframe_operations,
    gallery_operations,
    export_operations
)

# ------------------
# MCP Tools/Resources
# ------------------

@mcp.tool()
def transcribe_clip_to_cache(clip_name: str, model_size: str = "large-v3", force_retranscribe: bool = False) -> str:
    """Run Whisper transcription and save result to a .json file next to the media.
    
    Args:
        clip_name: Name of the clip to transcribe
        model_size: Whisper model size
        force_retranscribe: If True, ignore existing cache
    """
    return transcription_operations.transcribe_clip_to_cache(resolve, clip_name, model_size, force_retranscribe)


@mcp.tool()
def get_cached_transcription(clip_name: str) -> str:
    """Read transcription from cache without running Whisper.
    
    Args:
        clip_name: Name of the clip in Media Pool
    """
    return transcription_operations.get_cached_transcription(resolve, clip_name)

@mcp.tool()
def get_clip_transcription(clip_name: str, model_size: str = "large-v3") -> str:
    """Helper that transcribes OR loads from cache and returns text.
    """
    return transcription_operations.get_clip_transcription(resolve, clip_name, model_size)

@mcp.tool()
def assemble_viral_reels(clip_name: str, segments: List[Dict[str, Any]]) -> str:
    """Assemble vertical Reel timelines from selected segments.
    
    Args:
        clip_name: Source clip name
        segments: List of dicts with {"start": 0.0, "end": 10.0, "title": "Optional Name"}
    """
    if resolve is None: return "Error: Not connected"
    
    results = []
    for i, seg in enumerate(segments):
        title = seg.get("title", f"Reel_{i+1}")
        edits = [{
            "clip_name": clip_name,
            "start_time": seg["start"],
            "end_time": seg["end"]
        }]
        
        # Use create_vertical_timeline for each Reel
        res = create_vertical_timeline(resolve, edits, f"{title}_{clip_name}")
        results.append(res)
        
    return "\n".join(results)

@mcp.tool()
def create_trendy_timeline(edits: List[Dict[str, Any]], timeline_name: str = "Trendy Cut") -> str:
    """Create a new timeline structured with selected clips and gaps.
    
    Args:
         edits: List of edits with clip_name, start_time, end_time
         timeline_name: Name of the timeline to create
    """
    return create_trendy_impl(resolve, edits, timeline_name)

@mcp.tool()
def smart_jump_cut(clip_name: str, silence_threshold: float = 0.5) -> str:
    """Automatically remove silence from a clip and create a new timeline.
    
    Args:
        clip_name: Name of the clip in Media Pool
        silence_threshold: Silence duration to cut (default 0.5s)
    """
    if resolve is None: return "Error: Not connected"
    
    from src.api.media_operations import get_all_media_pool_clips
    project = resolve.GetProjectManager().GetCurrentProject()
    media_pool = project.GetMediaPool()
    clips = get_all_media_pool_clips(media_pool)
    target_clip = next((c for c in clips if c.GetName() == clip_name), None)
    
    if not target_clip: return f"Error: Clip '{clip_name}' not found"
    
    # Try to get absolute path from clip properties (Metalogging etc.)
    props = target_clip.GetClipProperty()
    file_path = props.get("File Path")
    
    if not file_path:
        return "Error: Could not determine file path of the clip for Whisper."
    
    # Node B: Transcribe
    logger.info(f"Transcribing {clip_name} with Whisper Node B...")
    whisper_data = transcribe_with_whisper_node(file_path)
    
    if "error" in whisper_data:
        return f"Whisper failed: {whisper_data['error']}"
        
    # Node C: Logic
    edits = generate_jump_cut_edits(whisper_data, clip_name, silence_threshold)
    
    # Node A: Assembly
    if not edits: return "No speech detected or entire clip is silence."
    
    from src.api.smart_editing import create_trendy_timeline
    result = create_trendy_timeline(resolve, edits, f"JumpCut_{clip_name}")
    return result

@mcp.tool()
def viral_reels_factory(clip_name: str) -> str:
    """Generate 1080x1920 Reels from a source clip.
    
    Currently generates segments based on detected speech.
    """
    if resolve is None: return "Error: Not connected"
    
    from src.api.media_operations import get_all_media_pool_clips
    project = resolve.GetProjectManager().GetCurrentProject()
    media_pool = project.GetMediaPool()
    clips = get_all_media_pool_clips(media_pool)
    target_clip = next((c for c in clips if c.GetName() == clip_name), None)
    
    if not target_clip: return f"Error: Clip '{clip_name}' not found"
    
    file_path = target_clip.GetClipProperty("File Path")
    whisper_data = transcribe_with_whisper_node(file_path)
    
    if "error" in whisper_data: return f"Whisper failed: {whisper_data['error']}"
    
    # Logic: Pick longer segments (3-8s) for 'viral' feel
    from src.api.jump_cut import generate_jump_cut_edits
    edits = generate_jump_cut_edits(whisper_data, clip_name, silence_threshold=2.0)
    
    # Assembly: Vertical
    result = create_vertical_timeline(resolve, edits, f"Reels_{clip_name}")
    return result

@mcp.resource("resolve://version")
def get_resolve_version() -> str:
    """Get DaVinci Resolve version information."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    return f"{resolve.GetProductName()} {resolve.GetVersionString()}"

@mcp.resource("resolve://current-page")
def get_current_page() -> str:
    """Get the current page open in DaVinci Resolve (Edit, Color, Fusion, etc.)."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    return resolve.GetCurrentPage()

@mcp.tool()
def switch_page(page: str) -> str:
    """Switch to a specific page in DaVinci Resolve.
    
    Args:
        page: The page to switch to. Options: 'media', 'cut', 'edit', 'fusion', 'color', 'fairlight', 'deliver'
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    valid_pages = ['media', 'cut', 'edit', 'fusion', 'color', 'fairlight', 'deliver']
    page = page.lower()
    
    if page not in valid_pages:
        return f"Error: Invalid page name. Must be one of: {', '.join(valid_pages)}"
    
    result = resolve.OpenPage(page)
    if result:
        return f"Successfully switched to {page} page"
    else:
        return f"Failed to switch to {page} page"

# ------------------
# Project Management
# ------------------

@mcp.resource("resolve://projects")
def list_projects() -> List[str]:
    """List all available projects in the current database."""
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
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "No project currently open"
    
    return current_project.GetName()

@mcp.resource("resolve://project-settings")
def get_project_settings() -> Dict[str, Any]:
    """Get all project settings from the current project."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    try:
        # Get all settings
        return current_project.GetSetting('')
    except Exception as e:
        return {"error": f"Failed to get project settings: {str(e)}"}

@mcp.resource("resolve://project-setting/{setting_name}")
def get_project_setting(setting_name: str) -> Dict[str, Any]:
    """Get a specific project setting by name.
    
    Args:
        setting_name: The specific setting to retrieve.
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    try:
        # Get specific setting
        value = current_project.GetSetting(setting_name)
        return {setting_name: value}
    except Exception as e:
        return {"error": f"Failed to get project setting '{setting_name}': {str(e)}"}

@mcp.tool()
def set_project_setting(setting_name: str, setting_value: Any) -> str:
    """Set a project setting to the specified value.
    
    Args:
        setting_name: The name of the setting to change
        setting_value: The new value for the setting (can be string, integer, float, or boolean)
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    try:
        # Convert setting_value to string if it's not already
        if not isinstance(setting_value, str):
            setting_value = str(setting_value)
            
        # Try to determine if this should be a numeric value
        # DaVinci Resolve sometimes expects numeric values for certain settings
        try:
            # Check if it's a number in string form
            if setting_value.isdigit() or (setting_value.startswith('-') and setting_value[1:].isdigit()):
                # It's an integer
                numeric_value = int(setting_value)
                # Try with numeric value first
                if current_project.SetSetting(setting_name, numeric_value):
                    return f"Successfully set project setting '{setting_name}' to numeric value {numeric_value}"
            elif '.' in setting_value and setting_value.replace('.', '', 1).replace('-', '', 1).isdigit():
                # It's a float
                numeric_value = float(setting_value)
                # Try with float value
                if current_project.SetSetting(setting_name, numeric_value):
                    return f"Successfully set project setting '{setting_name}' to numeric value {numeric_value}"
        except (ValueError, TypeError):
            # Not a number or conversion failed, continue with string value
            pass
            
        # Fall back to string value if numeric didn't work or wasn't applicable
        result = current_project.SetSetting(setting_name, setting_value)
        if result:
            return f"Successfully set project setting '{setting_name}' to '{setting_value}'"
        else:
            return f"Failed to set project setting '{setting_name}'"
    except Exception as e:
        return f"Error setting project setting: {str(e)}"

@mcp.tool()
def open_project(name: str) -> str:
    """Open a project by name.
    
    Args:
        name: The name of the project to open
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
    """Save the current project.
    
    Note that DaVinci Resolve typically auto-saves projects, so this may not be necessary.
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    project_name = current_project.GetName()
    success = False
    error_message = None
    
    # Try multiple approaches to save the project
    try:
        # Method 1: Try direct save method if available
        try:
            if hasattr(current_project, "SaveProject"):
                result = current_project.SaveProject()
                if result:
                    logger.info(f"Project '{project_name}' saved using SaveProject method")
                    success = True
        except Exception as e:
            logger.error(f"Error in SaveProject method: {str(e)}")
            error_message = str(e)
            
        # Method 2: Try project manager save method
        if not success:
            try:
                if hasattr(project_manager, "SaveProject"):
                    result = project_manager.SaveProject()
                    if result:
                        logger.info(f"Project '{project_name}' saved using ProjectManager.SaveProject method")
                        success = True
            except Exception as e:
                logger.error(f"Error in ProjectManager.SaveProject method: {str(e)}")
                if not error_message:
                    error_message = str(e)
        
        # Method 3: Try the export method as a backup approach
        if not success:
            try:
                # Get a temporary file path in the same location as other project files
                import tempfile
                import os
                temp_dir = tempfile.gettempdir()
                temp_file = os.path.join(temp_dir, f"{project_name}_temp.drp")
                
                # Try to export the project, which should trigger a save
                result = project_manager.ExportProject(project_name, temp_file)
                if result:
                    logger.info(f"Project '{project_name}' saved via temporary export to {temp_file}")
                    # Try to clean up temp file
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except:
                        pass
                    success = True
            except Exception as e:
                logger.error(f"Error in export method: {str(e)}")
                if not error_message:
                    error_message = str(e)
                    
        # If all else fails, rely on auto-save
        if not success:
            return f"Automatic save likely in effect for project '{project_name}'. Manual save attempts failed: {error_message if error_message else 'Unknown error'}"
        else:
            return f"Successfully saved project '{project_name}'"
            
    except Exception as e:
        logger.error(f"Error saving project: {str(e)}")
        return f"Error saving project: {str(e)}"

@mcp.tool()
def close_project() -> str:
    """Close the current project.
    
    This closes the current project without saving. If you need to save, use the save_project function first.
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    project_name = current_project.GetName()
    
    # Close the project
    try:
        result = project_manager.CloseProject(current_project)
        if result:
            logger.info(f"Project '{project_name}' closed successfully")
            return f"Successfully closed project '{project_name}'"
        else:
            logger.error(f"Failed to close project '{project_name}'")
            return f"Failed to close project '{project_name}'"
    except Exception as e:
        logger.error(f"Error closing project: {str(e)}")
        return f"Error closing project: {str(e)}"

# ------------------
# Timeline Operations
# ------------------

@mcp.resource("resolve://timelines")
def list_timelines() -> List[str]:
    """List all timelines in the current project."""
    logger.info("Received request to list timelines")
    
    if resolve is None:
        logger.error("Not connected to DaVinci Resolve")
        return ["Error: Not connected to DaVinci Resolve"]
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        logger.error("Failed to get Project Manager")
        return ["Error: Failed to get Project Manager"]
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        logger.error("No project currently open")
        return ["Error: No project currently open"]
    
    timeline_count = current_project.GetTimelineCount()
    logger.info(f"Timeline count: {timeline_count}")
    
    timelines = []
    
    for i in range(1, timeline_count + 1):
        timeline = current_project.GetTimelineByIndex(i)
        if timeline:
            timeline_name = timeline.GetName()
            timelines.append(timeline_name)
            logger.info(f"Found timeline {i}: {timeline_name}")
    
    if not timelines:
        logger.info("No timelines found in the current project")
        return ["No timelines found in the current project"]
    
    logger.info(f"Returning {len(timelines)} timelines: {', '.join(timelines)}")
    return timelines

@mcp.resource("resolve://current-timeline")
def get_current_timeline() -> Dict[str, Any]:
    """Get information about the current timeline."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return {"error": "No timeline currently active"}
    
    # Get basic timeline information
    result = {
        "name": current_timeline.GetName(),
        "fps": current_timeline.GetSetting("timelineFrameRate"),
        "resolution": {
            "width": current_timeline.GetSetting("timelineResolutionWidth"),
            "height": current_timeline.GetSetting("timelineResolutionHeight")
        },
        "duration": current_timeline.GetEndFrame() - current_timeline.GetStartFrame() + 1
    }
    
    return result

@mcp.resource("resolve://timeline-tracks/{timeline_name}")
def get_timeline_tracks(timeline_name: str = None) -> Dict[str, Any]:
    """Get the track structure of a timeline.
    
    Args:
        timeline_name: Optional name of the timeline to get tracks from. Uses current timeline if None.
    """
    from src.api.timeline_operations import get_timeline_tracks as get_tracks_func
    return get_tracks_func(resolve, timeline_name)

@mcp.tool()
def create_timeline(name: str) -> str:
    """Create a new timeline with the given name.
    
    Args:
        name: The name for the new timeline
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not name:
        return "Error: Timeline name cannot be empty"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    timeline = media_pool.CreateEmptyTimeline(name)
    if timeline:
        return f"Successfully created timeline '{name}'"
    else:
        return f"Failed to create timeline '{name}'"

@mcp.tool()
def create_empty_timeline(name: str, 
                       frame_rate: str = None, 
                       resolution_width: int = None, 
                       resolution_height: int = None,
                       start_timecode: str = None,
                       video_tracks: int = None,
                       audio_tracks: int = None) -> str:
    """Create a new timeline with the given name and custom settings.
    
    Args:
        name: The name for the new timeline
        frame_rate: Optional frame rate (e.g. "24", "29.97", "30", "60")
        resolution_width: Optional width in pixels (e.g. 1920)
        resolution_height: Optional height in pixels (e.g. 1080)
        start_timecode: Optional start timecode (e.g. "01:00:00:00")
        video_tracks: Optional number of video tracks (Default is project setting)
        audio_tracks: Optional number of audio tracks (Default is project setting)
    """
    from src.api.timeline_operations import create_empty_timeline as create_empty_timeline_func
    return create_empty_timeline_func(resolve, name, frame_rate, resolution_width, 
                                    resolution_height, start_timecode, 
                                    video_tracks, audio_tracks)

@mcp.tool()
def delete_timeline(name: str) -> str:
    """Delete a timeline by name.
    
    Args:
        name: The name of the timeline to delete
    """
    from src.api.timeline_operations import delete_timeline as delete_timeline_func
    return delete_timeline_func(resolve, name)

@mcp.tool()
def set_current_timeline(name: str) -> str:
    """Switch to a timeline by name.
    
    Args:
        name: The name of the timeline to set as current
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not name:
        return "Error: Timeline name cannot be empty"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Find the timeline by name
    timeline_count = current_project.GetTimelineCount()
    for i in range(1, timeline_count + 1):
        timeline = current_project.GetTimelineByIndex(i)
        if timeline and timeline.GetName() == name:
            result = current_project.SetCurrentTimeline(timeline)
            if result:
                return f"Successfully switched to timeline '{name}'"
            else:
                return f"Failed to switch to timeline '{name}'"
    
    return f"Error: Timeline '{name}' not found"

@mcp.tool()
def add_marker(frame: int = None, color: str = "Blue", note: str = "") -> str:
    """Add a marker at the specified frame in the current timeline.
    
    Args:
        frame: The frame number to add the marker at (defaults to current position if None)
        color: The marker color (Blue, Cyan, Green, Yellow, Red, Pink, Purple, Fuchsia, Rose, Lavender, Sky, Mint, Lemon, Sand, Cocoa, Cream)
        note: Text note to add to the marker
    """
    from src.api.timeline_operations import add_marker as add_marker_func
    return add_marker_func(resolve, frame, color, note)

# ------------------
# Media Pool Operations
# ------------------

@mcp.resource("resolve://media-pool-clips")
def list_media_pool_clips() -> List[Dict[str, Any]]:
    """List all clips in the media pool."""
    from src.api.media_operations import list_media_pool_clips as list_clips_func
    return list_clips_func(resolve)

@mcp.tool()
def import_media(file_path: str) -> str:
    """Import media file into the current project's media pool.
    
    Args:
        file_path: The path to the media file to import
    """
    from src.api.media_operations import import_media as import_media_func
    return import_media_func(resolve, file_path)

@mcp.tool()
def delete_media(clip_name: str) -> str:
    """Delete a media clip from the media pool by name.
    
    Args:
        clip_name: Name of the clip to delete
    """
    from src.api.media_operations import delete_media as delete_media_func
    return delete_media_func(resolve, clip_name)

@mcp.tool()
def move_media_to_bin(clip_name: str, bin_name: str) -> str:
    """Move a media clip to a specific bin in the media pool.
    
    Args:
        clip_name: Name of the clip to move
        bin_name: Name of the target bin
    """
    from src.api.media_operations import move_media_to_bin as move_media_func
    return move_media_func(resolve, clip_name, bin_name)

@mcp.tool()
def auto_sync_audio(clip_names: List[str], sync_method: str = "waveform", 
                   append_mode: bool = False, target_bin: str = None) -> str:
    """Sync audio between clips with customizable settings.
    
    Args:
        clip_names: List of clip names to sync
        sync_method: Method to use for synchronization - 'waveform' or 'timecode'
        append_mode: Whether to append the audio or replace it
        target_bin: Optional bin to move synchronized clips to
    """
    from src.api.media_operations import auto_sync_audio as auto_sync_audio_func
    return auto_sync_audio_func(resolve, clip_names, sync_method, append_mode, target_bin)

@mcp.tool()
def unlink_clips(clip_names: List[str]) -> str:
    """Unlink specified clips, disconnecting them from their media files.
    
    Args:
        clip_names: List of clip names to unlink
    """
    from src.api.media_operations import unlink_clips as unlink_clips_func
    return unlink_clips_func(resolve, clip_names)

@mcp.tool()
def relink_clips(clip_names: List[str], media_paths: List[str] = None, 
                folder_path: str = None, recursive: bool = False) -> str:
    """Relink specified clips to their media files.
    
    Args:
        clip_names: List of clip names to relink
        media_paths: Optional list of specific media file paths to use for relinking
        folder_path: Optional folder path to search for media files
        recursive: Whether to search the folder path recursively
    """
    from src.api.media_operations import relink_clips as relink_clips_func
    return relink_clips_func(resolve, clip_names, media_paths, folder_path, recursive)

@mcp.tool()
def create_sub_clip(clip_name: str, start_frame: int, end_frame: int, 
                   sub_clip_name: str = None, bin_name: str = None) -> str:
    """Create a subclip from the specified clip using in and out points.
    
    Args:
        clip_name: Name of the source clip
        start_frame: Start frame (in point)
        end_frame: End frame (out point)
        sub_clip_name: Optional name for the subclip (defaults to original name with '_subclip')
        bin_name: Optional bin to place the subclip in
    """
    from api.media_operations import create_sub_clip as create_sub_clip_func
    return create_sub_clip_func(resolve, clip_name, start_frame, end_frame, sub_clip_name, bin_name)

@mcp.tool()
def create_bin(name: str) -> str:
    """Create a new bin/folder in the media pool.
    
    Args:
        name: The name for the new bin
    """
    from api.media_operations import create_bin as create_bin_func
    return create_bin_func(resolve, name)

@mcp.resource("resolve://media-pool-bins")
def list_media_pool_bins() -> List[Dict[str, Any]]:
    """List all bins/folders in the media pool."""
    from api.media_operations import list_bins as list_bins_func
    return list_bins_func(resolve)

@mcp.resource("resolve://media-pool-bin/{bin_name}")
def get_media_pool_bin_contents(bin_name: str) -> List[Dict[str, Any]]:
    """Get contents of a specific bin/folder in the media pool.
    
    Args:
        bin_name: The name of the bin to get contents from. Use 'Master' for the root folder.
    """
    from api.media_operations import get_bin_contents as get_bin_contents_func
    return get_bin_contents_func(resolve, bin_name)

@mcp.resource("resolve://timeline-clips")
def list_timeline_clips() -> List[Dict[str, Any]]:
    """List all clips in the current timeline."""
    if resolve is None:
        return [{"error": "Not connected to DaVinci Resolve"}]
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return [{"error": "Failed to get Project Manager"}]
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return [{"error": "No project currently open"}]
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return [{"error": "No timeline currently active"}]
    
    try:
        # Get all tracks in the timeline
        # Video tracks are 1-based index (1 is first track)
        video_track_count = current_timeline.GetTrackCount("video")
        audio_track_count = current_timeline.GetTrackCount("audio")
        
        clips = []
        
        # Process video tracks
        for track_index in range(1, video_track_count + 1):
            track_items = current_timeline.GetItemListInTrack("video", track_index)
            if track_items:
                for item in track_items:
                    clips.append({
                        "name": item.GetName(),
                        "type": "video",
                        "track": track_index,
                        "start_frame": item.GetStart(),
                        "end_frame": item.GetEnd(),
                        "duration": item.GetDuration()
                    })
        
        # Process audio tracks
        for track_index in range(1, audio_track_count + 1):
            track_items = current_timeline.GetItemListInTrack("audio", track_index)
            if track_items:
                for item in track_items:
                    clips.append({
                        "name": item.GetName(),
                        "type": "audio",
                        "track": track_index,
                        "start_frame": item.GetStart(),
                        "end_frame": item.GetEnd(),
                        "duration": item.GetDuration()
                    })
        
        if not clips:
            return [{"info": "No clips found in the current timeline"}]
        
        return clips
    except Exception as e:
        return [{"error": f"Error listing timeline clips: {str(e)}"}]

@mcp.tool()
def list_timelines_tool() -> List[str]:
    """List all timelines in the current project as a tool."""
    logger.info("Received request to list timelines via tool")
    return list_timelines()

@mcp.tool()
def add_clip_to_timeline(clip_name: str, timeline_name: str = None) -> str:
    """Add a media pool clip to the timeline.
    
    Args:
        clip_name: Name of the clip in the media pool
        timeline_name: Optional timeline to target (uses current if not specified)
    """
    from api.media_operations import add_clip_to_timeline as add_clip_func
    return add_clip_func(resolve, clip_name, timeline_name)

# ------------------
# Color Page Operations
# ------------------

@mcp.resource("resolve://color/current-node")
def get_current_color_node() -> Dict[str, Any]:
    """Get information about the current node in the color page."""
    from api.color_operations import get_current_node as get_node_func
    return get_node_func(resolve)

@mcp.resource("resolve://color/wheels/{node_index}")
def get_color_wheel_params(node_index: int = None) -> Dict[str, Any]:
    """Get color wheel parameters for a specific node.
    
    Args:
        node_index: Index of the node to get color wheels from (uses current node if None)
    """
    from api.color_operations import get_color_wheels as get_wheels_func
    return get_wheels_func(resolve, node_index)

@mcp.tool()
def apply_lut(lut_path: str, node_index: int = None) -> str:
    """Apply a LUT to a node in the color page.
    
    Args:
        lut_path: Path to the LUT file to apply
        node_index: Index of the node to apply the LUT to (uses current node if None)
    """
    from api.color_operations import apply_lut as apply_lut_func
    return apply_lut_func(resolve, lut_path, node_index)

@mcp.tool()
def set_color_wheel_param(wheel: str, param: str, value: float, node_index: int = None) -> str:
    """Set a color wheel parameter for a node.
    
    Args:
        wheel: Which color wheel to adjust ('lift', 'gamma', 'gain', 'offset')
        param: Which parameter to adjust ('red', 'green', 'blue', 'master')
        value: The value to set (typically between -1.0 and 1.0)
        node_index: Index of the node to set parameter for (uses current node if None)
    """
    from api.color_operations import set_color_wheel_param as set_param_func
    return set_param_func(resolve, wheel, param, value, node_index)

@mcp.tool()
def add_node(node_type: str = "serial", label: str = None) -> str:
    """Add a new node to the current grade in the color page.
    
    Args:
        node_type: Type of node to add. Options: 'serial', 'parallel', 'layer'
        label: Optional label/name for the new node
    """
    from api.color_operations import add_node as add_node_func
    return add_node_func(resolve, node_type, label)

@mcp.tool()
def copy_grade(source_clip_name: str = None, target_clip_name: str = None, mode: str = "full") -> str:
    """Copy a grade from one clip to another in the color page.
    
    Args:
        source_clip_name: Name of the source clip to copy grade from (uses current clip if None)
        target_clip_name: Name of the target clip to apply grade to (uses current clip if None)
        mode: What to copy - 'full' (entire grade), 'current_node', or 'all_nodes'
    """
    from api.color_operations import copy_grade as copy_grade_func
    return copy_grade_func(resolve, source_clip_name, target_clip_name, mode)

# ------------------
# Delivery Page Operations
# ------------------

@mcp.resource("resolve://delivery/render-presets")
def get_render_presets() -> List[Dict[str, Any]]:
    """Get all available render presets in the current project."""
    from api.delivery_operations import get_render_presets as get_presets_func
    return get_presets_func(resolve)

@mcp.tool()
def add_to_render_queue(preset_name: str, timeline_name: str = None, use_in_out_range: bool = False) -> Dict[str, Any]:
    """Add a timeline to the render queue with the specified preset.
    
    Args:
        preset_name: Name of the render preset to use
        timeline_name: Name of the timeline to render (uses current if None)
        use_in_out_range: Whether to render only the in/out range instead of entire timeline
    """
    from api.delivery_operations import add_to_render_queue as add_queue_func
    return add_queue_func(resolve, preset_name, timeline_name, use_in_out_range)

@mcp.tool()
def start_render() -> Dict[str, Any]:
    """Start rendering the jobs in the render queue."""
    from api.delivery_operations import start_render as start_render_func
    return start_render_func(resolve)

@mcp.resource("resolve://delivery/render-queue/status")
def get_render_queue_status() -> Dict[str, Any]:
    """Get the status of jobs in the render queue."""
    from api.delivery_operations import get_render_queue_status as get_status_func
    return get_status_func(resolve)

@mcp.tool()
def clear_render_queue() -> Dict[str, Any]:
    """Clear all jobs from the render queue."""
    from api.delivery_operations import clear_render_queue as clear_queue_func
    return clear_queue_func(resolve)

@mcp.tool()
def link_proxy_media(clip_name: str, proxy_file_path: str) -> str:
    """Link a proxy media file to a clip.
    
    Args:
        clip_name: Name of the clip to link proxy to
        proxy_file_path: Path to the proxy media file
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the clip by name
    clips = get_all_media_pool_clips(media_pool)
    target_clip = None
    
    for clip in clips:
        if clip.GetName() == clip_name:
            target_clip = clip
            break
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    # Check if file exists
    if not os.path.exists(proxy_file_path):
        return f"Error: Proxy file '{proxy_file_path}' does not exist"
    
    try:
        result = target_clip.LinkProxyMedia(proxy_file_path)
        if result:
            return f"Successfully linked proxy media '{proxy_file_path}' to clip '{clip_name}'"
        else:
            return f"Failed to link proxy media to clip '{clip_name}'"
    except Exception as e:
        return f"Error linking proxy media: {str(e)}"

@mcp.tool()
def unlink_proxy_media(clip_name: str) -> str:
    """Unlink proxy media from a clip.
    
    Args:
        clip_name: Name of the clip to unlink proxy from
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the clip by name
    clips = get_all_media_pool_clips(media_pool)
    target_clip = None
    
    for clip in clips:
        if clip.GetName() == clip_name:
            target_clip = clip
            break
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    try:
        result = target_clip.UnlinkProxyMedia()
        if result:
            return f"Successfully unlinked proxy media from clip '{clip_name}'"
        else:
            return f"Failed to unlink proxy media from clip '{clip_name}'"
    except Exception as e:
        return f"Error unlinking proxy media: {str(e)}"

@mcp.tool()
def replace_clip(clip_name: str, replacement_path: str) -> str:
    """Replace a clip with another media file.
    
    Args:
        clip_name: Name of the clip to be replaced
        replacement_path: Path to the replacement media file
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the clip by name
    clips = get_all_media_pool_clips(media_pool)
    target_clip = None
    
    for clip in clips:
        if clip.GetName() == clip_name:
            target_clip = clip
            break
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    # Check if file exists
    if not os.path.exists(replacement_path):
        return f"Error: Replacement file '{replacement_path}' does not exist"
    
    try:
        result = target_clip.ReplaceClip(replacement_path)
        if result:
            return f"Successfully replaced clip '{clip_name}' with '{replacement_path}'"
        else:
            return f"Failed to replace clip '{clip_name}'"
    except Exception as e:
        return f"Error replacing clip: {str(e)}"

@mcp.tool()
def transcribe_audio(clip_name: str, language: str = "en-US") -> str:
    """Transcribe audio for a clip.
    
    Args:
        clip_name: Name of the clip to transcribe
        language: Language code for transcription (default: en-US)
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the clip by name
    clips = get_all_media_pool_clips(media_pool)
    target_clip = None
    
    for clip in clips:
        if clip.GetName() == clip_name:
            target_clip = clip
            break
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    try:
        result = target_clip.TranscribeAudio(language)
        if result:
            return f"Successfully started audio transcription for clip '{clip_name}' in language '{language}'"
        else:
            return f"Failed to start audio transcription for clip '{clip_name}'"
    except Exception as e:
        return f"Error during audio transcription: {str(e)}"

@mcp.tool()
def clear_transcription(clip_name: str) -> str:
    """Clear audio transcription for a clip.
    
    Args:
        clip_name: Name of the clip to clear transcription from
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the clip by name
    clips = get_all_media_pool_clips(media_pool)
    target_clip = None
    
    for clip in clips:
        if clip.GetName() == clip_name:
            target_clip = clip
            break
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    try:
        result = target_clip.ClearTranscription()
        if result:
            return f"Successfully cleared audio transcription for clip '{clip_name}'"
        else:
            return f"Failed to clear audio transcription for clip '{clip_name}'"
    except Exception as e:
        return f"Error clearing audio transcription: {str(e)}"

# Utility function to get all clips from the media pool (recursively)
def get_all_media_pool_clips(media_pool):
    """Get all clips from media pool recursively including subfolders."""
    clips = []
    root_folder = media_pool.GetRootFolder()
    
    def process_folder(folder):
        folder_clips = folder.GetClipList()
        if folder_clips:
            clips.extend(folder_clips)
        
        sub_folders = folder.GetSubFolderList()
        for sub_folder in sub_folders:
            process_folder(sub_folder)
    
    process_folder(root_folder)
    return clips

@mcp.tool()
def export_folder(folder_name: str, export_path: str, export_type: str = "DRB") -> str:
    """Export a folder to a DRB file or other format.
    
    Args:
        folder_name: Name of the folder to export
        export_path: Path to save the exported file
        export_type: Export format (DRB is default and currently the only supported option)
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the folder by name
    target_folder = None
    root_folder = media_pool.GetRootFolder()
    
    if folder_name.lower() == "root" or folder_name.lower() == "master":
        target_folder = root_folder
    else:
        # Search for the folder by name
        folders = get_all_media_pool_folders(media_pool)
        for folder in folders:
            if folder.GetName() == folder_name:
                target_folder = folder
                break
    
    if not target_folder:
        return f"Error: Folder '{folder_name}' not found in Media Pool"
    
    # Check if directory exists, create if not
    export_dir = os.path.dirname(export_path)
    if not os.path.exists(export_dir) and export_dir:
        try:
            os.makedirs(export_dir)
        except Exception as e:
            return f"Error creating directory for export: {str(e)}"
    
    # Export the folder
    try:
        result = target_folder.Export(export_path)
        if result:
            return f"Successfully exported folder '{folder_name}' to '{export_path}'"
        else:
            return f"Failed to export folder '{folder_name}'"
    except Exception as e:
        return f"Error exporting folder: {str(e)}"

@mcp.tool()
def transcribe_folder_audio(folder_name: str, language: str = "en-US") -> str:
    """Transcribe audio for all clips in a folder.
    
    Args:
        folder_name: Name of the folder containing clips to transcribe
        language: Language code for transcription (default: en-US)
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the folder by name
    target_folder = None
    root_folder = media_pool.GetRootFolder()
    
    if folder_name.lower() == "root" or folder_name.lower() == "master":
        target_folder = root_folder
    else:
        # Search for the folder by name
        folders = get_all_media_pool_folders(media_pool)
        for folder in folders:
            if folder.GetName() == folder_name:
                target_folder = folder
                break
    
    if not target_folder:
        return f"Error: Folder '{folder_name}' not found in Media Pool"
    
    # Transcribe audio in the folder
    try:
        result = target_folder.TranscribeAudio(language)
        if result:
            return f"Successfully started audio transcription for folder '{folder_name}' in language '{language}'"
        else:
            return f"Failed to start audio transcription for folder '{folder_name}'"
    except Exception as e:
        return f"Error during audio transcription: {str(e)}"

@mcp.tool()
def clear_folder_transcription(folder_name: str) -> str:
    """Clear audio transcription for all clips in a folder.
    
    Args:
        folder_name: Name of the folder to clear transcriptions from
    """
    return transcription_operations.clear_folder_transcription(resolve, folder_name)



# ------------------
# Cache Management
# ------------------

@mcp.resource("resolve://cache/settings")
def get_cache_settings() -> Dict[str, Any]:
    """Get current cache settings from the project."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    try:
        # Get all cache-related settings
        settings = {}
        cache_keys = [
            "CacheMode", 
            "CacheClipMode",
            "OptimizedMediaMode",
            "ProxyMode", 
            "ProxyQuality",
            "TimelineCacheMode",
            "LocalCachePath",
            "NetworkCachePath"
        ]
        
        for key in cache_keys:
            value = current_project.GetSetting(key)
            settings[key] = value
            
        return settings
    except Exception as e:
        return {"error": f"Failed to get cache settings: {str(e)}"}

@mcp.tool()
def set_cache_mode(mode: str) -> str:
    """Set cache mode for the current project.
    
    Args:
        mode: Cache mode to set. Options: 'auto', 'on', 'off'
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Validate mode
    valid_modes = ["auto", "on", "off"]
    mode = mode.lower()
    if mode not in valid_modes:
        return f"Error: Invalid cache mode. Must be one of: {', '.join(valid_modes)}"
    
    # Convert mode to API value
    mode_map = {
        "auto": "0",
        "on": "1",
        "off": "2"
    }
    
    try:
        result = current_project.SetSetting("CacheMode", mode_map[mode])
        if result:
            return f"Successfully set cache mode to '{mode}'"
        else:
            return f"Failed to set cache mode to '{mode}'"
    except Exception as e:
        return f"Error setting cache mode: {str(e)}"

@mcp.tool()
def set_optimized_media_mode(mode: str) -> str:
    """Set optimized media mode for the current project.
    
    Args:
        mode: Optimized media mode to set. Options: 'auto', 'on', 'off'
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Validate mode
    valid_modes = ["auto", "on", "off"]
    mode = mode.lower()
    if mode not in valid_modes:
        return f"Error: Invalid optimized media mode. Must be one of: {', '.join(valid_modes)}"
    
    # Convert mode to API value
    mode_map = {
        "auto": "0",
        "on": "1",
        "off": "2"
    }
    
    try:
        result = current_project.SetSetting("OptimizedMediaMode", mode_map[mode])
        if result:
            return f"Successfully set optimized media mode to '{mode}'"
        else:
            return f"Failed to set optimized media mode to '{mode}'"
    except Exception as e:
        return f"Error setting optimized media mode: {str(e)}"

@mcp.tool()
def set_proxy_mode(mode: str) -> str:
    """Set proxy media mode for the current project.
    
    Args:
        mode: Proxy mode to set. Options: 'auto', 'on', 'off'
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Validate mode
    valid_modes = ["auto", "on", "off"]
    mode = mode.lower()
    if mode not in valid_modes:
        return f"Error: Invalid proxy mode. Must be one of: {', '.join(valid_modes)}"
    
    # Convert mode to API value
    mode_map = {
        "auto": "0",
        "on": "1",
        "off": "2"
    }
    
    try:
        result = current_project.SetSetting("ProxyMode", mode_map[mode])
        if result:
            return f"Successfully set proxy mode to '{mode}'"
        else:
            return f"Failed to set proxy mode to '{mode}'"
    except Exception as e:
        return f"Error setting proxy mode: {str(e)}"

@mcp.tool()
def set_proxy_quality(quality: str) -> str:
    """Set proxy media quality for the current project.
    
    Args:
        quality: Proxy quality to set. Options: 'quarter', 'half', 'threeQuarter', 'full'
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Validate quality
    valid_qualities = ["quarter", "half", "threeQuarter", "full"]
    if quality not in valid_qualities:
        return f"Error: Invalid proxy quality. Must be one of: {', '.join(valid_qualities)}"
    
    # Convert quality to API value
    quality_map = {
        "quarter": "0",
        "half": "1",
        "threeQuarter": "2",
        "full": "3"
    }
    
    try:
        result = current_project.SetSetting("ProxyQuality", quality_map[quality])
        if result:
            return f"Successfully set proxy quality to '{quality}'"
        else:
            return f"Failed to set proxy quality to '{quality}'"
    except Exception as e:
        return f"Error setting proxy quality: {str(e)}"

@mcp.tool()
def set_cache_path(path_type: str, path: str) -> str:
    """Set cache file path for the current project.
    
    Args:
        path_type: Type of cache path to set. Options: 'local', 'network'
        path: File system path for the cache
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Validate path_type
    valid_path_types = ["local", "network"]
    path_type = path_type.lower()
    if path_type not in valid_path_types:
        return f"Error: Invalid path type. Must be one of: {', '.join(valid_path_types)}"
    
    # Check if directory exists
    if not os.path.exists(path):
        return f"Error: Path '{path}' does not exist"
    
    setting_key = "LocalCachePath" if path_type == "local" else "NetworkCachePath"
    
    try:
        result = current_project.SetSetting(setting_key, path)
        if result:
            return f"Successfully set {path_type} cache path to '{path}'"
        else:
            return f"Failed to set {path_type} cache path to '{path}'"
    except Exception as e:
        return f"Error setting cache path: {str(e)}"

@mcp.tool()
def generate_optimized_media(clip_names: List[str] = None) -> str:
    """Generate optimized media for specified clips or all clips if none specified.
    
    Args:
        clip_names: Optional list of clip names. If None, processes all clips in media pool
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Get clips to process
    if clip_names:
        # Get specified clips
        all_clips = get_all_media_pool_clips(media_pool)
        clips_to_process = []
        missing_clips = []
        
        for name in clip_names:
            found = False
            for clip in all_clips:
                if clip.GetName() == name:
                    clips_to_process.append(clip)
                    found = True
                    break
            if not found:
                missing_clips.append(name)
        
        if missing_clips:
            return f"Error: Could not find these clips: {', '.join(missing_clips)}"
        
        if not clips_to_process:
            return "Error: No valid clips found to process"
    else:
        # Get all clips
        clips_to_process = get_all_media_pool_clips(media_pool)
    
    try:
        # Select the clips
        media_pool.SetCurrentFolder(media_pool.GetRootFolder())
        for clip in clips_to_process:
            clip.AddFlag("Green")  # Temporarily add flag to help with selection
        
        # Switch to Media page if not already there
        current_page = resolve.GetCurrentPage()
        if current_page != "media":
            resolve.OpenPage("media")
        
        # Select clips with Green flag
        media_pool.SetClipSelection([clip for clip in clips_to_process])
        
        # Generate optimized media
        result = current_project.GenerateOptimizedMedia()
        
        # Remove temporary flags
        for clip in clips_to_process:
            clip.ClearFlags("Green")
        
        if result:
            return f"Successfully started optimized media generation for {len(clips_to_process)} clips"
        else:
            return f"Failed to start optimized media generation"
    except Exception as e:
        # Clean up flags in case of error
        try:
            for clip in clips_to_process:
                clip.ClearFlags("Green")
        except:
            pass
        return f"Error generating optimized media: {str(e)}"

@mcp.tool()
def delete_optimized_media(clip_names: List[str] = None) -> str:
    """Delete optimized media for specified clips or all clips if none specified.
    
    Args:
        clip_names: Optional list of clip names. If None, processes all clips in media pool
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Get clips to process
    if clip_names:
        # Get specified clips
        all_clips = get_all_media_pool_clips(media_pool)
        clips_to_process = []
        missing_clips = []
        
        for name in clip_names:
            found = False
            for clip in all_clips:
                if clip.GetName() == name:
                    clips_to_process.append(clip)
                    found = True
                    break
            if not found:
                missing_clips.append(name)
        
        if missing_clips:
            return f"Error: Could not find these clips: {', '.join(missing_clips)}"
        
        if not clips_to_process:
            return "Error: No valid clips found to process"
    else:
        # Get all clips
        clips_to_process = get_all_media_pool_clips(media_pool)
    
    try:
        # Select the clips
        media_pool.SetCurrentFolder(media_pool.GetRootFolder())
        for clip in clips_to_process:
            clip.AddFlag("Green")  # Temporarily add flag to help with selection
        
        # Switch to Media page if not already there
        current_page = resolve.GetCurrentPage()
        if current_page != "media":
            resolve.OpenPage("media")
        
        # Select clips with Green flag
        media_pool.SetClipSelection([clip for clip in clips_to_process])
        
        # Delete optimized media
        result = current_project.DeleteOptimizedMedia()
        
        # Remove temporary flags
        for clip in clips_to_process:
            clip.ClearFlags("Green")
        
        if result:
            return f"Successfully deleted optimized media for {len(clips_to_process)} clips"
        else:
            return f"Failed to delete optimized media"
    except Exception as e:
        # Clean up flags in case of error
        try:
            for clip in clips_to_process:
                clip.ClearFlags("Green")
        except:
            pass
        return f"Error deleting optimized media: {str(e)}"

# ------------------
# Timeline Item Properties
# ------------------

@mcp.resource("resolve://timeline-item/{timeline_item_id}")
def get_timeline_item_properties(timeline_item_id: str) -> Dict[str, Any]:
    """Get properties of a specific timeline item by ID.
    
    Args:
        timeline_item_id: The ID of the timeline item to get properties for
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return {"error": "No timeline currently active"}
    
    try:
        # Find the timeline item by ID
        # We'll need to get all items from all tracks and check their IDs
        video_track_count = current_timeline.GetTrackCount("video")
        audio_track_count = current_timeline.GetTrackCount("audio")
        
        timeline_item = None
        
        # Search video tracks
        for track_index in range(1, video_track_count + 1):
            items = current_timeline.GetItemListInTrack("video", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        break
            if timeline_item:
                break
        
        # If not found, search audio tracks
        if not timeline_item:
            for track_index in range(1, audio_track_count + 1):
                items = current_timeline.GetItemListInTrack("audio", track_index)
                if items:
                    for item in items:
                        if str(item.GetUniqueId()) == timeline_item_id:
                            timeline_item = item
                            break
                if timeline_item:
                    break
        
        if not timeline_item:
            return {"error": f"Timeline item with ID '{timeline_item_id}' not found"}
        
        # Get basic properties
        properties = {
            "id": timeline_item_id,
            "name": timeline_item.GetName(),
            "type": timeline_item.GetType(),
            "start_frame": timeline_item.GetStart(),
            "end_frame": timeline_item.GetEnd(),
            "duration": timeline_item.GetDuration()
        }
        
        # Get additional properties if it's a video item
        if timeline_item.GetType() == "Video":
            # Transform properties
            properties["transform"] = {
                "position": {
                    "x": timeline_item.GetProperty("Pan"),
                    "y": timeline_item.GetProperty("Tilt")
                },
                "zoom": timeline_item.GetProperty("ZoomX"),  # ZoomX/ZoomY can be different for non-uniform scaling
                "zoom_x": timeline_item.GetProperty("ZoomX"),
                "zoom_y": timeline_item.GetProperty("ZoomY"),
                "rotation": timeline_item.GetProperty("Rotation"),
                "anchor_point": {
                    "x": timeline_item.GetProperty("AnchorPointX"),
                    "y": timeline_item.GetProperty("AnchorPointY")
                },
                "pitch": timeline_item.GetProperty("Pitch"),
                "yaw": timeline_item.GetProperty("Yaw")
            }
            
            # Crop properties
            properties["crop"] = {
                "left": timeline_item.GetProperty("CropLeft"),
                "right": timeline_item.GetProperty("CropRight"),
                "top": timeline_item.GetProperty("CropTop"),
                "bottom": timeline_item.GetProperty("CropBottom")
            }
            
            # Composite properties
            properties["composite"] = {
                "mode": timeline_item.GetProperty("CompositeMode"),
                "opacity": timeline_item.GetProperty("Opacity")
            }
            
            # Dynamic zoom properties
            properties["dynamic_zoom"] = {
                "enabled": timeline_item.GetProperty("DynamicZoomEnable"),
                "mode": timeline_item.GetProperty("DynamicZoomMode")
            }
            
            # Retime properties
            properties["retime"] = {
                "speed": timeline_item.GetProperty("Speed"),
                "process": timeline_item.GetProperty("RetimeProcess")
            }
            
            # Stabilization properties
            properties["stabilization"] = {
                "enabled": timeline_item.GetProperty("StabilizationEnable"),
                "method": timeline_item.GetProperty("StabilizationMethod"),
                "strength": timeline_item.GetProperty("StabilizationStrength")
            }
        
        # Audio-specific properties
        if timeline_item.GetType() == "Audio" or timeline_item.GetMediaType() == "Audio":
            properties["audio"] = {
                "volume": timeline_item.GetProperty("Volume"),
                "pan": timeline_item.GetProperty("Pan"),
                "eq_enabled": timeline_item.GetProperty("EQEnable"),
                "normalize_enabled": timeline_item.GetProperty("NormalizeEnable"),
                "normalize_level": timeline_item.GetProperty("NormalizeLevel")
            }
        
        return properties
        
    except Exception as e:
        return {"error": f"Error getting timeline item properties: {str(e)}"}

@mcp.resource("resolve://timeline-items")
def get_timeline_items() -> List[Dict[str, Any]]:
    """Get all items in the current timeline with their IDs and basic properties."""
    if resolve is None:
        return [{"error": "Not connected to DaVinci Resolve"}]
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return [{"error": "Failed to get Project Manager"}]
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return [{"error": "No project currently open"}]
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return [{"error": "No timeline currently active"}]
    
    try:
        # Get all tracks in the timeline
        video_track_count = current_timeline.GetTrackCount("video")
        audio_track_count = current_timeline.GetTrackCount("audio")
        
        items = []
        
        # Process video tracks
        for track_index in range(1, video_track_count + 1):
            track_items = current_timeline.GetItemListInTrack("video", track_index)
            if track_items:
                for item in track_items:
                    items.append({
                        "id": str(item.GetUniqueId()),
                        "name": item.GetName(),
                        "type": "video",
                        "track": track_index,
                        "start_frame": item.GetStart(),
                        "end_frame": item.GetEnd(),
                        "duration": item.GetDuration()
                    })
        
        # Process audio tracks
        for track_index in range(1, audio_track_count + 1):
            track_items = current_timeline.GetItemListInTrack("audio", track_index)
            if track_items:
                for item in track_items:
                    items.append({
                        "id": str(item.GetUniqueId()),
                        "name": item.GetName(),
                        "type": "audio",
                        "track": track_index,
                        "start_frame": item.GetStart(),
                        "end_frame": item.GetEnd(),
                        "duration": item.GetDuration()
                    })
        
        if not items:
            return [{"info": "No items found in the current timeline"}]
        
        return items
    except Exception as e:
        return [{"error": f"Error listing timeline items: {str(e)}"}]

@mcp.tool()
def set_timeline_item_transform(timeline_item_id: str, 
                               property_name: str, 
                               property_value: float) -> str:
    """Set a transform property for a timeline item.
    
    Args:
        timeline_item_id: The ID of the timeline item to modify
        property_name: The name of the property to set. Options include:
                      'Pan', 'Tilt', 'ZoomX', 'ZoomY', 'Rotation', 'AnchorPointX', 
                      'AnchorPointY', 'Pitch', 'Yaw'
        property_value: The value to set for the property
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return "Error: No timeline currently active"
    
    # Validate property name
    valid_properties = [
        'Pan', 'Tilt', 'ZoomX', 'ZoomY', 'Rotation', 
        'AnchorPointX', 'AnchorPointY', 'Pitch', 'Yaw'
    ]
    
    if property_name not in valid_properties:
        return f"Error: Invalid property name. Must be one of: {', '.join(valid_properties)}"
    
    try:
        # Find the timeline item by ID
        video_track_count = current_timeline.GetTrackCount("video")
        
        timeline_item = None
        
        # Search video tracks
        for track_index in range(1, video_track_count + 1):
            items = current_timeline.GetItemListInTrack("video", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        break
            if timeline_item:
                break
        
        if not timeline_item:
            return f"Error: Video timeline item with ID '{timeline_item_id}' not found"
        
        if timeline_item.GetType() != "Video":
            return f"Error: Timeline item with ID '{timeline_item_id}' is not a video item"
        
        # Set the property
        result = timeline_item.SetProperty(property_name, property_value)
        if result:
            return f"Successfully set {property_name} to {property_value} for timeline item '{timeline_item.GetName()}'"
        else:
            return f"Failed to set {property_name} for timeline item '{timeline_item.GetName()}'"
    except Exception as e:
        return f"Error setting timeline item property: {str(e)}"

@mcp.tool()
def set_timeline_item_crop(timeline_item_id: str, 
                          crop_type: str, 
                          crop_value: float) -> str:
    """Set a crop property for a timeline item.
    
    Args:
        timeline_item_id: The ID of the timeline item to modify
        crop_type: The type of crop to set. Options: 'Left', 'Right', 'Top', 'Bottom'
        crop_value: The value to set for the crop (typically 0.0 to 1.0)
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return "Error: No timeline currently active"
    
    # Validate crop type
    valid_crop_types = ['Left', 'Right', 'Top', 'Bottom']
    
    if crop_type not in valid_crop_types:
        return f"Error: Invalid crop type. Must be one of: {', '.join(valid_crop_types)}"
    
    property_name = f"Crop{crop_type}"
    
    try:
        # Find the timeline item by ID
        video_track_count = current_timeline.GetTrackCount("video")
        
        timeline_item = None
        
        # Search video tracks
        for track_index in range(1, video_track_count + 1):
            items = current_timeline.GetItemListInTrack("video", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        break
            if timeline_item:
                break
        
        if not timeline_item:
            return f"Error: Video timeline item with ID '{timeline_item_id}' not found"
        
        if timeline_item.GetType() != "Video":
            return f"Error: Timeline item with ID '{timeline_item_id}' is not a video item"
        
        # Set the property
        result = timeline_item.SetProperty(property_name, crop_value)
        if result:
            return f"Successfully set crop {crop_type.lower()} to {crop_value} for timeline item '{timeline_item.GetName()}'"
        else:
            return f"Failed to set crop {crop_type.lower()} for timeline item '{timeline_item.GetName()}'"
    except Exception as e:
        return f"Error setting timeline item crop: {str(e)}"

@mcp.tool()
def set_timeline_item_composite(timeline_item_id: str, 
                               composite_mode: str = None, 
                               opacity: float = None) -> str:
    """Set composite properties for a timeline item.
    
    Args:
        timeline_item_id: The ID of the timeline item to modify
        composite_mode: Optional composite mode to set (e.g., 'Normal', 'Add', 'Multiply')
        opacity: Optional opacity value to set (0.0 to 1.0)
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return "Error: No timeline currently active"
    
    # Validate inputs
    if composite_mode is None and opacity is None:
        return "Error: Must specify at least one of composite_mode or opacity"
    
    # Valid composite modes
    valid_composite_modes = [
        'Normal', 'Add', 'Subtract', 'Difference', 'Multiply', 'Screen', 
        'Overlay', 'Hardlight', 'Softlight', 'Darken', 'Lighten', 'ColorDodge', 
        'ColorBurn', 'Exclusion', 'Hue', 'Saturation', 'Color', 'Luminosity'
    ]
    
    if composite_mode and composite_mode not in valid_composite_modes:
        return f"Error: Invalid composite mode. Must be one of: {', '.join(valid_composite_modes)}"
    
    if opacity is not None and (opacity < 0.0 or opacity > 1.0):
        return "Error: Opacity must be between 0.0 and 1.0"
    
    try:
        # Find the timeline item by ID
        video_track_count = current_timeline.GetTrackCount("video")
        
        timeline_item = None
        
        # Search video tracks
        for track_index in range(1, video_track_count + 1):
            items = current_timeline.GetItemListInTrack("video", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        break
            if timeline_item:
                break
        
        if not timeline_item:
            return f"Error: Video timeline item with ID '{timeline_item_id}' not found"
        
        if timeline_item.GetType() != "Video":
            return f"Error: Timeline item with ID '{timeline_item_id}' is not a video item"
        
        success = True
        
        # Set composite mode if specified
        if composite_mode:
            result = timeline_item.SetProperty("CompositeMode", composite_mode)
            if not result:
                success = False
        
        # Set opacity if specified
        if opacity is not None:
            result = timeline_item.SetProperty("Opacity", opacity)
            if not result:
                success = False
        
        if success:
            changes = []
            if composite_mode:
                changes.append(f"composite mode to '{composite_mode}'")
            if opacity is not None:
                changes.append(f"opacity to {opacity}")
            
            return f"Successfully set {' and '.join(changes)} for timeline item '{timeline_item.GetName()}'"
        else:
            return f"Failed to set some composite properties for timeline item '{timeline_item.GetName()}'"
    except Exception as e:
        return f"Error setting timeline item composite properties: {str(e)}"

@mcp.tool()
def set_timeline_item_retime(timeline_item_id: str, 
                            speed: float = None, 
                            process: str = None) -> str:
    """Set retiming properties for a timeline item.
    
    Args:
        timeline_item_id: The ID of the timeline item to modify
        speed: Optional speed factor (e.g., 0.5 for 50%, 2.0 for 200%)
        process: Optional retime process. Options: 'NearestFrame', 'FrameBlend', 'OpticalFlow'
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return "Error: No timeline currently active"
    
    # Validate inputs
    if speed is None and process is None:
        return "Error: Must specify at least one of speed or process"
    
    if speed is not None and speed <= 0:
        return "Error: Speed must be greater than 0"
    
    valid_processes = ['NearestFrame', 'FrameBlend', 'OpticalFlow']
    if process and process not in valid_processes:
        return f"Error: Invalid retime process. Must be one of: {', '.join(valid_processes)}"
    
    try:
        # Find the timeline item by ID
        video_track_count = current_timeline.GetTrackCount("video")
        
        timeline_item = None
        
        # Search video tracks
        for track_index in range(1, video_track_count + 1):
            items = current_timeline.GetItemListInTrack("video", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        break
            if timeline_item:
                break
        
        if not timeline_item:
            return f"Error: Video timeline item with ID '{timeline_item_id}' not found"
        
        success = True
        
        # Set speed if specified
        if speed is not None:
            result = timeline_item.SetProperty("Speed", speed)
            if not result:
                success = False
        
        # Set retime process if specified
        if process:
            result = timeline_item.SetProperty("RetimeProcess", process)
            if not result:
                success = False
        
        if success:
            changes = []
            if speed is not None:
                changes.append(f"speed to {speed}x")
            if process:
                changes.append(f"retime process to '{process}'")
            
            return f"Successfully set {' and '.join(changes)} for timeline item '{timeline_item.GetName()}'"
        else:
            return f"Failed to set some retime properties for timeline item '{timeline_item.GetName()}'"
    except Exception as e:
        return f"Error setting timeline item retime properties: {str(e)}"

@mcp.tool()
def set_timeline_item_stabilization(timeline_item_id: str, 
                                   enabled: bool = None, 
                                   method: str = None,
                                   strength: float = None) -> str:
    """Set stabilization properties for a timeline item.
    
    Args:
        timeline_item_id: The ID of the timeline item to modify
        enabled: Optional boolean to enable/disable stabilization
        method: Optional stabilization method. Options: 'Perspective', 'Similarity', 'Translation'
        strength: Optional strength value (0.0 to 1.0)
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return "Error: No timeline currently active"
    
    # Validate inputs
    if enabled is None and method is None and strength is None:
        return "Error: Must specify at least one parameter to modify"
    
    valid_methods = ['Perspective', 'Similarity', 'Translation']
    if method and method not in valid_methods:
        return f"Error: Invalid stabilization method. Must be one of: {', '.join(valid_methods)}"
    
    if strength is not None and (strength < 0.0 or strength > 1.0):
        return "Error: Strength must be between 0.0 and 1.0"
    
    try:
        # Find the timeline item by ID
        video_track_count = current_timeline.GetTrackCount("video")
        
        timeline_item = None
        
        # Search video tracks
        for track_index in range(1, video_track_count + 1):
            items = current_timeline.GetItemListInTrack("video", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        break
            if timeline_item:
                break
        
        if not timeline_item:
            return f"Error: Video timeline item with ID '{timeline_item_id}' not found"
        
        if timeline_item.GetType() != "Video":
            return f"Error: Timeline item with ID '{timeline_item_id}' is not a video item"
        
        success = True
        
        # Set enabled if specified
        if enabled is not None:
            result = timeline_item.SetProperty("StabilizationEnable", 1 if enabled else 0)
            if not result:
                success = False
        
        # Set method if specified
        if method:
            result = timeline_item.SetProperty("StabilizationMethod", method)
            if not result:
                success = False
        
        # Set strength if specified
        if strength is not None:
            result = timeline_item.SetProperty("StabilizationStrength", strength)
            if not result:
                success = False
        
        if success:
            changes = []
            if enabled is not None:
                changes.append(f"stabilization {'enabled' if enabled else 'disabled'}")
            if method:
                changes.append(f"stabilization method to '{method}'")
            if strength is not None:
                changes.append(f"stabilization strength to {strength}")
            
            return f"Successfully set {' and '.join(changes)} for timeline item '{timeline_item.GetName()}'"
        else:
            return f"Failed to set some stabilization properties for timeline item '{timeline_item.GetName()}'"
    except Exception as e:
        return f"Error setting timeline item stabilization properties: {str(e)}"

@mcp.tool()
def set_timeline_item_audio(timeline_item_id: str, 
                           volume: float = None, 
                           pan: float = None,
                           eq_enabled: bool = None) -> str:
    """Set audio properties for a timeline item.
    
    Args:
        timeline_item_id: The ID of the timeline item to modify
        volume: Optional volume level (usually 0.0 to 2.0, where 1.0 is unity gain)
        pan: Optional pan value (-1.0 to 1.0, where -1.0 is left, 0 is center, 1.0 is right)
        eq_enabled: Optional boolean to enable/disable EQ
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return "Error: No timeline currently active"
    
    # Validate inputs
    if volume is None and pan is None and eq_enabled is None:
        return "Error: Must specify at least one parameter to modify"
    
    if volume is not None and volume < 0.0:
        return "Error: Volume must be greater than or equal to 0.0"
    
    if pan is not None and (pan < -1.0 or pan > 1.0):
        return "Error: Pan must be between -1.0 and 1.0"
    
    try:
        # Find the timeline item by ID
        video_track_count = current_timeline.GetTrackCount("video")
        audio_track_count = current_timeline.GetTrackCount("audio")
        
        timeline_item = None
        is_audio = False
        
        # Search audio tracks first
        for track_index in range(1, audio_track_count + 1):
            items = current_timeline.GetItemListInTrack("audio", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        is_audio = True
                        break
            if timeline_item:
                break
        
        # If not found in audio tracks, search video tracks (might be a video clip with audio)
        if not timeline_item:
            for track_index in range(1, video_track_count + 1):
                items = current_timeline.GetItemListInTrack("video", track_index)
                if items:
                    for item in items:
                        if str(item.GetUniqueId()) == timeline_item_id:
                            timeline_item = item
                            break
                if timeline_item:
                    break
        
        if not timeline_item:
            return f"Error: Timeline item with ID '{timeline_item_id}' not found"
        
        # Check if the item has audio capabilities
        if not is_audio and timeline_item.GetMediaType() != "Audio":
            return f"Error: Timeline item with ID '{timeline_item_id}' does not have audio properties"
        
        success = True
        
        # Set volume if specified
        if volume is not None:
            result = timeline_item.SetProperty("Volume", volume)
            if not result:
                success = False
        
        # Set pan if specified
        if pan is not None:
            result = timeline_item.SetProperty("Pan", pan)
            if not result:
                success = False
        
        # Set EQ enabled if specified
        if eq_enabled is not None:
            result = timeline_item.SetProperty("EQEnable", 1 if eq_enabled else 0)
            if not result:
                success = False
        
        if success:
            changes = []
            if volume is not None:
                changes.append(f"volume to {volume}")
            if pan is not None:
                changes.append(f"pan to {pan}")
            if eq_enabled is not None:
                changes.append(f"EQ {'enabled' if eq_enabled else 'disabled'}")
            
            return f"Successfully set {' and '.join(changes)} for timeline item '{timeline_item.GetName()}'"
        else:
            return f"Failed to set some audio properties for timeline item '{timeline_item.GetName()}'"
    except Exception as e:
        return f"Error setting timeline item audio properties: {str(e)}"

# ------------------
# Keyframe Control
# ------------------

@mcp.resource("resolve://timeline-item/{timeline_item_id}/keyframes/{property_name}")
def get_timeline_item_keyframes(timeline_item_id: str, property_name: str) -> Dict[str, Any]:
    """Get keyframes for a specific timeline item by ID.
    
    Args:
        timeline_item_id: The ID of the timeline item to get keyframes for
        property_name: Optional property name to filter keyframes (e.g., 'Pan', 'ZoomX')
    """
    return keyframe_operations.get_timeline_item_keyframes(resolve, timeline_item_id, property_name)

@mcp.tool()
def add_keyframe(timeline_item_id: str, property_name: str, frame: int, value: float) -> str:
    """Add a keyframe at the specified frame for a timeline item property.
    
    Args:
        timeline_item_id: The ID of the timeline item to add keyframe to
        property_name: The name of the property to keyframe (e.g., 'Pan', 'ZoomX')
        frame: Frame position for the keyframe
        value: Value to set at the keyframe
    """
    return keyframe_operations.add_keyframe(resolve, timeline_item_id, property_name, frame, value)

@mcp.tool()
def modify_keyframe(timeline_item_id: str, property_name: str, frame: int, new_value: float = None, new_frame: int = None) -> str:
    """Modify an existing keyframe by changing its value or frame position.
    
    Args:
        timeline_item_id: The ID of the timeline item
        property_name: The name of the property with keyframe
        frame: Current frame position of the keyframe to modify
        new_value: Optional new value for the keyframe
        new_frame: Optional new frame position for the keyframe
    """
    return keyframe_operations.modify_keyframe(resolve, timeline_item_id, property_name, frame, new_value, new_frame)

@mcp.tool()
def delete_keyframe(timeline_item_id: str, property_name: str, frame: int) -> str:
    """Delete a keyframe at the specified frame for a timeline item property.
    
    Args:
        timeline_item_id: The ID of the timeline item
        property_name: The name of the property with keyframe to delete
        frame: Frame position of the keyframe to delete
    """
    return keyframe_operations.delete_keyframe(resolve, timeline_item_id, property_name, frame)

@mcp.tool()
def set_keyframe_interpolation(timeline_item_id: str, property_name: str, frame: int, interpolation_type: str) -> str:
    """Set the interpolation type for a keyframe.
    
    Args:
        timeline_item_id: The ID of the timeline item
        property_name: The name of the property with keyframe
        frame: Frame position of the keyframe
        interpolation_type: Type of interpolation. Options: 'Linear', 'Bezier', 'Ease-In', 'Ease-Out'
    """
    return keyframe_operations.set_keyframe_interpolation(resolve, timeline_item_id, property_name, frame, interpolation_type)

@mcp.tool()
def enable_keyframes(timeline_item_id: str, keyframe_mode: str = "All") -> str:
    """Enable keyframe mode for a timeline item.
    
    Args:
        timeline_item_id: The ID of the timeline item
        keyframe_mode: Keyframe mode to enable. Options: 'All', 'Color', 'Sizing'
    """
    return keyframe_operations.enable_keyframes(resolve, timeline_item_id, keyframe_mode)

# ------------------
# Color Preset Management
# ------------------

@mcp.resource("resolve://color/presets")
def get_color_presets() -> List[Dict[str, Any]]:
    """Get all available color presets in the current project."""
    return gallery_operations.get_color_presets(resolve)

@mcp.tool()
def save_color_preset(clip_name: str = None, preset_name: str = None, album_name: str = "DaVinci Resolve") -> str:
    """Save a color preset from the specified clip.
    
    Args:
        clip_name: Name of the clip to save preset from (uses current clip if None)
        preset_name: Name to give the preset (uses clip name if None)
        album_name: Album to save the preset to (default: "DaVinci Resolve")
    """
    return gallery_operations.save_color_preset(resolve, clip_name, preset_name, album_name)

@mcp.tool()
def apply_color_preset(preset_id: str = None, preset_name: str = None, 
                     clip_name: str = None, album_name: str = "DaVinci Resolve") -> str:
    """Apply a color preset to the specified clip.
    
    Args:
        preset_id: ID of the preset to apply (if known)
        preset_name: Name of the preset to apply (searches in album)
        clip_name: Name of the clip to apply preset to (uses current clip if None)
        album_name: Album containing the preset (default: "DaVinci Resolve")
    """
    return gallery_operations.apply_color_preset(resolve, preset_id, preset_name, clip_name, album_name)
        


@mcp.tool()
def delete_color_preset(preset_id: str = None, preset_name: str = None, 
                       album_name: str = "DaVinci Resolve") -> str:
    """Delete a color preset.
    
    Args:
        preset_id: ID of the preset to delete (if known)
        preset_name: Name of the preset to delete (searches in album)
        album_name: Album containing the preset (default: "DaVinci Resolve")
    """
    return gallery_operations.delete_color_preset(resolve, preset_id, preset_name, album_name)

@mcp.tool()
def create_color_preset_album(album_name: str) -> str:
    """Create a new album for color presets.
    
    Args:
        album_name: Name for the new album
    """
    return gallery_operations.create_color_preset_album(resolve, album_name)

@mcp.tool()
def delete_color_preset_album(album_name: str) -> str:
    """Delete a color preset album.
    
    Args:
        album_name: Name of the album to delete
    """
    return gallery_operations.delete_color_preset_album(resolve, album_name)

@mcp.tool()
def export_lut(clip_name: str = None, 
              export_path: str = None, 
              lut_format: str = "Cube", 
              lut_size: str = "33Point") -> str:
    """Export a LUT from the current clip's grade.
    
    Args:
        clip_name: Name of the clip to export grade from (uses current clip if None)
        export_path: Path to save the LUT file (generated if None)
        lut_format: Format of the LUT. Options: 'Cube', 'Davinci', '3dl', 'Panasonic'
        lut_size: Size of the LUT. Options: '17Point', '33Point', '65Point'
    """
    return export_operations.export_lut(resolve, clip_name, export_path, lut_format, lut_size)

@mcp.resource("resolve://color/lut-formats")
def get_lut_formats() -> Dict[str, Any]:
    """Get available LUT export formats and sizes."""
    return export_operations.get_lut_formats(resolve)

@mcp.tool()
def export_all_powergrade_luts(export_dir: str) -> str:
    """Export all PowerGrade presets as LUT files.
    
    Args:
        export_dir: Directory to save the exported LUTs
    """
    return export_operations.export_all_powergrade_luts(resolve, export_dir)

# ------------------
# Object Inspection
# ------------------

@mcp.resource("resolve://inspect/resolve")
def inspect_resolve_object() -> Dict[str, Any]:
    """Inspect the main resolve object and return its methods and properties."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    return inspect_object(resolve)

@mcp.resource("resolve://inspect/project-manager")
def inspect_project_manager_object() -> Dict[str, Any]:
    """Inspect the project manager object and return its methods and properties."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    return inspect_object(project_manager)

@mcp.resource("resolve://inspect/current-project")
def inspect_current_project_object() -> Dict[str, Any]:
    """Inspect the current project object and return its methods and properties."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    return inspect_object(current_project)

@mcp.resource("resolve://inspect/media-pool")
def inspect_media_pool_object() -> Dict[str, Any]:
    """Inspect the media pool object and return its methods and properties."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return {"error": "Failed to get Media Pool"}
    
    return inspect_object(media_pool)

@mcp.resource("resolve://inspect/current-timeline")
def inspect_current_timeline_object() -> Dict[str, Any]:
    """Inspect the current timeline object and return its methods and properties."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return {"error": "No timeline currently active"}
    
    return inspect_object(current_timeline)

@mcp.tool()
def object_help(object_type: str) -> str:
    """
    Get human-readable help for a DaVinci Resolve API object.
    
    Args:
        object_type: Type of object to get help for ('resolve', 'project_manager', 
                     'project', 'media_pool', 'timeline', 'media_storage')
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    # Map object type string to actual object
    obj = None
    
    if object_type == 'resolve':
        obj = resolve
    elif object_type == 'project_manager':
        obj = resolve.GetProjectManager()
    elif object_type == 'project':
        pm = resolve.GetProjectManager()
        if pm:
            obj = pm.GetCurrentProject()
    elif object_type == 'media_pool':
        pm = resolve.GetProjectManager()
        if pm:
            project = pm.GetCurrentProject()
            if project:
                obj = project.GetMediaPool()
    elif object_type == 'timeline':
        pm = resolve.GetProjectManager()
        if pm:
            project = pm.GetCurrentProject()
            if project:
                obj = project.GetCurrentTimeline()
    elif object_type == 'media_storage':
        obj = resolve.GetMediaStorage()
    else:
        return f"Error: Unknown object type '{object_type}'"
    
    if obj is None:
        return f"Error: Failed to get {object_type} object"
    
    # Generate and return help text
    return print_object_help(obj)

@mcp.tool()
def inspect_custom_object(object_path: str) -> Dict[str, Any]:
    """
    Inspect a custom DaVinci Resolve API object by path.
    
    Args:
        object_path: Path to the object using dot notation (e.g., 'resolve.GetMediaStorage()')
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    try:
        # Start with resolve object
        obj = resolve
        
        # Split the path and traverse down
        parts = object_path.split('.')
        
        # Skip the first part if it's 'resolve'
        start_index = 1 if parts[0].lower() == 'resolve' else 0
        
        for i in range(start_index, len(parts)):
            part = parts[i]
            
            # Check if it's a method call
            if part.endswith('()'):
                method_name = part[:-2]
                if hasattr(obj, method_name) and callable(getattr(obj, method_name)):
                    obj = getattr(obj, method_name)()
                else:
                    return {"error": f"Method '{method_name}' not found or not callable"}
            else:
                # It's an attribute access
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                else:
                    return {"error": f"Attribute '{part}' not found"}
        
        # Inspect the object we've retrieved
        return inspect_object(obj)
    except Exception as e:
        return {"error": f"Error inspecting object: {str(e)}"}

# ------------------
# Layout Presets
# ------------------

@mcp.resource("resolve://layout-presets")
def get_layout_presets() -> List[Dict[str, Any]]:
    """Get all available layout presets for DaVinci Resolve."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    return list_layout_presets(layout_type="ui")

@mcp.tool()
def save_layout_preset_tool(preset_name: str) -> str:
    """
    Save the current UI layout as a preset.
    
    Args:
        preset_name: Name for the saved preset
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = save_layout_preset(resolve, preset_name, layout_type="ui")
    if result:
        return f"Successfully saved layout preset '{preset_name}'"
    else:
        return f"Failed to save layout preset '{preset_name}'"

@mcp.tool()
def load_layout_preset_tool(preset_name: str) -> str:
    """
    Load a UI layout preset.
    
    Args:
        preset_name: Name of the preset to load
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = load_layout_preset(resolve, preset_name, layout_type="ui")
    if result:
        return f"Successfully loaded layout preset '{preset_name}'"
    else:
        return f"Failed to load layout preset '{preset_name}'"

@mcp.tool()
def export_layout_preset_tool(preset_name: str, export_path: str) -> str:
    """
    Export a layout preset to a file.
    
    Args:
        preset_name: Name of the preset to export
        export_path: Path to export the preset file to
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = export_layout_preset(preset_name, export_path, layout_type="ui")
    if result:
        return f"Successfully exported layout preset '{preset_name}' to {export_path}"
    else:
        return f"Failed to export layout preset '{preset_name}'"

@mcp.tool()
def import_layout_preset_tool(import_path: str, preset_name: str = None) -> str:
    """
    Import a layout preset from a file.
    
    Args:
        import_path: Path to the preset file to import
        preset_name: Name to save the imported preset as (uses filename if None)
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = import_layout_preset(import_path, preset_name, layout_type="ui")
    
    if preset_name is None:
        preset_name = os.path.splitext(os.path.basename(import_path))[0]
        
    if result:
        return f"Successfully imported layout preset as '{preset_name}'"
    else:
        return f"Failed to import layout preset from {import_path}"

@mcp.tool()
def delete_layout_preset_tool(preset_name: str) -> str:
    """
    Delete a layout preset.
    
    Args:
        preset_name: Name of the preset to delete
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = delete_layout_preset(preset_name, layout_type="ui")
    if result:
        return f"Successfully deleted layout preset '{preset_name}'"
    else:
        return f"Failed to delete layout preset '{preset_name}'"

# ------------------
# App Control
# ------------------

@mcp.resource("resolve://app/state")
def get_app_state_endpoint() -> Dict[str, Any]:
    """Get DaVinci Resolve application state information."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "connected": False}
    
    return get_app_state(resolve)

@mcp.tool()
def quit_app(force: bool = False, save_project: bool = True) -> str:
    """
    Quit DaVinci Resolve application.
    
    Args:
        force: Whether to force quit even if unsaved changes (potentially dangerous)
        save_project: Whether to save the project before quitting
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = quit_resolve_app(resolve, force, save_project)
    
    if result:
        return "DaVinci Resolve quit command sent successfully"
    else:
        return "Failed to quit DaVinci Resolve"

@mcp.tool()
def restart_app(wait_seconds: int = 5) -> str:
    """
    Restart DaVinci Resolve application.
    
    Args:
        wait_seconds: Seconds to wait between quit and restart
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = restart_resolve_app(resolve, wait_seconds)
    
    if result:
        return "DaVinci Resolve restart initiated successfully"
    else:
        return "Failed to restart DaVinci Resolve"

@mcp.tool()
def open_settings() -> str:
    """Open the Project Settings dialog in DaVinci Resolve."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = open_project_settings(resolve)
    
    if result:
        return "Project Settings dialog opened successfully"
    else:
        return "Failed to open Project Settings dialog"

@mcp.tool()
def open_app_preferences() -> str:
    """Open the Preferences dialog in DaVinci Resolve."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = open_preferences(resolve)
    
    if result:
        return "Preferences dialog opened successfully"
    else:
        return "Failed to open Preferences dialog"

# ------------------
# Cloud Project Operations
# ------------------

@mcp.resource("resolve://cloud/projects")
def get_cloud_projects() -> Dict[str, Any]:
    """Get list of available cloud projects."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}
    
    return get_cloud_project_list(resolve)

@mcp.tool()
def create_cloud_project_tool(project_name: str, folder_path: str = None) -> Dict[str, Any]:
    """Create a new cloud project.
    
    Args:
        project_name: Name for the new cloud project
        folder_path: Optional path for the cloud project folder
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}
    
    return create_cloud_project(resolve, project_name, folder_path)

@mcp.tool()
def import_cloud_project_tool(cloud_id: str, project_name: str = None) -> Dict[str, Any]:
    """Import a project from DaVinci Resolve cloud.
    
    Args:
        cloud_id: Cloud ID or reference of the project to import
        project_name: Optional custom name for the imported project (uses original name if None)
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}
    
    return import_cloud_project(resolve, cloud_id, project_name)

@mcp.tool()
def restore_cloud_project_tool(cloud_id: str, project_name: str = None) -> Dict[str, Any]:
    """Restore a project from DaVinci Resolve cloud.
    
    Args:
        cloud_id: Cloud ID or reference of the project to restore
        project_name: Optional custom name for the restored project (uses original name if None)
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}
    
    return restore_cloud_project(resolve, cloud_id, project_name)

@mcp.tool()
def export_project_to_cloud_tool(project_name: str = None) -> Dict[str, Any]:
    """Export current or specified project to DaVinci Resolve cloud.
    
    Args:
        project_name: Optional name of project to export (uses current project if None)
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}
    
    return export_project_to_cloud(resolve, project_name)

@mcp.tool()
def add_user_to_cloud_project_tool(cloud_id: str, user_email: str, permissions: str = "viewer") -> Dict[str, Any]:
    """Add a user to a cloud project with specified permissions.
    
    Args:
        cloud_id: Cloud ID of the project
        user_email: Email of the user to add
        permissions: Permission level (viewer, editor, admin)
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}
    
    return add_user_to_cloud_project(resolve, cloud_id, user_email, permissions)

@mcp.tool()
def remove_user_from_cloud_project_tool(cloud_id: str, user_email: str) -> Dict[str, Any]:
    """Remove a user from a cloud project.
    
    Args:
        cloud_id: Cloud ID of the project
        user_email: Email of the user to remove
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}
    
    return remove_user_from_cloud_project(resolve, cloud_id, user_email)

# ------------------
# Project Properties
# ------------------

@mcp.resource("resolve://project/properties")
def get_project_properties_endpoint() -> Dict[str, Any]:
    """Get all project properties for the current project."""
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
def get_project_property_endpoint(property_name: str) -> Dict[str, Any]:
    """Get a specific project property value.
    
    Args:
        property_name: Name of the property to get
    """
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
def get_superscale_settings_endpoint() -> Dict[str, Any]:
    """Get SuperScale settings for the current project."""
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
def get_color_settings_endpoint() -> Dict[str, Any]:
    """Get color science and color space settings for the current project."""
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
def get_project_metadata_endpoint() -> Dict[str, Any]:
    """Get metadata for the current project."""
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
def get_project_info_endpoint() -> Dict[str, Any]:
    """Get comprehensive information about the current project."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    return get_project_info(current_project)

@mcp.tool()
def append_clips_to_timeline(clip_names: List[str], timeline_name: str = None) -> str:
    """Append a list of clips (by name) to the timeline."""
    from src.api.media_operations import append_clips_to_timeline as append_func
    return append_func(resolve, clip_names, timeline_name)

@mcp.tool()
def create_timeline_from_clips(name: str, clip_names: List[str]) -> str:
    """Create a new timeline containing the specified clips."""
    from src.api.media_operations import create_timeline_from_clips as create_func
    return create_func(resolve, name, clip_names)

# ------------------
# Audio & Smart Editing
# ------------------

@mcp.tool()
def list_clips_tool() -> List[Dict[str, Any]]:
    """List all clips available in the Media Pool."""
    from src.api.media_operations import list_media_pool_clips as list_func
    return list_func(resolve)

@mcp.tool()
def transcribe_folder_tool(folder_name: str) -> Dict[str, Any]:
    """Transcribe all audio clips in a specific Media Pool folder using Native AI.
    
    Args:
        folder_name: Name of the folder to transcribe
    """
    from src.api.audio_operations import transcribe_folder as transcribe_func
    return transcribe_func(resolve, folder_name)

@mcp.tool()
def transcribe_clip_tool(clip_name: str, model_size: str = "base") -> Dict[str, Any]:
    """Transcribe audio from a specific clip using Whisper.
    
    Args:
        clip_name: Name of the clip to transcribe
        model_size: Whisper model size (tiny, base, small, medium, large)
    """
    from src.api.audio_operations import transcribe_clip as transcribe_func
    return transcribe_func(resolve, clip_name, model_size)

@mcp.tool()
def create_trendy_timeline_tool(edits: List[Dict[str, Any]], timeline_name: str = "Trendy Cut") -> str:
    """Create a new timeline with precisely trimmed clips and 1s gaps.
    
    Args:
        edits: List of segments, e.g. [{"clip_name": "A.mov", "start_time": 10, "end_time": 15}]
        timeline_name: Name for the result timeline
    """
    from src.api.smart_editing import create_trendy_timeline as create_func
    return create_func(resolve, edits, timeline_name)

# Start the server
if __name__ == "__main__":
    try:
        if resolve is None:
            logger.error("Cannot start server without connection to DaVinci Resolve")
            sys.exit(1)
        
        logger.info("Starting DaVinci Resolve MCP Server")
        # Start the MCP server with the simple run method
        # Note: The MCP CLI tool handles port configuration, not FastMCP directly
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1) 