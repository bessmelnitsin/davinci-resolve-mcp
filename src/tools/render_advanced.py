"""
DaVinci Resolve MCP - Advanced Render Operations

Implements advanced render and burn-in preset operations including:
- Render resolution query
- Burn-in preset import/export
- Render preset deletion
- Additional render configuration

MEDIUM PRIORITY: Useful for advanced delivery workflows
"""

from typing import Dict, Any, List, Optional
import json
import logging

logger = logging.getLogger("davinci-resolve-mcp.tools.render_advanced")

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


# ============================================================================
# Render Resolution Operations (MEDIUM PRIORITY)
# ============================================================================

def get_render_resolutions(
    render_format: str,
    codec: str
) -> Dict[str, Any]:
    """
    Get list of available render resolutions for a format/codec combination.

    Args:
        render_format: The render format (e.g., "QuickTime", "MP4")
        codec: The codec (e.g., "Apple ProRes 422 HQ", "H.264")

    Returns:
        Dictionary with available resolutions

    Example:
        >>> get_render_resolutions("QuickTime", "Apple ProRes 422 HQ")
        {
            "success": True,
            "format": "QuickTime",
            "codec": "Apple ProRes 422 HQ",
            "resolutions": ["3840x2160", "1920x1080", "1280x720"]
        }
    """
    try:
        project = get_current_project()

        # GetRenderResolutions(format, codec)
        resolutions = project.GetRenderResolutions(render_format, codec)

        if not resolutions:
            return {
                "success": False,
                "error": "No resolutions available for this format/codec combination",
                "format": render_format,
                "codec": codec
            }

        return {
            "success": True,
            "format": render_format,
            "codec": codec,
            "resolutions": resolutions,
            "count": len(resolutions)
        }

    except Exception as e:
        logger.error(f"Error getting render resolutions: {e}")
        return {
            "success": False,
            "error": str(e),
            "format": render_format,
            "codec": codec
        }


