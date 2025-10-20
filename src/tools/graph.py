"""
Graph Operations for DaVinci Resolve MCP

This module implements Graph (node graph) operations from the DaVinci Resolve API.
Graphs represent the node tree in the Color page for each clip.

API Coverage:
- GetNumNodes() - Get number of nodes in the graph
- SetLUT(nodeIndex, lutPath) - Apply LUT to a node
- GetLUT(nodeIndex) - Get LUT path from a node
- SetNodeCacheMode(nodeIndex, cacheMode) - Set node cache mode
- GetNodeCacheMode(nodeIndex) - Get node cache mode
- GetNodeLabel(nodeIndex) - Get node label/name
- GetToolsInNode(nodeIndex) - Get list of tools in a node
- SetNodeEnabled(nodeIndex, enabled) - Enable/disable a node
- ApplyGradeFromDRX(path, gradeMode) - Apply grade from DRX file
- ApplyArriCdlLut() - Apply ARRI CDL and LUT
- ResetAllGrades() - Reset all color grades
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("davinci-resolve-mcp.graph")

# Global resolve object (set by main server)
resolve = None


def set_resolve(resolve_instance):
    """Set the global resolve instance."""
    global resolve
    resolve = resolve_instance


def get_current_timeline_item_graph(layer_idx: Optional[int] = None):
    """
    Get the node graph for the currently selected timeline item.

    Args:
        layer_idx: Layer index (1-based, optional). Uses first layer if not specified.

    Returns:
        Graph object
    """
    if resolve is None:
        raise RuntimeError("Not connected to DaVinci Resolve")

    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        raise RuntimeError("No project open")

    timeline = project.GetCurrentTimeline()
    if not timeline:
        raise RuntimeError("No timeline selected")

    current_item = timeline.GetCurrentVideoItem()
    if not current_item:
        raise RuntimeError("No timeline item selected")

    if layer_idx:
        return current_item.GetNodeGraph(layer_idx)
    else:
        return current_item.GetNodeGraph()


# ------------------
# Graph Tools
# ------------------

def get_num_nodes(layer_idx: Optional[int] = None) -> int:
    """
    Get the number of nodes in the current timeline item's node graph.

    Args:
        layer_idx: Layer index (1-based, optional)

    Returns:
        Number of nodes in the graph

    Example:
        >>> get_num_nodes()
        5  # Graph has 5 nodes
    """
    try:
        graph = get_current_timeline_item_graph(layer_idx)
        num_nodes = graph.GetNumNodes()
        logger.info(f"Graph has {num_nodes} nodes")
        return num_nodes

    except Exception as e:
        logger.error(f"Error getting number of nodes: {e}")
        raise


def set_node_lut(
    node_index: int,
    lut_path: str,
    layer_idx: Optional[int] = None
) -> bool:
    """
    Apply a LUT (Look-Up Table) to a specific node.

    Args:
        node_index: Node index (1-based, 1 <= index <= num_nodes)
        lut_path: Path to LUT file (can be absolute or relative to LUT paths)
        layer_idx: Layer index (optional)

    Returns:
        True if successful, False otherwise

    Example:
        >>> set_node_lut(1, "/path/to/my_lut.cube")
        True

        >>> # Relative path (from custom LUT folders)
        >>> set_node_lut(2, "MyFolder/cool_look.cube")
        True
    """
    try:
        graph = get_current_timeline_item_graph(layer_idx)
        success = graph.SetLUT(node_index, lut_path)

        if success:
            logger.info(f"Successfully applied LUT to node {node_index}: {lut_path}")
        else:
            logger.warning(f"Failed to apply LUT to node {node_index}")

        return success

    except Exception as e:
        logger.error(f"Error setting LUT on node {node_index}: {e}")
        return False


def get_node_lut(
    node_index: int,
    layer_idx: Optional[int] = None
) -> str:
    """
    Get the LUT path applied to a specific node.

    Args:
        node_index: Node index (1-based)
        layer_idx: Layer index (optional)

    Returns:
        Relative LUT path, or empty string if no LUT applied

    Example:
        >>> get_node_lut(1)
        "MyFolder/cool_look.cube"
    """
    try:
        graph = get_current_timeline_item_graph(layer_idx)
        lut_path = graph.GetLUT(node_index)
        logger.info(f"Node {node_index} LUT: {lut_path or 'None'}")
        return lut_path or ""

    except Exception as e:
        logger.error(f"Error getting LUT from node {node_index}: {e}")
        return ""


def set_node_cache_mode(
    node_index: int,
    cache_mode: str,
    layer_idx: Optional[int] = None
) -> bool:
    """
    Set the cache mode for a specific node.

    Args:
        node_index: Node index (1-based)
        cache_mode: Cache mode - one of:
                   - "auto" or "AUTO_ENABLED" (-1)
                   - "disabled" or "DISABLED" (0)
                   - "enabled" or "ENABLED" (1)
        layer_idx: Layer index (optional)

    Returns:
        True if successful, False otherwise

    Example:
        >>> set_node_cache_mode(1, "enabled")
        True

        >>> set_node_cache_mode(2, "auto")
        True
    """
    try:
        graph = get_current_timeline_item_graph(layer_idx)

        # Map cache mode string to integer
        cache_mode_map = {
            "auto": -1,
            "AUTO_ENABLED": -1,
            "disabled": 0,
            "DISABLED": 0,
            "enabled": 1,
            "ENABLED": 1,
            -1: -1,
            0: 0,
            1: 1
        }

        cache_value = cache_mode_map.get(cache_mode)
        if cache_value is None:
            logger.error(f"Invalid cache mode: {cache_mode}")
            return False

        success = graph.SetNodeCacheMode(node_index, cache_value)

        if success:
            logger.info(f"Set node {node_index} cache mode to {cache_mode}")
        else:
            logger.warning(f"Failed to set cache mode for node {node_index}")

        return success

    except Exception as e:
        logger.error(f"Error setting cache mode for node {node_index}: {e}")
        return False


def get_node_cache_mode(
    node_index: int,
    layer_idx: Optional[int] = None
) -> str:
    """
    Get the cache mode for a specific node.

    Args:
        node_index: Node index (1-based)
        layer_idx: Layer index (optional)

    Returns:
        Cache mode: "auto", "disabled", or "enabled"

    Example:
        >>> get_node_cache_mode(1)
        "enabled"
    """
    try:
        graph = get_current_timeline_item_graph(layer_idx)
        cache_value = graph.GetNodeCacheMode(node_index)

        # Map integer to string
        cache_mode_map = {
            -1: "auto",
            0: "disabled",
            1: "enabled"
        }

        cache_mode = cache_mode_map.get(cache_value, "unknown")
        logger.info(f"Node {node_index} cache mode: {cache_mode}")
        return cache_mode

    except Exception as e:
        logger.error(f"Error getting cache mode from node {node_index}: {e}")
        return "unknown"


def get_node_label(
    node_index: int,
    layer_idx: Optional[int] = None
) -> str:
    """
    Get the label/name of a specific node.

    Args:
        node_index: Node index (1-based)
        layer_idx: Layer index (optional)

    Returns:
        Node label/name

    Example:
        >>> get_node_label(1)
        "Color Balance"
    """
    try:
        graph = get_current_timeline_item_graph(layer_idx)
        label = graph.GetNodeLabel(node_index)
        logger.info(f"Node {node_index} label: {label}")
        return label

    except Exception as e:
        logger.error(f"Error getting label from node {node_index}: {e}")
        return ""


def get_tools_in_node(
    node_index: int,
    layer_idx: Optional[int] = None
) -> List[str]:
    """
    Get list of tools (operations) in a specific node.

    Args:
        node_index: Node index (1-based)
        layer_idx: Layer index (optional)

    Returns:
        List of tool names used in the node

    Example:
        >>> get_tools_in_node(1)
        ["ColorWheels", "Curves", "Qualifier"]
    """
    try:
        graph = get_current_timeline_item_graph(layer_idx)
        tools = graph.GetToolsInNode(node_index)

        if tools:
            logger.info(f"Node {node_index} has {len(tools)} tools: {', '.join(tools)}")
        else:
            logger.info(f"Node {node_index} has no tools")

        return tools or []

    except Exception as e:
        logger.error(f"Error getting tools from node {node_index}: {e}")
        return []


def set_node_enabled(
    node_index: int,
    enabled: bool,
    layer_idx: Optional[int] = None
) -> bool:
    """
    Enable or disable a specific node.

    Args:
        node_index: Node index (1-based)
        enabled: True to enable, False to disable
        layer_idx: Layer index (optional)

    Returns:
        True if successful, False otherwise

    Example:
        >>> set_node_enabled(2, False)  # Disable node 2
        True

        >>> set_node_enabled(2, True)   # Enable node 2
        True
    """
    try:
        graph = get_current_timeline_item_graph(layer_idx)
        success = graph.SetNodeEnabled(node_index, enabled)

        if success:
            status = "enabled" if enabled else "disabled"
            logger.info(f"Successfully {status} node {node_index}")
        else:
            logger.warning(f"Failed to set enabled status for node {node_index}")

        return success

    except Exception as e:
        logger.error(f"Error setting enabled status for node {node_index}: {e}")
        return False


def apply_grade_from_drx(
    drx_path: str,
    grade_mode: int = 0,
    layer_idx: Optional[int] = None
) -> bool:
    """
    Apply a grade from a DRX (DaVinci Resolve eXchange) file.

    DRX files are still/grade export files from the Gallery.

    Args:
        drx_path: Absolute path to DRX file
        grade_mode: Grade application mode:
                   - 0: No keyframes
                   - 1: Source timecode aligned
                   - 2: Start frames aligned
        layer_idx: Layer index (optional)

    Returns:
        True if successful, False otherwise

    Example:
        >>> apply_grade_from_drx("/path/to/my_grade.drx", grade_mode=0)
        True
    """
    try:
        graph = get_current_timeline_item_graph(layer_idx)
        success = graph.ApplyGradeFromDRX(drx_path, grade_mode)

        if success:
            logger.info(f"Successfully applied grade from {drx_path}")
        else:
            logger.warning(f"Failed to apply grade from {drx_path}")

        return success

    except Exception as e:
        logger.error(f"Error applying grade from DRX: {e}")
        return False


def apply_arri_cdl_lut(layer_idx: Optional[int] = None) -> bool:
    """
    Apply ARRI CDL (Color Decision List) and LUT to the current node graph.

    This is specific to ARRI camera footage.

    Args:
        layer_idx: Layer index (optional)

    Returns:
        True if successful, False otherwise

    Example:
        >>> apply_arri_cdl_lut()
        True
    """
    try:
        graph = get_current_timeline_item_graph(layer_idx)
        success = graph.ApplyArriCdlLut()

        if success:
            logger.info("Successfully applied ARRI CDL and LUT")
        else:
            logger.warning("Failed to apply ARRI CDL and LUT")

        return success

    except Exception as e:
        logger.error(f"Error applying ARRI CDL and LUT: {e}")
        return False


def reset_all_grades(layer_idx: Optional[int] = None) -> bool:
    """
    Reset all color grades in the current node graph.

    This removes all color corrections and resets nodes to default.

    Args:
        layer_idx: Layer index (optional)

    Returns:
        True if successful, False otherwise

    Example:
        >>> reset_all_grades()
        True
    """
    try:
        graph = get_current_timeline_item_graph(layer_idx)
        success = graph.ResetAllGrades()

        if success:
            logger.info("Successfully reset all grades")
        else:
            logger.warning("Failed to reset grades")

        return success

    except Exception as e:
        logger.error(f"Error resetting grades: {e}")
        return False


def get_graph_info(layer_idx: Optional[int] = None) -> Dict[str, Any]:
    """
    Get comprehensive information about the current node graph.

    Returns:
        Dictionary with graph information:
        {
            "num_nodes": int,
            "nodes": [
                {
                    "index": int,
                    "label": str,
                    "lut": str,
                    "cache_mode": str,
                    "tools": [str, ...]
                },
                ...
            ]
        }

    Example:
        >>> get_graph_info()
        {
            "num_nodes": 3,
            "nodes": [
                {
                    "index": 1,
                    "label": "Color Balance",
                    "lut": "",
                    "cache_mode": "auto",
                    "tools": ["ColorWheels"]
                },
                ...
            ]
        }
    """
    try:
        graph = get_current_timeline_item_graph(layer_idx)
        num_nodes = graph.GetNumNodes()

        nodes_info = []
        for i in range(1, num_nodes + 1):
            node_info = {
                "index": i,
                "label": graph.GetNodeLabel(i),
                "lut": graph.GetLUT(i) or "",
                "cache_mode": get_node_cache_mode(i, layer_idx),
                "tools": graph.GetToolsInNode(i) or []
            }
            nodes_info.append(node_info)

        result = {
            "num_nodes": num_nodes,
            "nodes": nodes_info
        }

        logger.info(f"Retrieved info for {num_nodes} nodes")
        return result

    except Exception as e:
        logger.error(f"Error getting graph info: {e}")
        return {"num_nodes": 0, "nodes": [], "error": str(e)}


# ------------------
# Register Tools
# ------------------

def register_tools(mcp):
    """
    Register Graph tools with the MCP server.

    Args:
        mcp: FastMCP server instance

    Returns:
        Number of tools registered
    """
    from ..proxy import get_proxy

    proxy = get_proxy()

    # Register all tools
    tools = [
        ("get_num_nodes", get_num_nodes, "Get number of nodes in node graph", {}),
        ("set_node_lut", set_node_lut, "Apply LUT to a node", {
            "node_index": {"type": "integer", "description": "Node index (1-based)"},
            "lut_path": {"type": "string", "description": "Path to LUT file"},
            "layer_idx": {"type": "integer", "description": "Layer index (optional)"}
        }),
        ("get_node_lut", get_node_lut, "Get LUT from a node", {
            "node_index": {"type": "integer", "description": "Node index"},
            "layer_idx": {"type": "integer", "description": "Layer index (optional)"}
        }),
        ("set_node_cache_mode", set_node_cache_mode, "Set node cache mode", {
            "node_index": {"type": "integer", "description": "Node index"},
            "cache_mode": {"type": "string", "description": "auto, disabled, or enabled"},
            "layer_idx": {"type": "integer", "description": "Layer index (optional)"}
        }),
        ("get_node_cache_mode", get_node_cache_mode, "Get node cache mode", {
            "node_index": {"type": "integer", "description": "Node index"},
            "layer_idx": {"type": "integer", "description": "Layer index (optional)"}
        }),
        ("get_node_label", get_node_label, "Get node label/name", {
            "node_index": {"type": "integer", "description": "Node index"},
            "layer_idx": {"type": "integer", "description": "Layer index (optional)"}
        }),
        ("get_tools_in_node", get_tools_in_node, "Get list of tools in a node", {
            "node_index": {"type": "integer", "description": "Node index"},
            "layer_idx": {"type": "integer", "description": "Layer index (optional)"}
        }),
        ("set_node_enabled", set_node_enabled, "Enable or disable a node", {
            "node_index": {"type": "integer", "description": "Node index"},
            "enabled": {"type": "boolean", "description": "True to enable, False to disable"},
            "layer_idx": {"type": "integer", "description": "Layer index (optional)"}
        }),
        ("apply_grade_from_drx", apply_grade_from_drx, "Apply grade from DRX file", {
            "drx_path": {"type": "string", "description": "Path to DRX file"},
            "grade_mode": {"type": "integer", "description": "0=no keyframes, 1=timecode aligned, 2=start frames aligned"},
            "layer_idx": {"type": "integer", "description": "Layer index (optional)"}
        }),
        ("apply_arri_cdl_lut", apply_arri_cdl_lut, "Apply ARRI CDL and LUT", {
            "layer_idx": {"type": "integer", "description": "Layer index (optional)"}
        }),
        ("reset_all_grades", reset_all_grades, "Reset all color grades", {
            "layer_idx": {"type": "integer", "description": "Layer index (optional)"}
        }),
        ("get_graph_info", get_graph_info, "Get comprehensive node graph information", {
            "layer_idx": {"type": "integer", "description": "Layer index (optional)"}
        }),
    ]

    for name, func, description, parameters in tools:
        proxy.register_tool(name, func, "graph", description, parameters)

    logger.info(f"Registered {len(tools)} Graph tools")
    return len(tools)
