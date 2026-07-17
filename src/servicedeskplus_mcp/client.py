"""Async httpx client wrapper for ServiceDesk Plus API v3."""

import asyncio
import json
from contextvars import ContextVar
from typing import Any, cast

import httpx

from .auth import get_headers
from .config import settings

request_api_key: ContextVar[str] = ContextVar("sdp_api_key", default="")

_GET_RETRIES = 2
_RETRY_BACKOFF = 1.0

_INDETERMINATE_MESSAGE = (
    "The write may have been applied on the server — verify before retrying to avoid duplicates."
)


def _indeterminate_error(kind: str) -> dict[str, Any]:
    return {
        "error": f"{kind} request timed out — check SDP_SERVER and SDP_TIMEOUT",
        "indeterminate": True,
        "message": _INDETERMINATE_MESSAGE,
    }


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
        api_key = request_api_key.get() or settings.SDP_API_KEY
        self._headers = get_headers(api_key)
        self._client = httpx.AsyncClient(
            base_url=settings.base_url,
            headers=self._headers,
            timeout=httpx.Timeout(
                connect=10.0,
                read=settings.SDP_TIMEOUT,
                write=settings.SDP_TIMEOUT,
                pool=10.0,
            ),
            verify=settings.SDP_VERIFY_SSL,
        )

    async def __aenter__(self) -> "SDPClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._client.aclose()

    def _encode(self, data: dict[str, Any]) -> dict[str, str]:
        return {"input_data": json.dumps(data)}

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        for attempt in range(_GET_RETRIES + 1):
            try:
                resp = await self._client.get(path, params=params)
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                if attempt < _GET_RETRIES:
                    await asyncio.sleep(_RETRY_BACKOFF * (attempt + 1))
                    continue
                if isinstance(exc, httpx.ConnectError):
                    return {"error": f"Cannot connect to SDP: {exc}"}
                return {"error": "Request timed out — check SDP_SERVER and SDP_TIMEOUT"}
            if not resp.is_success:
                return _sdp_error(resp)
            result: dict[str, Any] = resp.json()
            return result
        return {"error": "Request failed after retries"}

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
            return _indeterminate_error("POST")
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
            return _indeterminate_error("PUT")
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
            return _indeterminate_error("DELETE")
        if not resp.is_success:
            return _sdp_error(resp)
        result: dict[str, Any] = resp.json()
        return result


def get_client() -> SDPClient:
    return SDPClient()
