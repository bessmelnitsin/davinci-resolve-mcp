"""
Tool safety annotations for DaVinci Resolve MCP Server.

Provides three pre-built `ToolAnnotations` presets that classify every MCP
tool by its effect on the project, so clients running in autonomous mode can
gate destructive operations behind confirmations.

Classification rules (applied by classify_tool_name):

- READ_ONLY: pure getters/listers. `get_*`, `list_*`, `find_*`, `search_*`,
  `show_*`, `describe_*`, `check_*`, `is_*`, `has_*`, `validate_*`,
  `inspect_*`, `read_*`, `monitor_*` (status only).

- DESTRUCTIVE: deletes, resets, clears, unlinks, removes, replaces,
  overwrites. Anything an agent should not invoke without explicit user
  approval.  `delete_*`, `remove_*`, `reset_*`, `clear_*`, `drop_*`,
  `discard_*`, `unlink_*`, `replace_*`, `overwrite_*`, `revert_*`,
  `close_project`, `close_current_timeline`, `empty_*`, `purge_*`.

- SAFE_WRITE: everything else — adds, creates, imports, exports, applies,
  sets, opens, switches. Modifies state but does not destroy data.
"""

from mcp.types import ToolAnnotations


READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

SAFE_WRITE = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False,
)

DESTRUCTIVE = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=False,
)


_READ_ONLY_PREFIXES = (
    "get_", "list_", "find_", "search_", "show_", "describe_",
    "check_", "is_", "has_", "validate_", "inspect_", "read_",
    "count_",
)

_DESTRUCTIVE_PREFIXES = (
    "delete_", "remove_", "reset_", "clear_", "drop_", "discard_",
    "unlink_", "overwrite_", "revert_", "empty_", "purge_",
    "destroy_", "erase_", "wipe_",
)

# Specific destructive tools whose name doesn't start with a destructive prefix.
_DESTRUCTIVE_EXACT = frozenset({
    "replace_clip",
    "replace_clip_preserve_sub_clip",
    "close_project",
    "close_current_timeline",
    "delete_media",
    "unlink_proxy_media",
    "unlink_clips",
    "clear_clip_flags",
    "clear_clip_color",
    "clear_clip_mark_in_out",
    "clear_transcription_native",
    "reset_all_node_colors",
    "reset_all_grades",
})


def classify_tool_name(name: str) -> ToolAnnotations:
    """Return the appropriate ToolAnnotations for a tool based on its name."""
    if name in _DESTRUCTIVE_EXACT:
        return DESTRUCTIVE
    lower = name.lower()
    for prefix in _DESTRUCTIVE_PREFIXES:
        if lower.startswith(prefix):
            return DESTRUCTIVE
    for prefix in _READ_ONLY_PREFIXES:
        if lower.startswith(prefix):
            return READ_ONLY
    return SAFE_WRITE
