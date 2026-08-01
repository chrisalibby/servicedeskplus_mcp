"""Tests for problem and change note/task/worklog tools."""

import httpx
import respx

from .conftest import BASE, decode_body, get_tool

# ---------------------------------------------------------------------------
# problems
# ---------------------------------------------------------------------------


@respx.mock
async def test_list_problem_notes_url() -> None:
    route = respx.get(f"{BASE}/problems/1/notes").mock(
        return_value=httpx.Response(200, json={"notes": []})
    )
    result = await get_tool("list_problem_notes").fn(problem_id="1")
    assert route.called
    assert result == {"notes": []}


@respx.mock
async def test_update_problem_note_payload_shape() -> None:
    route = respx.put(f"{BASE}/problems/1/notes/9").mock(
        return_value=httpx.Response(200, json={"note": {"id": "9", "description": "edited"}})
    )
    await get_tool("update_problem_note").fn(problem_id="1", note_id="9", note_text="edited")
    payload = decode_body(route.calls[0])
    assert payload["note"]["description"] == "edited"


@respx.mock
async def test_get_problem_note_url() -> None:
    route = respx.get(f"{BASE}/problems/1/notes/9").mock(
        return_value=httpx.Response(200, json={"note": {"id": "9"}})
    )
    result = await get_tool("get_problem_note").fn(problem_id="1", note_id="9")
    assert route.called
    assert result["note"]["id"] == "9"


@respx.mock
async def test_delete_problem_note_url() -> None:
    route = respx.delete(f"{BASE}/problems/1/notes/9").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    await get_tool("delete_problem_note").fn(problem_id="1", note_id="9")
    assert route.called


@respx.mock
async def test_delete_problem_url() -> None:
    route = respx.delete(f"{BASE}/problems/1").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    await get_tool("delete_problem").fn(problem_id="1")
    assert route.called


@respx.mock
async def test_list_problem_tasks_url() -> None:
    route = respx.get(f"{BASE}/problems/1/tasks").mock(
        return_value=httpx.Response(200, json={"tasks": []})
    )
    await get_tool("list_problem_tasks").fn(problem_id="1")
    assert route.called


@respx.mock
async def test_add_problem_task_payload_shape() -> None:
    route = respx.post(f"{BASE}/problems/1/tasks").mock(
        return_value=httpx.Response(200, json={"task": {"id": "1"}})
    )
    await get_tool("add_problem_task").fn(
        problem_id="1", title="Investigate root cause", assigned_to="jdoe"
    )
    payload = decode_body(route.calls[0])
    assert payload["task"]["title"] == "Investigate root cause"
    assert payload["task"]["owner"] == {"name": "jdoe"}


@respx.mock
async def test_list_problem_worklogs_url() -> None:
    route = respx.get(f"{BASE}/problems/1/worklogs").mock(
        return_value=httpx.Response(200, json={"worklogs": []})
    )
    await get_tool("list_problem_worklogs").fn(problem_id="1")
    assert route.called


@respx.mock
async def test_add_problem_worklog_payload_shape() -> None:
    route = respx.post(f"{BASE}/problems/1/worklogs").mock(
        return_value=httpx.Response(200, json={"worklog": {"id": "1"}})
    )
    await get_tool("add_problem_worklog").fn(
        problem_id="1", description="Root cause analysis",
        technician_email="jdoe@example.com", hours=1, minutes=15,
    )
    payload = decode_body(route.calls[0])
    assert payload["worklog"]["time_spent"] == {"hours": 1, "minutes": 15}
    assert payload["worklog"]["owner"] == {"email_id": "jdoe@example.com"}


# ---------------------------------------------------------------------------
# changes
# ---------------------------------------------------------------------------


@respx.mock
async def test_list_change_notes_url() -> None:
    route = respx.get(f"{BASE}/changes/1/notes").mock(
        return_value=httpx.Response(200, json={"notes": []})
    )
    result = await get_tool("list_change_notes").fn(change_id="1")
    assert route.called
    assert result == {"notes": []}


