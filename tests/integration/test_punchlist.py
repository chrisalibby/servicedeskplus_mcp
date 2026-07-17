"""
Integration tests for the real-world-usage punch list fixes against a live SDP instance.
Run with: uv run pytest tests/integration/ -v -m integration
"""

import json

import pytest

from .conftest import skip_if_no_server

pytestmark = [pytest.mark.integration, skip_if_no_server]


async def test_list_products(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 5}})}
    result = await client.get("/products", params=params)
    assert "error" not in result, result
    products = result.get("products", [])
    assert products, "Expected at least one product in the catalog"
    print(f"\nProducts (first 5): {[p.get('name') for p in products]}")


async def test_list_product_types(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 100}})}
    result = await client.get("/product_types", params=params)
    assert "error" not in result, result
    types = result.get("product_types", [])
    assert types, "Expected at least one product type"
    names = [t.get("name") for t in types]
    print(f"\nProduct types: {names[:15]}")


async def test_list_products_filtered_by_name(client) -> None:
    list_info = {
        "row_count": 10,
        "search_criteria": [{"field": "name", "condition": "contains", "value": "EliteBook"}],
    }
    result = await client.get(
        "/products", params={"input_data": json.dumps({"list_info": list_info})}
    )
    assert "error" not in result, result
    print(f"\nEliteBook products: {[p.get('name') for p in result.get('products', [])]}")


async def test_create_asset_end_to_end(client) -> None:
    """Create an asset with nested product ID, verify, then delete it."""
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 1}})}
    products = (await client.get("/products", params=params)).get("products", [])
    if not products:
        pytest.skip("No products in catalog")
    product_id = products[0]["id"]

    asset = {"name": "MCP-INTEGRATION-TEST-ASSET", "product": {"id": product_id}}
    created = await client.post("/assets", {"asset": asset})
    assert "error" not in created, created
    asset_id = created["asset"]["id"]
    print(f"\nCreated asset {asset_id} with product {product_id}")

    fetched = await client.get(f"/assets/{asset_id}")
    assert fetched["asset"]["name"] == "MCP-INTEGRATION-TEST-ASSET"

    deleted = await client.delete(f"/assets/{asset_id}")
    print(f"Delete result: {deleted.get('response_status', deleted.get('error'))}")


async def test_create_request_urgency_rejected_quirk(client) -> None:
    """Documented quirk: this instance rejects urgency on requests in every format
    (name and ID, on create and update) — the field is not on the request form.
    If this test starts failing, urgency became supported: update the quirk docs."""
    request = {
        "subject": "MCP integration test — urgency quirk probe",
        "description": "Safe to delete; created by automated test.",
        "requester": {"name": "Chris Libby"},
        "category": {"name": "User Administration"},
        "subcategory": {"name": "Password Reset"},
        "urgency": {"id": "2"},
    }
    created = await client.post("/requests", {"request": request})
    assert "error" in created, "urgency was accepted — quirk no longer applies, update docs"
    assert created["status_code"] == 400
    print("\nConfirmed: urgency rejected on create (400) — matches documented quirk")


async def test_list_changes_desc_sort(client) -> None:
    """Newest-first sort — the fix for 'oldest change from 2020 first'."""
    list_info = {"row_count": 5, "sort_field": "created_time", "sort_order": "desc"}
    result = await client.get(
        "/changes", params={"input_data": json.dumps({"list_info": list_info})}
    )
    assert "error" not in result, result
    changes = result.get("changes", [])
    times = [int(c["created_time"]["value"]) for c in changes if c.get("created_time")]
    assert times == sorted(times, reverse=True), f"Not desc-sorted: {times}"
    print(f"\nNewest change: {changes[0].get('title') if changes else 'none'}")


async def test_contracts_available(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 3}})}
    result = await client.get("/contracts", params=params)
    assert "error" not in result, result
    print(f"\nContracts (first 3): {[c.get('name') for c in result.get('contracts', [])]}")


async def test_purchase_orders_available(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 3}})}
    result = await client.get("/purchase_orders", params=params)
    assert "error" not in result, result
    pos = result.get("purchase_orders", [])
    print(f"\nPurchase orders (first 3): {[p.get('custom_po_id') for p in pos]}")


async def test_assets_missing_product_type_filter_accepted(client) -> None:
    """SDP null-check convention: condition 'is' with empty values — must not 400."""
    list_info = {
        "row_count": 3,
        "search_criteria": [{"field": "product_type", "condition": "is", "values": []}],
    }
    result = await client.get(
        "/assets", params={"input_data": json.dumps({"list_info": list_info})}
    )
    assert "error" not in result, result
    print(f"\nAssets missing product_type: {len(result.get('assets', []))}")
