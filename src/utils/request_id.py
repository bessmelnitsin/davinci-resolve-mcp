"""
Per-request correlation ID.

The HTTP auth middleware reads (or generates) an ``X-Request-ID`` header
and stashes it in a ContextVar so downstream code — logging, audit —
can attach it to records without plumbing the ID through every signature.

The ID is UUID4 (no security value, just correlation). Echoed back in the
response header so clients can grep for it.

Example audit line:

    {"ts": "...", "role": "color", "tool": "apply_lut",
     "request_id": "5c3f...", "ok": true, ...}
"""

from __future__ import annotations

import contextvars
import uuid
from typing import Optional

_request_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "mcp_request_id", default=None
)


def get() -> Optional[str]:
    """Current request ID, or None outside a request context."""
    return _request_id.get()


def set(value: str) -> contextvars.Token:
    """Set for the current context; returns a token for reset()."""
    return _request_id.set(value)


def reset(token: contextvars.Token) -> None:
    _request_id.reset(token)


def new() -> str:
    """Generate a fresh random request ID."""
    return uuid.uuid4().hex
