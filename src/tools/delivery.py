
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
