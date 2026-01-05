"""
Fusion Page Tools for DaVinci Resolve MCP

Visual effects and compositing functionality:
- Fusion composition access
- Node creation and manipulation
- Text and title effects
- Templates and presets
"""
from typing import Dict, Any, List, Tuple

from src.server_instance import mcp
from src.context import get_resolve
from src.api.fusion_operations import (
    get_fusion_comp,
    create_fusion_clip,
    add_text_plus,
    create_lower_third,
    list_fusion_templates,
    insert_generator,
    insert_title,
    get_fusion_node_list,
    export_fusion_comp,
    import_fusion_comp,
)


# ============================================================
# Fusion Composition Tools
# ============================================================

@mcp.tool()
def get_fusion_composition(clip_name: str = None) -> str:
    """Get Fusion composition information for a timeline clip.
    
    Args:
        clip_name: Name of the clip (uses current clip if not specified)
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = get_fusion_comp(resolve, clip_name)
    if "error" in result:
        return f"Error: {result['error']}"
    
    if result.get("success"):
        info = result.get("fusion_info", {})
        lines = ["Fusion Composition:"]
        lines.append(f"  Clip: {info.get('clip_name', 'Unknown')}")
        lines.append(f"  Comp Count: {info.get('comp_count', 0)}")
        
        comps = info.get("compositions", [])
        if comps:
            lines.append("  Compositions:")
            for comp in comps:
                lines.append(f"    • {comp}")
        
        return "\n".join(lines)
    
    return result.get("message", "Could not get Fusion composition")


@mcp.tool()
def create_fusion_clip_tool(clip_name: str = None) -> str:
    """Convert a timeline clip to a Fusion clip for advanced compositing.
    
    Args:
        clip_name: Name of the clip to convert (uses current selection if not specified)
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = create_fusion_clip(resolve, clip_name)
    if "error" in result:
        return f"Error: {result['error']}"
    
    if result.get("success"):
        return result.get("message", "Created Fusion clip")
    
    return result.get("message", "Failed to create Fusion clip")


@mcp.tool()
def list_fusion_templates_tool() -> str:
    """List available Fusion templates and generators.
    
    Returns categories of available Fusion elements.
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = list_fusion_templates(resolve)
    if "error" in result:
        return f"Error: {result['error']}"
    
    lines = ["Available Fusion Templates:"]
    
    generators = result.get("generators", [])
    if generators:
        lines.append(f"\nGenerators ({len(generators)}):")
        for gen in generators[:15]:
            lines.append(f"  • {gen}")
        if len(generators) > 15:
            lines.append(f"  ... and {len(generators) - 15} more")
    
    titles = result.get("titles", [])
    if titles:
        lines.append(f"\nTitles ({len(titles)}):")
        for title in titles[:15]:
            lines.append(f"  • {title}")
        if len(titles) > 15:
            lines.append(f"  ... and {len(titles) - 15} more")
    
    fusion_templates = result.get("fusion_templates", [])
    if fusion_templates:
        lines.append(f"\nFusion Templates ({len(fusion_templates)}):")
        for tmpl in fusion_templates[:15]:
            lines.append(f"  • {tmpl}")
        if len(fusion_templates) > 15:
            lines.append(f"  ... and {len(fusion_templates) - 15} more")
    
    return "\n".join(lines)


# ============================================================
# Text and Graphics Tools
# ============================================================

@mcp.tool()
def add_text_plus_node(text: str, font: str = "Arial", 
                       size: float = 0.1,
                       position_x: float = 0.5, 
                       position_y: float = 0.5,
                       color_r: float = 1.0,
                       color_g: float = 1.0,
                       color_b: float = 1.0) -> str:
    """Add a Text+ node to the current Fusion composition.
    
    Args:
        text: Text content to display
        font: Font family name (default: Arial)
        size: Text size relative to frame (0.0-1.0, default: 0.1)
        position_x: Horizontal position (0.0=left, 1.0=right, default: 0.5=center)
        position_y: Vertical position (0.0=bottom, 1.0=top, default: 0.5=center)
        color_r: Red component (0.0-1.0, default: 1.0)
        color_g: Green component (0.0-1.0, default: 1.0)
        color_b: Blue component (0.0-1.0, default: 1.0)
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    position = (position_x, position_y)
    color = (color_r, color_g, color_b)
    
    result = add_text_plus(resolve, text, font, size, position, color)
    if "error" in result:
        return f"Error: {result['error']}"
    
    if result.get("success"):
        return result.get("message", f"Added Text+ node with: '{text}'")
    
    return result.get("message", "Failed to add Text+ node")


