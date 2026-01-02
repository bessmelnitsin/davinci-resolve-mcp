
"""
DaVinci Resolve MCP Server (Refactored)
Main entry point that initializes functionality and registers tools.
"""

import logging
import sys

from src.server_instance import mcp
from src.context import set_resolve
from src.utils.resolve_connection import initialize_resolve

# Import tools to register them with the MCP server

import src.tools.media
import src.tools.timeline

import src.tools.project
import src.tools.color
import src.tools.delivery

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("davinci-resolve-mcp")

@mcp.resource("resolve://status")
def get_status() -> str:
    """Get the current status of the MCP server connection."""
    from src.context import get_resolve
    resolve = get_resolve()
    if resolve:
        return f"Connected to {resolve.GetProductName()} {resolve.GetVersionString()}"
    return "Not connected to DaVinci Resolve"

def main():
    """Main entry point for the MCP server."""
    logger.info("Initializing DaVinci Resolve MCP Server...")
    
    # Initialize connection to DaVinci Resolve
    resolve = initialize_resolve()
    
    if resolve:
        set_resolve(resolve)
        logger.info("Resolution context initialized.")
    else:
        logger.warning("Could not connect to DaVinci Resolve. Some tools will fail.")
    
    # Run the MCP server
    logger.info("Starting MCP server...")
    mcp.run()

if __name__ == "__main__":
    main()