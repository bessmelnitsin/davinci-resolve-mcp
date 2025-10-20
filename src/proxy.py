"""
Tool Proxy Layer for DaVinci Resolve MCP Server

This module implements a proxy/filtering layer that allows selective exposure
of tools based on configuration profiles. This is especially useful for:
- Cursor's 40-tool limitation
- Creating focused workflows (editing-only, color-grading-only, etc.)
- Reducing cognitive load by showing only relevant tools

The proxy supports:
- Profile-based filtering
- Category-based filtering
- Explicit tool inclusion/exclusion
- Maximum tool limits
- Search/Execute mode (2-tool mode for maximum flexibility)
"""

import os
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Set

logger = logging.getLogger("davinci-resolve-mcp.proxy")


class ToolProxy:
    """
    Manages tool registration, filtering, and execution based on configuration.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the tool proxy.

        Args:
            config_path: Path to configuration file. Defaults to ~/.resolve-mcp/config.yaml
        """
        self.config_path = config_path or Path.home() / ".resolve-mcp" / "config.yaml"
        self.config = self._load_config()
        self.tool_registry: Dict[str, Dict[str, Any]] = {}
        self.enabled_tools: Set[str] = set()
        self.categories: Dict[str, List[str]] = {}

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            logger.info(f"Config file not found at {self.config_path}, using defaults")
            return self._default_config()

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'mode': 'search_execute',  # 'search_execute' or 'full'
            'proxy_enabled': False,
            'max_tools': 40,
            'active_profile': 'full',
            'profiles': {
                'minimal': {
                    'description': 'Essential tools only (10 tools)',
                    'categories': ['core'],
                    'tools': [
                        'list_projects', 'open_project', 'list_timelines',
                        'set_current_timeline', 'list_media_pool_clips',
                        'import_media', 'add_clip_to_timeline', 'start_rendering'
                    ]
                },
                'editing': {
                    'description': 'Video editing workflow (35 tools)',
                    'categories': ['core', 'project', 'timeline', 'media'],
                    'exclude_tools': ['delete_project', 'quit_resolve_app']
                },
                'color_grading': {
                    'description': 'Color grading workflow (40 tools)',
                    'categories': ['core', 'project', 'color', 'gallery', 'graph']
                },
                'delivery': {
                    'description': 'Rendering and delivery (25 tools)',
                    'categories': ['core', 'project', 'delivery', 'cache']
                },
                'full': {
                    'description': 'All tools (100+ tools)',
                    'categories': 'all'
                }
            },
            'search_execute_mode': {
                'enabled': True,  # Changed to True by default
                'description': 'Recommended: Use search_davinci_resolve and execute_davinci_resolve (4 tools total)'
            }
        }

    def save_config(self):
        """Save current configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def register_tool(
        self,
        name: str,
        func: Callable,
        category: str,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Register a tool with the proxy.

        Args:
            name: Tool name (unique identifier)
            func: Callable function that implements the tool
            category: Category name (e.g., 'core', 'project', 'timeline')
            description: Human-readable description
            parameters: Dictionary describing parameters
        """
        self.tool_registry[name] = {
            'func': func,
            'category': category,
            'name': name,
            'description': description,
            'parameters': parameters or {}
        }

        # Add to category mapping
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(name)

        logger.debug(f"Registered tool: {name} (category: {category})")

    def get_enabled_tools(self) -> Set[str]:
        """
        Get set of tools to expose based on configuration.

        Returns:
            Set of tool names that should be enabled
        """
        # Check if proxy is enabled
        if not self.config.get('proxy_enabled', False):
            logger.info("Proxy disabled, enabling all tools")
            return set(self.tool_registry.keys())

        # Get active profile
        profile_name = self.config.get('active_profile', 'full')
        profile = self.config.get('profiles', {}).get(profile_name, {})

        if not profile:
            logger.warning(f"Profile '{profile_name}' not found, using all tools")
            return set(self.tool_registry.keys())

        logger.info(f"Loading profile: {profile_name}")

        # Start with empty set
        enabled = set()

        # Handle 'all' categories
        categories = profile.get('categories', [])
        if categories == 'all':
            enabled = set(self.tool_registry.keys())
        elif isinstance(categories, list):
            # Filter by category
            for category in categories:
                if category in self.categories:
                    enabled.update(self.categories[category])

        # Handle explicit tool list (overrides categories)
        if 'tools' in profile:
            explicit_tools = set(profile['tools'])
            # Only include tools that are registered
            enabled = enabled.intersection(explicit_tools) if enabled else explicit_tools

        # Handle exclusions
        exclude_tools = profile.get('exclude_tools', [])
        if exclude_tools:
            enabled = enabled - set(exclude_tools)

        # Apply max_tools limit
        max_tools = self.config.get('max_tools', 40)
        if len(enabled) > max_tools:
            logger.warning(
                f"Profile '{profile_name}' has {len(enabled)} tools, "
                f"but max is {max_tools}. Truncating."
            )
            # Sort to ensure consistent ordering
            enabled = set(sorted(enabled)[:max_tools])

        logger.info(f"Enabled {len(enabled)} tools from profile '{profile_name}'")
        return enabled

    def update_enabled_tools(self):
        """Update the cached set of enabled tools."""
        self.enabled_tools = self.get_enabled_tools()

    def is_tool_enabled(self, tool_name: str) -> bool:
        """
        Check if a tool is enabled.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool is enabled, False otherwise
        """
        return tool_name in self.enabled_tools

    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool

        Returns:
            Result from the tool execution

        Raises:
            ValueError: If tool not found or not enabled
        """
        if tool_name not in self.tool_registry:
            raise ValueError(f"Tool '{tool_name}' not found in registry")

        if not self.is_tool_enabled(tool_name):
            raise ValueError(
                f"Tool '{tool_name}' is not enabled in profile "
                f"'{self.config.get('active_profile')}'"
            )

        tool_info = self.tool_registry[tool_name]
        logger.debug(f"Executing tool: {tool_name}")

        try:
            return tool_info['func'](**kwargs)
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            raise

    def search_tools(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for tools matching query.

        Args:
            query: Search term (matches tool name or description)
            category: Filter by category (optional)
            limit: Maximum results to return

        Returns:
            List of matching tool information
        """
        results = []
        query_lower = query.lower()

        for name, info in self.tool_registry.items():
            # Filter by category if specified
            if category and info['category'] != category:
                continue

            # Check if enabled (if proxy is active)
            if self.config.get('proxy_enabled') and not self.is_tool_enabled(name):
                continue

            # Simple text matching
            if (query_lower in name.lower() or
                query_lower in info.get('description', '').lower()):
                results.append({
                    'name': name,
                    'category': info['category'],
                    'description': info.get('description', ''),
                    'parameters': info.get('parameters', {}),
                })

            if len(results) >= limit:
                break

        return results

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool information dictionary or None if not found
        """
        if tool_name not in self.tool_registry:
            return None

        info = self.tool_registry[tool_name].copy()
        # Remove the function reference (not serializable)
        info.pop('func', None)
        info['enabled'] = self.is_tool_enabled(tool_name)
        return info

    def get_categories(self) -> List[str]:
        """Get list of all available categories."""
        return sorted(self.categories.keys())

    def get_tools_by_category(self, category: str) -> List[str]:
        """
        Get list of tools in a category.

        Args:
            category: Category name

        Returns:
            List of tool names in the category
        """
        return self.categories.get(category, [])

    def get_profile_info(self) -> Dict[str, Any]:
        """
        Get information about the current profile.

        Returns:
            Dictionary with profile information
        """
        profile_name = self.config.get('active_profile', 'full')
        profile = self.config.get('profiles', {}).get(profile_name, {})

        return {
            'name': profile_name,
            'description': profile.get('description', ''),
            'categories': profile.get('categories', []),
            'tools': list(self.enabled_tools),
            'tool_count': len(self.enabled_tools),
            'max_tools': self.config.get('max_tools', 40),
            'proxy_enabled': self.config.get('proxy_enabled', False)
        }

    def switch_profile(self, profile_name: str) -> bool:
        """
        Switch to a different profile.

        Args:
            profile_name: Name of the profile to switch to

        Returns:
            True if successful, False otherwise
        """
        if profile_name not in self.config.get('profiles', {}):
            logger.error(f"Profile '{profile_name}' not found")
            return False

        self.config['active_profile'] = profile_name
        self.update_enabled_tools()
        self.save_config()

        logger.info(f"Switched to profile: {profile_name}")
        return True


# Global proxy instance
_proxy: Optional[ToolProxy] = None


def get_proxy(config_path: Optional[Path] = None) -> ToolProxy:
    """
    Get or create global proxy instance.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Global ToolProxy instance
    """
    global _proxy

    if _proxy is None:
        # Check environment variable for profile override
        env_profile = os.environ.get('RESOLVE_MCP_PROFILE')
        env_proxy_enabled = os.environ.get('RESOLVE_MCP_PROXY', 'false').lower() == 'true'
        env_max_tools = int(os.environ.get('RESOLVE_MCP_MAX_TOOLS', '40'))

        _proxy = ToolProxy(config_path)

        # Apply environment overrides
        if env_profile:
            _proxy.config['active_profile'] = env_profile
            logger.info(f"Profile overridden by environment: {env_profile}")

        if env_proxy_enabled:
            _proxy.config['proxy_enabled'] = True
            logger.info("Proxy enabled by environment")

        if env_max_tools:
            _proxy.config['max_tools'] = env_max_tools
            logger.info(f"Max tools overridden by environment: {env_max_tools}")

        # Update enabled tools
        _proxy.update_enabled_tools()

    return _proxy


def reset_proxy():
    """Reset the global proxy instance. Useful for testing."""
    global _proxy
    _proxy = None


# Decorator for easy tool registration
def tool(category: str, description: str = "", parameters: Optional[Dict] = None):
    """
    Decorator for registering tools with the proxy.

    Usage:
        @tool(category="project", description="Create a new project")
        def create_project(name: str) -> str:
            ...

    Args:
        category: Category name
        description: Tool description
        parameters: Parameter definitions
    """
    def decorator(func: Callable) -> Callable:
        proxy = get_proxy()
        proxy.register_tool(
            name=func.__name__,
            func=func,
            category=category,
            description=description or func.__doc__ or "",
            parameters=parameters
        )
        return func

    return decorator
