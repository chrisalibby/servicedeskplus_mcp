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
        "merge_requests", "get_request_summary", "associate_problem", "dissociate_problem",
        "associate_change", "dissociate_change",
        "add_request_note", "list_request_notes", "update_request_note",
        "get_request_note", "delete_request_note", "add_request_worklog",
        "list_request_worklogs", "update_request_worklog", "delete_request_worklog",
        "get_request_resolution", "update_request_resolution",
        "list_request_tasks", "add_request_task",
        "get_request_task", "update_request_task", "delete_request_task",
        "list_request_attachments", "get_request_attachment_content", "add_request_attachment",
        "list_request_approval_levels", "add_request_approval_level", "list_request_approvals",
        "add_request_approver", "send_request_approval_notification",
        "approve_request", "reject_request",
        "list_problems", "get_problem", "create_problem", "update_problem",
        "close_problem", "delete_problem", "add_problem_note", "list_problem_notes",
        "get_problem_note", "delete_problem_note",
        "list_problem_tasks", "add_problem_task",
        "get_problem_task", "update_problem_task", "delete_problem_task",
        "list_problem_worklogs", "add_problem_worklog",
        "update_problem_worklog", "delete_problem_worklog",
        "list_changes", "get_change", "create_change", "update_change",
        "close_change", "delete_change", "restore_change", "copy_change",
        "add_change_note", "list_change_notes",
        "get_change_note", "delete_change_note",
        "list_change_tasks", "add_change_task",
        "get_change_task", "update_change_task", "delete_change_task",
        "list_change_worklogs", "add_change_worklog",
        "update_change_worklog", "delete_change_worklog",
        "list_pending_approvals", "approve_change", "reject_change",
        "list_change_approval_levels",
        "list_releases", "get_release", "create_release", "update_release", "close_release",
        "add_release_note", "list_release_notes", "update_release_note",
        "list_release_tasks", "add_release_task",
        "list_release_worklogs", "add_release_worklog",
        "list_projects", "get_project", "create_project", "update_project", "delete_project",
        "list_project_milestones", "add_project_milestone",
        "list_project_tasks", "add_project_task",
        "list_project_members", "add_project_member",
        "list_project_comments", "add_project_comment",
        "list_assets", "get_asset", "create_asset", "update_asset", "delete_asset",
        "list_workstations", "get_workstation",
        "list_configuration_items", "get_configuration_item",
        "create_configuration_item", "update_configuration_item", "delete_configuration_item",
        "list_ci_relationships", "add_ci_relationship",
        "search_solutions", "get_solution", "create_solution", "update_solution",
        "delete_solution", "add_solution_attachment",
        "list_solution_topics", "create_solution_topic",
        "list_requesters", "get_requester", "list_technicians", "get_technician",
        "list_groups", "list_sites", "list_categories", "list_subcategories",
        "list_priorities", "list_statuses", "list_urgencies", "list_departments",
        "list_announcements", "list_products", "get_product", "list_product_types",
        "list_closure_codes", "list_change_types",
        "list_contracts", "get_contract", "create_contract", "update_contract",
        "list_purchase_orders", "get_purchase_order",
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


