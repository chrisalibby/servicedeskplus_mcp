"""Comprehensive tests for service request (ticket) tools."""

import httpx
import pytest
import respx

from .conftest import BASE, decode_body, decode_get_params, get_tool

# ---------------------------------------------------------------------------
# list_requests
# ---------------------------------------------------------------------------

@respx.mock
async def test_list_requests_default_no_filters() -> None:
    route = respx.get(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )
    result = await get_tool("list_requests").fn()
    assert route.called
    params = decode_get_params(route.calls[0])
    assert params["list_info"]["start_index"] == 0
    assert params["list_info"]["row_count"] == 25
    assert "search_criteria" not in params["list_info"]
    assert result == {"requests": []}


@respx.mock
async def test_list_requests_page2() -> None:
    route = respx.get(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )
    await get_tool("list_requests").fn(page=2, page_size=25)
    params = decode_get_params(route.calls[0])
    assert params["list_info"]["start_index"] == 25


@respx.mock
async def test_list_requests_custom_page_size() -> None:
    route = respx.get(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )
    await get_tool("list_requests").fn(page=1, page_size=10)
    params = decode_get_params(route.calls[0])
    assert params["list_info"]["row_count"] == 10


@respx.mock
async def test_list_requests_status_filter() -> None:
    route = respx.get(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )
    await get_tool("list_requests").fn(status="Open")
    params = decode_get_params(route.calls[0])
    criteria = params["list_info"]["search_criteria"]
    assert len(criteria) == 1
    assert criteria[0] == {"field": "status.name", "condition": "is", "value": "Open"}


@respx.mock
async def test_list_requests_technician_filter() -> None:
    route = respx.get(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )
    await get_tool("list_requests").fn(technician="jdoe")
    params = decode_get_params(route.calls[0])
    criteria = params["list_info"]["search_criteria"]
    assert criteria[0]["field"] == "technician.name"
    assert criteria[0]["value"] == "jdoe"


@respx.mock
async def test_list_requests_both_filters() -> None:
    route = respx.get(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )
    await get_tool("list_requests").fn(status="Open", technician="jdoe")
    params = decode_get_params(route.calls[0])
    fields = [c["field"] for c in params["list_info"]["search_criteria"]]
    assert "status.name" in fields
    assert "technician.name" in fields


# ---------------------------------------------------------------------------
# get_request
# ---------------------------------------------------------------------------

@respx.mock
async def test_get_request_url() -> None:
    route = respx.get(f"{BASE}/requests/42").mock(
        return_value=httpx.Response(200, json={"request": {"id": "42"}})
    )
    result = await get_tool("get_request").fn(request_id="42")
    assert route.called
    assert result["request"]["id"] == "42"


# ---------------------------------------------------------------------------
# create_request
# ---------------------------------------------------------------------------

@respx.mock
async def test_create_request_subject_only() -> None:
    route = respx.post(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"request": {"id": "1"}})
    )
    await get_tool("create_request").fn(subject="Laptop broken")
    payload = decode_body(route.calls[0])
    assert payload["request"] == {"subject": "Laptop broken"}


@respx.mock
async def test_create_request_omits_empty_optionals() -> None:
    route = respx.post(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"request": {"id": "1"}})
    )
    await get_tool("create_request").fn(
        subject="Test", description="", priority="", technician=""
    )
    payload = decode_body(route.calls[0])
    req = payload["request"]
    assert "description" not in req
    assert "priority" not in req
    assert "technician" not in req


@respx.mock
async def test_create_request_all_fields() -> None:
    route = respx.post(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"request": {"id": "2"}})
    )
    await get_tool("create_request").fn(
        subject="VPN down",
        description="Cannot connect",
        requester_name="jsmith",
        category="Network",
        priority="High",
        urgency="High",
        site="HQ",
        group="Network Team",
        technician="jdoe",
    )
    payload = decode_body(route.calls[0])
    req = payload["request"]
    assert req["subject"] == "VPN down"
    assert req["requester"] == {"name": "jsmith"}
    assert req["category"] == {"name": "Network"}
    assert req["priority"] == {"name": "High"}
    assert req["urgency"] == {"name": "High"}
    assert req["site"] == {"name": "HQ"}
    assert req["group"] == {"name": "Network Team"}
    assert req["technician"] == {"name": "jdoe"}


# ---------------------------------------------------------------------------
# update_request
# ---------------------------------------------------------------------------

@respx.mock
async def test_update_request_partial_fields() -> None:
    route = respx.put(f"{BASE}/requests/10").mock(
        return_value=httpx.Response(200, json={"request": {"id": "10"}})
    )
    await get_tool("update_request").fn(request_id="10", status="In Progress")
    payload = decode_body(route.calls[0])
    assert payload["request"] == {"status": {"name": "In Progress"}}


@respx.mock
async def test_update_request_technician_and_group() -> None:
    route = respx.put(f"{BASE}/requests/10").mock(
        return_value=httpx.Response(200, json={"request": {"id": "10"}})
    )
    await get_tool("update_request").fn(
        request_id="10", technician="jdoe", group="Help Desk"
    )
    payload = decode_body(route.calls[0])
    assert payload["request"]["technician"] == {"name": "jdoe"}
    assert payload["request"]["group"] == {"name": "Help Desk"}


