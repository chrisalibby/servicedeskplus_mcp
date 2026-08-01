"""Comprehensive tests for asset and workstation tools."""

import httpx
import respx

from .conftest import BASE, decode_body, decode_get_params, get_tool

# ---------------------------------------------------------------------------
# list_assets
# ---------------------------------------------------------------------------

@respx.mock
async def test_list_assets_default_no_filters() -> None:
    route = respx.get(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"assets": []})
    )
    await get_tool("list_assets").fn()
    params = decode_get_params(route.calls[0])
    assert params["list_info"]["start_index"] == 0
    assert params["list_info"]["row_count"] == 25
    assert "search_criteria" not in params["list_info"]


@respx.mock
async def test_list_assets_type_filter() -> None:
    route = respx.get(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"assets": []})
    )
    await get_tool("list_assets").fn(asset_type="Laptop")
    params = decode_get_params(route.calls[0])
    criteria = params["list_info"]["search_criteria"]
    assert criteria[0] == {"field": "product_type.name", "condition": "is", "value": "Laptop"}


@respx.mock
async def test_list_assets_state_filter() -> None:
    route = respx.get(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"assets": []})
    )
    await get_tool("list_assets").fn(state="In Use")
    params = decode_get_params(route.calls[0])
    criteria = params["list_info"]["search_criteria"]
    assert criteria[0] == {"field": "asset_state", "condition": "is", "value": "In Use"}


@respx.mock
async def test_list_assets_both_filters() -> None:
    route = respx.get(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"assets": []})
    )
    await get_tool("list_assets").fn(asset_type="Desktop", state="In Store")
    params = decode_get_params(route.calls[0])
    criteria = params["list_info"]["search_criteria"]
    assert len(criteria) == 2
    fields = {c["field"] for c in criteria}
    assert fields == {"product_type.name", "asset_state"}


@respx.mock
async def test_list_assets_serial_number_filter() -> None:
    route = respx.get(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"assets": []})
    )
    await get_tool("list_assets").fn(serial_number="SN12345")
    params = decode_get_params(route.calls[0])
    criteria = params["list_info"]["search_criteria"]
    assert criteria[0] == {"field": "serial_number", "condition": "is", "values": ["SN12345"]}


@respx.mock
async def test_list_assets_missing_product_type_filter() -> None:
    route = respx.get(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"assets": []})
    )
    await get_tool("list_assets").fn(missing_product_type=True)
    params = decode_get_params(route.calls[0])
    criteria = params["list_info"]["search_criteria"]
    assert criteria[0] == {"field": "product_type", "condition": "is", "values": []}


@respx.mock
async def test_list_assets_sort_params() -> None:
    route = respx.get(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"assets": []})
    )
    await get_tool("list_assets").fn(sort_field="created_time", sort_order="desc")
    params = decode_get_params(route.calls[0])
    assert params["list_info"]["sort_field"] == "created_time"
    assert params["list_info"]["sort_order"] == "desc"


@respx.mock
async def test_list_assets_pagination() -> None:
    route = respx.get(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"assets": []})
    )
    await get_tool("list_assets").fn(page=3, page_size=50)
    params = decode_get_params(route.calls[0])
    assert params["list_info"]["start_index"] == 100
    assert params["list_info"]["row_count"] == 50


# ---------------------------------------------------------------------------
# get_asset
# ---------------------------------------------------------------------------

@respx.mock
async def test_get_asset_url() -> None:
    route = respx.get(f"{BASE}/assets/100").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "100"}})
    )
    result = await get_tool("get_asset").fn(asset_id="100")
    assert route.called
    assert result["asset"]["id"] == "100"


# ---------------------------------------------------------------------------
# create_asset
# ---------------------------------------------------------------------------

@respx.mock
async def test_create_asset_numeric_product_id_skips_lookup() -> None:
    route = respx.post(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "200"}})
    )
    await get_tool("create_asset").fn(name="LAPTOP-001", product="4586")
    payload = decode_body(route.calls[0])
    assert payload["asset"]["name"] == "LAPTOP-001"
    assert payload["asset"]["product"] == {"id": "4586"}
    assert "asset_type" not in payload["asset"]
    assert "product_type" not in payload["asset"]


