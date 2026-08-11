"""FastMCP server entry point — imports and registers all tool modules."""

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from .client import request_api_key
from .tools import (
    admin,
    assets,
    changes,
    cmdb,
    contracts,
    problems,
    projects,
    releases,
    requests,
    schemas,
    solutions,
)

# FastMCP auto-enables DNS-rebinding Host-header checks (allowing only 127.0.0.1/localhost/::1)
# because it defaults to host="127.0.0.1", regardless of the SDP_HTTP_HOST uvicorn actually binds
# to in __main__.py. That 421s any request through a reverse proxy. Auth is already enforced by
# _ApiKeyMiddleware below, so disable the redundant Host check rather than maintaining an allowlist.
mcp = FastMCP(
    "ServiceDesk Plus",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

requests.register(mcp)
problems.register(mcp)
changes.register(mcp)
releases.register(mcp)
projects.register(mcp)
assets.register(mcp)
cmdb.register(mcp)
contracts.register(mcp)
solutions.register(mcp)
admin.register(mcp)
schemas.register(mcp)


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
