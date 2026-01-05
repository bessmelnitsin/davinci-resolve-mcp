
"""
Navigation Tools for DaVinci Resolve MCP
Page navigation, system info, and global Resolve operations.
"""
from typing import Dict, Any, List

from src.server_instance import mcp
from src.context import get_resolve


# Valid page names for OpenPage
VALID_PAGES = ["media", "cut", "edit", "fusion", "color", "fairlight", "deliver"]


@mcp.tool()
def open_page(page_name: str) -> str:
    """Switch to a specific page in DaVinci Resolve.
    
    Args:
        page_name: One of 'media', 'cut', 'edit', 'fusion', 'color', 'fairlight', 'deliver'
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    page_lower = page_name.lower()
    if page_lower not in VALID_PAGES:
        return f"Error: Invalid page name '{page_name}'. Valid pages: {', '.join(VALID_PAGES)}"
    
    try:
        if resolve.OpenPage(page_lower):
            return f"Switched to '{page_lower}' page"
        return f"Failed to switch to '{page_lower}' page"
    except Exception as e:
        return f"Error switching page: {e}"


@mcp.resource("resolve://current-page")
def get_current_page() -> Dict[str, Any]:
    """Get the currently displayed page in DaVinci Resolve."""
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    try:
        current = resolve.GetCurrentPage()
        return {
            "current_page": current if current else "unknown",
            "available_pages": VALID_PAGES
        }
    except Exception as e:
        return {"error": f"Failed to get current page: {e}"}


@mcp.resource("resolve://system-info")
def get_system_info() -> Dict[str, Any]:
    """Get DaVinci Resolve product and version information."""
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    try:
        info = {
            "product_name": resolve.GetProductName(),
            "version_string": resolve.GetVersionString(),
        }
        
        # GetVersion returns [major, minor, patch, build, suffix]
        version_fields = resolve.GetVersion()
        if version_fields and len(version_fields) >= 4:
            info["version"] = {
                "major": version_fields[0],
                "minor": version_fields[1],
                "patch": version_fields[2],
                "build": version_fields[3],
                "suffix": version_fields[4] if len(version_fields) > 4 else ""
            }
        
        return info
    except Exception as e:
        return {"error": f"Failed to get system info: {e}"}


@mcp.tool()
def quit_resolve() -> str:
    """Quit DaVinci Resolve application.
    
    WARNING: This will close DaVinci Resolve. Make sure to save your project first.
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    try:
        resolve.Quit()
        return "DaVinci Resolve is closing..."
    except Exception as e:
        return f"Error quitting Resolve: {e}"


# ============================================================
# Full Coverage: Remaining Resolve Functions
# ============================================================

@mcp.tool()
def update_layout_preset(preset_name: str) -> str:
    """Update an existing UI layout preset with current layout.
    
    Args:
        preset_name: Name of the preset to update
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    try:
        result = resolve.UpdateLayoutPreset(preset_name)
        if result:
            return f"Updated layout preset: {preset_name}"
        return f"Failed to update preset '{preset_name}' (may not exist)"
    except AttributeError:
        return "Error: UpdateLayoutPreset not available"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def import_render_preset(preset_path: str) -> str:
    """Import a render preset from file and set as current.
    
    Args:
        preset_path: Path to the preset file
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    try:
        result = resolve.ImportRenderPreset(preset_path)
        if result:
            return f"Imported render preset from: {preset_path}"
        return "Failed to import render preset"
    except AttributeError:
        return "Error: ImportRenderPreset not available"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def export_render_preset(preset_name: str, export_path: str) -> str:
    """Export a render preset to file.
    
    Args:
        preset_name: Name of the preset to export
        export_path: Path for the exported file
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    try:
        result = resolve.ExportRenderPreset(preset_name, export_path)
        if result:
            return f"Exported preset '{preset_name}' to: {export_path}"
        return f"Failed to export preset '{preset_name}'"
    except AttributeError:
        return "Error: ExportRenderPreset not available"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def import_burn_in_preset(preset_path: str) -> str:
    """Import a data burn-in preset from file.
    
    Args:
        preset_path: Path to the preset file
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    try:
        result = resolve.ImportBurnInPreset(preset_path)
        if result:
            return f"Imported burn-in preset from: {preset_path}"
        return "Failed to import burn-in preset"
    except AttributeError:
        return "Error: ImportBurnInPreset not available"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_keyframe_mode() -> Dict[str, Any]:
    """Get the current keyframe mode setting.
    
    Returns the mode value: 0=All, 1=Color, 2=Sizing
    """
    resolve = get_resolve()
    if not resolve:
        return {"error": "Not connected to DaVinci Resolve"}
    
    try:
        mode = resolve.GetKeyframeMode()
        mode_names = {0: "All", 1: "Color", 2: "Sizing"}
        return {
            "keyframe_mode": mode,
            "mode_name": mode_names.get(mode, "Unknown")
        }
    except AttributeError:
        return {"error": "GetKeyframeMode not available"}
    except Exception as e:
        return {"error": f"Error: {e}"}


@mcp.tool()
def set_keyframe_mode(mode: int) -> str:
    """Set the keyframe mode.
    
    Args:
        mode: 0=All, 1=Color, 2=Sizing
    """
    resolve = get_resolve()
    if not resolve:
        return "Error: Not connected to DaVinci Resolve"
    
    if mode not in [0, 1, 2]:
        return "Error: Mode must be 0 (All), 1 (Color), or 2 (Sizing)"
    
    try:
        result = resolve.SetKeyframeMode(mode)
        mode_names = {0: "All", 1: "Color", 2: "Sizing"}
        if result:
            return f"Set keyframe mode to: {mode_names[mode]}"
        return "Failed to set keyframe mode"
    except AttributeError:
        return "Error: SetKeyframeMode not available"
    except Exception as e:
        return f"Error: {e}"
