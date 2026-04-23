"""
Global context for DaVinci Resolve MCP Server.

Holds the singleton Resolve instance and provides an auto-reconnect layer:
if the underlying COM/py-bridge object dies (Resolve crashed or was
restarted), calls to `get_resolve()` will transparently re-initialize it.

Reconnect attempts are rate-limited (one every `_RECONNECT_COOLDOWN`
seconds) so a barrage of tool calls against a down Resolve doesn't DOS
the connection code path.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

logger = logging.getLogger("davinci-resolve-mcp.context")


_resolve_instance = None
_lock = threading.Lock()

# Reconnect policy -----------------------------------------------------------
_RECONNECT_COOLDOWN = 5.0  # seconds between attempts
_last_attempt: float = 0.0
_reconnect_enabled: bool = True


def get_resolve():
    """Get the global DaVinci Resolve instance.

    If the stored instance has gone stale (Resolve was closed or crashed),
    transparently tries to reconnect at most once per `_RECONNECT_COOLDOWN`.
    """
    global _resolve_instance, _last_attempt

    inst = _resolve_instance
    if inst is not None and _is_alive(inst):
        return inst

    if not _reconnect_enabled:
        return inst  # may be None

    now = time.monotonic()
    with _lock:
        # Double-checked: another thread may have reconnected already.
        inst = _resolve_instance
        if inst is not None and _is_alive(inst):
            return inst

        if now - _last_attempt < _RECONNECT_COOLDOWN:
            return inst  # honor the cooldown; caller gets stale/None

        _last_attempt = now
        new_inst = _try_reconnect()
        if new_inst is not None:
            _resolve_instance = new_inst
            logger.info("Resolve connection re-established")
            return new_inst

        return inst


def set_resolve(resolve) -> None:
    """Explicitly store the Resolve instance (used at startup)."""
    global _resolve_instance
    with _lock:
        _resolve_instance = resolve


def set_reconnect_enabled(enabled: bool) -> None:
    """Toggle auto-reconnect (useful in tests)."""
    global _reconnect_enabled
    _reconnect_enabled = enabled


def invalidate_resolve() -> None:
    """Drop the cached Resolve instance so the next get_resolve() reconnects.

    Called by the tool wrapper when a tool call raises an exception that
    looks like a lost connection (e.g. COM error). Next tool call will
    trigger a fresh _try_reconnect().
    """
    global _resolve_instance
    with _lock:
        _resolve_instance = None
        logger.info("Resolve instance invalidated; next call will attempt reconnect")


# Heuristic: error substrings that strongly suggest the Resolve bridge died.
_LOST_CONNECTION_SIGNS = (
    "com_error",
    "rpc server is unavailable",
    "the object invoked has disconnected",
    "attributeerror: 'nonetype'",
    "scripting is not available",
)


def looks_like_lost_connection(err: BaseException) -> bool:
    text = f"{type(err).__name__}: {err}".lower()
    return any(s in text for s in _LOST_CONNECTION_SIGNS)


def _is_alive(inst) -> bool:
    """Cheap liveness probe against a Resolve instance."""
    try:
        # GetProductName is one of the cheapest calls on the Resolve object.
        inst.GetProductName()
        return True
    except Exception as e:
        logger.debug(f"Resolve liveness probe failed: {e}")
        return False


def _try_reconnect() -> Optional[object]:
    """Attempt to obtain a fresh Resolve instance. Returns None on failure."""
    try:
        # Lazy import to avoid circular deps at module load.
        from src.utils.resolve_connection import initialize_resolve

        logger.info("Attempting to reconnect to DaVinci Resolve...")
        return initialize_resolve()
    except Exception as e:
        logger.warning(f"Reconnect attempt failed: {e}")
        return None
