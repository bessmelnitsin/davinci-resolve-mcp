#!/usr/bin/env python3
"""
DaVinci Resolve MCP Server - Search/Execute Mode

This is a streamlined version of the MCP server that uses search/execute pattern.
Instead of exposing 100+ tools directly, it exposes just 4 tools:

1. search_davinci_resolve - Search for available operations
2. execute_davinci_resolve - Execute an operation by name
3. get_davinci_resolve_categories - List tool categories
4. list_davinci_resolve_tools - List all available tools

This approach:
- Stays within Cursor's 40-tool limit (only uses 4!)
- Provides access to ALL DaVinci Resolve operations
- Better discoverability through search
- More flexible than pre-filtering toolsets

Usage:
    python src/server_search_execute.py

Environment Variables:
    RESOLVE_MCP_MODE=search_execute  # Use search/execute mode (default)
    RESOLVE_MCP_DEBUG=1              # Enable debug logging
"""

import os
import sys
import logging
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import platform utilities
from utils.platform import get_resolve_paths

# Setup platform-specific paths and environment variables
paths = get_resolve_paths()
RESOLVE_API_PATH = paths["api_path"]
RESOLVE_LIB_PATH = paths["lib_path"]
RESOLVE_MODULES_PATH = paths["modules_path"]

os.environ["RESOLVE_SCRIPT_API"] = RESOLVE_API_PATH
os.environ["RESOLVE_SCRIPT_LIB"] = RESOLVE_LIB_PATH

# Add the module path to Python's path
if RESOLVE_MODULES_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULES_PATH)

# Import MCP
from mcp.server.fastmcp import FastMCP

# Import proxy
from proxy import get_proxy

# Configure logging
log_level = logging.DEBUG if os.environ.get('RESOLVE_MCP_DEBUG') else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("davinci-resolve-mcp")

# Log server version and platform
VERSION = "2.0.0-search-execute"
logger.info(f"Starting DaVinci Resolve MCP Server v{VERSION}")
logger.info(f"Mode: Search/Execute (4 tools)")
logger.info(f"Using Resolve API path: {RESOLVE_API_PATH}")

# Create MCP server instance
mcp = FastMCP("DaVinciResolveMCP")

# Initialize connection to DaVinci Resolve
resolve = None
try:
    sys.path.insert(0, RESOLVE_MODULES_PATH)
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
    if resolve:
        logger.info(f"Connected to DaVinci Resolve: {resolve.GetProductName()} {resolve.GetVersionString()}")
    else:
        logger.error("Failed to get Resolve object. Is DaVinci Resolve running?")
except ImportError as e:
    logger.error(f"Failed to import DaVinciResolveScript: {str(e)}")
    logger.error("Check that DaVinci Resolve is installed and running.")
    resolve = None
except Exception as e:
    logger.error(f"Unexpected error initializing Resolve: {str(e)}")
    resolve = None

# Initialize proxy
proxy = get_proxy()
logger.info(f"Proxy initialized: {proxy.get_profile_info()}")

# ------------------
# Register all existing tools with proxy
# ------------------

# This section registers all your existing tools from resolve_mcp_server.py
# with the proxy so they can be discovered via search and executed via execute

def register_existing_tools():
    """
    Register all existing DaVinci Resolve tools with the proxy.
    This makes them available via search_davinci_resolve and execute_davinci_resolve.

    Note: In the full implementation, you would import and register all tools
    from the existing resolve_mcp_server.py. For now, this is a template showing
    how to register them.
    """

    # Example: Register a simple tool
    @proxy.tool(category="core", description="Get DaVinci Resolve version information")
    def get_resolve_version() -> str:
        """Get DaVinci Resolve version information."""
        if resolve is None:
            return "Error: Not connected to DaVinci Resolve"
        return f"{resolve.GetProductName()} {resolve.GetVersionString()}"

    @proxy.tool(category="core", description="Get the current page in DaVinci Resolve")
    def get_current_page() -> str:
        """Get the current page open in DaVinci Resolve."""
        if resolve is None:
            return "Error: Not connected to DaVinci Resolve"
        return resolve.GetCurrentPage()

    @proxy.tool(category="core", description="Switch to a specific page in DaVinci Resolve")
    def switch_page(page: str) -> str:
        """Switch to a specific page in DaVinci Resolve."""
        if resolve is None:
            return "Error: Not connected to DaVinci Resolve"

        valid_pages = ['media', 'cut', 'edit', 'fusion', 'color', 'fairlight', 'deliver']
        if page.lower() not in valid_pages:
            return f"Error: Invalid page. Must be one of: {', '.join(valid_pages)}"

        success = resolve.OpenPage(page.lower())
        return f"Successfully switched to {page}" if success else f"Failed to switch to {page}"

    # TODO: Import and register all tools from resolve_mcp_server.py
    # For example:
    # from resolve_mcp_server import (
    #     list_projects, create_project, open_project,
    #     list_timelines, create_timeline, set_current_timeline,
    #     import_media, add_clip_to_timeline,
    #     # ... all other tools
    # )
    #
    # Then register each one:
    # proxy.register_tool("list_projects", list_projects, "project", "List all projects")
    # proxy.register_tool("create_project", create_project, "project", "Create a new project")
    # etc.

    logger.info(f"Registered {len(proxy.tool_registry)} tools with proxy")


# Register all existing tools
register_existing_tools()

# Update enabled tools based on config
proxy.update_enabled_tools()

# ------------------
# Register Search/Execute Tools
# ------------------

from tools.search_execute import register_search_execute_mode

# Register the 4 search/execute tools
tool_count = register_search_execute_mode(mcp)
logger.info(f"Registered {tool_count} search/execute tools with MCP server")

# ------------------
# Start Server
# ------------------

if __name__ == "__main__":
    logger.info("="* 60)
    logger.info("DaVinci Resolve MCP Server - Search/Execute Mode")
    logger.info("="* 60)
    logger.info(f"Total operations available: {len(proxy.tool_registry)}")
    logger.info(f"MCP tools exposed: {tool_count}")
    logger.info("="* 60)
    logger.info("")
    logger.info("Usage in AI Assistant:")
    logger.info('  1. search_davinci_resolve(query="create timeline")')
    logger.info('  2. execute_davinci_resolve(tool="create_timeline", parameters={...})')
    logger.info("")
    logger.info("Server is ready!")
    logger.info("="* 60)

    # The FastMCP framework will handle the actual server startup
    # when this module is run via `mcp dev` or similar
