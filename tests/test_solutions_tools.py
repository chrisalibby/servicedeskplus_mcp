"""Tests for solutions / knowledge base tools."""

import httpx
import respx

from .conftest import BASE, decode_body, get_tool


@respx.mock
async def test_search_solutions_url() -> None:
    route = respx.get(f"{BASE}/solutions").mock(
        return_value=httpx.Response(200, json={"solutions": []})
    )
    result = await get_tool("search_solutions").fn(query="password")
    assert route.called
    assert result == {"solutions": []}


@respx.mock
async def test_get_solution_url() -> None:
    route = respx.get(f"{BASE}/solutions/1").mock(
        return_value=httpx.Response(200, json={"solution": {"id": "1"}})
    )
    await get_tool("get_solution").fn(solution_id="1")
    assert route.called


@respx.mock
async def test_create_solution_payload_shape() -> None:
    route = respx.post(f"{BASE}/solutions").mock(
        return_value=httpx.Response(200, json={"solution": {"id": "1"}})
    )
    await get_tool("create_solution").fn(
        title="MCP TEST SOLUTION", description="<p>desc</p>", topic="Hardware", keywords="a,b"
    )
    payload = decode_body(route.calls[0])
    assert payload["solution"]["title"] == "MCP TEST SOLUTION"
    assert payload["solution"]["description"] == "<p>desc</p>"
    assert payload["solution"]["topic"] == {"name": "Hardware"}
    assert payload["solution"]["keywords"] == "a,b"


@respx.mock
async def test_update_solution_payload_shape() -> None:
    route = respx.put(f"{BASE}/solutions/1").mock(
        return_value=httpx.Response(200, json={"solution": {"id": "1"}})
    )
    await get_tool("update_solution").fn(
        solution_id="1", title="Updated", approval_status="Approved"
    )
    payload = decode_body(route.calls[0])
    assert payload["solution"]["title"] == "Updated"
    assert payload["solution"]["approval_status"] == {"name": "Approved"}


@respx.mock
async def test_delete_solution_url() -> None:
    route = respx.delete(f"{BASE}/solutions/1").mock(
        return_value=httpx.Response(200, json={"response_status": {"status": "success"}})
    )
    await get_tool("delete_solution").fn(solution_id="1")
    assert route.called


@respx.mock
async def test_add_solution_attachment_multipart(tmp_path) -> None:
    f = tmp_path / "note.txt"
    f.write_text("hello")
    route = respx.put(f"{BASE}/solutions/1/upload").mock(
        return_value=httpx.Response(200, json={"attachment": {"id": "9"}})
    )
    result = await get_tool("add_solution_attachment").fn(solution_id="1", file_path=str(f))
    assert route.called
    assert result == {"attachment": {"id": "9"}}


@respx.mock
async def test_list_solution_topics_url() -> None:
    route = respx.get(f"{BASE}/topics").mock(
        return_value=httpx.Response(200, json={"topics": []})
    )
    result = await get_tool("list_solution_topics").fn()
    assert route.called
    assert result == {"topics": []}


@respx.mock
async def test_create_solution_topic_payload_shape() -> None:
    route = respx.post(f"{BASE}/topics").mock(
        return_value=httpx.Response(200, json={"topic": {"id": "1"}})
    )
    await get_tool("create_solution_topic").fn(name="New Topic", parent_topic_id="4")
    payload = decode_body(route.calls[0])
    assert payload["topic"] == {"name": "New Topic", "parent": {"id": "4"}}