def get_current_render_format_and_codec() -> Dict[str, Any]:
    """
    Get the current render format and codec settings.

    Returns:
        Dictionary with current format and codec

    Example:
        >>> get_current_render_format_and_codec()
        {
            "success": True,
            "format": "QuickTime",
            "codec": "Apple ProRes 422 HQ"
        }
    """
    try:
        project = get_current_project()

        # GetCurrentRenderFormatAndCodec()
        result = project.GetCurrentRenderFormatAndCodec()

        if not result:
            return {
                "success": False,
                "error": "Unable to get current render format and codec"
            }

        # Result is typically a dictionary or tuple
        if isinstance(result, dict):
            return {
                "success": True,
                **result
            }
        elif isinstance(result, (list, tuple)) and len(result) >= 2:
            return {
                "success": True,
                "format": result[0],
                "codec": result[1]
            }
        else:
            return {
                "success": True,
                "result": result
            }

    except Exception as e:
        logger.error(f"Error getting current render format and codec: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# Render Preset Management (MEDIUM PRIORITY)
# ============================================================================

def delete_render_preset(preset_name: str) -> Dict[str, Any]:
    """
    Delete a render preset.

    Args:
        preset_name: Name of the render preset to delete

    Returns:
        Deletion result

    Example:
        >>> delete_render_preset("Old Preset")
        {
            "success": True,
            "preset_name": "Old Preset",
            "message": "Render preset deleted"
        }
    """
    try:
        project = get_current_project()

        # DeleteRenderPreset(presetName)
        result = project.DeleteRenderPreset(preset_name)

        return {
            "success": bool(result),
            "preset_name": preset_name,
            "message": f"Render preset {'deleted' if result else 'deletion failed'}"
        }

    except Exception as e:
        logger.error(f"Error deleting render preset: {e}")
        return {
            "success": False,
            "error": str(e),
            "preset_name": preset_name
        }


# ============================================================================
# Burn-In Preset Operations (MEDIUM PRIORITY)
# ============================================================================

def import_burn_in_preset(preset_path: str) -> Dict[str, Any]:
    """
    Import a data burn-in preset from file.

    Data burn-ins overlay metadata (timecode, shot name, frame number, etc.)
    onto rendered video.

    Args:
        preset_path: Path to the burn-in preset file

    Returns:
        Import result

    Example:
        >>> import_burn_in_preset("/presets/timecode_burnin.xml")
        {
            "success": True,
            "preset_path": "/presets/timecode_burnin.xml"
        }
    """
    try:
        project = get_current_project()

        # ImportBurnInPreset(presetPath)
        result = project.ImportBurnInPreset(preset_path)

        return {
            "success": bool(result),
            "preset_path": preset_path,
            "message": f"Burn-in preset {'imported' if result else 'import failed'}"
        }

    except Exception as e:
        logger.error(f"Error importing burn-in preset: {e}")
        return {
            "success": False,
            "error": str(e),
            "preset_path": preset_path
        }


def export_burn_in_preset(
    preset_name: str,
    export_path: str
) -> Dict[str, Any]:
    """
    Export a data burn-in preset to file.

    Args:
        preset_name: Name of the burn-in preset to export
        export_path: Destination path for preset file

    Returns:
        Export result

    Example:
        >>> export_burn_in_preset(
        ...     preset_name="Custom Timecode",
        ...     export_path="/presets/custom_timecode.xml"
        ... )
        {
            "success": True,
            "preset_name": "Custom Timecode",
            "export_path": "/presets/custom_timecode.xml"
        }
    """
    try:
        project = get_current_project()

        # ExportBurnInPreset(presetName, exportPath)
        result = project.ExportBurnInPreset(preset_name, export_path)

        return {
            "success": bool(result),
            "preset_name": preset_name,
            "export_path": export_path,
            "message": f"Burn-in preset {'exported' if result else 'export failed'}"
        }

    except Exception as e:
        logger.error(f"Error exporting burn-in preset: {e}")
        return {
            "success": False,
            "error": str(e),
            "preset_name": preset_name
        }


# ============================================================================
# LUT Management (MEDIUM PRIORITY)
# ============================================================================

def refresh_lut_list() -> Dict[str, Any]:
    """
    Refresh the list of available LUTs.

    Scans LUT folders and updates the LUT list. Useful after adding
    new LUTs to the system.

    Returns:
        Refresh result

    Example:
        >>> refresh_lut_list()
        {
            "success": True,
            "message": "LUT list refreshed"
        }
    """
    try:
        project = get_current_project()

        # RefreshLUTList()
        result = project.RefreshLUTList()

        return {
            "success": bool(result),
            "message": f"LUT list {'refreshed' if result else 'refresh failed'}"
        }

    except Exception as e:
        logger.error(f"Error refreshing LUT list: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# Tool Registration
# ============================================================================

def register_tools(mcp):
    """
    Register Advanced Render Operations tools with the MCP server.

    Args:
        mcp: FastMCP server instance

    Returns:
        Number of tools registered
    """
    from ..proxy import get_proxy

    proxy = get_proxy()

    # Register MEDIUM priority render resolution tools
    proxy.register_tool(
        "get_render_resolutions",
        get_render_resolutions,
        "delivery",
        "Get list of available render resolutions for a format/codec combination",
        {
            "render_format": {"type": "string", "description": "The render format (e.g., QuickTime, MP4)"},
            "codec": {"type": "string", "description": "The codec (e.g., Apple ProRes 422 HQ)"}
        }
    )

    proxy.register_tool(
        "get_current_render_format_and_codec",
        get_current_render_format_and_codec,
        "delivery",
        "Get the current render format and codec settings",
        {}
    )

    # Register MEDIUM priority preset management tools
    proxy.register_tool(
        "delete_render_preset",
        delete_render_preset,
        "delivery",
        "Delete a render preset",
        {"preset_name": {"type": "string", "description": "Name of the render preset to delete"}}
    )

    # Register MEDIUM priority burn-in preset tools
    proxy.register_tool(
        "import_burn_in_preset",
        import_burn_in_preset,
        "delivery",
        "Import a data burn-in preset from file",
        {"preset_path": {"type": "string", "description": "Path to the burn-in preset file"}}
    )

    proxy.register_tool(
        "export_burn_in_preset",
        export_burn_in_preset,
        "delivery",
        "Export a data burn-in preset to file",
        {
            "preset_name": {"type": "string", "description": "Name of the burn-in preset to export"},
            "export_path": {"type": "string", "description": "Destination path for preset file"}
        }
    )

    # Register MEDIUM priority LUT management tool
    proxy.register_tool(
        "refresh_lut_list",
        refresh_lut_list,
        "color",
        "Refresh the list of available LUTs (scans LUT folders)",
        {}
    )

    logger.info("Registered 6 Advanced Render Operations tools")
    return 6


# For standalone testing
if __name__ == "__main__":
    print("Advanced Render Operations Tools - Testing")
    print("=" * 60)

    try:
        current_format = get_current_render_format_and_codec()
        print(f"\nCurrent render settings: {current_format}")
    except Exception as e:
        print(f"Error: {e}")
