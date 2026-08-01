"""Tests for contract write-support tools."""

import httpx
import respx

from .conftest import BASE, decode_body, get_tool


@respx.mock
async def test_create_contract_payload_shape() -> None:
    route = respx.post(f"{BASE}/contracts").mock(
        return_value=httpx.Response(200, json={"contract": {"id": "1"}})
    )
    await get_tool("create_contract").fn(
        name="Visio Annual Seat",
        custom_contract_id="TEST-0001",
        contract_type="Software",
        vendor_id="6308",
        from_date="2026-07-20",
        to_date="2027-07-20",
        total_price="3060.00",
    )
    payload = decode_body(route.calls[0])
    assert payload["contract"]["name"] == "Visio Annual Seat"
    assert payload["contract"]["custom_contract_id"] == "TEST-0001"
    assert payload["contract"]["type"] == {"name": "Software"}
    assert payload["contract"]["vendor"] == {"id": "6308"}
    assert payload["contract"]["total_price"] == "3060.00"
    assert "from_date" in payload["contract"]
    assert "to_date" in payload["contract"]


@respx.mock
async def test_update_contract_payload_shape() -> None:
    route = respx.put(f"{BASE}/contracts/1").mock(
        return_value=httpx.Response(200, json={"contract": {"id": "1"}})
    )
    await get_tool("update_contract").fn(contract_id="1", total_price="500.00")
    payload = decode_body(route.calls[0])
    assert payload["contract"] == {"total_price": "500.00"}


@respx.mock
async def test_create_purchase_order_payload_shape() -> None:
    route = respx.post(f"{BASE}/purchase_orders").mock(
        return_value=httpx.Response(201, json={"purchase_order": {"id": "21901"}})
    )
    await get_tool("create_purchase_order").fn(
        name="MCP TEST PO",
        custom_po_id="MCPTEST-0001",
        vendor="3901",
        requested_by="17702",
        items=[{"product": "12304", "quantity": "1.00", "price": "1.00"}],
    )
    payload = decode_body(route.calls[0])
    po = payload["purchase_order"]
    assert po["name"] == "MCP TEST PO"
    assert po["custom_po_id"] == "MCPTEST-0001"
    assert po["vendor"] == {"id": "3901"}
    assert po["requested_by"] == {"id": "17702"}
    assert po["items"] == [
        {
            "product": {"id": "12304"},
            "ordered_quantity": "1.00",
            "price": "1.00",
            "category": {"id": "1"},
        }
    ]


@respx.mock
async def test_create_purchase_order_name_requested_by() -> None:
    route = respx.post(f"{BASE}/purchase_orders").mock(
        return_value=httpx.Response(201, json={"purchase_order": {"id": "21902"}})
    )
    await get_tool("create_purchase_order").fn(
        name="MCP TEST PO 2",
        custom_po_id="MCPTEST-0002",
        vendor="3901",
        requested_by="Chris Libby",
        items=[{"product": "12304", "quantity": "1.00", "price": "1.00", "category": "1"}],
    )
    payload = decode_body(route.calls[0])
    assert payload["purchase_order"]["requested_by"] == {"name": "Chris Libby"}


@respx.mock
async def test_update_purchase_order_payload_shape() -> None:
    route = respx.put(f"{BASE}/purchase_orders/21901").mock(
        return_value=httpx.Response(200, json={"purchase_order": {"id": "21901"}})
    )
    await get_tool("update_purchase_order").fn(purchase_order_id="21901", name="Renamed PO")
    payload = decode_body(route.calls[0])
    assert payload["purchase_order"] == {"name": "Renamed PO"}
