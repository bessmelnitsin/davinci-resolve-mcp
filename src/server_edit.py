
import os
import sys
import logging
from typing import List, Dict, Any, Optional, Union

# Import MCP
from mcp.server.fastmcp import FastMCP

# Import our utility functions
from src.utils.platform import setup_environment, get_platform, get_resolve_paths
from src.utils.object_inspection import (
    inspect_object,
    get_object_methods,
    get_object_properties
)

# Import API modules provided in src/api
# We will use these for implementation where possible
from src.api.whisper_node import transcribe_with_whisper_node
from src.api.jump_cut import generate_jump_cut_edits
from src.api.smart_editing import create_vertical_timeline, create_trendy_timeline as create_trendy_impl
from src.api.viral_detector import (
    find_viral_segments as find_viral_segments_impl,
    format_segments_for_display
)
from src.api import (
    transcription_operations,
    keyframe_operations,
    media_operations,
    timeline_operations
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("davinci-resolve-mcp-edit")

# Connect to Resolve
# We duplicate the connection logic here to be self-contained or import it if modularized
# For safety/speed, duplicating the standard connection block
paths = get_resolve_paths()
RESOLVE_API_PATH = paths["api_path"]
RESOLVE_LIB_PATH = paths["lib_path"]
RESOLVE_MODULES_PATH = paths["modules_path"]

os.environ["RESOLVE_SCRIPT_API"] = RESOLVE_API_PATH
os.environ["RESOLVE_SCRIPT_LIB"] = RESOLVE_LIB_PATH

if sys.platform.startswith("win") and hasattr(os, "add_dll_directory"):
    resolve_dir = os.path.dirname(RESOLVE_LIB_PATH)
    if os.path.exists(resolve_dir):
        os.add_dll_directory(resolve_dir)

if RESOLVE_MODULES_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULES_PATH)

try:
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
    if resolve:
        logger.info(f"Connected to DaVinci Resolve: {resolve.GetProductName()} {resolve.GetVersionString()}")
    else:
        logger.error("Failed to get Resolve object")
        resolve = None
except ImportError:
    logger.error("Failed to import DaVinciResolveScript")
    resolve = None
except Exception as e:
    logger.error(f"Error connecting to Resolve: {e}")
    resolve = None

# Initialize MCP Server
mcp = FastMCP("DaVinciResolveEdit")

# ==========================================
# Core & Navigation Tools
# ==========================================

@mcp.resource("resolve://version")
def get_resolve_version() -> str:
    """Get DaVinci Resolve version information."""
    if resolve is None: return "Error: Not connected"
    return f"{resolve.GetProductName()} {resolve.GetVersionString()}"

@mcp.resource("resolve://current-page")
def get_current_page() -> str:
    """Get the current page open in DaVinci Resolve."""
    if resolve is None: return "Error: Not connected"
    return resolve.GetCurrentPage()

@mcp.tool()
def switch_page(page: str) -> str:
    """Switch to a specific page (media, cut, edit, fusion, color, fairlight, deliver)."""
    if resolve is None: return "Error: Not connected"
    valid_pages = ['media', 'cut', 'edit', 'fusion', 'color', 'fairlight', 'deliver']
    if page.lower() not in valid_pages:
        return f"Error: Invalid page. Must be one of: {', '.join(valid_pages)}"
    if resolve.OpenPage(page.lower()):
        return f"Switched to {page}"
    return f"Failed to switch to {page}"

# ==========================================
# Project Management
# ==========================================

@mcp.resource("resolve://projects")
def list_projects() -> List[str]:
    """List all available projects in the current database."""
    if resolve is None: return ["Error: Not connected"]
    pm = resolve.GetProjectManager()
    if not pm: return ["Error: No Project Manager"]
    return [p for p in pm.GetProjectListInCurrentFolder() if p]

@mcp.resource("resolve://current-project")
def get_current_project_name() -> str:
    """Get the name of the currently open project."""
    if resolve is None: return "Error: Not connected"
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject() if pm else None
    return proj.GetName() if proj else "No project open"

@mcp.tool()
def open_project(name: str) -> str:
    """Open a project by name."""
    if resolve is None: return "Error: Not connected"
    pm = resolve.GetProjectManager()
    if not pm: return "Error: No Project Manager"
    if pm.LoadProject(name):
        return f"Opened project '{name}'"
    return f"Failed to open project '{name}'"

@mcp.tool()
def save_project() -> str:
    """Save the current project."""
    if resolve is None: return "Error: Not connected"
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject() if pm else None
    if not proj: return "Error: No project open"
    if pm.SaveProject():
        return f"Saved project '{proj.GetName()}'"
    return "Failed to save project"

# ==========================================
# Media Pool Operations
# ==========================================

@mcp.resource("resolve://media-pool-clips")
def list_media_pool_clips() -> List[Dict[str, Any]]:
    """List all clips in the media pool."""
    return media_operations.list_media_pool_clips(resolve)

@mcp.tool()
def import_media(file_path: str) -> str:
    """Import media file into the media pool."""
    return media_operations.import_media(resolve, file_path)

