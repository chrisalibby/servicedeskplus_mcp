"""Tests for project tools."""

import httpx
import respx

from .conftest import BASE, decode_body, get_tool


@respx.mock
async def test_list_projects_url() -> None:
    route = respx.get(f"{BASE}/projects").mock(
        return_value=httpx.Response(200, json={"projects": []})
    )
    result = await get_tool("list_projects").fn()
    assert route.called
    assert result == {"projects": []}


@respx.mock
async def test_get_project_url() -> None:
    route = respx.get(f"{BASE}/projects/1").mock(
        return_value=httpx.Response(200, json={"project": {"id": "1"}})
    )
    await get_tool("get_project").fn(project_id="1")
    assert route.called


@respx.mock
async def test_create_project_payload_shape() -> None:
    route = respx.post(f"{BASE}/projects").mock(
        return_value=httpx.Response(200, json={"project": {"id": "1"}})
    )
    await get_tool("create_project").fn(title="MCP TEST PROJECT")
    payload = decode_body(route.calls[0])
    assert payload["project"] == {"title": "MCP TEST PROJECT"}


@respx.mock
async def test_create_project_full_payload_shape() -> None:
    route = respx.post(f"{BASE}/projects").mock(
        return_value=httpx.Response(200, json={"project": {"id": "1"}})
    )
    await get_tool("create_project").fn(
        title="Project", description="<p>desc</p>", priority="High", project_type="Departmental",
        scheduled_start="2026-08-01T00:00:00Z", scheduled_end="2026-08-02T00:00:00Z",
    )
    payload = decode_body(route.calls[0])
    assert payload["project"]["priority"] == {"name": "High"}
    assert payload["project"]["type"] == {"name": "Departmental"}
    assert payload["project"]["scheduled_start_time"] == {"value": "2026-08-01T00:00:00Z"}
    assert payload["project"]["scheduled_end_time"] == {"value": "2026-08-02T00:00:00Z"}


@respx.mock
async def test_update_project_payload_shape() -> None:
    route = respx.put(f"{BASE}/projects/1").mock(
        return_value=httpx.Response(200, json={"project": {"id": "1"}})
    )
    await get_tool("update_project").fn(project_id="1", title="Updated", priority="Low")
    payload = decode_body(route.calls[0])
    assert payload["project"]["title"] == "Updated"
    assert payload["project"]["priority"] == {"name": "Low"}


@respx.mock
async def test_delete_project_url() -> None:
    route = respx.delete(f"{BASE}/projects/1").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    await get_tool("delete_project").fn(project_id="1")
    assert route.called


@respx.mock
async def test_list_project_milestones_url() -> None:
    route = respx.get(f"{BASE}/projects/1/milestones").mock(
        return_value=httpx.Response(200, json={"milestones": []})
    )
    await get_tool("list_project_milestones").fn(project_id="1")
    assert route.called


@respx.mock
async def test_add_project_milestone_payload_shape() -> None:
    route = respx.post(f"{BASE}/projects/1/milestones").mock(
        return_value=httpx.Response(200, json={"milestone": {"id": "1"}})
    )
    await get_tool("add_project_milestone").fn(project_id="1", title="Milestone 1")
    payload = decode_body(route.calls[0])
    assert payload["milestone"] == {"title": "Milestone 1"}


@respx.mock
async def test_list_project_tasks_url() -> None:
    route = respx.get(f"{BASE}/projects/1/tasks").mock(
        return_value=httpx.Response(200, json={"tasks": []})
    )
    await get_tool("list_project_tasks").fn(project_id="1")
    assert route.called


@respx.mock
async def test_add_project_task_payload_shape() -> None:
    route = respx.post(f"{BASE}/projects/1/tasks").mock(
        return_value=httpx.Response(200, json={"task": {"id": "1"}})
    )
    await get_tool("add_project_task").fn(project_id="1", title="Prep rollout", assigned_to="jdoe")
    payload = decode_body(route.calls[0])
    assert payload["task"]["title"] == "Prep rollout"
    assert payload["task"]["owner"] == {"name": "jdoe"}


@respx.mock
async def test_list_project_members_url() -> None:
    route = respx.get(f"{BASE}/projects/1/members").mock(
        return_value=httpx.Response(200, json={"members": []})
    )
    await get_tool("list_project_members").fn(project_id="1")
    assert route.called


@respx.mock
async def test_add_project_member_payload_shape() -> None:
    route = respx.post(f"{BASE}/projects/1/members").mock(
        return_value=httpx.Response(200, json={"member": {"id": "1"}})
    )
    await get_tool("add_project_member").fn(project_id="1", technician_email="jdoe@example.com")
    payload = decode_body(route.calls[0])
    assert payload["member"]["user"] == {"email_id": "jdoe@example.com"}
    assert payload["member"]["role"] == {"name": "Team Member"}


@respx.mock
async def test_list_project_comments_url() -> None:
    route = respx.get(f"{BASE}/projects/1/comments").mock(
        return_value=httpx.Response(200, json={"comments": []})
    )
    await get_tool("list_project_comments").fn(project_id="1")
    assert route.called


@respx.mock
async def test_add_project_comment_payload_shape() -> None:
    route = respx.post(f"{BASE}/projects/1/comments").mock(
        return_value=httpx.Response(200, json={"comment": {"id": "1"}})
    )
    await get_tool("add_project_comment").fn(project_id="1", comment_text="a comment")
    payload = decode_body(route.calls[0])
    assert payload["comment"] == {"content": "a comment"}
