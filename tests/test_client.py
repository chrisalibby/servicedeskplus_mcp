"""Unit tests for the SDPClient wrapper."""

import json
from urllib.parse import parse_qs

import httpx
import respx

from servicedeskplus_mcp.client import request_api_key, get_client


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
async def test_4xx_returns_error_dict_not_exception() -> None:
    respx.get("http://sdp.test.local:8080/api/v3/requests").mock(
        return_value=httpx.Response(401, json={
            "response_status": {
                "status_code": 4000,
                "messages": [{"message": "Invalid API key"}],
                "status": "failed",
            }
        })
    )
    async with get_client() as c:
        result = await c.get("/requests")
    assert "error" in result
    assert "Invalid API key" in result["error"]
    assert result["status_code"] == 401


@respx.mock
async def test_400_with_mandatory_fields_surfaces_message() -> None:
    respx.post("http://sdp.test.local:8080/api/v3/requests").mock(
        return_value=httpx.Response(400, json={
            "response_status": {
                "status_code": 4000,
                "messages": [{"message": "Please fill the mandatory fields"}],
                "status": "failed",
            }
        })
    )
    async with get_client() as c:
        result = await c.post("/requests", {"request": {"subject": "test"}})
    assert "error" in result
    assert "mandatory fields" in result["error"]


@respx.mock
async def test_connect_error_returns_error_dict() -> None:
    respx.get("http://sdp.test.local:8080/api/v3/requests").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )
    async with get_client() as c:
        result = await c.get("/requests")
    assert "error" in result
    assert "connect" in result["error"].lower()


@respx.mock
async def test_context_var_overrides_settings_api_key() -> None:
    route = respx.get("http://sdp.test.local:8080/api/v3/requests").mock(
        return_value=httpx.Response(200, json={})
    )
    token = request_api_key.set("per-connection-key")
    try:
        async with get_client() as c:
            await c.get("/requests")
    finally:
        request_api_key.reset(token)
    assert route.calls[0].request.headers["Authtoken"] == "per-connection-key"


@respx.mock
async def test_falls_back_to_settings_when_context_var_empty() -> None:
    route = respx.get("http://sdp.test.local:8080/api/v3/requests").mock(
        return_value=httpx.Response(200, json={})
    )
    token = request_api_key.set("")
    try:
        async with get_client() as c:
            await c.get("/requests")
    finally:
        request_api_key.reset(token)
    assert route.calls[0].request.headers["Authtoken"] == "test-api-key"
