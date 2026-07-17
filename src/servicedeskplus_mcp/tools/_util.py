"""Shared helpers for ServiceDesk Plus tool modules."""

import json
import re
from typing import Any

from ..client import SDPClient

_CDATA_RE = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.DOTALL)


def strip_cdata(text: str) -> str:
    text = _CDATA_RE.sub(r"\1", text)
    return text.replace("<![CDATA[", "").replace("]]>", "")


def normalize_id(value: str) -> str:
    match = re.search(r"\d+", value)
    return match.group() if match else value


async def resolve_ref(
    client: SDPClient,
    path: str,
    plural_key: str,
    value: str,
    name_field: str = "name",
) -> dict[str, Any]:
    """Resolve a name or numeric ID to {"id": ...}; returns {"error": ...} on failure."""
    if value.isdigit():
        return {"id": value}
    for condition in ("is", "contains"):
        list_info = {
            "row_count": 25,
            "search_criteria": [
                {"field": name_field, "condition": condition, "value": value}
            ],
        }
        result = await client.get(
            path, params={"input_data": json.dumps({"list_info": list_info})}
        )
        if "error" in result:
            return {"error": f"Lookup on {path} failed: {result['error']}"}
        rows = [
            r
            for r in result.get(plural_key, [])
            if value.lower() in str(r.get(name_field, "")).lower()
        ]
        exact = [r for r in rows if str(r.get(name_field, "")).lower() == value.lower()]
        if len(exact) == 1:
            return {"id": exact[0]["id"]}
        if condition == "contains" and rows:
            if len(rows) == 1:
                return {"id": rows[0]["id"]}
            names = ", ".join(str(r.get(name_field, "?")) for r in rows[:10])
            return {
                "error": f"Ambiguous match for '{value}' on {path} — close matches: {names}"
            }
    return {"error": f"No match found for '{value}' on {path}"}
