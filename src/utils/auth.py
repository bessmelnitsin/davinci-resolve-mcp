"""
Simple Bearer-token authentication for HTTP transport.

For local stdio use, auth is not needed. For remote HTTP / multi-agent use,
every request must carry `Authorization: Bearer <token>`.

Tokens are supplied via environment variables:

  - MCP_AUTH_TOKEN=<token>          (single shared token; simplest)
  - MCP_AUTH_TOKENS=<role>:<token>,<role>:<token>,...   (per-role tokens)

If neither is set and `--transport http` is used, the server refuses to start.

This module exposes a helper that validates a request. Integration with
FastMCP's HTTP layer is done in server_factory.py via an ASGI middleware.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class AuthConfig:
    """Parsed auth configuration.

    Attributes:
        enabled: If False, auth is disabled (stdio mode).
        shared_token: A single token that grants access regardless of role.
        role_tokens: Mapping of role name -> token, for per-role auth.
    """
    enabled: bool
    shared_token: Optional[str] = None
    role_tokens: Dict[str, str] = None  # type: ignore[assignment]

    def validate_header(self, authorization_header: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate an incoming Authorization header.

        Args:
            authorization_header: Value of the Authorization HTTP header.

        Returns:
            (allowed, matched_role) — `matched_role` is the role the token
            maps to, or 'shared' for the shared token, or None if denied.
        """
        if not self.enabled:
            return True, "anonymous"

        if not authorization_header:
            return False, None

        parts = authorization_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return False, None

        token = parts[1]

        if self.shared_token and token == self.shared_token:
            return True, "shared"

        if self.role_tokens:
            for role, expected in self.role_tokens.items():
                if token == expected:
                    return True, role

        return False, None


def load_from_env(enabled: bool) -> AuthConfig:
    """Build an AuthConfig from environment variables.

    Args:
        enabled: Whether auth should be enforced. Typically True for HTTP.

    Returns:
        An AuthConfig. If `enabled` is True and no tokens are configured,
        raises RuntimeError rather than silently allowing open access.
    """
    if not enabled:
        return AuthConfig(enabled=False)

    shared = os.environ.get("MCP_AUTH_TOKEN") or None
    raw_role = os.environ.get("MCP_AUTH_TOKENS", "")
    role_tokens: Dict[str, str] = {}
    if raw_role:
        for pair in raw_role.split(","):
            pair = pair.strip()
            if not pair:
                continue
            if ":" not in pair:
                raise ValueError(
                    f"MCP_AUTH_TOKENS entry {pair!r} is not in 'role:token' form"
                )
            role, tok = pair.split(":", 1)
            role_tokens[role.strip()] = tok.strip()

    if not shared and not role_tokens:
        raise RuntimeError(
            "HTTP transport requested but no auth tokens configured. "
            "Set MCP_AUTH_TOKEN=<token> or MCP_AUTH_TOKENS=role1:tok1,role2:tok2"
        )

    return AuthConfig(
        enabled=True,
        shared_token=shared,
        role_tokens=role_tokens,
    )
