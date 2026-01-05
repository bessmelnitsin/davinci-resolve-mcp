
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
