"""Unit tests for role-scoped server factory + page lock."""
import os
import threading
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("RESOLVE_SCRIPT_API", "x")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", "x")


# ======================================================================
# Role parsing
# ======================================================================


def test_resolve_single_role():
    from src.roles import resolve_roles
    roles = resolve_roles("color")
    assert len(roles) == 1
    assert roles[0].name == "color"
    assert roles[0].page == "color"


def test_resolve_multi_role():
    from src.roles import resolve_roles
    roles = resolve_roles("color,deliver")
    assert [r.name for r in roles] == ["color", "deliver"]


def test_resolve_full():
    from src.roles import resolve_roles
    roles = resolve_roles("full")
    assert roles[0].name == "full"
    # 'full' spans every tool module
    assert len(roles[0].tool_modules) >= 7


def test_resolve_unknown_role_raises():
    from src.roles import resolve_roles
    with pytest.raises(ValueError, match="Unknown role"):
        resolve_roles("nonsense")


def test_resolve_empty_raises():
    from src.roles import resolve_roles
    with pytest.raises(ValueError):
        resolve_roles("")


def test_roles_dedup_preserves_order():
    from src.roles import resolve_roles
    roles = resolve_roles("color,color,deliver")
    assert [r.name for r in roles] == ["color", "deliver"]


# ======================================================================
# Server factory
# ======================================================================


def test_color_role_exposes_only_color_tools():
    from src.roles import resolve_roles
    from src.server_factory import list_tools_for_roles

    color_only = list_tools_for_roles(resolve_roles("color"))
    all_tools = list_tools_for_roles(resolve_roles("full"))

    assert len(color_only) < len(all_tools)
    # No media-pool tool should leak into the colorist's toolbox.
    for t in color_only:
        assert not t.startswith("delete_media"), t
        assert not t.startswith("import_media"), t
    # But color-specific tools must be present.
    assert any("color" in t or "node" in t or "still" in t or "lut" in t.lower()
               for t in color_only)


def test_director_has_project_and_navigation():
    from src.roles import resolve_roles
    from src.server_factory import list_tools_for_roles
    tools = list_tools_for_roles(resolve_roles("director"))
    assert "open_project" in tools
    assert "switch_page" in tools


def test_build_server_health_resource_exists():
    from src.roles import resolve_roles
    from src.server_factory import build_server

    server = build_server(resolve_roles("color"))
    # Walk registered resources
    uris = {str(r.uri) for r in server._resource_manager.list_resources()}
    assert "resolve://health" in uris


def test_build_server_tool_is_wrapped_with_page_lock(monkeypatch):
    """A copied tool, when called, must acquire the PageLock."""
    from src.roles import resolve_roles
    from src.server_factory import build_server
    from src.utils import page_lock as pl_module

    server = build_server(resolve_roles("color"))
    # Pick any color tool
    tools = server._tool_manager.list_tools()
    assert tools, "color role should register tools"
    sample = tools[0]

    acquired = []

    original_acquire = pl_module.page_lock.acquire_page

    from contextlib import contextmanager

    @contextmanager
    def spy(page, *, holder=None):
        acquired.append((page, holder))
        with original_acquire(page, holder=holder) as r:
            yield r

    monkeypatch.setattr(pl_module.page_lock, "acquire_page", spy)

    # Call the tool's fn directly (without real Resolve, it'll just error out
    # inside — that's fine, we only care that the lock was taken).
    try:
        sample.fn()
    except Exception:
        pass

    assert acquired, "page_lock.acquire_page should have been called"
    assert acquired[0][0] == "color", f"expected color page, got {acquired[0][0]}"
    assert acquired[0][1] == "color", f"expected holder=color, got {acquired[0][1]}"


# ======================================================================
# PageLock
# ======================================================================


def test_page_lock_snapshot_initial():
    from src.utils.page_lock import PageLock
    pl = PageLock()
    snap = pl.snapshot()
    assert snap["locked"] is False
    assert snap["reentrant_depth"] == 0


def test_page_lock_reentrant():
    from src.utils.page_lock import PageLock
    pl = PageLock()
    with pl.acquire_page(None, holder="a"):
        with pl.acquire_page(None, holder="a"):
            assert pl.snapshot()["reentrant_depth"] == 2
        assert pl.snapshot()["reentrant_depth"] == 1
    assert pl.snapshot()["reentrant_depth"] == 0


def test_page_lock_invalid_page():
    from src.utils.page_lock import PageLock
    pl = PageLock()
    with pytest.raises(ValueError):
        with pl.acquire_page("nonsense"):
            pass


def test_page_lock_serializes_across_threads(monkeypatch):
    """Two threads trying to hold the lock must serialize."""
    from src.utils.page_lock import PageLock
    from src import context

    # Stub Resolve so acquire_page doesn't need a real connection
    fake = MagicMock()
    fake.GetCurrentPage.return_value = "color"
    context.set_resolve(fake)

    pl = PageLock()
    order = []
    start_b = threading.Event()

    def a():
        with pl.acquire_page("color", holder="a"):
            order.append("a-in")
            start_b.set()
            # Hold the lock for a moment to force b to wait
            import time
            time.sleep(0.05)
            order.append("a-out")

    def b():
        start_b.wait()
        with pl.acquire_page("color", holder="b"):
            order.append("b-in")
            order.append("b-out")

    ta = threading.Thread(target=a)
    tb = threading.Thread(target=b)
    ta.start()
    tb.start()
    ta.join()
    tb.join()

    # cleanup
    context.set_resolve(None)

    assert order == ["a-in", "a-out", "b-in", "b-out"], order


# ======================================================================
# Auth
# ======================================================================


def test_auth_disabled_allows_all():
    from src.utils.auth import AuthConfig
    cfg = AuthConfig(enabled=False)
    assert cfg.validate_header(None) == (True, "anonymous")


def test_auth_shared_token():
    from src.utils.auth import AuthConfig
    cfg = AuthConfig(enabled=True, shared_token="s3cret", role_tokens={})
    assert cfg.validate_header("Bearer s3cret") == (True, "shared")
    assert cfg.validate_header("Bearer wrong") == (False, None)
    assert cfg.validate_header(None) == (False, None)
    assert cfg.validate_header("Basic xxx") == (False, None)


def test_auth_role_tokens():
    from src.utils.auth import AuthConfig
    cfg = AuthConfig(
        enabled=True,
        shared_token=None,
        role_tokens={"color": "c-tok", "deliver": "d-tok"},
    )
    assert cfg.validate_header("Bearer c-tok") == (True, "color")
    assert cfg.validate_header("Bearer d-tok") == (True, "deliver")
    assert cfg.validate_header("Bearer nope") == (False, None)


def test_auth_load_from_env_rejects_empty(monkeypatch):
    from src.utils.auth import load_from_env
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("MCP_AUTH_TOKENS", raising=False)
    with pytest.raises(RuntimeError):
        load_from_env(enabled=True)


def test_auth_load_from_env_per_role(monkeypatch):
    from src.utils.auth import load_from_env
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("MCP_AUTH_TOKENS", "color:tok1, deliver:tok2")
    cfg = load_from_env(enabled=True)
    assert cfg.role_tokens == {"color": "tok1", "deliver": "tok2"}
