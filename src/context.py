
"""
Global context for DaVinci Resolve MCP Server
Holds the singleton instance of the Resolve object
"""

_resolve_instance = None

def get_resolve():
    """Get the global DaVinci Resolve instance."""
    return _resolve_instance

def set_resolve(resolve):
    """Set the global DaVinci Resolve instance."""
    global _resolve_instance
    _resolve_instance = resolve
