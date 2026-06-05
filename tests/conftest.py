"""Shared fixtures and helpers for the test suite."""

import json
import os
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
import respx

# Ensure settings can be constructed without a real .env
os.environ.setdefault("SDP_SERVER", "sdp.test.local")
os.environ.setdefault("SDP_PORT", "8080")
os.environ.setdefault("SDP_API_KEY", "test-api-key")
os.environ.setdefault("SDP_PORTAL_ID", "")

BASE = "http://sdp.test.local:8080/api/v3"


def decode_body(call: Any) -> dict[str, Any]:
    """Decode the input_data JSON from a POST/PUT form body."""
    raw: str = call.request.content.decode()
    return json.loads(parse_qs(raw)["input_data"][0])


def decode_get_params(call: Any) -> dict[str, Any]:
    """Decode the input_data JSON from a GET query string."""
    qs = parse_qs(urlparse(str(call.request.url)).query)
    return json.loads(qs["input_data"][0])


def get_tool(name: str) -> Any:
    """Return a registered MCP tool function by name."""
    from servicedeskplus_mcp.server import mcp
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    return next(t for t in tools if t.name == name)


@pytest.fixture
def sdp_mock() -> Any:
    """Active respx router that intercepts all httpx requests."""
    with respx.mock(base_url=BASE) as router:
        yield router
