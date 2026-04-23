"""
Server factory for role-scoped DaVinci Resolve MCP servers.

Given one or more agent roles, builds a FastMCP instance that exposes only
the tools and resources belonging to those roles. Always adds a shared
`resolve://health` resource for observability.

The implementation reuses the singleton tool/resource decorators from
`src.server_instance` — tool modules register themselves on the singleton
at import time — then copies the matching registrations into a fresh
FastMCP. This keeps tool code unchanged.
"""

from __future__ import annotations

import functools
import importlib
import inspect
import logging
from typing import Callable, Dict, List, Sequence

from mcp.server.fastmcp import FastMCP

from src.roles import Role
from src.server_instance import mcp as global_mcp
from src.utils.page_lock import page_lock
from src.utils.audit import get_audit_log, hash_args, now_ms
from src.utils.dry_run import is_dry_run, describe_skipped_call
from src.utils.rate_limit import rate_limiter
from src.context import get_resolve

logger = logging.getLogger("davinci-resolve-mcp.factory")


def _is_destructive(tool) -> bool:
    """Inspect a FastMCP Tool for the destructiveHint annotation."""
    try:
        ann = getattr(tool, "annotations", None)
        if ann is None:
            return False
        return bool(getattr(ann, "destructiveHint", False))
    except Exception:
        return False


def _wrap_tool(
    fn: Callable,
    *,
    page: str | None,
    holder: str,
    tool_name: str,
    destructive: bool,
) -> Callable:
    """Wrap a tool function with dry-run check, page lock, and audit log.

    Preserves the original signature so FastMCP's schema introspection still works.
    """
    audit = get_audit_log()

    def _maybe_dry_run(args, kwargs):
        if destructive and is_dry_run(holder):
            return describe_skipped_call(tool_name, args, kwargs)
        return None

    def _check_rate():
        allowed, reason = rate_limiter.check(destructive=destructive)
        if not allowed:
            return f"Error: {reason}. Retry in a moment."
        return None

    def _record(args, kwargs, start, *, ok, error, dry_run):
        try:
            audit.write(
                role=holder,
                tool=tool_name,
                destructive=destructive,
                dry_run=dry_run,
                args_hash=hash_args(args, kwargs),
                duration_ms=now_ms() - start,
                ok=ok,
                error=error,
            )
        except Exception:
            pass

    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def awrapper(*args, **kwargs):
            start = now_ms()
            rl = _check_rate()
            if rl is not None:
                _record(args, kwargs, start, ok=False, error="rate_limited", dry_run=False)
                return rl
            dry = _maybe_dry_run(args, kwargs)
            if dry is not None:
                _record(args, kwargs, start, ok=True, error=None, dry_run=True)
                return dry
            try:
                with page_lock.acquire_page(page, holder=holder):
                    result = await fn(*args, **kwargs)
                _record(args, kwargs, start, ok=True, error=None, dry_run=False)
                return result
            except Exception as e:
                # If the bridge died mid-call, invalidate so the next call reconnects.
                try:
                    from src.context import looks_like_lost_connection, invalidate_resolve
                    if looks_like_lost_connection(e):
                        invalidate_resolve()
                except Exception:
                    pass
                _record(args, kwargs, start, ok=False, error=str(e), dry_run=False)
                raise
        return awrapper

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = now_ms()
        rl = _check_rate()
        if rl is not None:
            _record(args, kwargs, start, ok=False, error="rate_limited", dry_run=False)
            return rl
        dry = _maybe_dry_run(args, kwargs)
        if dry is not None:
            _record(args, kwargs, start, ok=True, error=None, dry_run=True)
            return dry
        try:
            with page_lock.acquire_page(page, holder=holder):
                result = fn(*args, **kwargs)
            _record(args, kwargs, start, ok=True, error=None, dry_run=False)
            return result
        except Exception as e:
            try:
                from src.context import looks_like_lost_connection, invalidate_resolve
                if looks_like_lost_connection(e):
                    invalidate_resolve()
            except Exception:
                pass
            _record(args, kwargs, start, ok=False, error=str(e), dry_run=False)
            raise
    return wrapper


def _wrap_with_page_lock(fn: Callable, page: str | None, holder: str) -> Callable:
    """Back-compat shim for callers/tests that expect the old name."""
    return _wrap_tool(
        fn,
        page=page,
        holder=holder,
        tool_name=getattr(fn, "__name__", "anon"),
        destructive=False,
    )


