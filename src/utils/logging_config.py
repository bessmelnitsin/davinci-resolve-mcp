"""
Logging configuration — text or JSON format, selectable via env var.

Enable JSON output with ``MCP_LOG_JSON=1``. Intended for production
deployments where logs are shipped to Loki / ELK / Datadog. Text format
remains the default for local development.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Minimal JSON log formatter — one record per line."""

    _STD_ATTRS = frozenset({
        "name", "msg", "args", "levelname", "levelno", "pathname",
        "filename", "module", "exc_info", "exc_text", "stack_info",
        "lineno", "funcName", "created", "msecs", "relativeCreated",
        "thread", "threadName", "processName", "process", "message",
        "taskName",
    })

    def format(self, record: logging.LogRecord) -> str:
        from src.utils import request_id as req_id  # avoid import cycle on cold start
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        rid = req_id.get()
        if rid:
            payload["request_id"] = rid
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        # Carry any extra fields passed via `logger.info(..., extra={...})`.
        for k, v in record.__dict__.items():
            if k in self._STD_ATTRS or k.startswith("_"):
                continue
            try:
                json.dumps(v)  # ensure serializable
                payload[k] = v
            except Exception:
                payload[k] = repr(v)

        return json.dumps(payload, ensure_ascii=False)


def configure(debug: bool = False) -> None:
    """Configure root logging handler based on env."""
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    if os.environ.get("MCP_LOG_JSON") == "1":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

    root = logging.getLogger()
    # Remove prior handlers so we don't double-log under pytest / reload.
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(handler)
    root.setLevel(level)
