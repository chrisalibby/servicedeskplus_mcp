"""Smoke tests for MCP tool registration and basic round-trips."""

import json
from urllib.parse import parse_qs

import httpx
import respx

from servicedeskplus_mcp.server import mcp


def test_tool_count() -> None:
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    assert len(tools) >= 40, f"Expected at least 40 tools, got {len(tools)}"


def test_expected_tools_registered() -> None:
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    names = {t.name for t in tools}
    required = {
        "list_requests", "get_request", "create_request", "update_request",
        "close_request", "delete_request", "assign_request", "pickup_request",
        "add_request_note", "list_request_notes", "add_request_worklog",
        "list_request_worklogs", "get_request_resolution", "update_request_resolution",
        "list_request_tasks", "add_request_task",
        "list_problems", "get_problem", "create_problem", "update_problem",
        "close_problem", "add_problem_note",
        "list_changes", "get_change", "create_change", "update_change",
        "close_change", "add_change_note", "list_change_tasks",
        "list_pending_approvals", "approve_change", "reject_change",
        "list_assets", "get_asset", "create_asset", "update_asset",
        "list_workstations", "get_workstation",
        "list_configuration_items", "get_configuration_item",
        "create_configuration_item", "update_configuration_item",
        "list_ci_relationships", "add_ci_relationship",
        "search_solutions", "get_solution", "create_solution", "list_solution_topics",
        "list_requesters", "get_requester", "list_technicians", "get_technician",
        "list_groups", "list_sites", "list_categories", "list_subcategories",
        "list_priorities", "list_statuses", "list_urgencies", "list_departments",
        "list_announcements", "list_products", "list_product_types",
        "list_contracts", "get_contract", "list_purchase_orders", "get_purchase_order",
    }
    missing = required - names
    assert not missing, f"Missing tools: {missing}"


@respx.mock
async def test_list_requests_calls_api() -> None:
    route = respx.get("http://sdp.test.local:8080/api/v3/requests").mock(
        return_value=httpx.Response(200, json={"requests": [{"id": "1", "subject": "Test"}]})
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    list_req = next(t for t in tools if t.name == "list_requests")
    result = await list_req.fn()
    assert route.called
    assert result["requests"][0]["id"] == "1"


@respx.mock
async def test_create_request_sends_subject() -> None:
    route = respx.post("http://sdp.test.local:8080/api/v3/requests").mock(
        return_value=httpx.Response(
            200, json={"request": {"id": "99", "subject": "Printer broken"}}
        )
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    create_req = next(t for t in tools if t.name == "create_request")
    result = await create_req.fn(subject="Printer broken", priority="High")
    assert route.called
    body = route.calls[0].request.content.decode()
    payload = json.loads(parse_qs(body)["input_data"][0])
    assert payload["request"]["subject"] == "Printer broken"
    assert payload["request"]["priority"]["name"] == "High"
    assert result["request"]["id"] == "99"


@respx.mock
async def test_close_request_sets_status() -> None:
    route = respx.put("http://sdp.test.local:8080/api/v3/requests/7").mock(
        return_value=httpx.Response(
            200, json={"request": {"id": "7", "status": {"name": "Closed"}}}
        )
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    close_req = next(t for t in tools if t.name == "close_request")
    result = await close_req.fn(request_id="7")
    assert route.called
    body = route.calls[0].request.content.decode()
    payload = json.loads(parse_qs(body)["input_data"][0])
    assert payload["request"]["status"]["name"] == "Closed"
    assert result["request"]["status"]["name"] == "Closed"
