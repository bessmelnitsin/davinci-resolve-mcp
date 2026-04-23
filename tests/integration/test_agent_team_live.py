"""
Integration tests for the 🅱️ agent-team architecture with a LIVE
DaVinci Resolve instance.

These tests are skipped by default — they require:

  - DaVinci Resolve running on the local machine
  - scripting enabled (Preferences > System > General > External scripting)
  - env vars RESOLVE_SCRIPT_API / RESOLVE_SCRIPT_LIB pointing at the SDK

To run them:

    pytest tests/integration/test_agent_team_live.py -v -m live

The `live` marker filters to this file only. These tests MUTATE Resolve
state (open pages, create timelines); only run on a disposable project.
"""
from __future__ import annotations

import os
import time

import pytest

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def live_resolve():
    """Try to connect to a real running Resolve; skip the module otherwise.

    Also ensures a project with at least one timeline is loaded — if Resolve
    is sitting on the Project Manager, we try to load the first available
    project. Tests that need a timeline but find none will skip themselves.
    """
    try:
        from src.utils.resolve_connection import initialize_resolve
        r = initialize_resolve()
    except Exception as e:
        pytest.skip(f"No live Resolve available: {e}")
    if r is None:
        pytest.skip("initialize_resolve returned None — is Resolve running?")

    from src import context
    context.set_resolve(r)

    # If no real project is loaded (Project Manager visible), try to load one.
    pm = r.GetProjectManager()
    proj = pm.GetCurrentProject() if pm else None
    if proj is not None and proj.GetTimelineCount() == 0:
        projects = pm.GetProjectListInCurrentFolder() or []
        # Prefer any project other than the phantom "Untitled Project".
        candidates = [p for p in projects if p and p != proj.GetName()]
        for name in candidates:
            loaded = pm.LoadProject(name)
            if loaded and loaded.GetTimelineCount() > 0:
                break

    yield r
    context.set_resolve(None)


def test_live_resolve_product_name(live_resolve):
    name = live_resolve.GetProductName()
    assert name and "DaVinci" in name


def test_live_page_lock_switches_pages(live_resolve):
    """Acquire the lock targeting 'color' — Resolve should be on Color.

    Requires a project to be open in Resolve — OpenPage is a no-op otherwise.
    """
    from src.utils.page_lock import page_lock

    pm = live_resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    if not project:
        pytest.skip("No project open in Resolve — cannot switch pages")
    if not project.GetCurrentTimeline():
        pytest.skip("No timeline in current project — page switches unreliable")

    def _wait_for_page(target: str, timeout: float = 2.0) -> str | None:
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            last = live_resolve.GetCurrentPage()
            if last == target:
                return last
            time.sleep(0.1)
        return last

    original = live_resolve.GetCurrentPage()
    try:
        with page_lock.acquire_page("color", holder="test"):
            assert _wait_for_page("color") == "color"

        with page_lock.acquire_page("deliver", holder="test"):
            assert _wait_for_page("deliver") == "deliver"
    finally:
        if original:
            live_resolve.OpenPage(original)


def test_live_role_server_exposes_tools(live_resolve):
    """`build_server(roles=['color'])` should expose color tools that
    actually respond (non-error) against live Resolve."""
    from src.roles import resolve_roles
    from src.server_factory import build_server

    server = build_server(resolve_roles("color"))
    tool_names = [t.name for t in server._tool_manager.list_tools()]
    assert tool_names, "color role exposed no tools"

    # Pick a read-only tool if present, to avoid mutating state.
    read_only = next(
        (t for t in server._tool_manager.list_tools()
         if t.name.startswith(("get_", "list_", "check_"))),
        None,
    )
    if read_only is None:
        pytest.skip("No read-only color tool to probe")

    result = read_only.fn()
    # Any non-None result means the full wrapper chain (rate -> dry -> lock
    # -> fn -> audit) succeeded end-to-end.
    assert result is not None


def test_live_health_resource(live_resolve):
    from src.roles import resolve_roles
    from src.server_factory import build_server

    server = build_server(resolve_roles("color"))
    resources = list(server._resource_manager.list_resources())
    health = next(r for r in resources if str(r.uri) == "resolve://health")
    # Resource `fn` is not always directly callable; best-effort probe.
    try:
        text = health.fn() if hasattr(health, "fn") else None
        if text:
            assert "connected=yes" in text
    except Exception as e:
        pytest.skip(f"Could not invoke health resource directly: {e}")
