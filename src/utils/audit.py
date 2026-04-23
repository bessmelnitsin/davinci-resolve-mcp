"""
JSONL audit log for MCP tool calls.

Every tool wrapped by the server factory emits an audit entry when called,
including:

    - timestamp (ISO-8601, UTC)
    - role (e.g. "color", "deliver")
    - tool (tool name)
    - destructive (bool)
    - dry_run (bool; see src/utils/dry_run.py)
    - args_hash (SHA256 hex prefix of repr(args, kwargs) — avoids dumping
      binary paths, LUT blobs, etc. to log, while still giving a stable
      fingerprint for deduplication)
    - duration_ms
    - ok (bool)
    - error (string, if ok is False)

File location is configurable via ``MCP_AUDIT_LOG`` env var; defaults to
``<project>/logs/audit.jsonl``. The log is append-only and safe to tail /
rotate externally (logrotate, etc.).

Writes are guarded by a threading.Lock to avoid interleaved lines. For
cross-process writes, we rely on POSIX/Windows append-mode semantics —
small JSONL records (< 4 KiB) are atomic on every mainstream filesystem.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.utils import request_id as req_id

logger = logging.getLogger("davinci-resolve-mcp.audit")


def _default_log_path() -> Path:
    # src/utils/audit.py -> project root
    root = Path(__file__).resolve().parent.parent.parent
    return root / "logs" / "audit.jsonl"


class AuditLog:
    def __init__(self, path: Optional[str] = None) -> None:
        env_path = os.environ.get("MCP_AUDIT_LOG")
        resolved = Path(env_path) if env_path else (Path(path) if path else _default_log_path())
        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"audit: could not mkdir {resolved.parent}: {e}")
        self.path = resolved
        self._lock = threading.Lock()

    def write(
        self,
        *,
        role: str,
        tool: str,
        destructive: bool,
        dry_run: bool,
        args_hash: str,
        duration_ms: float,
        ok: bool,
        error: Optional[str] = None,
    ) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "tool": tool,
            "destructive": destructive,
            "dry_run": dry_run,
            "args_hash": args_hash,
            "duration_ms": round(duration_ms, 2),
            "ok": ok,
        }
        rid = req_id.get()
        if rid:
            record["request_id"] = rid
        if error:
            # Truncate extremely long errors.
            record["error"] = error[:500]
        try:
            line = json.dumps(record, ensure_ascii=False)
        except Exception:
            line = json.dumps({**record, "error": "audit_encoding_failed"})
        with self._lock:
            try:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception as e:
                # Audit must never crash the tool. Log and swallow.
                logger.error(f"audit write failed ({self.path}): {e}")


def hash_args(args: tuple, kwargs: dict) -> str:
    """Return an 8-hex-char SHA256 prefix of repr((args, kwargs))."""
    try:
        blob = repr((args, sorted(kwargs.items()))).encode("utf-8", errors="replace")
    except Exception:
        blob = b"<unreprable>"
    return hashlib.sha256(blob).hexdigest()[:8]


# Module-level singleton — created lazily to honor env vars set after import.
_singleton: Optional[AuditLog] = None
_singleton_lock = threading.Lock()


def get_audit_log() -> AuditLog:
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:
                _singleton = AuditLog()
    return _singleton


def now_ms() -> float:
    return time.monotonic() * 1000.0
