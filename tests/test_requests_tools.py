"""Comprehensive tests for service request (ticket) tools."""

import httpx
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


@respx.mock
async def test_list_requests_opened_after() -> None:
    route = respx.get(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )
    await get_tool("list_requests").fn(opened_after="2026-06-01")
    params = decode_get_params(route.calls[0])
    criteria = params["list_info"]["search_criteria"]
    assert len(criteria) == 1
    assert criteria[0]["field"] == "created_time"
    assert criteria[0]["condition"] == "gt"
    assert criteria[0]["value"] == "1780272000000"  # 2026-06-01 UTC midnight


@respx.mock
async def test_list_requests_opened_before() -> None:
    route = respx.get(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )
    await get_tool("list_requests").fn(opened_before="2026-07-01")
    params = decode_get_params(route.calls[0])
    criteria = params["list_info"]["search_criteria"]
    assert criteria[0]["field"] == "created_time"
    assert criteria[0]["condition"] == "lt"


@respx.mock
async def test_list_requests_subject_search() -> None:
    route = respx.get(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )
    await get_tool("list_requests").fn(search="VPN")
    params = decode_get_params(route.calls[0])
    criteria = params["list_info"]["search_criteria"]
    assert criteria[0] == {"field": "subject", "condition": "contains", "value": "VPN"}


@respx.mock
async def test_list_requests_sort_params() -> None:
    route = respx.get(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )
    await get_tool("list_requests").fn(sort_field="created_time", sort_order="desc")
    params = decode_get_params(route.calls[0])
    assert params["list_info"]["sort_field"] == "created_time"
    assert params["list_info"]["sort_order"] == "desc"


@respx.mock
async def test_list_requests_due_before() -> None:
    route = respx.get(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"requests": []})
    )
    await get_tool("list_requests").fn(due_before="2026-07-01")
    params = decode_get_params(route.calls[0])
    criteria = params["list_info"]["search_criteria"]
    assert criteria[0]["field"] == "due_by_time"
    assert criteria[0]["condition"] == "lt"


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


@respx.mock
async def test_get_request_normalizes_prefixed_id() -> None:
    route = respx.get(f"{BASE}/requests/42").mock(
        return_value=httpx.Response(200, json={"request": {"id": "42"}})
    )
    await get_tool("get_request").fn(request_id="RE-42")
    assert route.called


@respx.mock
async def test_get_request_normalizes_hash_prefix() -> None:
    route = respx.get(f"{BASE}/requests/42").mock(
        return_value=httpx.Response(200, json={"request": {"id": "42"}})
    )
    await get_tool("get_request").fn(request_id="#42")
    assert route.called


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
    respx.get(f"{BASE}/urgencies").mock(
        return_value=httpx.Response(200, json={"urgencies": [{"id": "3", "name": "High"}]})
    )
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
    assert req["urgency"] == {"id": "3"}
    assert req["site"] == {"name": "HQ"}
    assert req["group"] == {"name": "Network Team"}
    assert req["technician"] == {"name": "jdoe"}


@respx.mock
async def test_create_request_urgency_numeric_id_skips_lookup() -> None:
    route = respx.post(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"request": {"id": "3"}})
    )
    await get_tool("create_request").fn(subject="Test", urgency="4")
    payload = decode_body(route.calls[0])
    assert payload["request"]["urgency"] == {"id": "4"}


@respx.mock
async def test_create_request_unresolvable_urgency_returns_error() -> None:
    respx.get(f"{BASE}/urgencies").mock(
        return_value=httpx.Response(200, json={"urgencies": [{"id": "1", "name": "Low"}]})
    )
    post_route = respx.post(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"request": {"id": "4"}})
    )
    result = await get_tool("create_request").fn(subject="Test", urgency="Bogus")
    assert "error" in result
    assert not post_route.called


