"""Change management tools for ServiceDesk Plus."""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client
from ._util import normalize_id, strip_cdata


def register(app: FastMCP) -> None:
    @app.tool()
    async def list_changes(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
        status: Annotated[str, "Filter by status name"] = "",
        sort_field: Annotated[str, "Field to sort by"] = "created_time",
        sort_order: Annotated[str, "Sort order: 'asc' or 'desc'"] = "desc",
    ) -> dict[str, Any]:
        """List change records with optional filtering. Sorted newest-first by default."""
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
            return await c.get("/changes", params=params)

    @app.tool()
    async def get_change(
        change_id: Annotated[str, "Change record ID"],
    ) -> dict[str, Any]:
        """Get a single change record by ID."""
        async with get_client() as c:
            return await c.get(f"/changes/{change_id}")

    @app.tool()
    async def create_change(
        title: Annotated[str, "Change title"],
        description: Annotated[
            str, "Change description. Raw HTML is supported; do not wrap in CDATA."
        ] = "",
        change_type: Annotated[str, "Change type, e.g. 'Standard', 'Emergency'"] = "",
        priority: Annotated[str, "Priority name"] = "",
        technician: Annotated[str, "Assigned technician login name"] = "",
        scheduled_start: Annotated[str, "Scheduled start time (ISO 8601)"] = "",
        scheduled_end: Annotated[str, "Scheduled end time (ISO 8601)"] = "",
    ) -> dict[str, Any]:
        """Create a new change record."""
        change: dict[str, Any] = {"title": title}
        if description:
            change["description"] = strip_cdata(description)
        if change_type:
            change["change_type"] = {"name": change_type}
        if priority:
            change["priority"] = {"name": priority}
        if technician:
            change["technician"] = {"name": technician}
        if scheduled_start:
            change["scheduled_start_time"] = {"value": scheduled_start}
        if scheduled_end:
            change["scheduled_end_time"] = {"value": scheduled_end}
        async with get_client() as c:
            return await c.post("/changes", {"change": change})

    @app.tool()
    async def update_change(
        change_id: Annotated[str, "Change ID"],
        title: Annotated[str, "Updated title"] = "",
        description: Annotated[
            str, "Updated description. Raw HTML is supported; do not wrap in CDATA."
        ] = "",
        status: Annotated[str, "New status name"] = "",
        priority: Annotated[str, "New priority name"] = "",
        technician: Annotated[str, "New assigned technician login name"] = "",
    ) -> dict[str, Any]:
        """Update an existing change record."""
        change: dict[str, Any] = {}
        if title:
            change["title"] = title
        if description:
            change["description"] = strip_cdata(description)
        if status:
            change["status"] = {"name": status}
        if priority:
            change["priority"] = {"name": priority}
        if technician:
            change["technician"] = {"name": technician}
        async with get_client() as c:
            return await c.put(f"/changes/{change_id}", {"change": change})

    @app.tool()
    async def close_change(
        change_id: Annotated[str, "Change ID to close"],
        closure_comments: Annotated[str, "Closure comments"] = "",
    ) -> dict[str, Any]:
        """Close a change record. Note: requires the change to be in a closeable workflow state."""
        change: dict[str, Any] = {"status": {"name": "Completed"}}
        if closure_comments:
            change["closure_comments"] = closure_comments
        async with get_client() as c:
            return await c.put(f"/changes/{change_id}", {"change": change})

    @app.tool()
    async def delete_change(
        change_id: Annotated[str, "Change ID to move to trash"],
    ) -> dict[str, Any]:
        """Move a change record to trash (recoverable via restore_change). Confirmed live
        2026-08-01 on an existing test change: DELETE /changes/{id}/move_to_trash, paired
        with a successful restore_from_trash — same recoverable pattern as delete_request."""
        cid = normalize_id(change_id)
        async with get_client() as c:
            return await c.delete(f"/changes/{cid}/move_to_trash")

    @app.tool()
    async def restore_change(
        change_id: Annotated[str, "Change ID to restore from trash"],
    ) -> dict[str, Any]:
        """Restore a trashed change record. Confirmed live 2026-08-01: this instance rejects
        any input_data body on this endpoint ("Extra parameter(s) not allowed") — the PUT
        must carry no body at all."""
        cid = normalize_id(change_id)
        async with get_client() as c:
            return await c.put(f"/changes/{cid}/restore_from_trash")

    @app.tool()
    async def copy_change(
        change_id: Annotated[str, "Change ID to copy"],
    ) -> dict[str, Any]:
        """Create a copy of a change record. Unverified live — not exercised in this round
        since POST-adjacent operations on /changes are rate-limited on this instance and a
        copy would need its own cleanup. Implemented per ManageEngine docs: PUT
        /changes/{id}/copy with no body."""
        cid = normalize_id(change_id)
        async with get_client() as c:
            return await c.put(f"/changes/{cid}/copy")

    @app.tool()
    async def add_change_note(
        change_id: Annotated[str, "Change ID"],
        note_text: Annotated[str, "Note content. Raw HTML is supported; do not wrap in CDATA."],
    ) -> dict[str, Any]:
        """Add a note to a change record. Note: show_to_requester is not supported on
        change notes (unlike request notes) — do not pass it."""
        async with get_client() as c:
            return await c.post(
                f"/changes/{change_id}/notes", {"note": {"description": strip_cdata(note_text)}}
            )

    @app.tool()
    async def list_change_notes(
        change_id: Annotated[str, "Change ID"],
    ) -> dict[str, Any]:
        """List all notes on a change record."""
        async with get_client() as c:
            return await c.get(f"/changes/{change_id}/notes")

    @app.tool()
    async def update_change_note(
        change_id: Annotated[str, "Change ID"],
        note_id: Annotated[str, "Note ID"],
        note_text: Annotated[str, "New note content. Raw HTML is supported; do not wrap in CDATA."],
    ) -> dict[str, Any]:
        """Edit an existing note on a change record."""
        async with get_client() as c:
            return await c.put(
                f"/changes/{change_id}/notes/{note_id}",
                {"note": {"description": strip_cdata(note_text)}},
            )

    @app.tool()
    async def get_change_note(
        change_id: Annotated[str, "Change ID"],
        note_id: Annotated[str, "Note ID"],
    ) -> dict[str, Any]:
        """Get a single note on a change record."""
        cid = normalize_id(change_id)
        async with get_client() as c:
            return await c.get(f"/changes/{cid}/notes/{note_id}")

    @app.tool()
    async def delete_change_note(
        change_id: Annotated[str, "Change ID"],
        note_id: Annotated[str, "Note ID"],
    ) -> dict[str, Any]:
        """Delete a note from a change record. This is a permanent delete."""
        cid = normalize_id(change_id)
        async with get_client() as c:
            return await c.delete(f"/changes/{cid}/notes/{note_id}")

    @app.tool()
    async def list_change_tasks(
        change_id: Annotated[str, "Change ID"],
    ) -> dict[str, Any]:
        """List all tasks associated with a change record."""
        async with get_client() as c:
            return await c.get(f"/changes/{change_id}/tasks")

    @app.tool()
    async def add_change_task(
        change_id: Annotated[str, "Change ID"],
        title: Annotated[str, "Task title"],
        description: Annotated[str, "Task description"] = "",
        assigned_to: Annotated[str, "Technician login name to assign task"] = "",
    ) -> dict[str, Any]:
        """Add a task to a change record."""
        task: dict[str, Any] = {"title": title}
        if description:
            task["description"] = description
        if assigned_to:
            task["owner"] = {"name": assigned_to}
        async with get_client() as c:
            return await c.post(f"/changes/{change_id}/tasks", {"task": task})

    @app.tool()
    async def get_change_task(
        change_id: Annotated[str, "Change ID"],
        task_id: Annotated[str, "Task ID"],
    ) -> dict[str, Any]:
        """Get a single task on a change record."""
        async with get_client() as c:
            return await c.get(f"/changes/{change_id}/tasks/{task_id}")

    @app.tool()
    async def update_change_task(
        change_id: Annotated[str, "Change ID"],
        task_id: Annotated[str, "Task ID"],
        title: Annotated[str, "Updated task title"] = "",
        description: Annotated[str, "Updated task description"] = "",
        assigned_to: Annotated[str, "New technician login name to assign task"] = "",
        status: Annotated[str, "New task status name, e.g. 'Open', 'Closed'"] = "",
    ) -> dict[str, Any]:
        """Update a task on a change record."""
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
            return await c.put(f"/changes/{change_id}/tasks/{task_id}", {"task": task})

    @app.tool()
    async def delete_change_task(
        change_id: Annotated[str, "Change ID"],
        task_id: Annotated[str, "Task ID"],
    ) -> dict[str, Any]:
        """Delete a task from a change record. This is a permanent delete."""
        async with get_client() as c:
            return await c.delete(f"/changes/{change_id}/tasks/{task_id}")

    @app.tool()
    async def list_change_worklogs(
        change_id: Annotated[str, "Change ID"],
    ) -> dict[str, Any]:
        """List all worklog entries for a change record."""
        async with get_client() as c:
            return await c.get(f"/changes/{change_id}/worklogs")

    @app.tool()
    async def add_change_worklog(
        change_id: Annotated[str, "Change ID"],
        description: Annotated[str, "Work performed"],
        technician_email: Annotated[str, "Technician email address (e.g. jsmith@spero.financial)"],
        hours: Annotated[int, "Whole hours spent"] = 0,
        minutes: Annotated[int, "Additional minutes spent (0–59)"] = 0,
    ) -> dict[str, Any]:
        """Add a worklog entry to a change record."""
        worklog: dict[str, Any] = {
            "description": description,
            "time_spent": {"hours": hours, "minutes": minutes},
            "owner": {"email_id": technician_email},
        }
        async with get_client() as c:
            return await c.post(f"/changes/{change_id}/worklogs", {"worklog": worklog})

    @app.tool()
    async def update_change_worklog(
        change_id: Annotated[str, "Change ID"],
        worklog_id: Annotated[str, "Worklog ID"],
        description: Annotated[str, "Updated work performed"] = "",
        hours: Annotated[int, "Updated whole hours spent (omit to leave unchanged)"] = -1,
        minutes: Annotated[int, "Updated additional minutes spent (0–59)"] = -1,
    ) -> dict[str, Any]:
        """Edit an existing worklog entry on a change record."""
        worklog: dict[str, Any] = {}
        if description:
            worklog["description"] = description
        if hours >= 0 or minutes >= 0:
            worklog["time_spent"] = {
                "hours": hours if hours >= 0 else 0,
                "minutes": minutes if minutes >= 0 else 0,
            }
        async with get_client() as c:
            return await c.put(f"/changes/{change_id}/worklogs/{worklog_id}", {"worklog": worklog})

    @app.tool()
    async def delete_change_worklog(
        change_id: Annotated[str, "Change ID"],
        worklog_id: Annotated[str, "Worklog ID"],
    ) -> dict[str, Any]:
        """Delete a worklog entry from a change record. This is a permanent delete."""
        async with get_client() as c:
            return await c.delete(f"/changes/{change_id}/worklogs/{worklog_id}")

    @app.tool()
    async def list_change_approval_levels(
        change_id: Annotated[str, "Change ID"],
    ) -> dict[str, Any]:
        """List approval levels configured on a change record. Read-only: on this instance
        GET returns 'Internal Error' for changes that have no approval levels configured
        (confirmed on 3 live changes with has_approvals=false in their stage history) —
        unverified whether it works once a level actually exists. Approver/level write
        operations are documented (POST/PUT/DELETE on this same path) but not implemented
        here since they weren't safely verifiable without creating a real change."""
        async with get_client() as c:
            return await c.get(f"/changes/{change_id}/approval_levels")

    @app.tool()
    async def list_pending_approvals(
        change_id: Annotated[str, "Change ID"],
    ) -> dict[str, Any]:
        """List all pending approvals for a change record. NOTE: re-confirmed 2026-08-01
        that GET /changes/{id}/approvals returns 4007 'Invalid URL' on this instance — no
        flat approvals path exists here (change_approvals, approvers, approval variants
        also 404). Use list_change_approval_levels instead; per-level approvals require a
        configured approval level, which this instance's test changes don't have."""
        async with get_client() as c:
            return await c.get(f"/changes/{change_id}/approvals")

    @app.tool()
    async def approve_change(
        change_id: Annotated[str, "Change ID"],
        approval_id: Annotated[str, "Approval record ID"],
        comments: Annotated[str, "Approval comments"] = "",
    ) -> dict[str, Any]:
        """Approve a pending change approval."""
        data: dict[str, Any] = {"approval": {"status": {"name": "Approved"}}}
        if comments:
            data["approval"]["comments"] = comments
        async with get_client() as c:
            return await c.put(f"/changes/{change_id}/approvals/{approval_id}", data)

    @app.tool()
    async def reject_change(
        change_id: Annotated[str, "Change ID"],
        approval_id: Annotated[str, "Approval record ID"],
        comments: Annotated[str, "Rejection reason"] = "",
    ) -> dict[str, Any]:
        """Reject a pending change approval."""
        data: dict[str, Any] = {"approval": {"status": {"name": "Rejected"}}}
        if comments:
            data["approval"]["comments"] = comments
        async with get_client() as c:
            return await c.put(f"/changes/{change_id}/approvals/{approval_id}", data)