@respx.mock
async def test_update_request_note_sends_description() -> None:
    route = respx.put("http://sdp.test.local:8080/api/v3/requests/7/notes/99").mock(
        return_value=httpx.Response(
            200, json={"note": {"id": "99", "description": "edited note"}}
        )
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    update_note = next(t for t in tools if t.name == "update_request_note")
    result = await update_note.fn(request_id="7", note_id="99", note_text="edited note")
    assert route.called
    body = route.calls[0].request.content.decode()
    payload = json.loads(parse_qs(body)["input_data"][0])
    assert payload["note"]["description"] == "edited note"
    assert result["note"]["description"] == "edited note"


@respx.mock
async def test_list_requests_category_filters() -> None:
    route = respx.get("http://sdp.test.local:8080/api/v3/requests").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    list_req = next(t for t in tools if t.name == "list_requests")
    await list_req.fn(category="Hardware", subcategory="Printer", item="Toner")
    assert route.called
    params = dict(route.calls[0].request.url.params)
    criteria = json.loads(params["input_data"])["list_info"]["search_criteria"]
    assert {"field": "category.name", "condition": "is", "value": "Hardware"} in criteria
    assert {"field": "subcategory.name", "condition": "is", "value": "Printer"} in criteria
    assert {"field": "item.name", "condition": "is", "value": "Toner"} in criteria


@respx.mock
async def test_assign_request_resolves_technician_email() -> None:
    respx.get("http://sdp.test.local:8080/api/v3/technicians").mock(
        return_value=httpx.Response(
            200,
            json={"technicians": [{"id": "42", "email_id": "jsmith@example.com"}]},
        )
    )
    route = respx.put("http://sdp.test.local:8080/api/v3/requests/7").mock(
        return_value=httpx.Response(200, json={"request": {"id": "7"}})
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    assign_req = next(t for t in tools if t.name == "assign_request")
    await assign_req.fn(request_id="7", technician="jsmith@example.com")
    assert route.called
    body = route.calls[0].request.content.decode()
    payload = json.loads(parse_qs(body)["input_data"][0])
    assert payload["request"]["technician"] == {"id": "42"}


@respx.mock
async def test_assign_request_uses_name_directly() -> None:
    route = respx.put("http://sdp.test.local:8080/api/v3/requests/7").mock(
        return_value=httpx.Response(200, json={"request": {"id": "7"}})
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    assign_req = next(t for t in tools if t.name == "assign_request")
    await assign_req.fn(request_id="7", technician="Jane Smith")
    assert route.called
    body = route.calls[0].request.content.decode()
    payload = json.loads(parse_qs(body)["input_data"][0])
    assert payload["request"]["technician"] == {"name": "Jane Smith"}


@respx.mock
async def test_close_request_rejects_long_closure_comments() -> None:
    route = respx.put("http://sdp.test.local:8080/api/v3/requests/7").mock(
        return_value=httpx.Response(200, json={"request": {"id": "7"}})
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    close_req = next(t for t in tools if t.name == "close_request")
    result = await close_req.fn(request_id="7", closure_comments="x" * 900)
    assert not route.called
    assert "error" in result
    assert "250" in result["error"]


@respx.mock
async def test_create_configuration_item_uses_module_scoped_path() -> None:
    route = respx.post("http://sdp.test.local:8080/api/v3/cmdb_itservice").mock(
        return_value=httpx.Response(
            200, json={"cmdb_itservice": {"id": "1", "name": "Phone System"}}
        )
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    create_ci = next(t for t in tools if t.name == "create_configuration_item")
    result = await create_ci.fn(module_type="cmdb_itservice", name="Phone System")
    assert route.called
    body = route.calls[0].request.content.decode()
    payload = json.loads(parse_qs(body)["input_data"][0])
    assert payload["cmdb_itservice"]["name"] == "Phone System"
    assert result["cmdb_itservice"]["id"] == "1"


@respx.mock
async def test_update_configuration_item_uses_module_scoped_path() -> None:
    route = respx.put("http://sdp.test.local:8080/api/v3/cmdb_itservice/1").mock(
        return_value=httpx.Response(
            200, json={"cmdb_itservice": {"id": "1", "description": "Updated"}}
        )
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    update_ci = next(t for t in tools if t.name == "update_configuration_item")
    result = await update_ci.fn(
        ci_id="1", module_type="cmdb_itservice", description="Updated"
    )
    assert route.called
    body = route.calls[0].request.content.decode()
    payload = json.loads(parse_qs(body)["input_data"][0])
    assert payload["cmdb_itservice"]["description"] == "Updated"
    assert result["cmdb_itservice"]["description"] == "Updated"


@respx.mock
async def test_list_ci_relationships_uses_ci_relationships_path() -> None:
    route = respx.get("http://sdp.test.local:8080/api/v3/cmdb/1/ci_relationships").mock(
        return_value=httpx.Response(200, json={"ci_relationships": []})
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    list_rel = next(t for t in tools if t.name == "list_ci_relationships")
    result = await list_rel.fn(ci_id="1")
    assert route.called
    assert result["ci_relationships"] == []


@respx.mock
async def test_get_product() -> None:
    route = respx.get("http://sdp.test.local:8080/api/v3/products/5").mock(
        return_value=httpx.Response(200, json={"product": {"id": "5", "name": "Laptop"}})
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    get_prod = next(t for t in tools if t.name == "get_product")
    result = await get_prod.fn(product_id="5")
    assert route.called
    assert result["product"]["id"] == "5"


@respx.mock
async def test_list_request_attachments() -> None:
    route = respx.get("http://sdp.test.local:8080/api/v3/requests/48120/attachments").mock(
        return_value=httpx.Response(
            200,
            json={
                "attachments": [
                    {"id": "226848", "name": "report.txt", "content_type": "text/plain",
                     "size": {"value": 8864, "display_value": "8.65KB"}}
                ]
            },
        )
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    list_att = next(t for t in tools if t.name == "list_request_attachments")
    result = await list_att.fn(request_id="48120")
    assert route.called
    assert result["attachments"][0]["id"] == "226848"


@respx.mock
async def test_get_request_attachment_content_returns_base64() -> None:
    route = respx.get(
        "http://sdp.test.local:8080/api/v3/requests/48120/attachments/226848/_download"
    ).mock(
        return_value=httpx.Response(
            200, content=b"hello world", headers={"content-type": "text/plain"}
        )
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    get_att = next(t for t in tools if t.name == "get_request_attachment_content")
    result = await get_att.fn(request_id="48120", attachment_id="226848")
    assert route.called
    assert result["size"] == 11
    assert result["content_type"] == "text/plain"
    import base64
    assert base64.b64decode(result["content_base64"]) == b"hello world"


@respx.mock
async def test_get_request_attachment_content_saves_to_path(tmp_path) -> None:
    dest = tmp_path / "attachment.txt"
    respx.get(
        "http://sdp.test.local:8080/api/v3/requests/48120/attachments/226848/_download"
    ).mock(
        return_value=httpx.Response(
            200, content=b"hello world", headers={"content-type": "text/plain"}
        )
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    get_att = next(t for t in tools if t.name == "get_request_attachment_content")
    result = await get_att.fn(
        request_id="48120", attachment_id="226848", save_to_path=str(dest)
    )
    assert result["saved_to"] == str(dest)
    assert "content_base64" not in result
    assert dest.read_bytes() == b"hello world"


@respx.mock
async def test_add_request_attachment(tmp_path) -> None:
    src = tmp_path / "upload.txt"
    src.write_bytes(b"hello upload")
    route = respx.put("http://sdp.test.local:8080/api/v3/requests/48120/upload").mock(
        return_value=httpx.Response(
            200,
            json={
                "attachment": {"id": "226850", "name": "upload.txt", "content_type": "text/plain"}
            },
        )
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    add_att = next(t for t in tools if t.name == "add_request_attachment")
    result = await add_att.fn(request_id="48120", file_path=str(src), description="probe")
    assert route.called
    sent = route.calls[0].request
    assert b'name="input_file"' in sent.content
    assert b"hello upload" in sent.content
    assert parse_qs(sent.url.query.decode())["description"] == ["probe"]
    assert result["attachment"]["id"] == "226850"


@respx.mock
async def test_delete_configuration_item_url() -> None:
    route = respx.delete("http://sdp.test.local:8080/api/v3/cmdb_itservice/50").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    delete_ci = next(t for t in tools if t.name == "delete_configuration_item")
    result = await delete_ci.fn(ci_id="50", module_type="cmdb_itservice")
    assert route.called
    assert result["response_status"]["status"] == "success"


@respx.mock
async def test_list_closure_codes_url() -> None:
    route = respx.get("http://sdp.test.local:8080/api/v3/closure_codes").mock(
        return_value=httpx.Response(200, json={"closure_codes": []})
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    list_cc = next(t for t in tools if t.name == "list_closure_codes")
    await list_cc.fn()
    assert route.called


@respx.mock
async def test_list_change_types_url() -> None:
    route = respx.get("http://sdp.test.local:8080/api/v3/change_types").mock(
        return_value=httpx.Response(200, json={"change_types": []})
    )
    tools = mcp._tool_manager.list_tools()  # type: ignore[attr-defined]
    list_ct = next(t for t in tools if t.name == "list_change_types")
    await list_ct.fn()
    assert route.called
