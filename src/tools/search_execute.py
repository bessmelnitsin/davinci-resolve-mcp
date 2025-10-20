"""
Search and Execute Tools for DaVinci Resolve MCP

This module implements a two-tool interface that provides access to all
DaVinci Resolve operations while staying within tool count limits (e.g., Cursor's 40-tool limit).

Instead of exposing 100+ individual tools, we expose just 2:
1. search_davinci_resolve - Search for available tools
2. execute_davinci_resolve - Execute a tool by name with parameters

This pattern allows AI assistants to:
- Discover available operations dynamically
- Execute any operation without tool count limits
- Provide better discoverability through search

Usage in AI Assistant:
1. AI searches: search_davinci_resolve(query="create timeline")
2. AI gets results with tool names and parameters
3. AI executes: execute_davinci_resolve(tool="create_timeline", parameters={...})
"""

import logging
from typing import List, Dict, Any, Optional
from ..proxy import get_proxy

logger = logging.getLogger("davinci-resolve-mcp.search_execute")


def search_davinci_resolve(
    query: str,
    category: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Search for DaVinci Resolve tools matching the query.

    This tool allows you to discover what operations are available in DaVinci Resolve.
    Search by keywords, operation names, or descriptions to find the right tool.

    Args:
        query: Search term (e.g., "timeline", "import media", "color grading", "render")
        category: Optional filter by category. Options:
                  - "core" - Basic operations (switch page, version info)
                  - "project" - Project management (create, open, save projects)
                  - "timeline" - Timeline operations (create, edit timelines)
                  - "media" - Media pool operations (import, organize media)
                  - "color" - Color grading operations (LUTs, color wheels, nodes)
                  - "delivery" - Rendering and export operations
                  - "fusion" - Fusion page operations
                  - "fairlight" - Fairlight audio operations
                  - "gallery" - Gallery and stills management
                  - "graph" - Node graph operations
                  - "cache" - Cache management
                  - "advanced" - Object inspection and app control
        limit: Maximum number of results to return (default: 10)

    Returns:
        JSON string containing matching tools with their:
        - name: Tool name to use with execute_davinci_resolve
        - description: What the tool does
        - category: Tool category
        - parameters: Required and optional parameters

    Examples:
        >>> search_davinci_resolve("create timeline")
        Returns tools for creating timelines

        >>> search_davinci_resolve("import", category="media")
        Returns media import tools

        >>> search_davinci_resolve("render", limit=5)
        Returns up to 5 rendering-related tools
    """
    import json

    try:
        proxy = get_proxy()
        results = proxy.search_tools(query=query, category=category, limit=limit)

        # Format results for better readability
        formatted_results = {
            "query": query,
            "category": category,
            "found": len(results),
            "tools": results
        }

        return json.dumps(formatted_results, indent=2)

    except Exception as e:
        logger.error(f"Error searching tools: {e}")
        return json.dumps({
            "error": str(e),
            "query": query,
            "tools": []
        })


def execute_davinci_resolve(
    tool: str,
    parameters: Optional[Dict[str, Any]] = None
) -> str:
    """
    Execute a DaVinci Resolve tool by name.

    After finding a tool using search_davinci_resolve, use this function to execute it.
    Provide the tool name and any required parameters.

    Args:
        tool: Name of the tool to execute (from search results)
        parameters: Dictionary of parameters for the tool. Parameters should match
                   those returned by search_davinci_resolve for this tool.

    Returns:
        Result from the tool execution as a JSON string.
        On success: {"success": true, "result": <tool result>}
        On error: {"success": false, "error": <error message>}

    Examples:
        >>> # First, search for the tool
        >>> search_davinci_resolve("create timeline")

        >>> # Then execute it
        >>> execute_davinci_resolve(
        ...     tool="create_timeline",
        ...     parameters={"name": "My New Timeline"}
        ... )

        >>> # Import media
        >>> execute_davinci_resolve(
        ...     tool="import_media",
        ...     parameters={"file_path": "/path/to/video.mp4"}
        ... )

        >>> # Start rendering
        >>> execute_davinci_resolve(tool="start_rendering")
    """
    import json

    try:
        proxy = get_proxy()
        params = parameters or {}

        logger.info(f"Executing tool: {tool} with parameters: {params}")

        # Execute the tool through the proxy
        result = proxy.execute_tool(tool, **params)

        return json.dumps({
            "success": True,
            "tool": tool,
            "result": result
        }, indent=2)

    except ValueError as e:
        # Tool not found or not enabled
        logger.error(f"Tool execution failed: {e}")
        return json.dumps({
            "success": False,
            "tool": tool,
            "error": str(e),
            "suggestion": "Use search_davinci_resolve to find available tools"
        })

    except Exception as e:
        # Execution error
        logger.error(f"Error executing tool '{tool}': {e}")
        return json.dumps({
            "success": False,
            "tool": tool,
            "error": str(e)
        })


def get_tool_categories() -> str:
    """
    Get a list of all available tool categories.

    Returns:
        JSON string with category names and descriptions.
    """
    import json

    categories = {
        "core": "Basic operations - version info, page switching, connection",
        "project": "Project management - create, open, save, settings",
        "timeline": "Timeline operations - create, edit, markers, tracks",
        "media": "Media pool - import, organize, bins, clips",
        "color": "Color grading - LUTs, color wheels, nodes, grades",
        "delivery": "Rendering and export - render queue, presets, jobs",
        "fusion": "Fusion page - compositions, nodes, effects",
        "fairlight": "Fairlight audio - tracks, mixing, effects",
        "media_storage": "Media storage - volumes, folders, files",
        "gallery": "Gallery and stills - albums, stills, PowerGrades",
        "graph": "Node graphs - color nodes, operations",
        "cache": "Cache management - render cache, optimization",
        "advanced": "Advanced - object inspection, app control"
    }

    proxy = get_proxy()
    available_categories = proxy.get_categories()

    return json.dumps({
        "categories": {
            cat: desc
            for cat, desc in categories.items()
            if cat in available_categories
        }
    }, indent=2)


def list_all_tools(category: Optional[str] = None) -> str:
    """
    List all available tools, optionally filtered by category.

    Args:
        category: Optional category to filter by

    Returns:
        JSON string with all tools organized by category
    """
    import json

    try:
        proxy = get_proxy()

        if category:
            tools = proxy.get_tools_by_category(category)
            result = {
                "category": category,
                "count": len(tools),
                "tools": [
                    proxy.get_tool_info(tool_name)
                    for tool_name in tools
                ]
            }
        else:
            # Get all categories
            categories = proxy.get_categories()
            result = {
                "categories": {}
            }

            for cat in categories:
                tools = proxy.get_tools_by_category(cat)
                result["categories"][cat] = {
                    "count": len(tools),
                    "tools": [tool for tool in tools]
                }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return json.dumps({"error": str(e)})


# Register tools with MCP
def register_tools(mcp):
    """
    Register search and execute tools with the MCP server.

    This is the recommended approach for clients with tool count limits.
    Instead of registering 100+ individual tools, we register just 2 tools
    that provide access to all functionality.

    Args:
        mcp: FastMCP server instance
    """
    from ..proxy import get_proxy

    proxy = get_proxy()

    # Register the search tool
    @mcp.tool()
    def search_davinci_resolve_tool(
        query: str,
        category: str = None,
        limit: int = 10
    ) -> str:
        """Search for DaVinci Resolve tools matching the query."""
        return search_davinci_resolve(query, category, limit)

    # Register the execute tool
    @mcp.tool()
    def execute_davinci_resolve_tool(
        tool: str,
        parameters: Dict[str, Any] = None
    ) -> str:
        """Execute a DaVinci Resolve tool by name."""
        return execute_davinci_resolve(tool, parameters)

    # Optional: Register helper tools
    @mcp.tool()
    def get_davinci_resolve_categories() -> str:
        """Get list of all tool categories."""
        return get_tool_categories()

    @mcp.tool()
    def list_davinci_resolve_tools(category: str = None) -> str:
        """List all available tools, optionally filtered by category."""
        return list_all_tools(category)

    logger.info("Registered search/execute tools for DaVinci Resolve")

    # Return count of tools registered
    return 4  # search, execute, categories, list


# Convenience function for backward compatibility
def register_search_execute_mode(mcp):
    """
    Enable search/execute mode - exposes only search and execute tools.

    This is the recommended mode for clients with tool count limits like Cursor (40 tools).
    Instead of exposing all individual tools, exposes just:
    1. search_davinci_resolve - Find tools
    2. execute_davinci_resolve - Run tools
    3. get_categories - List categories (helper)
    4. list_tools - List all tools (helper)

    Total: 4 tools that provide access to 100+ operations

    Args:
        mcp: FastMCP server instance

    Returns:
        Number of tools registered (4)
    """
    return register_tools(mcp)
