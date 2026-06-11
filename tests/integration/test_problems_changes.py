"""
Integration tests for problem and change round-trips against a live SDP instance.
Run with: pytest tests/integration/ -v -m integration
"""

import pytest

from .conftest import skip_if_no_server

pytestmark = [pytest.mark.integration, skip_if_no_server]


# ---------------------------------------------------------------------------
# Problems
# ---------------------------------------------------------------------------

async def _create_problem(client, title: str) -> str:
    result = await client.post("/problems", {
        "problem": {
            "title": f"[MCP TEST] {title}",
            "description": "Integration test — safe to close/delete",
        }
    })
    assert "problem" in result, f"Create problem failed: {result}"
    return result["problem"]["id"]


async def _close_problem(client, problem_id: str) -> None:
    await client.put(f"/problems/{problem_id}", {"problem": {"status": {"name": "Closed"}}})


async def test_problem_create_and_get(client) -> None:
    """Create a problem and verify get returns it."""
    pid = await _create_problem(client, "create-and-get")
    try:
        result = await client.get(f"/problems/{pid}")
        assert "problem" in result, result
        assert result["problem"]["id"] == pid
    finally:
        await _close_problem(client, pid)


async def test_problem_update(client) -> None:
    """Create a problem, update its title, verify the change persists."""
    pid = await _create_problem(client, "update-test")
    try:
        updated_title = "[MCP TEST] update-test (updated)"
        result = await client.put(f"/problems/{pid}", {
            "problem": {"title": updated_title}
        })
        assert "error" not in result, result.get("error")
        fetched = await client.get(f"/problems/{pid}")
        assert fetched["problem"]["title"] == updated_title
    finally:
        await _close_problem(client, pid)


async def test_problem_add_note(client) -> None:
    """Add a note to a problem and verify it appears in the notes list."""
    pid = await _create_problem(client, "note-test")
    try:
        result = await client.post(f"/problems/{pid}/notes", {
            "note": {"description": "Integration test note"}
        })
        assert "error" not in result, result.get("error")
        notes = await client.get(f"/problems/{pid}/notes")
        assert "error" not in notes, notes.get("error")
        texts = [n.get("description", "") for n in notes.get("notes", [])]
        assert any("Integration test note" in t for t in texts)
    finally:
        await _close_problem(client, pid)


async def test_problem_close(client) -> None:
    """Close a problem and verify the status is updated."""
    pid = await _create_problem(client, "close-test")
    result = await client.put(f"/problems/{pid}", {
        "problem": {"status": {"name": "Closed"}}
    })
    assert "error" not in result, result.get("error")
    fetched = await client.get(f"/problems/{pid}")
    assert fetched["problem"]["status"]["name"] == "Closed"


# ---------------------------------------------------------------------------
# Changes
# ---------------------------------------------------------------------------

async def _create_change(client, title: str) -> str:
    result = await client.post("/changes", {
        "change": {
            "title": f"[MCP TEST] {title}",
            "description": "Integration test — safe to close/delete",
        }
    })
    assert "change" in result, f"Create change failed: {result}"
    return result["change"]["id"]


async def _close_change(client, change_id: str) -> None:
    await client.put(f"/changes/{change_id}", {"change": {"status": {"name": "Completed"}}})


async def test_change_create_and_get(client) -> None:
    """Create a change and verify get returns it."""
    cid = await _create_change(client, "create-and-get")
    try:
        result = await client.get(f"/changes/{cid}")
        assert "change" in result, result
        assert result["change"]["id"] == cid
    finally:
        await _close_change(client, cid)


async def test_change_update(client) -> None:
    """Create a change, update its title, verify the change persists."""
    cid = await _create_change(client, "update-test")
    try:
        updated_title = "[MCP TEST] update-test (updated)"
        result = await client.put(f"/changes/{cid}", {
            "change": {"title": updated_title}
        })
        assert "error" not in result, result.get("error")
        fetched = await client.get(f"/changes/{cid}")
        assert fetched["change"]["title"] == updated_title
    finally:
        await _close_change(client, cid)


async def test_change_add_note(client) -> None:
    """Add a note to a change and verify it appears in the notes list.

    Note: GET /changes/{id}/notes omits description from list items (SDP quirk) —
    we verify count > 0 rather than text content.
    """
    cid = await _create_change(client, "note-test")
    try:
        result = await client.post(f"/changes/{cid}/notes", {
            "note": {"description": "Integration test note"}
        })
        assert "error" not in result, result.get("error")
        notes = await client.get(f"/changes/{cid}/notes")
        assert "error" not in notes, notes.get("error")
        assert len(notes.get("notes", [])) > 0
    finally:
        await _close_change(client, cid)


async def test_change_list_tasks(client) -> None:
    """Verify list_change_tasks endpoint returns without error."""
    cid = await _create_change(client, "tasks-test")
    try:
        result = await client.get(f"/changes/{cid}/tasks")
        assert "error" not in result, result.get("error")
    finally:
        await _close_change(client, cid)


@pytest.mark.skip(
    reason="Changes on this instance require workflow progression (Requested → In Review → "
           "Approved → In Progress → Completed) — direct status PUT is rejected for all "
           "terminal statuses. close_change tool is kept for instances with simpler workflows."
)
async def test_change_close(client) -> None:
    """Close a change and verify the status is updated."""
    cid = await _create_change(client, "close-test")
    result = await client.put(f"/changes/{cid}", {
        "change": {"status": {"name": "Completed"}}
    })
    assert "error" not in result, result.get("error")
    fetched = await client.get(f"/changes/{cid}")
    assert fetched["change"]["status"]["name"] == "Completed"
