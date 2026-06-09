"""
Smoke tests — verify basic connectivity and auth against a live SDP instance.
Run with: uv run pytest tests/integration/ -v -m integration
"""

import pytest

from .conftest import skip_if_no_server

pytestmark = [pytest.mark.integration, skip_if_no_server]


async def test_can_reach_server(client) -> None:
    """Server responds and auth header is accepted (no 401/403)."""
    result = await client.get("/requests", params={"input_data": '{"list_info":{"row_count":1}}'})
    assert "requests" in result or "response_status" in result


async def test_list_requests_returns_data(client) -> None:
    """list_requests returns a parseable response with expected keys."""
    import json
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 5}})}
    result = await client.get("/requests", params=params)
    assert isinstance(result, dict)
    # SDP always returns response_status on success
    assert "response_status" in result or "requests" in result


async def test_list_statuses(client) -> None:
    """Fetch statuses — confirms lookup endpoints work and reveals your status names."""
    import json
    params = {"input_data": json.dumps({"list_info": {"row_count": 50}})}
    result = await client.get("/statuses", params=params)
    assert isinstance(result, dict)
    print("\nStatuses on this instance:")
    for s in result.get("statuses", []):
        print(f"  {s.get('id')} — {s.get('name')}")


async def test_list_priorities(client) -> None:
    """Fetch priorities — reveals your priority names for use in other tests."""
    import json
    params = {"input_data": json.dumps({"list_info": {"row_count": 50}})}
    result = await client.get("/priorities", params=params)
    assert isinstance(result, dict)
    print("\nPriorities on this instance:")
    for p in result.get("priorities", []):
        print(f"  {p.get('id')} — {p.get('name')}")


async def test_list_categories(client) -> None:
    """Fetch categories."""
    import json
    params = {"input_data": json.dumps({"list_info": {"row_count": 50}})}
    result = await client.get("/categories", params=params)
    assert isinstance(result, dict)
    print("\nCategories on this instance:")
    for c in result.get("categories", []):
        print(f"  {c.get('id')} — {c.get('name')}")


async def test_list_technicians(client) -> None:
    """Fetch technicians — use names from output in other tests."""
    import json
    params = {"input_data": json.dumps({"list_info": {"row_count": 50}})}
    result = await client.get("/technicians", params=params)
    assert isinstance(result, dict)
    print("\nTechnicians on this instance:")
    for t in result.get("/api/v3/technicians", result.get("technicians", [])):
        print(f"  {t.get('id')} — {t.get('name')}")