@respx.mock
async def test_update_change_note_payload_shape() -> None:
    route = respx.put(f"{BASE}/changes/1/notes/9").mock(
        return_value=httpx.Response(200, json={"note": {"id": "9", "description": "edited"}})
    )
    await get_tool("update_change_note").fn(change_id="1", note_id="9", note_text="edited")
    payload = decode_body(route.calls[0])
    assert payload["note"]["description"] == "edited"


@respx.mock
async def test_get_change_note_url() -> None:
    route = respx.get(f"{BASE}/changes/1/notes/9").mock(
        return_value=httpx.Response(200, json={"note": {"id": "9"}})
    )
    result = await get_tool("get_change_note").fn(change_id="1", note_id="9")
    assert route.called
    assert result["note"]["id"] == "9"


@respx.mock
async def test_delete_change_note_url() -> None:
    route = respx.delete(f"{BASE}/changes/1/notes/9").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    await get_tool("delete_change_note").fn(change_id="1", note_id="9")
    assert route.called


@respx.mock
async def test_delete_change_url() -> None:
    route = respx.delete(f"{BASE}/changes/1/move_to_trash").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    await get_tool("delete_change").fn(change_id="1")
    assert route.called


@respx.mock
async def test_restore_change_no_body() -> None:
    route = respx.put(f"{BASE}/changes/1/restore_from_trash").mock(
        return_value=httpx.Response(200, json={"change": {"id": "1"}})
    )
    await get_tool("restore_change").fn(change_id="1")
    assert route.called
    assert route.calls[0].request.content == b""


@respx.mock
async def test_copy_change_url() -> None:
    route = respx.put(f"{BASE}/changes/1/copy").mock(
        return_value=httpx.Response(200, json={"change": {"id": "2"}})
    )
    await get_tool("copy_change").fn(change_id="1")
    assert route.called


@respx.mock
async def test_add_change_task_payload_shape() -> None:
    route = respx.post(f"{BASE}/changes/1/tasks").mock(
        return_value=httpx.Response(200, json={"task": {"id": "1"}})
    )
    await get_tool("add_change_task").fn(
        change_id="1", title="Prepare rollback plan", assigned_to="jdoe"
    )
    payload = decode_body(route.calls[0])
    assert payload["task"]["title"] == "Prepare rollback plan"
    assert payload["task"]["owner"] == {"name": "jdoe"}


@respx.mock
async def test_list_change_worklogs_url() -> None:
    route = respx.get(f"{BASE}/changes/1/worklogs").mock(
        return_value=httpx.Response(200, json={"worklogs": []})
    )
    await get_tool("list_change_worklogs").fn(change_id="1")
    assert route.called


@respx.mock
async def test_add_change_worklog_payload_shape() -> None:
    route = respx.post(f"{BASE}/changes/1/worklogs").mock(
        return_value=httpx.Response(200, json={"worklog": {"id": "1"}})
    )
    await get_tool("add_change_worklog").fn(
        change_id="1", description="Executed change", technician_email="jdoe@example.com",
        hours=0, minutes=45,
    )
    payload = decode_body(route.calls[0])
    assert payload["worklog"]["time_spent"] == {"hours": 0, "minutes": 45}
    assert payload["worklog"]["owner"] == {"email_id": "jdoe@example.com"}


# ---------------------------------------------------------------------------
# problem tasks: get / update / delete
# ---------------------------------------------------------------------------

@respx.mock
async def test_get_problem_task_url() -> None:
    route = respx.get(f"{BASE}/problems/1/tasks/9").mock(
        return_value=httpx.Response(200, json={"task": {"id": "9"}})
    )
    result = await get_tool("get_problem_task").fn(problem_id="1", task_id="9")
    assert route.called
    assert result["task"]["id"] == "9"


@respx.mock
async def test_update_problem_task_payload_shape() -> None:
    route = respx.put(f"{BASE}/problems/1/tasks/9").mock(
        return_value=httpx.Response(200, json={"task": {"id": "9"}})
    )
    await get_tool("update_problem_task").fn(
        problem_id="1", task_id="9", title="updated", assigned_to="jdoe", status="Closed"
    )
    payload = decode_body(route.calls[0])
    assert payload["task"]["title"] == "updated"
    assert payload["task"]["owner"] == {"name": "jdoe"}
    assert payload["task"]["status"] == {"name": "Closed"}


