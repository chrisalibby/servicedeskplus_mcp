"""Async httpx client wrapper for ServiceDesk Plus API v3."""

import json
from typing import Any

import httpx

from .auth import get_headers
from .config import settings


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
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result

    async def post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        resp = await self._client.post(
            path,
            data=self._encode(data),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result

    async def put(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        resp = await self._client.put(
            path,
            data=self._encode(data),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result

    async def delete(self, path: str) -> dict[str, Any]:
        resp = await self._client.delete(path)
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result


def get_client() -> SDPClient:
    return SDPClient()
