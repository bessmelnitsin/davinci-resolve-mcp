"""Unit tests for the infrastructure added in the agent-team phase:
file lock, audit log, dry-run, auto-reconnect, rate limiter, health
endpoint, JSON log formatter.
"""

import asyncio
import json
import os
import threading
import time
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("RESOLVE_SCRIPT_API", "x")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", "x")


# ======================================================================
# File lock
# ======================================================================


def test_file_lock_reentrant(tmp_path):
    from src.utils.file_lock import ProcessFileLock
    pl = ProcessFileLock(str(tmp_path / "a.lock"))
    with pl.acquire(holder="x"):
        with pl.acquire(holder="x"):
            assert pl.snapshot()["depth"] == 2
        assert pl.snapshot()["depth"] == 1
    assert pl.snapshot()["depth"] == 0


def test_file_lock_serializes_threads(tmp_path):
    from src.utils.file_lock import ProcessFileLock
    pl = ProcessFileLock(str(tmp_path / "b.lock"))

    order = []
    started = threading.Event()

    def a():
        with pl.acquire(holder="a"):
            order.append("a-in")
            started.set()
            time.sleep(0.05)
            order.append("a-out")

    def b():
        started.wait()
        with pl.acquire(holder="b"):
            order.append("b-in")
            order.append("b-out")

    ta = threading.Thread(target=a)
    tb = threading.Thread(target=b)
    ta.start(); tb.start()
    ta.join(); tb.join()
    assert order == ["a-in", "a-out", "b-in", "b-out"], order


def test_file_lock_disabled_is_noop(monkeypatch):
    monkeypatch.setenv("MCP_DISABLE_FILE_LOCK", "1")
    # Re-import to pick up env var.
    import importlib
    from src.utils import file_lock as fl
    importlib.reload(fl)
    assert fl.process_file_lock.snapshot() == {"enabled": False}


# ======================================================================
# Audit log
# ======================================================================


def test_audit_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_AUDIT_LOG", str(tmp_path / "audit.jsonl"))
    import importlib
    from src.utils import audit as audit_mod
    importlib.reload(audit_mod)
    log = audit_mod.AuditLog()
    log.write(
        role="color", tool="delete_node", destructive=True, dry_run=False,
        args_hash="abc123", duration_ms=12.3, ok=True, error=None,
    )
    log.write(
        role="deliver", tool="render", destructive=False, dry_run=False,
        args_hash="ef0011", duration_ms=1.0, ok=False, error="boom",
    )
    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    rec = json.loads(lines[0])
    assert rec["tool"] == "delete_node"
    assert rec["destructive"] is True
    assert rec["ok"] is True
    rec2 = json.loads(lines[1])
    assert rec2["error"] == "boom"


def test_audit_hash_args_stable():
    from src.utils.audit import hash_args
    a = hash_args((1, 2), {"x": "y"})
    b = hash_args((1, 2), {"x": "y"})
    c = hash_args((1, 3), {"x": "y"})
    assert a == b
    assert a != c
    assert len(a) == 8


# ======================================================================
# Dry-run
# ======================================================================


def test_dry_run_global_flag(monkeypatch):
    monkeypatch.setenv("MCP_DRY_RUN", "1")
    from src.utils.dry_run import is_dry_run
    assert is_dry_run("color") is True
    assert is_dry_run("deliver") is True


def test_dry_run_per_role(monkeypatch):
    monkeypatch.delenv("MCP_DRY_RUN", raising=False)
    monkeypatch.setenv("MCP_DRY_RUN_ROLES", "color, deliver")
    from src.utils.dry_run import is_dry_run
    assert is_dry_run("color") is True
    assert is_dry_run("deliver") is True
    assert is_dry_run("edit") is False


def test_dry_run_describe():
    from src.utils.dry_run import describe_skipped_call
    msg = describe_skipped_call("delete_media", ("id1",), {"force": True})
    payload = json.loads(msg)
    assert payload["dry_run"] is True
    assert payload["tool"] == "delete_media"
    assert "delete_media" in payload["would_call"]


# ======================================================================
# Auto-reconnect
# ======================================================================


def test_get_resolve_returns_live_instance(monkeypatch):
    from src import context as ctx
    inst = MagicMock()
    inst.GetProductName.return_value = "DaVinci Resolve"
    ctx.set_resolve(inst)
    assert ctx.get_resolve() is inst


def test_get_resolve_reconnects_on_dead(monkeypatch):
    from src import context as ctx

    # Dead instance raises on probe
    dead = MagicMock()
    dead.GetProductName.side_effect = RuntimeError("COM disconnected")
    ctx.set_resolve(dead)

    fresh = MagicMock()
    fresh.GetProductName.return_value = "DaVinci Resolve"

    monkeypatch.setattr(
        "src.utils.resolve_connection.initialize_resolve", lambda: fresh
    )
    # Bypass cooldown
    ctx._last_attempt = 0
    assert ctx.get_resolve() is fresh
    # cleanup
    ctx.set_resolve(None)