@respx.mock
async def test_update_request_all_empty_sends_empty_dict() -> None:
    route = respx.put(f"{BASE}/requests/10").mock(
        return_value=httpx.Response(200, json={"request": {"id": "10"}})
    )
    await get_tool("update_request").fn(request_id="10")
    payload = decode_body(route.calls[0])
    assert payload["request"] == {}


# ---------------------------------------------------------------------------
# close_request
# ---------------------------------------------------------------------------

@respx.mock
async def test_close_request_no_closure_info_by_default() -> None:
    route = respx.put(f"{BASE}/requests/7").mock(
        return_value=httpx.Response(200, json={"request": {"id": "7"}})
    )
    await get_tool("close_request").fn(request_id="7")
    payload = decode_body(route.calls[0])
    req = payload["request"]
    assert req["status"] == {"name": "Closed"}
    assert "closure_info" not in req


@respx.mock
async def test_close_request_with_closure_code() -> None:
    route = respx.put(f"{BASE}/requests/7").mock(
        return_value=httpx.Response(200, json={"request": {"id": "7"}})
    )
    await get_tool("close_request").fn(
        request_id="7",
        closure_code="Fixed",
        closure_comments="Replaced the cable",
    )
    payload = decode_body(route.calls[0])
    ci = payload["request"]["closure_info"]
    assert ci["closure_code"] == {"name": "Fixed"}
    assert ci["closure_comments"] == "Replaced the cable"


@respx.mock
async def test_close_request_comments_only_includes_closure_info() -> None:
    route = respx.put(f"{BASE}/requests/7").mock(
        return_value=httpx.Response(200, json={"request": {"id": "7"}})
    )
    await get_tool("close_request").fn(
        request_id="7", closure_comments="Done"
    )
    payload = decode_body(route.calls[0])
    assert "closure_info" in payload["request"]
    assert payload["request"]["closure_info"]["closure_comments"] == "Done"


# ---------------------------------------------------------------------------
# delete_request
# ---------------------------------------------------------------------------

@respx.mock
async def test_delete_request_moves_to_trash_only() -> None:
    route = respx.delete(f"{BASE}/requests/99/move_to_trash").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    result = await get_tool("delete_request").fn(request_id="99")
    assert route.called
    assert result["response_status"]["status"] == "success"


# ---------------------------------------------------------------------------
# assign_request / pickup_request
# ---------------------------------------------------------------------------

@respx.mock
async def test_assign_request_technician_only() -> None:
    route = respx.put(f"{BASE}/requests/5").mock(
        return_value=httpx.Response(200, json={"request": {"id": "5"}})
    )
    await get_tool("assign_request").fn(request_id="5", technician="jdoe")
    payload = decode_body(route.calls[0])
    assert payload["request"]["technician"] == {"name": "jdoe"}
    assert "group" not in payload["request"]


@respx.mock
async def test_assign_request_with_group() -> None:
    route = respx.put(f"{BASE}/requests/5").mock(
        return_value=httpx.Response(200, json={"request": {"id": "5"}})
    )
    await get_tool("assign_request").fn(
        request_id="5", technician="jdoe", group="Help Desk"
    )
    payload = decode_body(route.calls[0])
    assert payload["request"]["group"] == {"name": "Help Desk"}


@respx.mock
async def test_pickup_request_url_and_method() -> None:
    route = respx.put(f"{BASE}/requests/3/pickup").mock(
        return_value=httpx.Response(200, json={"request": {"id": "3"}})
    )
    await get_tool("pickup_request").fn(request_id="3")
    assert route.called


# ---------------------------------------------------------------------------
# notes
# ---------------------------------------------------------------------------

@respx.mock
async def test_add_request_note_private_by_default() -> None:
    route = respx.post(f"{BASE}/requests/8/notes").mock(
        return_value=httpx.Response(200, json={"note": {"id": "1"}})
    )
    await get_tool("add_request_note").fn(request_id="8", note_text="Investigating")
    payload = decode_body(route.calls[0])
    assert payload["note"]["description"] == "Investigating"
    assert payload["note"]["show_to_requester"] is False


@respx.mock
async def test_add_request_note_public() -> None:
    route = respx.post(f"{BASE}/requests/8/notes").mock(
        return_value=httpx.Response(200, json={"note": {"id": "2"}})
    )
    await get_tool("add_request_note").fn(
        request_id="8", note_text="We're on it", is_public=True
    )
    payload = decode_body(route.calls[0])
    assert payload["note"]["show_to_requester"] is True


@respx.mock
async def test_list_request_notes_url() -> None:
    route = respx.get(f"{BASE}/requests/8/notes").mock(
        return_value=httpx.Response(200, json={"notes": []})
    )
    await get_tool("list_request_notes").fn(request_id="8")
    assert route.called


