"""Async httpx client wrapper for ServiceDesk Plus API v3."""

import json
from typing import Any, cast

import httpx

from .auth import get_headers
from .config import settings


def _sdp_error(resp: httpx.Response) -> dict[str, Any]:
    """Extract human-readable error text from an SDP error response."""
    try:
        body = cast(dict[str, Any], resp.json())
        raw_rs = body.get("response_status", {})
        rs = cast(
            dict[str, Any],
            (raw_rs[0] if raw_rs else {}) if isinstance(raw_rs, list) else raw_rs,
        )
        messages = cast(list[dict[str, Any]], rs.get("messages", []))
        text = "; ".join(str(m.get("message", "")) for m in messages if m.get("message"))
        return {
            "error": text or f"HTTP {resp.status_code}",
            "status_code": resp.status_code,
            "response_status": rs,
        }
    except Exception:
        return {"error": f"HTTP {resp.status_code}", "status_code": resp.status_code}


class SDPClient:
    def __init__(self) -> None:
        self._headers = get_headers(settings.SDP_API_KEY)
        self._client = httpx.AsyncClient(
            base_url=settings.base_url,
            headers=self._headers,
            timeout=settings.SDP_TIMEOUT,
            verify=settings.SDP_VERIFY_SSL,
        )

    async def __aenter__(self) -> "SDPClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._client.aclose()

    def _encode(self, data: dict[str, Any]) -> dict[str, str]:
        return {"input_data": json.dumps(data)}

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            resp = await self._client.get(path, params=params)
        except httpx.ConnectError as exc:
            return {"error": f"Cannot connect to SDP: {exc}"}
        except httpx.TimeoutException:
            return {"error": "Request timed out — check SDP_SERVER and SDP_TIMEOUT"}
        if not resp.is_success:
            return _sdp_error(resp)
        result: dict[str, Any] = resp.json()
        return result

    async def post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = await self._client.post(
                path,
                data=self._encode(data),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.ConnectError as exc:
            return {"error": f"Cannot connect to SDP: {exc}"}
        except httpx.TimeoutException:
            return {"error": "Request timed out — check SDP_SERVER and SDP_TIMEOUT"}
        if not resp.is_success:
            return _sdp_error(resp)
        result: dict[str, Any] = resp.json()
        return result

    async def put(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = await self._client.put(
                path,
                data=self._encode(data),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.ConnectError as exc:
            return {"error": f"Cannot connect to SDP: {exc}"}
        except httpx.TimeoutException:
            return {"error": "Request timed out — check SDP_SERVER and SDP_TIMEOUT"}
        if not resp.is_success:
            return _sdp_error(resp)
        result: dict[str, Any] = resp.json()
        return result

    async def delete(self, path: str) -> dict[str, Any]:
        try:
            resp = await self._client.delete(path)
        except httpx.ConnectError as exc:
            return {"error": f"Cannot connect to SDP: {exc}"}
        except httpx.TimeoutException:
            return {"error": "Request timed out — check SDP_SERVER and SDP_TIMEOUT"}
        if not resp.is_success:
            return _sdp_error(resp)
        result: dict[str, Any] = resp.json()
        return result


def get_client() -> SDPClient:
    return SDPClient()
