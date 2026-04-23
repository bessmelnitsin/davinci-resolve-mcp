"""
Agent role definitions for the DaVinci Resolve MCP Server.

The server mirrors the human post-production team structure: each role is
scoped to a single DaVinci Resolve page (or a small cross-cutting concern)
and only exposes the tools that a human in that role would use.

This has three benefits for an autonomous agent team:

1. **Smaller tool surface per agent.** An LLM sees 20-50 focused tools instead
   of 289, giving it sharper tool selection and less context bloat.

2. **Natural safety boundary.** A Colorist agent cannot delete media pool items
   because those tools are not registered on its endpoint. This is enforced
   at registration time, on top of the `destructiveHint` annotations.

3. **Observability.** Each role gets its own auth token, so logs show which
   agent did what — critical for debugging a team of agents editing the same
   project.

Roles:

  - media      : Media page (import, bins, metadata, proxies, transcription)
  - edit       : Edit / Cut pages (timeline, clips, markers, subclips)
  - color      : Color page (grades, nodes, gallery, LUTs, color groups)
  - fusion     : Fusion page (compositions, nodes, generators, titles)
  - fairlight  : Fairlight page (audio tracks, volume, voice isolation)
  - deliver    : Deliver page (render queue, presets, formats)
  - director   : Cross-cutting — project + navigation. The "PM" that
                 opens/closes projects, switches pages, and queries status.
                 Usually paired with other roles or used alone as an
                 orchestrator.
  - full       : All tools — single-agent mode (the original server).
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class Role:
    name: str
    description: str
    # Tool-module dotted paths that this role exposes.
    tool_modules: Tuple[str, ...]
    # The Resolve page this role is "anchored" to. Tools registered by this
    # role will be auto-guarded by a PageLock that ensures the page is active
    # before they run. `None` = no page binding (cross-cutting).
    page: str | None = None


ROLES: Dict[str, Role] = {
    "media": Role(
        name="media",
        description="Media Librarian — imports, bins, metadata, proxies.",
        tool_modules=("src.tools.media", "src.tools.media_storage"),
        page="media",
    ),
    "edit": Role(
        name="edit",
        description="Editor — timeline assembly, clips, markers, subclips.",
        tool_modules=("src.tools.timeline",),
        page="edit",
    ),
    "color": Role(
        name="color",
        description="Colorist — grades, nodes, LUTs, gallery, color groups.",
        tool_modules=("src.tools.color",),
        page="color",
    ),
    "fusion": Role(
        name="fusion",
        description="VFX Artist — Fusion compositions, nodes, titles.",
        tool_modules=("src.tools.fusion",),
        page="fusion",
    ),
    "fairlight": Role(
        name="fairlight",
        description="Sound Designer — audio tracks, volume, voice isolation.",
        tool_modules=("src.tools.fairlight",),
        page="fairlight",
    ),
    "deliver": Role(
        name="deliver",
        description="Deliverer — render queue, presets, formats, export.",
        tool_modules=("src.tools.delivery",),
        page="deliver",
    ),
    "director": Role(
        name="director",
        description="Project Manager / orchestrator — projects, navigation.",
        tool_modules=("src.tools.project", "src.tools.navigation"),
        page=None,  # cross-cutting
    ),
    "full": Role(
        name="full",
        description="All tools combined — single-agent / legacy mode.",
        tool_modules=(
            "src.tools.media",
            "src.tools.media_storage",
            "src.tools.timeline",
            "src.tools.color",
            "src.tools.fusion",
            "src.tools.fairlight",
            "src.tools.delivery",
            "src.tools.project",
            "src.tools.navigation",
        ),
        page=None,
    ),
}


def resolve_roles(role_spec: str) -> List[Role]:
    """Parse a role spec like 'color' or 'color,deliver' or 'full' into Role objects.

    Args:
        role_spec: Comma-separated list of role names, or a single role name.

    Returns:
        List of Role objects in input order, deduplicated.

    Raises:
        ValueError: if any role name is unknown.
    """
    if not role_spec:
        raise ValueError("role spec must be non-empty")

    names = [n.strip().lower() for n in role_spec.split(",") if n.strip()]
    unknown = [n for n in names if n not in ROLES]
    if unknown:
        raise ValueError(
            f"Unknown role(s): {unknown}. Available: {sorted(ROLES.keys())}"
        )

    # Dedup preserving order
    seen: set = set()
    result: List[Role] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            result.append(ROLES[n])
    return result


def list_role_names() -> List[str]:
    """Return the sorted list of valid role names."""
    return sorted(ROLES.keys())
