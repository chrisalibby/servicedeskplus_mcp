"""FastMCP server entry point — imports and registers all tool modules."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import request_api_key
from .tools import admin, assets, changes, cmdb, problems, requests, solutions

mcp = FastMCP("ServiceDesk Plus")

requests.register(mcp)
problems.register(mcp)
changes.register(mcp)
assets.register(mcp)
cmdb.register(mcp)
solutions.register(mcp)
admin.register(mcp)


class _ApiKeyMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            key = headers.get(b"x-sdp-api-key", b"").decode()
            if key:
                token = request_api_key.set(key)
                try:
                    await self.app(scope, receive, send)
                finally:
                    request_api_key.reset(token)
                return
        await self.app(scope, receive, send)


def create_http_app() -> Any:
    return _ApiKeyMiddleware(mcp.streamable_http_app())
