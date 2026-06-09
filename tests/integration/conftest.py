"""Shared fixtures for integration tests against a live SDP instance."""

from pathlib import Path
from typing import Any

import httpx
import pytest
import pytest_asyncio
from dotenv import dotenv_values

from servicedeskplus_mcp.auth import get_headers
from servicedeskplus_mcp.config import Settings

_env_file = Path(__file__).parents[2] / ".env"
_env = dotenv_values(_env_file) if _env_file.exists() else {}

_key = _env.get("SDP_API_KEY", "")
_server = _env.get("SDP_SERVER", "")
_live = bool(_key and _server and _key != "your-api-key-here")

skip_if_no_server = pytest.mark.skipif(
    not _live,
    reason="No live SDP server configured — set SDP_SERVER and SDP_API_KEY in .env",
)


def _live_settings() -> Settings:
    """Build a Settings instance directly from .env values, bypassing the module singleton."""
    return Settings(
        SDP_SERVER=_env.get("SDP_SERVER", "localhost"),
        SDP_PORT=int(_env.get("SDP_PORT", 8080)),
        SDP_API_KEY=_env.get("SDP_API_KEY", ""),
        SDP_PORTAL_ID=_env.get("SDP_PORTAL_ID", ""),
        SDP_TIMEOUT=float(_env.get("SDP_TIMEOUT", 30)),
        SDP_VERIFY_SSL=_env.get("SDP_VERIFY_SSL", "true").lower() != "false",
    )


class _LiveClient:
    """Minimal client wrapper that mirrors SDPClient but uses live settings directly."""

    def __init__(self, s: Settings) -> None:
        self._http = httpx.AsyncClient(
            base_url=s.base_url,
            headers=get_headers(s.SDP_API_KEY),
            timeout=s.SDP_TIMEOUT,
            verify=s.SDP_VERIFY_SSL,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    def _encode(self, data: dict[str, Any]) -> dict[str, str]:
        import json
        return {"input_data": json.dumps(data)}

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        r = await self._http.get(path, params=params)
        r.raise_for_status()
        result: dict[str, Any] = r.json()
        return result

    async def post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        r = await self._http.post(
            path, data=self._encode(data),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        result: dict[str, Any] = r.json()
        return result

    async def put(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        r = await self._http.put(
            path, data=self._encode(data),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        result: dict[str, Any] = r.json()
        return result

    async def delete(self, path: str) -> dict[str, Any]:
        r = await self._http.delete(path)
        r.raise_for_status()
        result: dict[str, Any] = r.json()
        return result


@pytest_asyncio.fixture
async def client() -> Any:
    """Authenticated client connected to the live SDP instance."""
    c = _LiveClient(_live_settings())
    try:
        yield c
    finally:
        await c.aclose()