def test_get_resolve_honors_cooldown(monkeypatch):
    from src import context as ctx
    dead = MagicMock()
    dead.GetProductName.side_effect = RuntimeError("down")
    ctx.set_resolve(dead)

    calls = []
    def fake_init():
        calls.append(1)
        return None

    monkeypatch.setattr(
        "src.utils.resolve_connection.initialize_resolve", fake_init
    )
    ctx._last_attempt = 0
    ctx.get_resolve()   # triggers one attempt
    ctx.get_resolve()   # within cooldown — must NOT retry
    assert len(calls) == 1
    ctx.set_resolve(None)


# ======================================================================
# Rate limiter
# ======================================================================


def test_token_bucket_basic():
    from src.utils.rate_limit import TokenBucket
    b = TokenBucket(rate=100, capacity=2)
    assert b.try_take() is True
    assert b.try_take() is True
    assert b.try_take() is False  # bucket empty
    time.sleep(0.05)
    assert b.try_take() is True   # refilled


def test_token_bucket_disabled():
    from src.utils.rate_limit import TokenBucket
    b = TokenBucket(rate=0)
    for _ in range(100):
        assert b.try_take() is True


def test_rate_limiter_destructive_gates():
    from src.utils.rate_limit import RateLimiter
    rl = RateLimiter()
    # Force tiny bucket
    rl.destructive.rate = 0.1
    rl.destructive.capacity = 1
    rl.destructive._tokens = 1
    ok1, _ = rl.check(destructive=True)
    ok2, reason = rl.check(destructive=True)
    assert ok1 is True
    assert ok2 is False
    assert "destructive" in reason


# ======================================================================
# Health endpoint (middleware-integrated)
# ======================================================================


def _collect_send():
    msgs = []

    async def send(m):
        msgs.append(m)

    return msgs, send


def test_health_endpoint_bypasses_auth():
    from src.utils.auth import AuthConfig
    from src.utils.auth_middleware import BearerAuthMiddleware

    cfg = AuthConfig(enabled=True, shared_token="s", role_tokens={})
    called = {"inner": False}

    async def inner(scope, receive, send):
        called["inner"] = True

    mw = BearerAuthMiddleware(inner, cfg)
    scope = {"type": "http", "path": "/health", "headers": []}
    msgs, send = _collect_send()
    asyncio.run(mw(scope, None, send))
    assert called["inner"] is False
    assert msgs[0]["status"] == 200
    body = msgs[1]["body"]
    assert b"ok" in body


# ======================================================================
# JSON log formatter
# ======================================================================


# ======================================================================
# Full wrapper chain (rate-limit -> dry-run -> page-lock -> fn -> audit)
# ======================================================================