@respx.mock
async def test_create_asset_resolves_product_name() -> None:
    respx.get(f"{BASE}/products").mock(
        return_value=httpx.Response(200, json={
            "products": [{"id": "4586", "name": "HP EliteBook 840 G8"}]
        })
    )
    route = respx.post(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "201"}})
    )
    await get_tool("create_asset").fn(name="LAPTOP-002", product="HP EliteBook 840 G8")
    payload = decode_body(route.calls[0])
    assert payload["asset"]["product"] == {"id": "4586"}


@respx.mock
async def test_create_asset_unresolvable_product_returns_error() -> None:
    respx.get(f"{BASE}/products").mock(
        return_value=httpx.Response(200, json={"products": []})
    )
    post_route = respx.post(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "202"}})
    )
    result = await get_tool("create_asset").fn(name="LAPTOP-003", product="Nonexistent")
    assert "error" in result
    assert "No match" in result["error"]
    assert not post_route.called


@respx.mock
async def test_create_asset_with_product_type_id() -> None:
    route = respx.post(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "203"}})
    )
    await get_tool("create_asset").fn(
        name="LAPTOP-004", product="4586", product_type="3361"
    )
    payload = decode_body(route.calls[0])
    assert payload["asset"]["product"] == {"id": "4586"}
    assert payload["asset"]["product_type"] == {"id": "3361"}


@respx.mock
async def test_create_asset_all_optional_fields() -> None:
    route = respx.post(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "204"}})
    )
    await get_tool("create_asset").fn(
        name="DESKTOP-010",
        product="4590",
        serial_number="SN12345",
        vendor="Dell",
        site="HQ",
        department="IT",
        assigned_to="jdoe",
    )
    payload = decode_body(route.calls[0])
    asset = payload["asset"]
    assert asset["serial_number"] == "SN12345"
    assert asset["vendor"] == {"name": "Dell"}
    assert asset["site"] == {"name": "HQ"}
    assert asset["department"] == {"name": "IT"}
    assert asset["used_by"] == {"name": "jdoe"}


@respx.mock
async def test_create_asset_depreciation_with_numeric_type() -> None:
    route = respx.post(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "205"}})
    )
    await get_tool("create_asset").fn(
        name="LAPTOP-005",
        product="4586",
        depreciation_type="1",
        useful_life="36",
        salvage_value="150.00",
    )
    payload = decode_body(route.calls[0])
    assert payload["asset"]["asset_depreciation"] == {
        "depreciation_type": {"id": "1"},
        "useful_life": "36",
        "salvage_value": "150.00",
    }


@respx.mock
async def test_create_asset_depreciation_resolves_type_name() -> None:
    respx.get(f"{BASE}/depreciation_types").mock(
        return_value=httpx.Response(200, json={
            "depreciation_types": [{"id": "1", "name": "Straight Line"}]
        })
    )
    route = respx.post(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "206"}})
    )
    await get_tool("create_asset").fn(
        name="LAPTOP-006", product="4586", depreciation_type="Straight Line"
    )
    payload = decode_body(route.calls[0])
    assert payload["asset"]["asset_depreciation"] == {"depreciation_type": {"id": "1"}}


@respx.mock
async def test_create_asset_no_depreciation_fields_omits_key() -> None:
    route = respx.post(f"{BASE}/assets").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "207"}})
    )
    await get_tool("create_asset").fn(name="LAPTOP-007", product="4586")
    payload = decode_body(route.calls[0])
    assert "asset_depreciation" not in payload["asset"]


# ---------------------------------------------------------------------------
# update_asset
# ---------------------------------------------------------------------------

@respx.mock
async def test_update_asset_state_key_name() -> None:
    route = respx.put(f"{BASE}/assets/100").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "100"}})
    )
    await get_tool("update_asset").fn(asset_id="100", state="In Repair")
    payload = decode_body(route.calls[0])
    # SDP on-prem uses "asset_state" not "state"
    assert payload["asset"]["asset_state"] == "In Repair"
    assert "state" not in payload["asset"]


@respx.mock
async def test_update_asset_assigned_to_uses_used_by() -> None:
    route = respx.put(f"{BASE}/assets/100").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "100"}})
    )
    await get_tool("update_asset").fn(asset_id="100", assigned_to="jdoe")
    payload = decode_body(route.calls[0])
    # SDP on-prem uses "used_by" not "assigned_to"
    assert payload["asset"]["used_by"] == {"name": "jdoe"}
    assert "assigned_to" not in payload["asset"]


