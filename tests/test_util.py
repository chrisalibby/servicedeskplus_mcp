"""Unit tests for shared tool helpers."""

import httpx
import respx

from servicedeskplus_mcp.client import get_client
from servicedeskplus_mcp.tools._util import normalize_id, resolve_ref, strip_cdata

from .conftest import BASE


def test_strip_cdata_wrapped() -> None:
    assert strip_cdata("<![CDATA[<b>hi</b>]]>") == "<b>hi</b>"


def test_strip_cdata_stray_trailing() -> None:
    assert strip_cdata("<b>hi</b>]]>") == "<b>hi</b>"


def test_strip_cdata_plain_text_untouched() -> None:
    assert strip_cdata("plain <b>html</b>") == "plain <b>html</b>"


def test_strip_cdata_multiple_sections() -> None:
    assert strip_cdata("<![CDATA[a]]> and <![CDATA[b]]>") == "a and b"


def test_normalize_id_plain() -> None:
    assert normalize_id("42") == "42"


def test_normalize_id_re_prefix() -> None:
    assert normalize_id("RE-1234") == "1234"


def test_normalize_id_hash_prefix() -> None:
    assert normalize_id("#567") == "567"


def test_normalize_id_no_digits_passthrough() -> None:
    assert normalize_id("abc") == "abc"


@respx.mock
async def test_resolve_ref_numeric_skips_lookup() -> None:
    async with get_client() as c:
        result = await resolve_ref(c, "/urgencies", "urgencies", "5")
    assert result == {"id": "5"}


@respx.mock
async def test_resolve_ref_exact_name_match() -> None:
    respx.get(f"{BASE}/urgencies").mock(
        return_value=httpx.Response(200, json={
            "urgencies": [{"id": "2", "name": "Normal"}]
        })
    )
    async with get_client() as c:
        result = await resolve_ref(c, "/urgencies", "urgencies", "normal")
    assert result == {"id": "2"}


@respx.mock
async def test_resolve_ref_ambiguous_lists_matches() -> None:
    respx.get(f"{BASE}/products").mock(
        return_value=httpx.Response(200, json={
            "products": [
                {"id": "1", "name": "EliteBook 840 G8"},
                {"id": "2", "name": "EliteBook 840 G9"},
            ]
        })
    )
    async with get_client() as c:
        result = await resolve_ref(c, "/products", "products", "EliteBook")
    assert "error" in result
    assert "EliteBook 840 G8" in result["error"]


@respx.mock
async def test_resolve_ref_no_match() -> None:
    respx.get(f"{BASE}/products").mock(
        return_value=httpx.Response(200, json={"products": []})
    )
    async with get_client() as c:
        result = await resolve_ref(c, "/products", "products", "Nothing")
    assert "error" in result
    assert "No match" in result["error"]
