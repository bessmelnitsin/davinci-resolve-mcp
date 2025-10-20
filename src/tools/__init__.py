"""
Tools Module for DaVinci Resolve MCP

This module provides two modes of operation:

1. Search/Execute Mode (Recommended for tool-limited clients like Cursor)
   - Exposes only 4 tools: search, execute, get_categories, list_tools
   - Provides access to all 100+ operations through search and execute
   - Perfect for Cursor (40-tool limit)

2. Full Tool Mode (For clients without tool limits)
   - Exposes all individual tools directly
   - Better for exploration and auto-completion
   - Requires client to support 100+ tools

The mode is determined by the RESOLVE_MCP_MODE environment variable:
- "search_execute" or "search" -> Search/Execute Mode (default)
- "full" -> Full Tool Mode
"""

import os
import logging
from typing import Optional

logger = logging.getLogger("davinci-resolve-mcp.tools")

# Tool category modules (to be implemented in Phase 2)
TOOL_CATEGORIES = {
    'core': 'tools.core',
    'project': 'tools.project',
    'timeline': 'tools.timeline',
    'media': 'tools.media',
    'color': 'tools.color',
    'delivery': 'tools.delivery',
    'fusion': 'tools.fusion',
    'fairlight': 'tools.fairlight',
    'media_storage': 'tools.media_storage',
    'gallery': 'tools.gallery',
    'cache': 'tools.cache',
    'graph': 'tools.graph',
    'advanced': 'tools.advanced',
}


def get_mode() -> str:
    """
    Get the current tool mode from environment or config.

    Returns:
        "search_execute" or "full"
    """
    mode = os.environ.get('RESOLVE_MCP_MODE', 'search_execute').lower()

    # Normalize mode names
    if mode in ['search', 'search_execute', 'searchexecute']:
        return 'search_execute'
    elif mode in ['full', 'direct', 'all']:
        return 'full'
    else:
        logger.warning(f"Unknown mode '{mode}', defaulting to 'search_execute'")
        return 'search_execute'


def load_tools(mcp_server, mode: Optional[str] = None):
    """
    Load and register tools with the MCP server.

    Args:
        mcp_server: FastMCP server instance
        mode: Override mode ("search_execute" or "full"). If None, uses environment.

    Returns:
        Number of tools registered
    """
    actual_mode = mode or get_mode()
    logger.info(f"Loading tools in '{actual_mode}' mode")

    if actual_mode == 'search_execute':
        return load_search_execute_mode(mcp_server)
    else:
        return load_full_tool_mode(mcp_server)


def load_search_execute_mode(mcp_server):
    """
    Load search/execute mode - exposes only 4 tools.

    Recommended for Cursor and other tool-limited clients.

    Tools registered:
    1. search_davinci_resolve - Search for tools
    2. execute_davinci_resolve - Execute a tool
    3. get_davinci_resolve_categories - List categories
    4. list_davinci_resolve_tools - List all tools

    Args:
        mcp_server: FastMCP server instance

    Returns:
        Number of tools registered (4)
    """
    from .search_execute import register_search_execute_mode

    count = register_search_execute_mode(mcp_server)
    logger.info(f"Registered {count} search/execute tools")
    return count


def load_full_tool_mode(mcp_server):
    """
    Load full tool mode - exposes all individual tools.

    This mode dynamically loads all tool categories and registers
    each tool individually with the MCP server.

    Note: This will register 100+ tools. Only use if your client
    supports it (e.g., Claude Desktop without tool limits).

    Args:
        mcp_server: FastMCP server instance

    Returns:
        Number of tools registered
    """
    import importlib

    total_count = 0

    # Check if we should load only specific categories
    enabled_categories = os.environ.get('RESOLVE_MCP_CATEGORIES')
    if enabled_categories:
        categories = [cat.strip() for cat in enabled_categories.split(',')]
    else:
        categories = list(TOOL_CATEGORIES.keys())

    logger.info(f"Loading categories: {', '.join(categories)}")

    for category in categories:
        if category not in TOOL_CATEGORIES:
            logger.warning(f"Unknown category '{category}', skipping")
            continue

        module_path = TOOL_CATEGORIES[category]

        try:
            # Dynamically import the module
            module = importlib.import_module(module_path)

            # Call register_tools function in the module
            if hasattr(module, 'register_tools'):
                count = module.register_tools(mcp_server)
                total_count += count
                logger.info(f"Loaded {count} tools from '{category}' category")
            else:
                logger.warning(f"Module '{module_path}' has no register_tools function")

        except ModuleNotFoundError:
            logger.warning(f"Category module '{module_path}' not yet implemented, skipping")
        except Exception as e:
            logger.error(f"Error loading category '{category}': {e}")

    logger.info(f"Total tools registered: {total_count}")
    return total_count


# Convenience exports
__all__ = [
    'load_tools',
    'load_search_execute_mode',
    'load_full_tool_mode',
    'get_mode',
    'TOOL_CATEGORIES'
]
