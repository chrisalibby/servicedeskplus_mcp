"""
Integration tests for problems, changes, CMDB, solutions, and admin tools.
Run with: uv run pytest tests/integration/ -v -m integration
"""

import json

import pytest

from .conftest import skip_if_no_server

pytestmark = [pytest.mark.integration, skip_if_no_server]


# ---------------------------------------------------------------------------
# Problems
# ---------------------------------------------------------------------------

async def test_list_problems(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 5}})}
    result = await client.get("/problems", params=params)
    assert "error" not in result, result.get("error")
    print(f"\nProblems (first 5): {len(result.get('problems', []))}")
    for p in result.get("problems", []):
        print(f"  {p.get('id')} — {p.get('title')}")


# ---------------------------------------------------------------------------
# Changes
# ---------------------------------------------------------------------------

async def test_list_changes(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 5}})}
    result = await client.get("/changes", params=params)
    assert "error" not in result, result.get("error")
    print(f"\nChanges (first 5): {len(result.get('changes', []))}")
    for ch in result.get("changes", []):
        print(f"  {ch.get('id')} — {ch.get('title')}")


# ---------------------------------------------------------------------------
# CMDB — may not be enabled on this instance
# ---------------------------------------------------------------------------

async def test_list_configuration_items(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 5}})}
    result = await client.get("/ci", params=params)
    if "error" in result:
        pytest.skip(f"CMDB (/ci) not available on this instance: {result['error']}")
    assert "error" not in result, result.get("error")
    print(f"\nCIs (first 5): {len(result.get('ci', []))}")


# ---------------------------------------------------------------------------
# Solutions / Knowledge Base
# ---------------------------------------------------------------------------

async def test_search_solutions(client) -> None:
    params = {"input_data": json.dumps({
        "list_info": {
            "start_index": 0,
            "row_count": 5,
            "search_criteria": [{"field": "title", "condition": "contains", "value": "password"}],
        }
    })}
    result = await client.get("/solutions", params=params)
    assert "error" not in result, result.get("error")
    print(f"\nSolutions matching 'password': {len(result.get('solutions', []))}")
    for s in result.get("solutions", []):
        print(f"  {s.get('id')} — {s.get('title')}")


async def test_list_solution_topics(client) -> None:
    """Solution topics live at /topics on this instance, not /solution_topics."""
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 20}})}
    result = await client.get("/topics", params=params)
    assert "error" not in result, result.get("error")
    print(f"\nSolution topics: {[(t.get('id'), t.get('name')) for t in result.get('topics', [])]}")


# ---------------------------------------------------------------------------
# Admin lookups
# ---------------------------------------------------------------------------

async def test_list_groups(client) -> None:
    """/groups returns 404 on this instance — endpoint not exposed in API v3 here."""
    params = {"input_data": json.dumps({"list_info": {"row_count": 50}})}
    result = await client.get("/groups", params=params)
    if "error" in result:
        pytest.skip(f"Groups endpoint not available on this SDP instance: {result['error']}")
    assert "error" not in result, result.get("error")


async def test_list_sites(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"row_count": 50}})}
    result = await client.get("/sites", params=params)
    assert "error" not in result, result.get("error")
    print(f"\nSites: {[(s.get('id'), s.get('name')) for s in result.get('sites', [])]}")


async def test_list_departments(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"row_count": 50}})}
    result = await client.get("/departments", params=params)
    assert "error" not in result, result.get("error")
    print(f"\nDepts: {[(d.get('id'), d.get('name')) for d in result.get('departments', [])]}")


async def test_list_urgencies(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"row_count": 20}})}
    result = await client.get("/urgencies", params=params)
    assert "error" not in result, result.get("error")
    print(f"\nUrgencies: {[(u.get('id'), u.get('name')) for u in result.get('urgencies', [])]}")


async def test_list_subcategories(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"row_count": 50}})}
    result = await client.get("/subcategories", params=params)
    assert "error" not in result, result.get("error")
    subs = result.get("subcategories", [])
    print(f"\nSubcategories ({len(subs)} total, showing first 15):")
    for s in subs[:15]:
        cat = s.get("category", {}).get("name", "?")
        print(f"  [{cat}] {s.get('id')} — {s.get('name')}")


# ---------------------------------------------------------------------------
# Filtered request list and subcategory in create
# ---------------------------------------------------------------------------

async def test_list_requests_filtered_by_open_status(client) -> None:
    params = {"input_data": json.dumps({
        "list_info": {
            "start_index": 0,
            "row_count": 5,
            "search_criteria": [{"field": "status.name", "condition": "is", "value": "Open"}],
        }
    })}
    result = await client.get("/requests", params=params)
    assert "error" not in result, result.get("error")
    for r in result.get("requests", []):
        assert r.get("status", {}).get("name") == "Open"


async def test_create_request_with_subcategory(client) -> None:
    """Verify subcategory is accepted and the tool parameter works end-to-end."""
    payload = {
        "subject": "[MCP TEST] subcategory test",
        "description": "Integration test",
        "requester": {"name": "Chris Libby"},
        "category": {"name": "User Administration"},
        "subcategory": {"name": "Password Reset"},
    }
    result = await client.post("/requests", {"request": payload})
    assert "error" not in result, result.get("error")
    assert "request" in result
    rid = result["request"]["id"]
    await client.delete(f"/requests/{rid}/move_to_trash")
    await client.delete(f"/requests/{rid}")