@mcp.tool()
def create_bin(name: str) -> str:
    """Create a new bin in the media pool."""
    return media_operations.create_bin(resolve, name)

# ==========================================
# Timeline Operations
# ==========================================

@mcp.resource("resolve://timelines")
def list_timelines() -> List[str]:
    """List all timelines in the current project."""
    if resolve is None: return ["Error: Not connected"]
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject() if pm else None
    if not proj: return ["Error: No project open"]
    
    count = proj.GetTimelineCount()
    timelines = []
    for i in range(1, count + 1):
        tl = proj.GetTimelineByIndex(i)
        if tl: timelines.append(tl.GetName())
    return timelines

@mcp.tool()
def create_timeline(name: str) -> str:
    """Create a new timeline."""
    if resolve is None: return "Error: Not connected"
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject() if pm else None
    if not proj: return "Error: No project open"
    pool = proj.GetMediaPool()
    if pool and pool.CreateEmptyTimeline(name):
        return f"Created timeline '{name}'"
    return f"Failed to create timeline '{name}'"

@mcp.tool()
def set_current_timeline(name: str) -> str:
    """Switch to a timeline by name."""
    if resolve is None: return "Error: Not connected"
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject() if pm else None
    if not proj: return "Error: No project open"
    
    count = proj.GetTimelineCount()
    for i in range(1, count + 1):
        tl = proj.GetTimelineByIndex(i)
        if tl and tl.GetName() == name:
            if proj.SetCurrentTimeline(tl):
                return f"Switched to '{name}'"
    return f"Timeline '{name}' not found"

@mcp.tool()
def add_clip_to_timeline(clip_name: str, timeline_name: str = None) -> str:
    """Append a clip to the timeline."""
    return media_operations.add_clip_to_timeline(resolve, clip_name, timeline_name)

@mcp.tool()
def add_marker(frame: int = None, color: str = "Blue", note: str = "") -> str:
    """Add a marker to the timeline."""
    return timeline_operations.add_marker(resolve, frame, color, note)


# Utility function for media pool (needed for object access)
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

# ==========================================
# Smart / AI Tools (Edit Focused)
# ==========================================

@mcp.tool()
def transcribe(file_path: str, language: str = "auto", output_format: str = "json") -> str:
    """Transcribe audio/video file using Whisper."""
    import json
    if not os.path.exists(file_path): return "Error: File not found"
    
    result = transcribe_with_whisper_node(file_path)
    if "error" in result: return f"Error: {result['error']}"
    
    if output_format == "text": return result.get("text", "")
    elif output_format == "json": return json.dumps(result, ensure_ascii=False, indent=2)
    return f"Transcription complete ({len(result.get('text', ''))} chars)"

@mcp.tool()
def smart_jump_cut(clip_name: str, silence_threshold: float = 0.5) -> str:
    """Automatically remove silence from a clip."""
    if resolve is None: return "Error: Not connected"
    
    # 1. Find clip and path
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject() if pm else None
    if not proj: return "Error: No project"
    pool = proj.GetMediaPool()
    
    # Use local helper
    clips = get_all_media_pool_clips(pool)
    
    target_clip = next((c for c in clips if c.GetName() == clip_name), None)
    if not target_clip: return f"Clip '{clip_name}' not found"
    
    path = target_clip.GetClipProperty("File Path")
    
    # 2. Transcribe
    whisper_data = transcribe_with_whisper_node(path)
    if "error" in whisper_data: return f"Whisper failed: {whisper_data['error']}"
    
    # 3. Generate Edits
    edits = generate_jump_cut_edits(whisper_data, clip_name, silence_threshold)
    
    # 4. Create Timeline
    return create_trendy_impl(resolve, edits, f"JumpCut_{clip_name}")

@mcp.tool()
def podcast_to_clips(clip_name: str, max_clips: int = 5) -> str:
    """Convert podcast to viral clips."""
    if resolve is None: return "Error: Not connected"
    
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject() if pm else None
    if not proj: return "Error: No project open"
    pool = proj.GetMediaPool()
    
    clips = get_all_media_pool_clips(pool)
    target_clip = next((c for c in clips if c.GetName() == clip_name), None)
    if not target_clip: return f"Clip '{clip_name}' not found"
    
    path = target_clip.GetClipProperty("File Path")
    logger.info(f"Analying podcast: {clip_name}")
    
    # Transcribe & Detect
    whisper_data = transcribe_with_whisper_node(path)
    if "error" in whisper_data: return f"Error: {whisper_data['error']}"
    
    segments = find_viral_segments_impl(whisper_data, max_segments=max_clips)
    if not segments: return "No viral segments found."
    
    # Create Timelines
    results = []
    for i, seg in enumerate(segments, 1):
        tl_name = f"Clip_{i}_{clip_name}"
        edits = [{"clip_name": clip_name, "start_time": seg["start"], "end_time": seg["end"]}]
        res = create_trendy_impl(resolve, edits, tl_name)
        results.append(f"[{i}] {tl_name} (Score: {seg.get('total_score',0)}): {res}")
        
    return "\n".join(results)