# ---------------------------------------------------------------------------
# worklogs
# ---------------------------------------------------------------------------

@respx.mock
async def test_add_worklog_hours_to_minutes_conversion() -> None:
    route = respx.post(f"{BASE}/requests/8/worklogs").mock(
        return_value=httpx.Response(200, json={"worklog": {"id": "1"}})
    )
    await get_tool("add_request_worklog").fn(
        request_id="8", description="Fixed switch", hours=1.5
    )
    payload = decode_body(route.calls[0])
    assert payload["worklog"]["time_spent"] == 90
    assert isinstance(payload["worklog"]["time_spent"], int)


@respx.mock
async def test_add_worklog_with_technician() -> None:
    route = respx.post(f"{BASE}/requests/8/worklogs").mock(
        return_value=httpx.Response(200, json={"worklog": {"id": "2"}})
    )
    await get_tool("add_request_worklog").fn(
        request_id="8", description="Work done", hours=0.5, technician="jdoe"
    )
    payload = decode_body(route.calls[0])
    assert payload["worklog"]["technician"] == {"name": "jdoe"}


@respx.mock
async def test_add_worklog_without_technician_omits_key() -> None:
    route = respx.post(f"{BASE}/requests/8/worklogs").mock(
        return_value=httpx.Response(200, json={"worklog": {"id": "3"}})
    )
    await get_tool("add_request_worklog").fn(
        request_id="8", description="Work done"
    )
    payload = decode_body(route.calls[0])
    assert "technician" not in payload["worklog"]


@respx.mock
async def test_list_request_worklogs_url() -> None:
    route = respx.get(f"{BASE}/requests/8/worklogs").mock(
        return_value=httpx.Response(200, json={"worklogs": []})
    )
    await get_tool("list_request_worklogs").fn(request_id="8")
    assert route.called


# ---------------------------------------------------------------------------
# resolution
# ---------------------------------------------------------------------------

@respx.mock
async def test_get_request_resolution_url() -> None:
    route = respx.get(f"{BASE}/requests/8/resolutions").mock(
        return_value=httpx.Response(200, json={"resolution": {"content": "Fixed"}})
    )
    await get_tool("get_request_resolution").fn(request_id="8")
    assert route.called


@respx.mock
async def test_update_request_resolution_payload() -> None:
    route = respx.put(f"{BASE}/requests/8/resolutions").mock(
        return_value=httpx.Response(200, json={"resolution": {"content": "Done"}})
    )
    await get_tool("update_request_resolution").fn(
        request_id="8", resolution_content="Replaced the NIC"
    )
    payload = decode_body(route.calls[0])
    assert payload["resolution"]["content"] == "Replaced the NIC"


# ---------------------------------------------------------------------------
# tasks
# ---------------------------------------------------------------------------

@respx.mock
async def test_list_request_tasks_url() -> None:
    route = respx.get(f"{BASE}/requests/8/tasks").mock(
        return_value=httpx.Response(200, json={"tasks": []})
    )
    await get_tool("list_request_tasks").fn(request_id="8")
    assert route.called


@respx.mock
async def test_add_request_task_minimal() -> None:
    route = respx.post(f"{BASE}/requests/8/tasks").mock(
        return_value=httpx.Response(200, json={"task": {"id": "1"}})
    )
    await get_tool("add_request_task").fn(request_id="8", title="Check cable")
    payload = decode_body(route.calls[0])
    assert payload["task"]["title"] == "Check cable"
    assert "description" not in payload["task"]
    assert "owner" not in payload["task"]


@respx.mock
async def test_add_request_task_with_assignee() -> None:
    route = respx.post(f"{BASE}/requests/8/tasks").mock(
        return_value=httpx.Response(200, json={"task": {"id": "2"}})
    )
    await get_tool("add_request_task").fn(
        request_id="8",
        title="Replace hardware",
        description="Swap out the RAM",
        assigned_to="jdoe",
    )
    payload = decode_body(route.calls[0])
    assert payload["task"]["description"] == "Swap out the RAM"
    assert payload["task"]["owner"] == {"name": "jdoe"}


# ---------------------------------------------------------------------------
# error propagation
# ---------------------------------------------------------------------------

@respx.mock
async def test_404_raises_through_get_request() -> None:
    respx.get(f"{BASE}/requests/999").mock(
        return_value=httpx.Response(404, json={"message": "Not found"})
    )
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await get_tool("get_request").fn(request_id="999")
    assert exc_info.value.response.status_code == 404


@respx.mock
async def test_500_raises_through_create_request() -> None:
    respx.post(f"{BASE}/requests").mock(
        return_value=httpx.Response(500, json={"message": "Internal error"})
    )
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await get_tool("create_request").fn(subject="Test")
    assert exc_info.value.response.status_code == 500


@respx.mock
async def test_401_raises_through_list_requests() -> None:
    respx.get(f"{BASE}/requests").mock(
        return_value=httpx.Response(401, json={"message": "Unauthorized"})
    )
    with pytest.raises(httpx.HTTPStatusError):
        await get_tool("list_requests").fn()