@mcp.tool()
def create_lower_third_tool(name: str, title: str, 
                            subtitle: str = "",
                            style: str = "minimal") -> str:
    """Create a lower third graphic template.
    
    Args:
        name: Name for the Fusion composition
        title: Main title text
        subtitle: Secondary text (optional)
        style: Style preset - 'minimal', 'modern', or 'classic' (default: minimal)
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = create_lower_third(resolve, name, title, subtitle, style)
    if "error" in result:
        return f"Error: {result['error']}"
    
    lines = [f"Lower Third Template: {name}"]
    lines.append(f"  Title: {title}")
    if subtitle:
        lines.append(f"  Subtitle: {subtitle}")
    lines.append(f"  Style: {style}")
    
    if result.get("instructions"):
        lines.append("\nInstructions:")
        lines.append(result["instructions"])
    
    return "\n".join(lines)


# ============================================================
# Insert Elements Tools
# ============================================================

@mcp.tool()
def insert_fusion_generator(generator_name: str, 
                            duration_frames: int = 150,
                            track_index: int = 1) -> str:
    """Insert a generator into the timeline.
    
    Args:
        generator_name: Name of the generator (e.g., 'Solid Color', '10 Point Grid')
        duration_frames: Duration in frames (default: 150)
        track_index: Video track to insert on (default: 1)
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = insert_generator(resolve, generator_name, duration_frames, track_index)
    if "error" in result:
        return f"Error: {result['error']}"
    
    if result.get("success"):
        return f"Inserted generator '{generator_name}' ({duration_frames} frames) on track {track_index}"
    
    return result.get("message", "Failed to insert generator")


@mcp.tool()
def insert_fusion_title(title_name: str = "Text+") -> str:
    """Insert a Fusion title into the timeline.
    
    Args:
        title_name: Name of the title template (default: Text+)
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = insert_title(resolve, title_name)
    if "error" in result:
        return f"Error: {result['error']}"
    
    if result.get("success"):
        return f"Inserted title '{title_name}' into timeline"
    
    return result.get("message", "Failed to insert title")


# ============================================================
# Fusion Node Tools
# ============================================================

@mcp.tool()
def get_fusion_nodes() -> str:
    """Get list of nodes in the current Fusion composition.
    
    Shows all nodes and their connections in the active Fusion comp.
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = get_fusion_node_list(resolve)
    if "error" in result:
        return f"Error: {result['error']}"
    
    nodes = result.get("nodes", [])
    if not nodes:
        return "No nodes found in current Fusion composition"
    
    lines = [f"Fusion Nodes ({len(nodes)}):"]
    for node in nodes:
        node_type = node.get("type", "Unknown")
        node_name = node.get("name", "Unnamed")
        lines.append(f"  • {node_name} ({node_type})")
    
    return "\n".join(lines)


# ============================================================
# Export/Import Tools
# ============================================================

@mcp.tool()
def export_fusion_composition(output_path: str) -> str:
    """Export current Fusion composition as a .setting file.
    
    The exported file can be reused in other projects or shared.
    
    Args:
        output_path: Path to save the .setting file
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = export_fusion_comp(resolve, output_path)
    if "error" in result:
        return f"Error: {result['error']}"
    
    if result.get("success"):
        return f"Exported Fusion composition to: {output_path}"
    
    return result.get("message", "Failed to export Fusion composition")


@mcp.tool()
def import_fusion_composition(setting_path: str, 
                              clip_name: str = None) -> str:
    """Import a .setting file as a Fusion composition.
    
    Args:
        setting_path: Path to the .setting file
        clip_name: Clip to apply to (uses first clip if not specified)
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    result = import_fusion_comp(resolve, setting_path, clip_name)
    if "error" in result:
        return f"Error: {result['error']}"
    
    if result.get("success"):
        target = clip_name or "selected clip"
        return f"Imported Fusion composition from '{setting_path}' to {target}"
    
    return result.get("message", "Failed to import Fusion composition")


# ============================================================
# Resources
# ============================================================

@mcp.resource("resolve://fusion/templates")
def get_templates_resource() -> Dict[str, Any]:
    """Get all available Fusion templates."""
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    return list_fusion_templates(resolve)


@mcp.resource("resolve://fusion/current-comp")
def get_current_comp_resource() -> Dict[str, Any]:
    """Get current Fusion composition info."""
    resolve = get_resolve()
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    return get_fusion_comp(resolve)
