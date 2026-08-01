"""Tests for release tools."""

import httpx
import respx

from .conftest import BASE, decode_body, get_tool


@respx.mock
async def test_list_releases_url() -> None:
    route = respx.get(f"{BASE}/releases").mock(
        return_value=httpx.Response(200, json={"releases": []})
    )
    result = await get_tool("list_releases").fn()
    assert route.called
    assert result == {"releases": []}


@respx.mock
async def test_get_release_url() -> None:
    route = respx.get(f"{BASE}/releases/1").mock(
        return_value=httpx.Response(200, json={"release": {"id": "1"}})
    )
    await get_tool("get_release").fn(release_id="1")
    assert route.called


@respx.mock
async def test_create_release_payload_shape() -> None:
    route = respx.post(f"{BASE}/releases").mock(
        return_value=httpx.Response(200, json={"release": {"id": "1"}})
    )
    await get_tool("create_release").fn(title="MCP TEST RELEASE")
    payload = decode_body(route.calls[0])
    assert payload["release"] == {"title": "MCP TEST RELEASE"}


@respx.mock
async def test_create_release_full_payload_shape() -> None:
    route = respx.post(f"{BASE}/releases").mock(
        return_value=httpx.Response(200, json={"release": {"id": "1"}})
    )
    await get_tool("create_release").fn(
        title="Release", description="<p>desc</p>", release_type="Major", priority="High",
        scheduled_start="2026-08-01T00:00:00Z", scheduled_end="2026-08-02T00:00:00Z",
    )
    payload = decode_body(route.calls[0])
    assert payload["release"]["release_type"] == {"name": "Major"}
    assert payload["release"]["priority"] == {"name": "High"}
    assert payload["release"]["scheduled_start_time"] == {"value": "2026-08-01T00:00:00Z"}
    assert payload["release"]["scheduled_end_time"] == {"value": "2026-08-02T00:00:00Z"}


@respx.mock
async def test_update_release_payload_shape() -> None:
    route = respx.put(f"{BASE}/releases/1").mock(
        return_value=httpx.Response(200, json={"release": {"id": "1"}})
    )
    await get_tool("update_release").fn(release_id="1", title="Updated", priority="Low")
    payload = decode_body(route.calls[0])
    assert payload["release"]["title"] == "Updated"
    assert payload["release"]["priority"] == {"name": "Low"}


@respx.mock
async def test_close_release_payload_shape() -> None:
    route = respx.put(f"{BASE}/releases/1/_close").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    await get_tool("close_release").fn(release_id="1", comment="done")
    payload = decode_body(route.calls[0])
    assert payload == {"status": "completed", "comment": "done"}


@respx.mock
async def test_add_release_note_payload_shape() -> None:
    route = respx.post(f"{BASE}/releases/1/notes").mock(
        return_value=httpx.Response(200, json={"note": {"id": "1"}})
    )
    await get_tool("add_release_note").fn(release_id="1", note_text="a note")
    payload = decode_body(route.calls[0])
    assert payload["note"]["description"] == "a note"


@respx.mock
async def test_list_release_notes_url() -> None:
    route = respx.get(f"{BASE}/releases/1/notes").mock(
        return_value=httpx.Response(200, json={"notes": []})
    )
    result = await get_tool("list_release_notes").fn(release_id="1")
    assert route.called
    assert result == {"notes": []}


@respx.mock
async def test_update_release_note_payload_shape() -> None:
    route = respx.put(f"{BASE}/releases/1/notes/9").mock(
        return_value=httpx.Response(200, json={"note": {"id": "9", "description": "edited"}})
    )
    await get_tool("update_release_note").fn(release_id="1", note_id="9", note_text="edited")
    payload = decode_body(route.calls[0])
    assert payload["note"]["description"] == "edited"


@respx.mock
async def test_list_release_tasks_url() -> None:
    route = respx.get(f"{BASE}/releases/1/tasks").mock(
        return_value=httpx.Response(200, json={"tasks": []})
    )
    await get_tool("list_release_tasks").fn(release_id="1")
    assert route.called


@respx.mock
async def test_add_release_task_payload_shape() -> None:
    route = respx.post(f"{BASE}/releases/1/tasks").mock(
        return_value=httpx.Response(200, json={"task": {"id": "1"}})
    )
    await get_tool("add_release_task").fn(release_id="1", title="Prep rollout", assigned_to="jdoe")
    payload = decode_body(route.calls[0])
    assert payload["task"]["title"] == "Prep rollout"
    assert payload["task"]["stage"] == {"id": "2"}
    assert payload["task"]["owner"] == {"name": "jdoe"}


@respx.mock
async def test_list_release_worklogs_url() -> None:
    route = respx.get(f"{BASE}/releases/1/worklogs").mock(
        return_value=httpx.Response(200, json={"worklogs": []})
    )
    await get_tool("list_release_worklogs").fn(release_id="1")
    assert route.called


@respx.mock
async def test_add_release_worklog_payload_shape() -> None:
    route = respx.post(f"{BASE}/releases/1/worklogs").mock(
        return_value=httpx.Response(200, json={"worklog": {"id": "1"}})
    )
    await get_tool("add_release_worklog").fn(
        release_id="1", description="Rolled out change", technician_email="jdoe@example.com",
        hours=2, minutes=30,
    )
    payload = decode_body(route.calls[0])
    assert payload["worklog"]["time_spent"] == {"hours": 2, "minutes": 30}
    assert payload["worklog"]["owner"] == {"email_id": "jdoe@example.com"}