def _ensure_all_tool_modules_imported() -> None:
    """Import the union of all tool modules so the global `mcp` is populated."""
    all_modules = {
        "src.tools.media",
        "src.tools.media_storage",
        "src.tools.timeline",
        "src.tools.color",
        "src.tools.fusion",
        "src.tools.fairlight",
        "src.tools.delivery",
        "src.tools.project",
        "src.tools.navigation",
    }
    for m in all_modules:
        importlib.import_module(m)


def _register_health(server: FastMCP, role_names: Sequence[str]) -> None:
    """Register the `resolve://health` resource on the given server."""

    @server.resource("resolve://health")
    def _health() -> str:
        resolve = get_resolve()
        lock = page_lock.snapshot()
        parts = [
            f"roles={','.join(role_names)}",
            f"connected={'yes' if resolve else 'no'}",
        ]
        if resolve:
            try:
                parts.append(f"product={resolve.GetProductName()}")
                parts.append(f"version={resolve.GetVersionString()}")
                parts.append(f"page={resolve.GetCurrentPage()}")
            except Exception as e:
                parts.append(f"probe_error={e}")
        parts.append(f"lock_holder={lock['holder']}")
        parts.append(f"lock_depth={lock['reentrant_depth']}")
        return "; ".join(parts)


def build_server(
    roles: Sequence[Role],
    *,
    server_name: str | None = None,
) -> FastMCP:
    """Build a FastMCP server exposing only tools/resources for `roles`.

    Args:
        roles: One or more Role objects. Their tool_modules are unioned.
        server_name: Optional server identity; defaults to 'DaVinciResolveMCP-<roles>'.

    Returns:
        A fresh FastMCP instance ready for `.run(...)`.
    """
    if not roles:
        raise ValueError("at least one role is required")

    # Populate the global singleton by importing every tool module first.
    _ensure_all_tool_modules_imported()

    # Build a module -> (role_name, page) mapping so each tool is wrapped
    # with the correct page-lock binding.
    module_binding: Dict[str, tuple[str, str | None]] = {}
    for r in roles:
        for m in r.tool_modules:
            # Later roles override earlier — but since we union them and
            # most modules map to exactly one role, collisions are rare.
            module_binding.setdefault(m, (r.name, r.page))

    allowed_modules = set(module_binding.keys())
    role_names = [r.name for r in roles]
    name = server_name or f"DaVinciResolveMCP-{'-'.join(role_names)}"
    server = FastMCP(name)

    # ------------------------------------------------------------------
    # Copy matching tools, wrapping each in the page-lock.
    # ------------------------------------------------------------------
    copied_tools = 0
    for tool in global_mcp._tool_manager.list_tools():
        module = getattr(tool.fn, "__module__", None)
        if module not in allowed_modules:
            continue
        holder, page = module_binding[module]
        wrapped_fn = _wrap_tool(
            tool.fn,
            page=page,
            holder=holder,
            tool_name=tool.name,
            destructive=_is_destructive(tool),
        )
        server._tool_manager.add_tool(
            fn=wrapped_fn,
            name=tool.name,
            title=tool.title,
            description=tool.description,
            annotations=tool.annotations,
            icons=tool.icons,
            meta=tool.meta,
        )
        copied_tools += 1

    # ------------------------------------------------------------------
    # Copy matching resources and resource templates
    # ------------------------------------------------------------------
    copied_resources = 0
    for res in global_mcp._resource_manager.list_resources():
        module = getattr(res.fn, "__module__", None) if hasattr(res, "fn") else None
        if module not in allowed_modules:
            continue
        server._resource_manager.add_resource(res)
        copied_resources += 1

    copied_templates = 0
    for tmpl in global_mcp._resource_manager.list_templates():
        module = getattr(tmpl.fn, "__module__", None)
        if module not in allowed_modules:
            continue
        server._resource_manager._templates[tmpl.uri_template] = tmpl
        copied_templates += 1

    _register_health(server, role_names)

    logger.info(
        f"Built server '{name}': "
        f"{copied_tools} tools, {copied_resources} resources, "
        f"{copied_templates} templates "
        f"from roles={role_names}"
    )

    return server


def list_tools_for_roles(roles: Sequence[Role]) -> List[str]:
    """Return the sorted list of tool names a given role set would expose."""
    _ensure_all_tool_modules_imported()
    allowed = {m for r in roles for m in r.tool_modules}
    return sorted(
        t.name
        for t in global_mcp._tool_manager.list_tools()
        if getattr(t.fn, "__module__", None) in allowed
    )
