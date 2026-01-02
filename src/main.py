#!/usr/bin/env python3
"""
DaVinci Resolve MCP Server - Main Entry Point
This file serves as the main entry point for running the DaVinci Resolve MCP server
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the parent directory to sys.path to ensure imports work
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

# Import the connection utils first to set environment variables
from src.utils.resolve_connection import check_environment_variables, set_default_environment_variables

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("davinci-resolve-mcp.main")

def check_setup():
    """Check if the environment is properly set up."""
    env_status = check_environment_variables()
    if not env_status["all_set"]:
        logger.warning(f"Setting default environment variables. Missing: {env_status['missing']}")
        set_default_environment_variables()
        
    return True

def run_server(variant="full", debug=False):
    """Run the MCP server."""
    if variant == "edit":
        from src.server_edit import mcp
        logger_name = "davinci-resolve-mcp-edit"
    else:
        # Default to full server
        from src.resolve_mcp_server import mcp
        logger_name = "davinci-resolve-mcp"
    
    # Set logging level based on debug flag
    if debug:
        logging.getLogger(logger_name).setLevel(logging.DEBUG)
        logger.info("Debug mode enabled")
    
    # Run the server
    logger.info(f"Starting DaVinci Resolve MCP Server ({variant})...")
    mcp.run()

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="DaVinci Resolve MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--variant", choices=["full", "edit"], default="full", 
                      help="Server variant to run (default: full)")
    args = parser.parse_args()
    
    if check_setup():
        run_server(variant=args.variant, debug=args.debug)
    else:
        logger.error("Failed to set up the environment. Please check the configuration.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 