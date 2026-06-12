"""Unit tests for HTTP transport middleware."""

from typing import Any

import pytest

from servicedeskplus_mcp.client import request_api_key
from servicedeskplus_mcp.server import _ApiKeyMiddleware


async def test_middleware_sets_context_var_from_header() -> None:
    captured: list[str] = []

    async def app(scope: Any, receive: Any, send: Any) -> None:
        captured.append(request_api_key.get())

    middleware = _ApiKeyMiddleware(app)
    scope = {
        "type": "http",
        "headers": [(b"x-sdp-api-key", b"user-token-123")],
    }
    await middleware(scope, None, None)
    assert captured == ["user-token-123"]


async def test_middleware_clears_context_var_after_request() -> None:
    async def app(scope: Any, receive: Any, send: Any) -> None:
        pass

    middleware = _ApiKeyMiddleware(app)
    scope = {
        "type": "http",
        "headers": [(b"x-sdp-api-key", b"user-token-123")],
    }
    await middleware(scope, None, None)
    assert request_api_key.get() == ""


async def test_middleware_passes_through_without_header() -> None:
    captured: list[str] = []

    async def app(scope: Any, receive: Any, send: Any) -> None:
        captured.append(request_api_key.get())

    middleware = _ApiKeyMiddleware(app)
    scope = {"type": "http", "headers": []}
    await middleware(scope, None, None)
    assert captured == [""]


async def test_middleware_passes_through_non_http_scope() -> None:
    called: list[bool] = []

    async def app(scope: Any, receive: Any, send: Any) -> None:
        called.append(True)

    middleware = _ApiKeyMiddleware(app)
    await middleware({"type": "lifespan"}, None, None)
    assert called == [True]
