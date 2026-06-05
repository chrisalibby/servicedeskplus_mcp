"""Unit tests for the SDPClient wrapper."""

import json
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from servicedeskplus_mcp.client import get_client


@respx.mock
async def test_get_encodes_params() -> None:
    route = respx.get("http://sdp.test.local:8080/api/v3/requests").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )
    async with get_client() as c:
        result = await c.get("/requests")
    assert route.called
    assert result == {"requests": []}


@respx.mock
async def test_post_sends_input_data() -> None:
    route = respx.post("http://sdp.test.local:8080/api/v3/requests").mock(
        return_value=httpx.Response(200, json={"request": {"id": "1"}})
    )
    async with get_client() as c:
        result = await c.post("/requests", {"request": {"subject": "Test"}})
    assert route.called
    body = route.calls[0].request.content.decode()
    parsed = parse_qs(body)
    assert "input_data" in parsed
    payload = json.loads(parsed["input_data"][0])
    assert payload["request"]["subject"] == "Test"
    assert result == {"request": {"id": "1"}}


@respx.mock
async def test_put_sends_input_data() -> None:
    route = respx.put("http://sdp.test.local:8080/api/v3/requests/42").mock(
        return_value=httpx.Response(200, json={"request": {"id": "42"}})
    )
    async with get_client() as c:
        result = await c.put("/requests/42", {"request": {"status": {"name": "Closed"}}})
    assert route.called
    assert result["request"]["id"] == "42"


@respx.mock
async def test_delete_request() -> None:
    route = respx.delete("http://sdp.test.local:8080/api/v3/requests/5").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "Success"}})
    )
    async with get_client() as c:
        result = await c.delete("/requests/5")
    assert route.called
    assert result["response_status"]["status"] == "Success"


@respx.mock
async def test_auth_header_sent() -> None:
    route = respx.get("http://sdp.test.local:8080/api/v3/requests").mock(
        return_value=httpx.Response(200, json={})
    )
    async with get_client() as c:
        await c.get("/requests")
    request = route.calls[0].request
    assert request.headers["Authtoken"] == "test-api-key"
    assert "sdp.v3" in request.headers["Accept"]


@respx.mock
async def test_http_error_raises() -> None:
    respx.get("http://sdp.test.local:8080/api/v3/requests").mock(
        return_value=httpx.Response(401, json={"message": "Unauthorized"})
    )
    async with get_client() as c:
        with pytest.raises(httpx.HTTPStatusError):
            await c.get("/requests")
