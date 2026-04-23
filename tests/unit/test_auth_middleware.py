"""Unit tests for BearerAuthMiddleware."""
import asyncio
import os

os.environ.setdefault("RESOLVE_SCRIPT_API", "x")
os.environ.setdefault("RESOLVE_SCRIPT_LIB", "x")


class _CollectSend:
    def __init__(self):
        self.messages = []

    async def __call__(self, msg):
        self.messages.append(msg)


class _DummyApp:
    def __init__(self):
        self.called = False
        self.scope_seen = None

    async def __call__(self, scope, receive, send):
        self.called = True
        self.scope_seen = scope
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok", "more_body": False})


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


def _http_scope(auth_header=None):
    headers = []
    if auth_header is not None:
        headers.append((b"authorization", auth_header.encode("latin-1")))
    return {"type": "http.http", "headers": headers}.copy() or {
        "type": "http",
        "headers": headers,
    }


def _scope(auth=None, type_="http"):
    headers = []
    if auth is not None:
        headers.append((b"authorization", auth.encode("latin-1")))
    return {"type": type_, "headers": headers}


def test_middleware_allows_valid_shared_token():
    from src.utils.auth import AuthConfig
    from src.utils.auth_middleware import BearerAuthMiddleware

    cfg = AuthConfig(enabled=True, shared_token="good", role_tokens={})
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, cfg)

    send = _CollectSend()
    _run(mw(_scope("Bearer good"), None, send))
    assert inner.called
    assert send.messages[0]["status"] == 200


def test_middleware_rejects_missing_token():
    from src.utils.auth import AuthConfig
    from src.utils.auth_middleware import BearerAuthMiddleware

    cfg = AuthConfig(enabled=True, shared_token="good", role_tokens={})
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, cfg)
    send = _CollectSend()
    _run(mw(_scope(None), None, send))
    assert not inner.called
    assert send.messages[0]["status"] == 401
    headers = dict(send.messages[0]["headers"])
    assert b"www-authenticate" in headers


def test_middleware_rejects_wrong_token():
    from src.utils.auth import AuthConfig
    from src.utils.auth_middleware import BearerAuthMiddleware

    cfg = AuthConfig(enabled=True, shared_token="good", role_tokens={})
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, cfg)
    send = _CollectSend()
    _run(mw(_scope("Bearer bad"), None, send))
    assert not inner.called
    assert send.messages[0]["status"] == 401


def test_middleware_passthrough_non_http():
    from src.utils.auth import AuthConfig
    from src.utils.auth_middleware import BearerAuthMiddleware

    cfg = AuthConfig(enabled=True, shared_token="good", role_tokens={})
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, cfg)
    send = _CollectSend()
    _run(mw(_scope(None, type_="lifespan"), None, send))
    assert inner.called  # lifespan bypasses auth


def test_middleware_rejects_cross_role_token():
    """Token issued for role 'deliver' must be rejected by a 'color' server."""
    from src.utils.auth import AuthConfig
    from src.utils.auth_middleware import BearerAuthMiddleware

    cfg = AuthConfig(
        enabled=True,
        shared_token=None,
        role_tokens={"color": "c-tok", "deliver": "d-tok"},
    )
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, cfg, allowed_roles={"color"})
    send = _CollectSend()
    _run(mw(_scope("Bearer d-tok"), None, send))
    assert not inner.called
    assert send.messages[0]["status"] == 401


def test_middleware_allows_own_role_token():
    from src.utils.auth import AuthConfig
    from src.utils.auth_middleware import BearerAuthMiddleware

    cfg = AuthConfig(
        enabled=True,
        shared_token=None,
        role_tokens={"color": "c-tok", "deliver": "d-tok"},
    )
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, cfg, allowed_roles={"color"})
    send = _CollectSend()
    _run(mw(_scope("Bearer c-tok"), None, send))
    assert inner.called
    assert send.messages[0]["status"] == 200