@respx.mock
async def test_create_request_strips_cdata() -> None:
    route = respx.post(f"{BASE}/requests").mock(
        return_value=httpx.Response(200, json={"request": {"id": "5"}})
    )
    await get_tool("create_request").fn(
        subject="Test", description="<![CDATA[<b>bold</b>]]>"
    )
    payload = decode_body(route.calls[0])
    assert payload["request"]["description"] == "<b>bold</b>"


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
async def test_add_request_note_indeterminate_verify_found() -> None:
    respx.post(f"{BASE}/requests/8/notes").mock(
        side_effect=httpx.ReadTimeout("timed out")
    )
    respx.get(f"{BASE}/requests/8/notes").mock(
        return_value=httpx.Response(200, json={
            "notes": [{"id": "1", "description": "Investigating the outage"}]
        })
    )
    result = await get_tool("add_request_note").fn(
        request_id="8", note_text="Investigating the outage"
    )
    assert result["indeterminate"] is True
    assert result["posted"] is True


@respx.mock
async def test_add_request_note_indeterminate_verify_not_found() -> None:
    respx.post(f"{BASE}/requests/8/notes").mock(
        side_effect=httpx.ReadTimeout("timed out")
    )
    respx.get(f"{BASE}/requests/8/notes").mock(
        return_value=httpx.Response(200, json={"notes": []})
    )
    result = await get_tool("add_request_note").fn(request_id="8", note_text="Lost note")
    assert result["indeterminate"] is True
    assert result["posted"] is False


@respx.mock
async def test_add_request_note_indeterminate_verify_fails() -> None:
    respx.post(f"{BASE}/requests/8/notes").mock(
        side_effect=httpx.ReadTimeout("timed out")
    )
    respx.get(f"{BASE}/requests/8/notes").mock(
        side_effect=httpx.ReadTimeout("timed out")
    )
    result = await get_tool("add_request_note").fn(request_id="8", note_text="Unknown")
    assert result["indeterminate"] is True
    assert result["posted"] == "unknown"


@respx.mock
async def test_add_request_note_strips_cdata() -> None:
    route = respx.post(f"{BASE}/requests/8/notes").mock(
        return_value=httpx.Response(200, json={"note": {"id": "3"}})
    )
    await get_tool("add_request_note").fn(
        request_id="8", note_text="<![CDATA[<p>hello</p>]]>"
    )
    payload = decode_body(route.calls[0])
    assert payload["note"]["description"] == "<p>hello</p>"


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
async def test_add_worklog_payload_shape() -> None:
    route = respx.post(f"{BASE}/requests/8/worklogs").mock(
        return_value=httpx.Response(200, json={"worklog": {"id": "1"}})
    )
    await get_tool("add_request_worklog").fn(
        request_id="8", description="Fixed switch",
        technician_email="jdoe@example.com", hours=1, minutes=30,
    )
    payload = decode_body(route.calls[0])
    assert payload["worklog"]["time_spent"] == {"hours": 1, "minutes": 30}
    assert payload["worklog"]["owner"] == {"email_id": "jdoe@example.com"}


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
# error handling — errors return readable dicts, not exceptions
# ---------------------------------------------------------------------------

@respx.mock
async def test_404_returns_error_dict() -> None:
    respx.get(f"{BASE}/requests/999").mock(
        return_value=httpx.Response(404, json={
            "response_status": {"messages": [{"message": "Request not found"}], "status": "failed"}
        })
    )
    result = await get_tool("get_request").fn(request_id="999")
    assert "error" in result
    assert result["status_code"] == 404


@respx.mock
async def test_400_surfaces_sdp_message() -> None:
    respx.post(f"{BASE}/requests").mock(
        return_value=httpx.Response(400, json={
            "response_status": {
                "messages": [{"message": "Please fill the mandatory fields"}],
                "status": "failed",
            }
        })
    )
    result = await get_tool("create_request").fn(subject="Test")
    assert "error" in result
    assert "mandatory" in result["error"]


@respx.mock
async def test_401_returns_error_dict() -> None:
    respx.get(f"{BASE}/requests").mock(
        return_value=httpx.Response(401, json={
            "response_status": {"messages": [{"message": "Invalid API key"}], "status": "failed"}
        })
    )
    result = await get_tool("list_requests").fn()
    assert "error" in result
    assert result["status_code"] == 401
