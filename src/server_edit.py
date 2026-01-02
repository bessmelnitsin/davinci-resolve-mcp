"""
DaVinci Resolve MCP Server - Edit Page Variant
A focused server for Edit page operations using shared modules.
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP
from src.context import set_resolve, get_resolve
from src.utils.resolve_connection import initialize_resolve

# Import tools to register them

import src.tools.media
import src.tools.timeline


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("davinci-resolve-mcp-edit")

# Initialize MCP Server (separate instance for Edit variant)
mcp = FastMCP("DaVinciResolveEdit")

# ==========================================
# Core & Navigation Tools
# ==========================================

@mcp.resource("resolve://version")
def get_resolve_version() -> str:
    """Get DaVinci Resolve version information."""
    resolve = get_resolve()
    if resolve is None: return "Error: Not connected"
    return f"{resolve.GetProductName()} {resolve.GetVersionString()}"

@mcp.resource("resolve://current-page")
def get_current_page() -> str:
    """Get the current page open in DaVinci Resolve."""
    resolve = get_resolve()
    if resolve is None: return "Error: Not connected"
    return resolve.GetCurrentPage()

@mcp.tool()
def switch_page(page: str) -> str:
    """Switch to a specific page (media, cut, edit, fusion, color, fairlight, deliver)."""
    resolve = get_resolve()
    if resolve is None: return "Error: Not connected"
    valid_pages = ['media', 'cut', 'edit', 'fusion', 'color', 'fairlight', 'deliver']
    if page.lower() not in valid_pages:
        return f"Error: Invalid page. Available: {', '.join(valid_pages)}"
    if resolve.OpenPage(page.lower()):
        return f"Switched to {page} page"
    return f"Failed to switch to {page} page"

def main():
    """Main entry point for the Edit server variant."""
    logger.info("Initializing DaVinci Resolve MCP Edit Server...")
    
    # Initialize connection
    resolve = initialize_resolve()
    if resolve:
        set_resolve(resolve)
        logger.info(f"Connected to {resolve.GetProductName()} {resolve.GetVersionString()}")
    else:
        logger.warning("Could not connect to DaVinci Resolve. Some tools will fail.")
    
    # Run the MCP server
    logger.info("Starting MCP Edit server...")
    mcp.run()

if __name__ == "__main__":
    main()
