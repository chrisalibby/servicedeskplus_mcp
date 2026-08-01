"""Release management tools for ServiceDesk Plus."""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client
from ._util import strip_cdata


def register(app: FastMCP) -> None:
    @app.tool()
    async def list_releases(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
        status: Annotated[str, "Filter by status name"] = "",
        sort_field: Annotated[str, "Field to sort by"] = "created_time",
        sort_order: Annotated[str, "Sort order: 'asc' or 'desc'"] = "desc",
    ) -> dict[str, Any]:
        """List release records with optional filtering. Sorted newest-first by default."""
        list_info: dict[str, Any] = {
            "start_index": (page - 1) * page_size,
            "row_count": page_size,
        }
        if sort_field:
            list_info["sort_field"] = sort_field
        if sort_order:
            list_info["sort_order"] = sort_order
        if status:
            list_info["search_criteria"] = [
                {"field": "status.name", "condition": "is", "value": status}
            ]
        params = {"input_data": json.dumps({"list_info": list_info})}
        async with get_client() as c:
            return await c.get("/releases", params=params)

    @app.tool()
    async def get_release(
        release_id: Annotated[str, "Release record ID"],
    ) -> dict[str, Any]:
        """Get a single release record by ID."""
        async with get_client() as c:
            return await c.get(f"/releases/{release_id}")

    @app.tool()
    async def create_release(
        title: Annotated[str, "Release title"],
        description: Annotated[
            str, "Release description. Raw HTML is supported; do not wrap in CDATA."
        ] = "",
        release_type: Annotated[str, "Release type, e.g. 'Major', 'Minor'"] = "",
        priority: Annotated[str, "Priority name"] = "",
        scheduled_start: Annotated[str, "Scheduled start time (ISO 8601)"] = "",
        scheduled_end: Annotated[str, "Scheduled end time (ISO 8601)"] = "",
    ) -> dict[str, Any]:
        """Create a new release record. Only title is mandatory — SDP assigns the default
        template and workflow automatically."""
        release: dict[str, Any] = {"title": title}
        if description:
            release["description"] = strip_cdata(description)
        if release_type:
            release["release_type"] = {"name": release_type}
        if priority:
            release["priority"] = {"name": priority}
        if scheduled_start:
            release["scheduled_start_time"] = {"value": scheduled_start}
        if scheduled_end:
            release["scheduled_end_time"] = {"value": scheduled_end}
        async with get_client() as c:
            return await c.post("/releases", {"release": release})

    @app.tool()
    async def update_release(
        release_id: Annotated[str, "Release ID"],
        title: Annotated[str, "Updated title"] = "",
        description: Annotated[
            str, "Updated description. Raw HTML is supported; do not wrap in CDATA."
        ] = "",
        priority: Annotated[str, "New priority name"] = "",
    ) -> dict[str, Any]:
        """Update an existing release record. Note: status cannot be changed via this
        endpoint (rejected as Invalid Input) — use close_release for stage transitions."""
        release: dict[str, Any] = {}
        if title:
            release["title"] = title
        if description:
            release["description"] = strip_cdata(description)
        if priority:
            release["priority"] = {"name": priority}
        async with get_client() as c:
            return await c.put(f"/releases/{release_id}", {"release": release})

    @app.tool()
    async def close_release(
        release_id: Annotated[str, "Release ID to close"],
        comment: Annotated[str, "Closure comment"] = "Release has been closed",
    ) -> dict[str, Any]:
        """Close a release record. Note: on this instance this returns 403 'User does not
        have this permission' for the standard technician role — closing releases may
        require an elevated permission not granted by default."""
        async with get_client() as c:
            return await c.put(
                f"/releases/{release_id}/_close", {"status": "completed", "comment": comment}
            )

    @app.tool()
    async def add_release_note(
        release_id: Annotated[str, "Release ID"],
        note_text: Annotated[str, "Note content. Raw HTML is supported; do not wrap in CDATA."],
    ) -> dict[str, Any]:
        """Add a note to a release record."""
        async with get_client() as c:
            return await c.post(
                f"/releases/{release_id}/notes", {"note": {"description": strip_cdata(note_text)}}
            )

    @app.tool()
    async def list_release_notes(
        release_id: Annotated[str, "Release ID"],
    ) -> dict[str, Any]:
        """List all notes on a release record."""
        async with get_client() as c:
            return await c.get(f"/releases/{release_id}/notes")

    @app.tool()
    async def update_release_note(
        release_id: Annotated[str, "Release ID"],
        note_id: Annotated[str, "Note ID"],
        note_text: Annotated[str, "New note content. Raw HTML is supported; do not wrap in CDATA."],
    ) -> dict[str, Any]:
        """Edit an existing note on a release record."""
        async with get_client() as c:
            return await c.put(
                f"/releases/{release_id}/notes/{note_id}",
                {"note": {"description": strip_cdata(note_text)}},
            )

    @app.tool()
    async def list_release_tasks(
        release_id: Annotated[str, "Release ID"],
    ) -> dict[str, Any]:
        """List all tasks associated with a release record."""
        async with get_client() as c:
            return await c.get(f"/releases/{release_id}/tasks")

    @app.tool()
    async def add_release_task(
        release_id: Annotated[str, "Release ID"],
        title: Annotated[str, "Task title"],
        stage_id: Annotated[
            str, "Release stage ID the task belongs to (e.g. '1' Submission, '2' Planning)"
        ] = "2",
        description: Annotated[str, "Task description"] = "",
        assigned_to: Annotated[str, "Technician login name to assign task"] = "",
    ) -> dict[str, Any]:
        """Add a task to a release record. Note: stage is mandatory on this instance
        (rejected with 'Value not provided' otherwise) — defaults to Planning."""
        task: dict[str, Any] = {"title": title, "stage": {"id": stage_id}}
        if description:
            task["description"] = description
        if assigned_to:
            task["owner"] = {"name": assigned_to}
        async with get_client() as c:
            return await c.post(f"/releases/{release_id}/tasks", {"task": task})

    @app.tool()
    async def list_release_worklogs(
        release_id: Annotated[str, "Release ID"],
    ) -> dict[str, Any]:
        """List all worklog entries for a release record."""
        async with get_client() as c:
            return await c.get(f"/releases/{release_id}/worklogs")

    @app.tool()
    async def add_release_worklog(
        release_id: Annotated[str, "Release ID"],
        description: Annotated[str, "Work performed"],
        technician_email: Annotated[str, "Technician email address (e.g. jsmith@spero.financial)"],
        hours: Annotated[int, "Whole hours spent"] = 0,
        minutes: Annotated[int, "Additional minutes spent (0–59)"] = 0,
    ) -> dict[str, Any]:
        """Add a worklog entry to a release record."""
        worklog: dict[str, Any] = {
            "description": description,
            "time_spent": {"hours": hours, "minutes": minutes},
            "owner": {"email_id": technician_email},
        }
        async with get_client() as c:
            return await c.post(f"/releases/{release_id}/worklogs", {"worklog": worklog})
