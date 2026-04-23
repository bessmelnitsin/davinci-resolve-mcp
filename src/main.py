#!/usr/bin/env python3
"""
DaVinci Resolve MCP Server - Main Entry Point

Supports two operating modes:

  1. Single-agent stdio (legacy):
       python src/main.py                    # all tools, stdio
       python src/main.py --role full

  2. Agent-team HTTP (new):
       python src/main.py --role color --transport http --port 8101
       python src/main.py --role deliver --transport http --port 8104

Run several processes, one per role, each on its own port. All processes
share the single local DaVinci Resolve instance. Page switching between
agents is coordinated by a process-wide `PageLock`.

Auth (HTTP only):
  - export MCP_AUTH_TOKEN=<token>              # shared token
  - export MCP_AUTH_TOKENS=color:tk1,edit:tk2  # per-role tokens
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure `src.` imports work when launched directly.
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from src.utils.resolve_connection import (
    check_environment_variables,
    set_default_environment_variables,
)

from src.utils.logging_config import configure as configure_logging

configure_logging(debug=False)
logger = logging.getLogger("davinci-resolve-mcp.main")


def check_setup() -> bool:
    env_status = check_environment_variables()
    if not env_status["all_set"]:
        logger.warning(
            f"Setting default environment variables. Missing: {env_status['missing']}"
        )
        set_default_environment_variables()
    return True


def _connect_resolve() -> None:
    """Initialize Resolve and store in global context."""
    from src.context import set_resolve
    from src.utils.resolve_connection import initialize_resolve

    resolve = initialize_resolve()
    if resolve:
        set_resolve(resolve)
        logger.info("Connected to DaVinci Resolve.")
    else:
        logger.warning(
            "Could not connect to DaVinci Resolve. Tools will return errors "
            "until Resolve is available."
        )


def _log_startup_banner(roles, transport, host, port) -> None:
    """Emit a multi-line banner summarizing effective config. Secrets are
    reduced to booleans — we never log tokens."""
    from src.utils.audit import get_audit_log
    from src.utils.rate_limit import rate_limiter

    has_shared = bool(os.environ.get("MCP_AUTH_TOKEN"))
    has_per_role = bool(os.environ.get("MCP_AUTH_TOKENS"))
    dry_global = os.environ.get("MCP_DRY_RUN") == "1"
    dry_roles = os.environ.get("MCP_DRY_RUN_ROLES", "")
    json_log = os.environ.get("MCP_LOG_JSON") == "1"
    file_lock_disabled = os.environ.get("MCP_DISABLE_FILE_LOCK") == "1"

    audit_path = get_audit_log().path
    rl = rate_limiter.snapshot()

    logger.info("=" * 60)
    logger.info("DaVinci Resolve MCP Server — startup")
    logger.info(f"  roles        : {roles}")
    logger.info(f"  transport    : {transport}")
    if transport == "http":
        logger.info(f"  bind         : {host}:{port}")
        logger.info(f"  auth.shared  : {has_shared}")
        logger.info(f"  auth.per_role: {has_per_role}")
    logger.info(f"  dry_run.all  : {dry_global}")
    if dry_roles:
        logger.info(f"  dry_run.roles: {dry_roles}")
    logger.info(f"  rate.all     : {rl['all']['rate']}/s")
    logger.info(f"  rate.destr   : {rl['destructive']['rate']}/s")
    logger.info(f"  file_lock    : {'DISABLED' if file_lock_disabled else 'enabled'}")
    logger.info(f"  log_format   : {'json' if json_log else 'text'}")
    logger.info(f"  audit_log    : {audit_path}")
    logger.info("=" * 60)


def run_server(
    role_spec: str,
    transport: str,
    host: str,
    port: int,
    debug: bool,
) -> int:
    # Late imports so argparse errors are fast.
    from src.roles import resolve_roles, list_role_names
    from src.server_factory import build_server

    # Variant compatibility shim: --variant edit still works.
    try:
        roles = resolve_roles(role_spec)
    except ValueError as e:
        logger.error(f"Invalid --role: {e}")
        logger.error(f"Valid roles: {list_role_names()}")
        return 2

    if debug:
        configure_logging(debug=True)
        logger.info("Debug mode enabled")

    _connect_resolve()

    server = build_server(roles)

    role_names = [r.name for r in roles]
    _log_startup_banner(role_names, transport, host, port)

    if transport == "stdio":
        server.run()
        return 0

    # HTTP transport: require auth.
    from src.utils.auth import load_from_env

    try:
        auth = load_from_env(enabled=True)
    except RuntimeError as e:
        logger.error(str(e))
        return 2

    logger.info(
        f"HTTP transport: listening on {host}:{port} (auth={'shared' if auth.shared_token else 'per-role'})"
    )

    # Build the Starlette ASGI app ourselves so we can wrap it with our
    # Bearer-auth middleware, then serve via uvicorn.
    import uvicorn
    from src.utils.auth_middleware import BearerAuthMiddleware

    server.settings.host = host
    server.settings.port = port

    asgi_app = server.streamable_http_app()
    asgi_app = BearerAuthMiddleware(
        asgi_app,
        auth,
        allowed_roles={r.name for r in roles},
    )

    uvicorn.run(
        asgi_app,
        host=host,
        port=port,
        log_level="debug" if debug else "info",
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="DaVinci Resolve MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Legacy --variant kept for backwards compatibility.
    parser.add_argument(
        "--variant",
        choices=["full", "edit"],
        default=None,
        help="[deprecated, use --role] 'full' = all tools, 'edit' = edit+timeline.",
    )

    parser.add_argument(
        "--role",
        default=None,
        help=(
            "Agent role(s): media, edit, color, fusion, fairlight, deliver, "
            "director, full. Comma-separated for multi-role, e.g. 'color,deliver'."
        ),
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="Transport layer (default: stdio; set MCP_TRANSPORT=http for remote).",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "127.0.0.1"),
        help="HTTP bind address (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8100")),
        help="HTTP port (default: 8100).",
    )
    args = parser.parse_args()

    # Resolve role from --role or --variant (compat).
    if args.role:
        role_spec = args.role
    elif args.variant == "edit":
        role_spec = "edit"
    else:
        role_spec = "full"

    if not check_setup():
        logger.error("Failed to set up the environment.")
        return 1

    return run_server(
        role_spec=role_spec,
        transport=args.transport,
        host=args.host,
        port=args.port,
        debug=args.debug,
    )


if __name__ == "__main__":
    sys.exit(main())
