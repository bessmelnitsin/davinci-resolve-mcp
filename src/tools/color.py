
"""
Color Page Tools for DaVinci Resolve MCP
"""
from typing import Dict, Any

from src.server_instance import mcp
from src.context import get_resolve
from src.api.color_operations import (
    get_current_node as get_node_impl,
    get_color_wheels as get_wheels_impl,
    apply_lut as apply_lut_impl,
    set_color_wheel_param as set_param_impl,
    add_node as add_node_impl,
    copy_grade as copy_grade_impl
)

@mcp.resource("resolve://color/current-node")
def get_current_color_node() -> Dict[str, Any]:
    """Get information about the current node in the color page."""
    resolve = get_resolve()
    return get_node_impl(resolve)

@mcp.resource("resolve://color/wheels/{node_index}")
def get_color_wheel_params(node_index: int = None) -> Dict[str, Any]:
    """Get color wheel parameters for a specific node."""
    resolve = get_resolve()
    return get_wheels_impl(resolve, node_index)

@mcp.tool()
def apply_lut(lut_path: str, node_index: int = None) -> str:
    """Apply a LUT to a node."""
    resolve = get_resolve()
    return apply_lut_impl(resolve, lut_path, node_index)

@mcp.tool()
def set_color_wheel_param(wheel: str, param: str, value: float, node_index: int = None) -> str:
    """Set a color wheel parameter for a node."""
    resolve = get_resolve()
    return set_param_impl(resolve, wheel, param, value, node_index)

@mcp.tool()
def add_node(node_type: str = "serial", label: str = None) -> str:
    """Add a new node to the current grade."""
    resolve = get_resolve()
    return add_node_impl(resolve, node_type, label)

@mcp.tool()
def copy_grade(source_clip_name: str = None, target_clip_name: str = None, mode: str = "full") -> str:
    """Copy a grade from one clip to another."""
    resolve = get_resolve()
    return copy_grade_impl(resolve, source_clip_name, target_clip_name, mode)