@respx.mock
async def test_update_asset_all_empty_sends_empty_body() -> None:
    route = respx.put(f"{BASE}/assets/100").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "100"}})
    )
    await get_tool("update_asset").fn(asset_id="100")
    payload = decode_body(route.calls[0])
    assert payload["asset"] == {}


@respx.mock
async def test_update_asset_site_and_department() -> None:
    route = respx.put(f"{BASE}/assets/100").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "100"}})
    )
    await get_tool("update_asset").fn(
        asset_id="100", site="Branch Office", department="Finance"
    )
    payload = decode_body(route.calls[0])
    assert payload["asset"]["site"] == {"name": "Branch Office"}
    assert payload["asset"]["department"] == {"name": "Finance"}


@respx.mock
async def test_update_asset_depreciation_fields() -> None:
    route = respx.put(f"{BASE}/assets/100").mock(
        return_value=httpx.Response(200, json={"asset": {"id": "100"}})
    )
    await get_tool("update_asset").fn(
        asset_id="100",
        depreciation_type="2",
        useful_life="48",
        salvage_value="200.00",
    )
    payload = decode_body(route.calls[0])
    assert payload["asset"]["asset_depreciation"] == {
        "depreciation_type": {"id": "2"},
        "useful_life": "48",
        "salvage_value": "200.00",
    }


# ---------------------------------------------------------------------------
# list_depreciation_types
# ---------------------------------------------------------------------------

@respx.mock
async def test_list_depreciation_types() -> None:
    route = respx.get(f"{BASE}/depreciation_types").mock(
        return_value=httpx.Response(200, json={"depreciation_types": []})
    )
    await get_tool("list_depreciation_types").fn()
    assert route.called


# ---------------------------------------------------------------------------
# list_workstations / get_workstation
# ---------------------------------------------------------------------------

@respx.mock
async def test_list_workstations_default() -> None:
    route = respx.get(f"{BASE}/workstations").mock(
        return_value=httpx.Response(200, json={"workstations": []})
    )
    await get_tool("list_workstations").fn()
    params = decode_get_params(route.calls[0])
    assert params["list_info"]["start_index"] == 0
    assert params["list_info"]["row_count"] == 25


@respx.mock
async def test_list_workstations_page2() -> None:
    route = respx.get(f"{BASE}/workstations").mock(
        return_value=httpx.Response(200, json={"workstations": []})
    )
    await get_tool("list_workstations").fn(page=2)
    params = decode_get_params(route.calls[0])
    assert params["list_info"]["start_index"] == 25


@respx.mock
async def test_get_workstation_url() -> None:
    route = respx.get(f"{BASE}/workstations/55").mock(
        return_value=httpx.Response(200, json={"workstation": {"id": "55"}})
    )
    result = await get_tool("get_workstation").fn(workstation_id="55")
    assert route.called
    assert result["workstation"]["id"] == "55"


# ---------------------------------------------------------------------------
# error handling — errors return readable dicts, not exceptions
# ---------------------------------------------------------------------------

@respx.mock
async def test_404_returns_error_dict() -> None:
    respx.get(f"{BASE}/assets/999").mock(
        return_value=httpx.Response(404, json={
            "response_status": {"messages": [{"message": "Asset not found"}], "status": "failed"}
        })
    )
    result = await get_tool("get_asset").fn(asset_id="999")
    assert "error" in result
    assert result["status_code"] == 404


@respx.mock
async def test_500_returns_error_dict() -> None:
    respx.post(f"{BASE}/assets").mock(
        return_value=httpx.Response(500, json={
            "response_status": {"messages": [{"message": "Internal error"}], "status": "failed"}
        })
    )
    result = await get_tool("create_asset").fn(name="X", product="4586")
    assert "error" in result
    assert result["status_code"] == 500


@respx.mock
async def test_403_returns_error_dict() -> None:
    respx.get(f"{BASE}/assets").mock(
        return_value=httpx.Response(403, json={
            "response_status": {"messages": [{"message": "Forbidden"}], "status": "failed"}
        })
    )
    result = await get_tool("list_assets").fn()
    assert "error" in result
    assert result["status_code"] == 403


# ---------------------------------------------------------------------------
# delete_asset
# ---------------------------------------------------------------------------

@respx.mock
async def test_delete_asset_url() -> None:
    route = respx.delete(f"{BASE}/assets/100").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    await get_tool("delete_asset").fn(asset_id="100")
    assert route.called
