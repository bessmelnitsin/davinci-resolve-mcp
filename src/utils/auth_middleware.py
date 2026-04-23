"""
ASGI middleware that enforces Bearer-token auth in front of FastMCP's
streamable-HTTP app.

Usage (in main.py):

    from src.utils.auth_middleware import BearerAuthMiddleware
    app = server.streamable_http_app()
    app = BearerAuthMiddleware(app, auth_config)
    uvicorn.run(app, host=..., port=...)

The middleware rejects any non-lifespan request whose Authorization header
does not validate against the supplied AuthConfig. On reject, it returns
HTTP 401 with a WWW-Authenticate header.

Role-scoped auth note: for single-role server processes, this middleware
also enforces that the token's matched role (if not 'shared' / 'anonymous')
equals the role the process was launched with — preventing, e.g., a
token issued for the color agent from being used against the deliver
server. Pass `allowed_roles` = set of role names for this process.
"""

from __future__ import annotations

import json
import logging
from typing import Iterable, Optional

from src.utils.auth import AuthConfig
from src.utils import request_id as req_id

logger = logging.getLogger("davinci-resolve-mcp.auth_mw")


class BearerAuthMiddleware:
    """Pure-ASGI middleware enforcing Bearer auth."""

    def __init__(
        self,
        app,
        auth: AuthConfig,
        *,
        allowed_roles: Optional[Iterable[str]] = None,
    ) -> None:
        self.app = app
        self.auth = auth
        self.allowed_roles = set(allowed_roles) if allowed_roles else None

    async def __call__(self, scope, receive, send):
        # Pass-through for non-HTTP (lifespan, websocket).
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Unauthenticated liveness endpoint for orchestrators (k8s, docker-compose).
        # Returns 200 with a minimal JSON body. Does NOT expose any project data.
        if scope.get("path") == "/health":
            await self._healthy(send)
            return

        # Auth disabled — pass through (shouldn't happen in HTTP mode, but safe).
        if not self.auth.enabled:
            await self.app(scope, receive, send)
            return

        # Extract Authorization header (headers is list[tuple[bytes, bytes]]).
        auth_header: Optional[str] = None
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                try:
                    auth_header = value.decode("latin-1")
                except Exception:
                    auth_header = None
                break

        allowed, matched_role = self.auth.validate_header(auth_header)

        # If per-role tokens are in use and this process only serves a subset
        # of roles, reject tokens issued for other roles.
        if allowed and self.allowed_roles is not None and matched_role not in (
            "shared",
            "anonymous",
            None,
        ):
            if matched_role not in self.allowed_roles:
                logger.warning(
                    f"token for role={matched_role!r} rejected on server "
                    f"serving roles={sorted(self.allowed_roles)}"
                )
                allowed = False

        if not allowed:
            await self._reject(send)
            return

        # Stash matched role in scope for downstream logging / tools.
        scope.setdefault("state", {})
        try:
            scope["state"]["auth_role"] = matched_role
        except Exception:
            pass

        # ------------------------------------------------------------------
        # Request ID correlation.
        # ------------------------------------------------------------------
        rid: Optional[str] = None
        for name, value in scope.get("headers", []):
            if name == b"x-request-id":
                try:
                    rid = value.decode("latin-1").strip() or None
                except Exception:
                    rid = None
                break
        if not rid:
            rid = req_id.new()
        token = req_id.set(rid)

        # Wrap `send` so the response carries back X-Request-ID.
        async def send_with_rid(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", rid.encode("ascii", errors="ignore")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_rid)
        finally:
            req_id.reset(token)

    async def _healthy(self, send) -> None:
        body = b'{"status":"ok"}'
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        })
        await send({"type": "http.response.body", "body": body, "more_body": False})

    async def _reject(self, send) -> None:
        body = json.dumps({
            "error": "unauthorized",
            "message": "Valid Bearer token required.",
        }).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"www-authenticate", b'Bearer realm="davinci-resolve-mcp"'),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
            "more_body": False,
        })
