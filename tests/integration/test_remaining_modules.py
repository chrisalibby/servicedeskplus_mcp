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


async def test_problem_notes_tasks_worklogs(client) -> None:
    """Backfilled note/task/worklog tools for problems — mirrors requests.py's pattern.
    Adds a task and worklog to a real problem and cleans them up immediately after."""
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 1}})}
    problems = await client.get("/problems", params=params)
    plist = problems.get("problems", [])
    if not plist:
        pytest.skip("No problems on this instance to test against")
    problem_id = plist[0]["id"]

    notes = await client.get(f"/problems/{problem_id}/notes")
    assert "error" not in notes, notes.get("error")

    task = await client.post(
        f"/problems/{problem_id}/tasks",
        {"task": {"title": "[TEST] integration probe - safe to delete"}},
    )
    assert "error" not in task, task.get("error")
    task_id = task["task"]["id"]
    try:
        tasks = await client.get(f"/problems/{problem_id}/tasks")
        assert "error" not in tasks, tasks.get("error")
    finally:
        await client.delete(f"/problems/{problem_id}/tasks/{task_id}")

    worklog = await client.post(
        f"/problems/{problem_id}/worklogs",
        {
            "worklog": {
                "description": "[TEST] integration probe - safe to delete",
                "time_spent": {"hours": 0, "minutes": 1},
                "owner": {"email_id": "clibby@spero.financial"},
            }
        },
    )
    assert "error" not in worklog, worklog.get("error")
    worklog_id = worklog["worklog"]["id"]
    try:
        worklogs = await client.get(f"/problems/{problem_id}/worklogs")
        assert "error" not in worklogs, worklogs.get("error")
    finally:
        await client.delete(f"/problems/{problem_id}/worklogs/{worklog_id}")


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


async def test_change_notes_tasks_worklogs(client) -> None:
    """Backfilled note/task/worklog tools for changes — mirrors requests.py's pattern.
    Adds a task and worklog to a real change and cleans them up immediately after."""
    list_info = {
        "start_index": 0,
        "row_count": 5,
        "sort_field": "created_time",
        "sort_order": "desc",
    }
    params = {"input_data": json.dumps({"list_info": list_info})}
    changes = await client.get("/changes", params=params)
    clist = changes.get("changes", [])
    if not clist:
        pytest.skip("No changes on this instance to test against")

    task = None
    change_id = None
    for ch in clist:
        change_id = ch["id"]
        notes = await client.get(f"/changes/{change_id}/notes")
        assert "error" not in notes, notes.get("error")
        task = await client.post(
            f"/changes/{change_id}/tasks",
            {"task": {"title": "[TEST] integration probe - safe to delete"}},
        )
        if "permission" not in str(task.get("error", "")):
            break
    assert task is not None
    if "permission" in str(task.get("error", "")):
        pytest.skip("All sampled changes are in stages that disallow task writes")
    assert "error" not in task, task.get("error")
    task_id = task["task"]["id"]
    try:
        tasks = await client.get(f"/changes/{change_id}/tasks")
        assert "error" not in tasks, tasks.get("error")
    finally:
        await client.delete(f"/changes/{change_id}/tasks/{task_id}")

    worklog = await client.post(
        f"/changes/{change_id}/worklogs",
        {
            "worklog": {
                "description": "[TEST] integration probe - safe to delete",
                "time_spent": {"hours": 0, "minutes": 1},
                "owner": {"email_id": "clibby@spero.financial"},
            }
        },
    )
    assert "error" not in worklog, worklog.get("error")
    worklog_id = worklog["worklog"]["id"]
    try:
        worklogs = await client.get(f"/changes/{change_id}/worklogs")
        assert "error" not in worklogs, worklogs.get("error")
    finally:
        await client.delete(f"/changes/{change_id}/worklogs/{worklog_id}")


# ---------------------------------------------------------------------------
# Releases
# ---------------------------------------------------------------------------

async def test_list_releases(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 5}})}
    result = await client.get("/releases", params=params)
    assert "error" not in result, result.get("error")
    print(f"\nReleases (first 5): {len(result.get('releases', []))}")
    for r in result.get("releases", []):
        print(f"  {r.get('id')} — {r.get('title')}")


async def test_release_create_get_note_roundtrip(client) -> None:
    """Creates a real release (title is the only mandatory field on this instance),
    round-trips get/note/task/worklog, then trashes it (move_to_trash — recoverable)."""
    created = await client.post(
        "/releases", {"release": {"title": "[TEST] MCP integration probe - safe to delete"}}
    )
    assert "error" not in created, created.get("error")
    release_id = created["release"]["id"]
    try:
        fetched = await client.get(f"/releases/{release_id}")
        assert "error" not in fetched, fetched.get("error")
        assert fetched["release"]["id"] == release_id

        note = await client.post(
            f"/releases/{release_id}/notes",
            {"note": {"description": "[TEST] integration probe - safe to delete"}},
        )
        assert "error" not in note, note.get("error")
        notes = await client.get(f"/releases/{release_id}/notes")
        assert "error" not in notes, notes.get("error")
        assert any(n["id"] == note["note"]["id"] for n in notes.get("notes", []))

        task = await client.post(
            f"/releases/{release_id}/tasks",
            {"task": {"title": "[TEST] integration probe - safe to delete", "stage": {"id": "2"}}},
        )
        assert "error" not in task, task.get("error")

        worklog = await client.post(
            f"/releases/{release_id}/worklogs",
            {
                "worklog": {
                    "description": "[TEST] integration probe - safe to delete",
                    "time_spent": {"hours": 0, "minutes": 1},
                    "owner": {"email_id": "clibby@spero.financial"},
                }
            },
        )
        assert "error" not in worklog, worklog.get("error")
    finally:
        await client.delete(f"/releases/{release_id}/move_to_trash")


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