def _reset_audit(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_AUDIT_LOG", str(tmp_path / "audit.jsonl"))
    import src.utils.audit as audit_mod
    audit_mod._singleton = None
    return tmp_path / "audit.jsonl"


def test_wrapper_chain_success_writes_audit(tmp_path, monkeypatch):
    audit_path = _reset_audit(tmp_path, monkeypatch)
    monkeypatch.delenv("MCP_DRY_RUN", raising=False)
    monkeypatch.delenv("MCP_DRY_RUN_ROLES", raising=False)

    from src.server_factory import _wrap_tool
    from src import context

    fake = MagicMock()
    fake.GetCurrentPage.return_value = "color"
    context.set_resolve(fake)

    calls = []
    def tool_fn(x, y=0):
        calls.append((x, y))
        return f"ok {x}/{y}"

    wrapped = _wrap_tool(tool_fn, page="color", holder="color",
                        tool_name="tool_fn", destructive=False)
    result = wrapped(7, y=3)
    context.set_resolve(None)

    assert result == "ok 7/3"
    assert calls == [(7, 3)]
    rec = json.loads(audit_path.read_text(encoding="utf-8").splitlines()[0])
    assert rec["tool"] == "tool_fn" and rec["role"] == "color"
    assert rec["ok"] is True and rec["dry_run"] is False


def test_wrapper_chain_dry_run_short_circuits(tmp_path, monkeypatch):
    audit_path = _reset_audit(tmp_path, monkeypatch)
    monkeypatch.setenv("MCP_DRY_RUN", "1")

    from src.server_factory import _wrap_tool

    calls = []
    def destructive_tool(x):
        calls.append(x)
        return "SHOULD NOT RUN"

    wrapped = _wrap_tool(destructive_tool, page="deliver", holder="deliver",
                        tool_name="destructive_tool", destructive=True)
    result = wrapped("proj")

    assert calls == []
    payload = json.loads(result)
    assert payload["dry_run"] is True
    rec = json.loads(audit_path.read_text(encoding="utf-8").splitlines()[0])
    assert rec["dry_run"] is True and rec["ok"] is True


def test_wrapper_chain_records_exception(tmp_path, monkeypatch):
    audit_path = _reset_audit(tmp_path, monkeypatch)
    monkeypatch.delenv("MCP_DRY_RUN", raising=False)
    monkeypatch.delenv("MCP_DRY_RUN_ROLES", raising=False)

    from src.server_factory import _wrap_tool
    from src import context

    fake = MagicMock()
    fake.GetCurrentPage.return_value = "color"
    context.set_resolve(fake)

    def tool_fn():
        raise RuntimeError("boom")

    wrapped = _wrap_tool(tool_fn, page="color", holder="color",
                        tool_name="broken", destructive=False)
    with pytest.raises(RuntimeError, match="boom"):
        wrapped()
    context.set_resolve(None)

    rec = json.loads(audit_path.read_text(encoding="utf-8").splitlines()[0])
    assert rec["ok"] is False
    assert "boom" in rec["error"]


# ======================================================================
# JSON log formatter
# ======================================================================


# ======================================================================
# Request ID
# ======================================================================


def test_request_id_contextvar_roundtrip():
    from src.utils import request_id as rid
    assert rid.get() is None
    token = rid.set("abc123")
    try:
        assert rid.get() == "abc123"
    finally:
        rid.reset(token)
    assert rid.get() is None


def test_request_id_new_is_unique():
    from src.utils import request_id as rid
    ids = {rid.new() for _ in range(100)}
    assert len(ids) == 100


def test_middleware_echoes_request_id():
    from src.utils.auth import AuthConfig
    from src.utils.auth_middleware import BearerAuthMiddleware

    cfg = AuthConfig(enabled=True, shared_token="s", role_tokens={})

    async def inner(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    mw = BearerAuthMiddleware(inner, cfg)
    scope = {
        "type": "http",
        "path": "/x",
        "headers": [
            (b"authorization", b"Bearer s"),
            (b"x-request-id", b"my-trace-001"),
        ],
    }
    msgs, send = _collect_send()
    asyncio.run(mw(scope, None, send))
    start = msgs[0]
    assert start["status"] == 200
    header_names = [k for k, _ in start["headers"]]
    assert b"x-request-id" in header_names
    rid_val = dict(start["headers"])[b"x-request-id"]
    assert rid_val == b"my-trace-001"


def test_middleware_generates_request_id_when_missing():
    from src.utils.auth import AuthConfig
    from src.utils.auth_middleware import BearerAuthMiddleware

    cfg = AuthConfig(enabled=True, shared_token="s", role_tokens={})

    async def inner(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    mw = BearerAuthMiddleware(inner, cfg)
    scope = {
        "type": "http",
        "path": "/x",
        "headers": [(b"authorization", b"Bearer s")],
    }
    msgs, send = _collect_send()
    asyncio.run(mw(scope, None, send))
    headers = dict(msgs[0]["headers"])
    assert b"x-request-id" in headers
    assert len(headers[b"x-request-id"]) >= 16


# ======================================================================
# Smart reconnect on lost connection
# ======================================================================


def test_invalidate_resolve_clears_instance():
    from src import context
    context.set_resolve(MagicMock())
    assert context._resolve_instance is not None
    context.invalidate_resolve()
    assert context._resolve_instance is None


def test_looks_like_lost_connection_detects_com():
    from src.context import looks_like_lost_connection
    e1 = Exception("The RPC server is unavailable.")
    e2 = Exception("The object invoked has disconnected from its clients")
    e3 = Exception("business logic error — not a connection issue")
    assert looks_like_lost_connection(e1) is True
    assert looks_like_lost_connection(e2) is True
    assert looks_like_lost_connection(e3) is False


def test_wrapper_invalidates_on_com_error(tmp_path, monkeypatch):
    _reset_audit(tmp_path, monkeypatch)
    monkeypatch.delenv("MCP_DRY_RUN", raising=False)
    monkeypatch.delenv("MCP_DRY_RUN_ROLES", raising=False)

    from src import context
    from src.server_factory import _wrap_tool

    fake = MagicMock()
    fake.GetCurrentPage.return_value = "color"
    fake.GetProductName.return_value = "DaVinci Resolve"
    context.set_resolve(fake)

    def tool_fn():
        raise Exception("The RPC server is unavailable.")

    wrapped = _wrap_tool(tool_fn, page="color", holder="color",
                        tool_name="broken_com", destructive=False)

    # Disable reconnect so invalidate_resolve() leaves _resolve_instance None.
    context.set_reconnect_enabled(False)
    try:
        with pytest.raises(Exception):
            wrapped()
        assert context._resolve_instance is None
    finally:
        context.set_reconnect_enabled(True)


# ======================================================================
# JSON log formatter
# ======================================================================


def test_json_formatter_emits_valid_json():
    import logging as _logging
    from src.utils.logging_config import JsonFormatter

    rec = _logging.LogRecord(
        name="x", level=_logging.INFO, pathname="", lineno=1,
        msg="hello %s", args=("world",), exc_info=None,
    )
    rec.role = "color"
    out = JsonFormatter().format(rec)
    data = json.loads(out)
    assert data["msg"] == "hello world"
    assert data["logger"] == "x"
    assert data["level"] == "INFO"
    assert data["role"] == "color"
