"""
Integration tests for asset tools against a live SDP instance.
Run with: uv run pytest tests/integration/ -v -m integration
"""

import json

import pytest

from .conftest import skip_if_no_server

pytestmark = [pytest.mark.integration, skip_if_no_server]


async def test_list_assets(client) -> None:
    """Fetch first page of assets — confirms endpoint and auth."""
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 5}})}
    result = await client.get("/assets", params=params)
    assert isinstance(result, dict)
    print(f"\nAsset count (first 5): {len(result.get('assets', []))}")
    for a in result.get("assets", []):
        print(f"  {a.get('id')} — {a.get('name')} ({a.get('asset_type', {}).get('name', '?')})")


async def test_list_workstations(client) -> None:
    """Fetch first page of workstations."""
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 5}})}
    result = await client.get("/workstations", params=params)
    assert isinstance(result, dict)
    print(f"\nWorkstation count (first 5): {len(result.get('workstations', []))}")
    for w in result.get("workstations", []):
        print(f"  {w.get('id')} — {w.get('name')}")


async def test_get_first_asset(client) -> None:
    """Fetch the first asset in the list and retrieve it by ID."""
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 1}})}
    listing = await client.get("/assets", params=params)
    assets = listing.get("assets", [])
    if not assets:
        pytest.skip("No assets found on this instance")

    asset_id = assets[0]["id"]
    result = await client.get(f"/assets/{asset_id}")
    assert result["asset"]["id"] == asset_id
    print(f"\nFetched asset: {result['asset'].get('name')} (id={asset_id})")