async def test_list_projects(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 5}})}
    result = await client.get("/projects", params=params)
    assert "error" not in result, result.get("error")
    print(f"\nProjects (first 5): {len(result.get('projects', []))}")
    for p in result.get("projects", []):
        print(f"  {p.get('id')} — {p.get('title')}")


async def test_project_create_get_milestone_task_roundtrip(client) -> None:
    """Creates a real project (title is the only mandatory field on this instance),
    round-trips get/update/milestone/task/comment, then hard-deletes it — there is no
    move_to_trash endpoint for projects on this instance (404s)."""
    created = await client.post(
        "/projects", {"project": {"title": "[TEST] MCP integration probe - safe to delete"}}
    )
    assert "error" not in created, created.get("error")
    project_id = created["project"]["id"]
    try:
        fetched = await client.get(f"/projects/{project_id}")
        assert "error" not in fetched, fetched.get("error")
        assert fetched["project"]["id"] == project_id

        milestone = await client.post(
            f"/projects/{project_id}/milestones",
            {"milestone": {"title": "[TEST] integration probe - safe to delete"}},
        )
        assert "error" not in milestone, milestone.get("error")
        milestones = await client.get(f"/projects/{project_id}/milestones")
        assert "error" not in milestones, milestones.get("error")
        assert any(
            m["id"] == milestone["milestone"]["id"] for m in milestones.get("milestones", [])
        )

        task = await client.post(
            f"/projects/{project_id}/tasks",
            {"task": {"title": "[TEST] integration probe - safe to delete"}},
        )
        assert "error" not in task, task.get("error")

        comment = await client.post(
            f"/projects/{project_id}/comments",
            {"comment": {"content": "[TEST] integration probe - safe to delete"}},
        )
        assert "error" not in comment, comment.get("error")
        comments = await client.get(f"/projects/{project_id}/comments")
        assert "error" not in comments, comments.get("error")
        assert any(c["id"] == comment["comment"]["id"] for c in comments.get("comments", []))
    finally:
        deleted = await client.delete(f"/projects/{project_id}")
        assert "error" not in deleted, deleted.get("error")


# ---------------------------------------------------------------------------
# CMDB — may not be enabled on this instance
# ---------------------------------------------------------------------------

async def test_list_configuration_items(client) -> None:
    params = {"input_data": json.dumps({"list_info": {"start_index": 0, "row_count": 5}})}
    result = await client.get("/cmdb", params=params)
    assert "error" not in result, result.get("error")
    cis = result.get("cmdb", [])
    print(f"\nCIs (first 5): {len(cis)}")
    for ci in cis:
        print(f"  {ci.get('id')} [{ci.get('module', {}).get('display_name')}] — {ci.get('name')}")

    # Verify get-by-id works
    if cis:
        single = await client.get(f"/cmdb/{cis[0]['id']}")
        assert "cmdb" in single, single
        assert single["cmdb"]["id"] == cis[0]["id"]

    # Verify module-type filter works
    result2 = await client.get("/cmdb_itservice", params=params)
    assert "error" not in result2, result2.get("error")
    print(f"  cmdb_itservice count: {len(result2.get('cmdb_itservice', []))}")


async def test_configuration_item_create_update_relationships(client) -> None:
    """Confirms module-scoped create/update (and generic /cmdb ci_relationships GET)
    work once addressed correctly — see CLAUDE.md CMDB quirk entry. Cleans up after
    itself since this creates a real CI on the live instance."""
    module_type = "cmdb_itservice"
    created = await client.post(
        f"/{module_type}", {module_type: {"name": "[DEBUG] cmdb integration test"}}
    )
    assert "error" not in created, created.get("error")
    ci_id = created[module_type]["id"]
    try:
        updated = await client.put(
            f"/{module_type}/{ci_id}", {module_type: {"description": "updated"}}
        )
        assert "error" not in updated, updated.get("error")
        assert updated[module_type]["description"] == "updated"

        rel = await client.get(f"/cmdb/{ci_id}/ci_relationships")
        assert "error" not in rel, rel.get("error")
        assert rel["ci_relationships"] == []
    finally:
        cleanup = await client.delete(f"/{module_type}/{ci_id}")
        assert "error" not in cleanup, cleanup.get("error")


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


async def test_solution_create_update_delete_roundtrip(client) -> None:
    """DELETE /solutions/{id} consistently returns 'Not in trash' on this instance — there is
    no working move-to-trash sub-route for solutions (confirmed 2026-08-01), so the delete
    step is expected to fail here and is not treated as a hard test failure."""
    created = await client.post(
        "/solutions",
        {"solution": {
            "title": "[TEST] integration probe - safe to delete",
            "description": "<p>integration test solution</p>",
            "topic": {"id": "4"},
        }},
    )
    assert "error" not in created, created.get("error")
    solution_id = created["solution"]["id"]

    updated = await client.put(
        f"/solutions/{solution_id}",
        {"solution": {
            "title": "[TEST] integration probe - updated",
            "approval_status": {"name": "Approved"},
        }},
    )
    assert "error" not in updated, updated.get("error")
    assert updated["solution"]["title"] == "[TEST] integration probe - updated"
    assert updated["solution"]["approval_status"]["name"] == "Approved"

    deleted = await client.delete(f"/solutions/{solution_id}")
    if "error" in deleted:
        print(f"\nSolution {solution_id} delete failed as expected: {deleted['error']}")
        print("Manual cleanup via SDP UI trash may be required.")
    else:
        print(f"\nSolution {solution_id} deleted successfully.")


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
