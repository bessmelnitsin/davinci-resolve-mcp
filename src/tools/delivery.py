
"""
Delivery Tools for DaVinci Resolve MCP
"""
from typing import List, Dict, Any

from src.server_instance import mcp
from src.context import get_resolve
from src.api.delivery_operations import (
    get_render_presets as get_presets_impl,
    add_to_render_queue as add_queue_impl,
    start_render as start_render_impl,
    get_render_queue_status as get_status_impl,
    clear_render_queue as clear_queue_impl,
    add_render_job_robust as add_render_job_impl,
    get_render_formats as get_formats_impl,
)

@mcp.resource("resolve://delivery/render-presets")
def get_render_presets() -> List[Dict[str, Any]]:
    """Get all available render presets in the current project."""
    resolve = get_resolve()
    return get_presets_impl(resolve)

@mcp.tool()
def add_to_render_queue(preset_name: str, timeline_name: str = None, use_in_out_range: bool = False) -> Dict[str, Any]:
    """Add a timeline to the render queue with the specified preset."""
    resolve = get_resolve()
    return add_queue_impl(resolve, preset_name, timeline_name, use_in_out_range)

@mcp.tool()
def start_render() -> Dict[str, Any]:
    """Start rendering the jobs in the render queue."""
    resolve = get_resolve()
    return start_render_impl(resolve)

@mcp.resource("resolve://delivery/render-queue/status")
def get_render_queue_status() -> Dict[str, Any]:
    """Get the status of jobs in the render queue."""
    resolve = get_resolve()
    return get_status_impl(resolve)

@mcp.tool()
def clear_render_queue() -> Dict[str, Any]:
    """Clear all jobs from the render queue."""
    resolve = get_resolve()
    return clear_queue_impl(resolve)


# ============================================================
# Phase 8: Extended Delivery Tools
# ============================================================

@mcp.tool()
def stop_render() -> Dict[str, Any]:
    """Stop the current rendering process."""
    resolve = get_resolve()
    if not resolve:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    if not pm:
        return {"error": "Failed to get Project Manager"}
    
    project = pm.GetCurrentProject()
    if not project:
        return {"error": "No project currently open"}
    
    try:
        result = project.StopRendering()
        if result:
            return {"success": True, "message": "Rendering stopped"}
        return {"success": False, "message": "No active render to stop"}
    except Exception as e:
        return {"error": f"Failed to stop rendering: {e}"}


@mcp.tool()
def delete_render_job(job_id: str) -> Dict[str, Any]:
    """Delete a specific render job from the queue.
    
    Args:
        job_id: The ID of the render job to delete
    """
    resolve = get_resolve()
    if not resolve:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    if not pm:
        return {"error": "Failed to get Project Manager"}
    
    project = pm.GetCurrentProject()
    if not project:
        return {"error": "No project currently open"}
    
    try:
        result = project.DeleteRenderJob(job_id)
        if result:
            return {"success": True, "message": f"Deleted render job {job_id}"}
        return {"error": f"Failed to delete render job {job_id}"}
    except Exception as e:
        return {"error": f"Error deleting render job: {e}"}


@mcp.tool()
def add_render_job(preset_name: str = None, output_dir: str = None,
                   output_filename: str = None, timeline_name: str = None) -> Dict[str, Any]:
    """Add a render job with robust fallback methods.
    
    Args:
        preset_name: Render preset name (optional)
        output_dir: Output directory path (optional)
        output_filename: Output filename without extension (optional)
        timeline_name: Timeline to render (uses current if not specified)
    """
    resolve = get_resolve()
    return add_render_job_impl(resolve, preset_name, output_dir, output_filename, 
                               None, None, timeline_name)


@mcp.tool()
def get_render_formats() -> Dict[str, Any]:
    """Get all available render formats and their codecs."""
    resolve = get_resolve()
    return get_formats_impl(resolve)


