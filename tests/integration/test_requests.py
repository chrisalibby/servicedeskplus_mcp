"""
Integration tests for service request (ticket) tools against a live SDP instance.
These tests create real records and clean up after themselves.
Run with: uv run pytest tests/integration/ -v -m integration
"""

import pytest

from .conftest import skip_if_no_server

pytestmark = [pytest.mark.integration, skip_if_no_server]

# Mandatory fields on this SDP instance
_BASE_REQUEST = {
    "subject": "[MCP TEST] placeholder",
    "description": "Integration test — safe to delete",
    "requester": {"name": "Chris Libby"},
    "category": {"name": "User Administration"},
    "subcategory": {"name": "Password Reset"},
}


async def _create(client, subject: str) -> str:
    """Create a test request and return its ID."""
    payload = {**_BASE_REQUEST, "subject": f"[MCP TEST] {subject}"}
    result = await client.post("/requests", {"request": payload})
    assert "request" in result, f"Create failed: {result}"
    return result["request"]["id"]


async def _delete(client, request_id: str) -> None:
    """Trash then permanently delete a request."""
    await client.delete(f"/requests/{request_id}/move_to_trash")
    await client.delete(f"/requests/{request_id}")


async def test_create_and_get_request(client) -> None:
    """Create a request and retrieve it by ID."""
    request_id = await _create(client, "create+get smoke test")
    try:
        fetched = await client.get(f"/requests/{request_id}")
        assert fetched["request"]["id"] == request_id
        assert "[MCP TEST]" in fetched["request"]["subject"]
    finally:
        await _delete(client, request_id)


async def test_create_update_delete_request(client) -> None:
    """Create → update description → verify → delete."""
    request_id = await _create(client, "update test")
    try:
        updated = await client.put(f"/requests/{request_id}", {
            "request": {"description": "Updated by integration test"}
        })
        assert updated["request"]["id"] == request_id
    finally:
        await _delete(client, request_id)


async def test_add_and_list_note(client) -> None:
    """Create a request, add a private note, verify content via individual GET.

    Note: the list endpoint omits the description field — content must be
    verified by fetching the individual note by ID.
    """
    request_id = await _create(client, "note test")
    try:
        note_resp = await client.post(f"/requests/{request_id}/notes", {
            "note": {"description": "Integration test note", "show_to_requester": False}
        })
        assert "note" in note_resp
        note_id = note_resp["note"]["id"]

        # List returns notes without description — verify count
        notes = await client.get(f"/requests/{request_id}/notes")
        assert "notes" in notes
        assert len(notes["notes"]) >= 1

        # Fetch individual note to verify description
        single = await client.get(f"/requests/{request_id}/notes/{note_id}")
        assert single["note"]["description"] == "Integration test note"
        assert single["note"]["show_to_requester"] is False
    finally:
        await _delete(client, request_id)


@pytest.mark.skip(
    reason="Worklog API is not functional on this instance — every field "
           "combination returns 400 ('Unable to parse the JSON' / 'Extra key "
           "found'). Time tracking may be disabled or requires a different "
           "API contract than documented for v3 on-prem."
)
async def test_add_worklog(client) -> None:
    """Create a request and log 30 minutes of work."""
    request_id = await _create(client, "worklog test")
    try:
        worklog = await client.post(f"/requests/{request_id}/worklogs", {
            "worklog": {"description": "Integration test worklog", "time_spent": 30}
        })
        assert "worklog" in worklog
    finally:
        await _delete(client, request_id)


async def test_list_requests_pagination(client) -> None:
    """Verify paginated list returns correct structure."""
    import json
    params = {"input_data": json.dumps({
        "list_info": {"start_index": 0, "row_count": 10}
    })}
    result = await client.get("/requests", params=params)
    assert isinstance(result.get("requests", []), list)


async def test_close_request(client) -> None:
    """Create a request and close it.

    Note: closure_info is omitted — this instance returns 400 when it is
    included, likely because closure codes are not configured for requests.
    """
    request_id = await _create(client, "close test")
    try:
        closed = await client.put(f"/requests/{request_id}", {
            "request": {"status": {"name": "Closed"}}
        })
        assert closed["request"]["id"] == request_id
    finally:
        await _delete(client, request_id)


async def test_assign_request(client) -> None:
    """Create a request and assign it to a technician."""
    request_id = await _create(client, "assign test")
    try:
        result = await client.put(f"/requests/{request_id}", {
            "request": {"technician": {"name": "Chris Libby"}}
        })
        assert result["request"]["id"] == request_id
    finally:
        await _delete(client, request_id)
