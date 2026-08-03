"""Problem management tools for ServiceDesk Plus."""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client
from ._util import normalize_id, strip_cdata


def register(app: FastMCP) -> None:
    @app.tool()
    async def list_problems(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
        status: Annotated[str, "Filter by status name"] = "",
    ) -> dict[str, Any]:
        """List problems with optional filtering."""
        list_info: dict[str, Any] = {
            "start_index": (page - 1) * page_size,
            "row_count": page_size,
        }
        if status:
            list_info["search_criteria"] = [
                {"field": "status.name", "condition": "is", "value": status}
            ]
        params = {"input_data": json.dumps({"list_info": list_info})}
        async with get_client() as c:
            return await c.get("/problems", params=params)

    @app.tool()
    async def get_problem(
        problem_id: Annotated[str, "Problem ID"],
    ) -> dict[str, Any]:
        """Get a single problem record by ID."""
        async with get_client() as c:
            return await c.get(f"/problems/{problem_id}")

    @app.tool()
    async def create_problem(
        title: Annotated[str, "Problem title"],
        description: Annotated[
            str, "Problem description. Raw HTML is supported; do not wrap in CDATA."
        ] = "",
        priority: Annotated[str, "Priority name"] = "",
        technician: Annotated[str, "Assigned technician login name"] = "",
    ) -> dict[str, Any]:
        """Create a new problem record."""
        problem: dict[str, Any] = {"title": title}
        if description:
            problem["description"] = strip_cdata(description)
        if priority:
            problem["priority"] = {"name": priority}
        if technician:
            problem["technician"] = {"name": technician}
        async with get_client() as c:
            return await c.post("/problems", {"problem": problem})

    @app.tool()
    async def update_problem(
        problem_id: Annotated[str, "Problem ID"],
        title: Annotated[str, "Updated title"] = "",
        description: Annotated[
            str, "Updated description. Raw HTML is supported; do not wrap in CDATA."
        ] = "",
        status: Annotated[str, "New status name"] = "",
        priority: Annotated[str, "New priority name"] = "",
        technician: Annotated[str, "New assigned technician login name"] = "",
    ) -> dict[str, Any]:
        """Update an existing problem record."""
        problem: dict[str, Any] = {}
        if title:
            problem["title"] = title
        if description:
            problem["description"] = strip_cdata(description)
        if status:
            problem["status"] = {"name": status}
        if priority:
            problem["priority"] = {"name": priority}
        if technician:
            problem["technician"] = {"name": technician}
        async with get_client() as c:
            return await c.put(f"/problems/{problem_id}", {"problem": problem})

    @app.tool()
    async def close_problem(
        problem_id: Annotated[str, "Problem ID to close"],
        closure_comments: Annotated[str, "Comments explaining closure"] = "",
    ) -> dict[str, Any]:
        """Close a problem record."""
        problem: dict[str, Any] = {"status": {"name": "Closed"}}
        if closure_comments:
            problem["closure_comments"] = closure_comments
        async with get_client() as c:
            return await c.put(f"/problems/{problem_id}", {"problem": problem})

    @app.tool()
    async def delete_problem(
        problem_id: Annotated[str, "Problem ID to delete"],
    ) -> dict[str, Any]:
        """Permanently delete a problem record. Confirmed live 2026-08-01: unlike
        delete_request, there is no move_to_trash variant for problems on this instance
        (PUT .../restore_from_trash 404s "Invalid URL") — this delete cannot be undone."""
        pid = normalize_id(problem_id)
        async with get_client() as c:
            return await c.delete(f"/problems/{pid}")

    @app.tool()
    async def add_problem_note(
        problem_id: Annotated[str, "Problem ID"],
        note_text: Annotated[str, "Note content. Raw HTML is supported; do not wrap in CDATA."],
    ) -> dict[str, Any]:
        """Add a note to a problem record. Note: show_to_requester is not supported on
        problem notes (unlike request notes) — do not pass it."""
        async with get_client() as c:
            return await c.post(
                f"/problems/{problem_id}/notes", {"note": {"description": strip_cdata(note_text)}}
            )

    @app.tool()
    async def list_problem_notes(
        problem_id: Annotated[str, "Problem ID"],
    ) -> dict[str, Any]:
        """List all notes on a problem record."""
        async with get_client() as c:
            return await c.get(f"/problems/{problem_id}/notes")

    @app.tool()
    async def update_problem_note(
        problem_id: Annotated[str, "Problem ID"],
        note_id: Annotated[str, "Note ID"],
        note_text: Annotated[str, "New note content. Raw HTML is supported; do not wrap in CDATA."],
    ) -> dict[str, Any]:
        """Edit an existing note on a problem record."""
        async with get_client() as c:
            return await c.put(
                f"/problems/{problem_id}/notes/{note_id}",
                {"note": {"description": strip_cdata(note_text)}},
            )

    @app.tool()
    async def get_problem_note(
        problem_id: Annotated[str, "Problem ID"],
        note_id: Annotated[str, "Note ID"],
    ) -> dict[str, Any]:
        """Get a single note on a problem record."""
        pid = normalize_id(problem_id)
        async with get_client() as c:
            return await c.get(f"/problems/{pid}/notes/{note_id}")

    @app.tool()
    async def delete_problem_note(
        problem_id: Annotated[str, "Problem ID"],
        note_id: Annotated[str, "Note ID"],
    ) -> dict[str, Any]:
        """Delete a note from a problem record. This is a permanent delete."""
        pid = normalize_id(problem_id)
        async with get_client() as c:
            return await c.delete(f"/problems/{pid}/notes/{note_id}")

    @app.tool()
    async def list_problem_tasks(
        problem_id: Annotated[str, "Problem ID"],
    ) -> dict[str, Any]:
        """List all tasks associated with a problem record."""
        async with get_client() as c:
            return await c.get(f"/problems/{problem_id}/tasks")

    @app.tool()
    async def add_problem_task(
        problem_id: Annotated[str, "Problem ID"],
        title: Annotated[str, "Task title"],
        description: Annotated[str, "Task description"] = "",
        assigned_to: Annotated[str, "Technician login name to assign task"] = "",
    ) -> dict[str, Any]:
        """Add a task to a problem record."""
        task: dict[str, Any] = {"title": title}
        if description:
            task["description"] = description
        if assigned_to:
            task["owner"] = {"name": assigned_to}
        async with get_client() as c:
            return await c.post(f"/problems/{problem_id}/tasks", {"task": task})

    @app.tool()
    async def get_problem_task(
        problem_id: Annotated[str, "Problem ID"],
        task_id: Annotated[str, "Task ID"],
    ) -> dict[str, Any]:
        """Get a single task on a problem record."""
        async with get_client() as c:
            return await c.get(f"/problems/{problem_id}/tasks/{task_id}")

    @app.tool()
    async def update_problem_task(
        problem_id: Annotated[str, "Problem ID"],
        task_id: Annotated[str, "Task ID"],
        title: Annotated[str, "Updated task title"] = "",
        description: Annotated[str, "Updated task description"] = "",
        assigned_to: Annotated[str, "New technician login name to assign task"] = "",
        status: Annotated[str, "New task status name, e.g. 'Open', 'Closed'"] = "",
    ) -> dict[str, Any]:
        """Update a task on a problem record."""
        task: dict[str, Any] = {}
        if title:
            task["title"] = title
        if description:
            task["description"] = description
        if assigned_to:
            task["owner"] = {"name": assigned_to}
        if status:
            task["status"] = {"name": status}
        async with get_client() as c:
            return await c.put(f"/problems/{problem_id}/tasks/{task_id}", {"task": task})

    @app.tool()
    async def delete_problem_task(
        problem_id: Annotated[str, "Problem ID"],
        task_id: Annotated[str, "Task ID"],
    ) -> dict[str, Any]:
        """Delete a task from a problem record. This is a permanent delete."""
        async with get_client() as c:
            return await c.delete(f"/problems/{problem_id}/tasks/{task_id}")

    @app.tool()
    async def list_problem_worklogs(
        problem_id: Annotated[str, "Problem ID"],
    ) -> dict[str, Any]:
        """List all worklog entries for a problem record."""
        async with get_client() as c:
            return await c.get(f"/problems/{problem_id}/worklogs")

    @app.tool()
    async def add_problem_worklog(
        problem_id: Annotated[str, "Problem ID"],
        description: Annotated[str, "Work performed"],
        technician_email: Annotated[str, "Technician email address (e.g. jsmith@example.com)"],
        hours: Annotated[int, "Whole hours spent"] = 0,
        minutes: Annotated[int, "Additional minutes spent (0–59)"] = 0,
    ) -> dict[str, Any]:
        """Add a worklog entry to a problem record."""
        worklog: dict[str, Any] = {
            "description": description,
            "time_spent": {"hours": hours, "minutes": minutes},
            "owner": {"email_id": technician_email},
        }
        async with get_client() as c:
            return await c.post(f"/problems/{problem_id}/worklogs", {"worklog": worklog})

    @app.tool()
    async def update_problem_worklog(
        problem_id: Annotated[str, "Problem ID"],
        worklog_id: Annotated[str, "Worklog ID"],
        description: Annotated[str, "Updated work performed"] = "",
        hours: Annotated[int, "Updated whole hours spent (omit to leave unchanged)"] = -1,
        minutes: Annotated[int, "Updated additional minutes spent (0–59)"] = -1,
    ) -> dict[str, Any]:
        """Edit an existing worklog entry on a problem record."""
        worklog: dict[str, Any] = {}
        if description:
            worklog["description"] = description
        if hours >= 0 or minutes >= 0:
            worklog["time_spent"] = {
                "hours": hours if hours >= 0 else 0,
                "minutes": minutes if minutes >= 0 else 0,
            }
        async with get_client() as c:
            return await c.put(
                f"/problems/{problem_id}/worklogs/{worklog_id}", {"worklog": worklog}
            )

    @app.tool()
    async def delete_problem_worklog(
        problem_id: Annotated[str, "Problem ID"],
        worklog_id: Annotated[str, "Worklog ID"],
    ) -> dict[str, Any]:
        """Delete a worklog entry from a problem record. This is a permanent delete."""
        async with get_client() as c:
            return await c.delete(f"/problems/{problem_id}/worklogs/{worklog_id}")