@mcp.tool()
def set_render_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Apply render settings to the current project.
    
    Args:
        settings: Dictionary of render settings (TargetDir, CustomName, etc.)
    """
    resolve = get_resolve()
    if not resolve:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    if not pm:
        return {"error": "Failed to get Project Manager"}
    
    project = pm.GetCurrentProject()
    if not project:
        return {"error": "No project currently open"}
    
    # Switch to deliver page
    if resolve.GetCurrentPage() != "deliver":
        resolve.OpenPage("deliver")
    
    try:
        render_settings = project.GetRenderSettings()
        if render_settings and render_settings.SetRenderSettings(settings):
            return {"success": True, "message": "Render settings applied"}
        return {"error": "Failed to apply render settings"}
    except Exception as e:
        return {"error": f"Error applying settings: {e}"}


@mcp.tool()
def get_current_render_mode() -> Dict[str, Any]:
    """Get the current render mode and settings overview."""
    resolve = get_resolve()
    if not resolve:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    if not pm:
        return {"error": "Failed to get Project Manager"}
    
    project = pm.GetCurrentProject()
    if not project:
        return {"error": "No project currently open"}
    
    try:
        result = {
            "is_rendering": project.IsRenderingInProgress(),
        }
        
        # Try to get current format/codec
        try:
            format_codec = project.GetCurrentRenderFormatAndCodec()
            if format_codec:
                result["format"] = format_codec.get("format")
                result["codec"] = format_codec.get("codec")
        except:
            pass
        
        # Get queue count
        try:
            jobs = project.GetRenderJobList()
            result["queue_jobs"] = len(jobs) if jobs else 0
        except:
            pass
        
        return result
    except Exception as e:
        return {"error": f"Error getting render mode: {e}"}


@mcp.tool()
def load_render_preset(preset_name: str) -> str:
    """Load a render preset by name.
    
    Args:
        preset_name: Name of the preset to load
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return "Error: Failed to get Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return "Error: No project currently open"
    
    try:
        if project.LoadRenderPreset(preset_name):
            return f"Loaded render preset '{preset_name}'"
        return f"Failed to load preset '{preset_name}'"
    except Exception as e:
        return f"Error loading preset: {e}"


@mcp.tool()
def save_render_preset(preset_name: str) -> str:
    """Save current render settings as a preset.
    
    Args:
        preset_name: Name for the new preset
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return "Error: Failed to get Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return "Error: No project currently open"
    
    try:
        if project.SaveAsNewRenderPreset(preset_name):
            return f"Saved render preset as '{preset_name}'"
        return f"Failed to save preset '{preset_name}'"
    except Exception as e:
        return f"Error saving preset: {e}"


# ============================================================
# Phase 1.4: Critical Delivery Extensions
# ============================================================

@mcp.tool()
def is_rendering_in_progress() -> Dict[str, Any]:
    """Check if rendering is currently in progress.
    
    Returns status of any active render jobs.
    """
    resolve = get_resolve()
    if not resolve:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    if not pm:
        return {"error": "Failed to get Project Manager"}
    
    project = pm.GetCurrentProject()
    if not project:
        return {"error": "No project currently open"}
    
    try:
        is_rendering = project.IsRenderingInProgress()
        return {
            "is_rendering": is_rendering,
            "message": "Rendering in progress" if is_rendering else "No active render"
        }
    except Exception as e:
        return {"error": f"Error checking render status: {e}"}


@mcp.tool()
def set_current_render_format(format_name: str, codec_name: str) -> str:
    """Set the current render format and codec.
    
    Args:
        format_name: Render format (e.g., 'mp4', 'mov', 'mxf')
        codec_name: Codec name (e.g., 'H.264', 'H.265', 'ProRes 422 HQ')
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return "Error: Failed to get Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return "Error: No project currently open"
    
    try:
        result = project.SetCurrentRenderFormatAndCodec(format_name, codec_name)
        if result:
            return f"Set render format to '{format_name}' with codec '{codec_name}'"
        return f"Failed to set format/codec. Check format '{format_name}' and codec '{codec_name}' are valid."
    except Exception as e:
        return f"Error setting format: {e}"


@mcp.tool()
def get_current_render_format() -> Dict[str, Any]:
    """Get the currently selected render format and codec."""
    resolve = get_resolve()
    if not resolve:
        return {"error": "Not connected to DaVinci Resolve"}
    
    pm = resolve.GetProjectManager()
    if not pm:
        return {"error": "Failed to get Project Manager"}
    
    project = pm.GetCurrentProject()
    if not project:
        return {"error": "No project currently open"}
    
    try:
        format_codec = project.GetCurrentRenderFormatAndCodec()
        if format_codec:
            return {
                "format": format_codec.get("format"),
                "codec": format_codec.get("codec")
            }
        return {"error": "Could not get current format/codec"}
    except Exception as e:
        return {"error": f"Error getting format: {e}"}


@mcp.tool()
def set_render_mode(render_mode: int) -> str:
    """Set the render mode.
    
    Args:
        render_mode: 0 for Individual clips, 1 for Single clip
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return "Error: Failed to get Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return "Error: No project currently open"
    
    try:
        result = project.SetCurrentRenderMode(render_mode)
        mode_name = "Individual clips" if render_mode == 0 else "Single clip"
        if result:
            return f"Set render mode to '{mode_name}'"
        return f"Failed to set render mode"
    except Exception as e:
        return f"Error setting render mode: {e}"


@mcp.tool()
def export_current_frame_as_still(file_path: str) -> str:
    """Export the current frame as a still image.
    
    Args:
        file_path: Path for the exported file (must include valid extension like .jpg, .png, .tiff)
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return "Error: Failed to get Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return "Error: No project currently open"
    
    try:
        result = project.ExportCurrentFrameAsStill(file_path)
        if result:
            return f"Exported current frame to: {file_path}"
        return "Failed to export frame (check file path and extension)"
    except Exception as e:
        return f"Error exporting frame: {e}"
