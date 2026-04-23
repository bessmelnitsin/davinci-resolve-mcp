"""
Dry-run mode for DESTRUCTIVE tools.

When enabled, any tool with ``destructiveHint=True`` returns a textual
description of what it WOULD do, instead of executing. Useful for:

  - Onboarding a new LLM (let it try everything risk-free first)
  - Integration-testing a prompt chain
  - A/B'ing an agent's plan before approval

Enabled via either:
  * env var ``MCP_DRY_RUN=1`` (process-wide, set at launch)
  * env var ``MCP_DRY_RUN_ROLES=color,deliver`` (per-role scoping)

The check is made at tool-invocation time, so toggling the env var in a
long-running process has no effect until restart — by design, so an agent
can't flip it mid-session.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

logger = logging.getLogger("davinci-resolve-mcp.dry_run")


def _env_roles() -> Optional[set[str]]:
    raw = os.environ.get("MCP_DRY_RUN_ROLES", "").strip()
    if not raw:
        return None
    return {r.strip() for r in raw.split(",") if r.strip()}


def is_dry_run(role: str) -> bool:
    """Return True if `role` should skip destructive execution."""
    if os.environ.get("MCP_DRY_RUN") == "1":
        return True
    roles = _env_roles()
    if roles and role in roles:
        return True
    return False


def describe_skipped_call(tool: str, args: tuple, kwargs: dict) -> str:
    """Format a human-readable 'would-do' message."""
    try:
        arg_repr = ", ".join([repr(a) for a in args])
        kwarg_repr = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
        sig = ", ".join(s for s in [arg_repr, kwarg_repr] if s)
    except Exception:
        sig = "<unreprable args>"
    payload = {
        "dry_run": True,
        "tool": tool,
        "would_call": f"{tool}({sig})",
        "note": "DRY_RUN is enabled; no changes were made to DaVinci Resolve.",
    }
    return json.dumps(payload, ensure_ascii=False)