@respx.mock
async def test_delete_problem_task_url() -> None:
    route = respx.delete(f"{BASE}/problems/1/tasks/9").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    await get_tool("delete_problem_task").fn(problem_id="1", task_id="9")
    assert route.called


# ---------------------------------------------------------------------------
# problem worklogs: update / delete
# ---------------------------------------------------------------------------

@respx.mock
async def test_update_problem_worklog_payload_shape() -> None:
    route = respx.put(f"{BASE}/problems/1/worklogs/5").mock(
        return_value=httpx.Response(200, json={"worklog": {"id": "5"}})
    )
    await get_tool("update_problem_worklog").fn(
        problem_id="1", worklog_id="5", description="edited", hours=1, minutes=0
    )
    payload = decode_body(route.calls[0])
    assert payload["worklog"]["description"] == "edited"
    assert payload["worklog"]["time_spent"] == {"hours": 1, "minutes": 0}


@respx.mock
async def test_delete_problem_worklog_url() -> None:
    route = respx.delete(f"{BASE}/problems/1/worklogs/5").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    await get_tool("delete_problem_worklog").fn(problem_id="1", worklog_id="5")
    assert route.called


# ---------------------------------------------------------------------------
# change tasks: get / update / delete
# ---------------------------------------------------------------------------

@respx.mock
async def test_get_change_task_url() -> None:
    route = respx.get(f"{BASE}/changes/1/tasks/9").mock(
        return_value=httpx.Response(200, json={"task": {"id": "9"}})
    )
    result = await get_tool("get_change_task").fn(change_id="1", task_id="9")
    assert route.called
    assert result["task"]["id"] == "9"


@respx.mock
async def test_update_change_task_payload_shape() -> None:
    route = respx.put(f"{BASE}/changes/1/tasks/9").mock(
        return_value=httpx.Response(200, json={"task": {"id": "9"}})
    )
    await get_tool("update_change_task").fn(
        change_id="1", task_id="9", title="updated", assigned_to="jdoe", status="Closed"
    )
    payload = decode_body(route.calls[0])
    assert payload["task"]["title"] == "updated"
    assert payload["task"]["owner"] == {"name": "jdoe"}
    assert payload["task"]["status"] == {"name": "Closed"}


@respx.mock
async def test_delete_change_task_url() -> None:
    route = respx.delete(f"{BASE}/changes/1/tasks/9").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    await get_tool("delete_change_task").fn(change_id="1", task_id="9")
    assert route.called


# ---------------------------------------------------------------------------
# change worklogs: update / delete
# ---------------------------------------------------------------------------

@respx.mock
async def test_update_change_worklog_payload_shape() -> None:
    route = respx.put(f"{BASE}/changes/1/worklogs/5").mock(
        return_value=httpx.Response(200, json={"worklog": {"id": "5"}})
    )
    await get_tool("update_change_worklog").fn(
        change_id="1", worklog_id="5", description="edited", hours=0, minutes=45
    )
    payload = decode_body(route.calls[0])
    assert payload["worklog"]["description"] == "edited"
    assert payload["worklog"]["time_spent"] == {"hours": 0, "minutes": 45}


@respx.mock
async def test_delete_change_worklog_url() -> None:
    route = respx.delete(f"{BASE}/changes/1/worklogs/5").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    await get_tool("delete_change_worklog").fn(change_id="1", worklog_id="5")
    assert route.called


# ---------------------------------------------------------------------------
# change approval levels
# ---------------------------------------------------------------------------

@respx.mock
async def test_list_change_approval_levels_url() -> None:
    route = respx.get(f"{BASE}/changes/1/approval_levels").mock(
        return_value=httpx.Response(200, json={"approval_levels": []})
    )
    await get_tool("list_change_approval_levels").fn(change_id="1")
    assert route.called
