"""Change management tools for ServiceDesk Plus."""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client


def register(app: FastMCP) -> None:
    @app.tool()
    async def list_changes(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
        status: Annotated[str, "Filter by status name"] = "",
    ) -> dict[str, Any]:
        """List change records with optional filtering."""
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
        description: Annotated[str, "Change description"] = "",
        change_type: Annotated[str, "Change type, e.g. 'Standard', 'Emergency'"] = "",
        priority: Annotated[str, "Priority name"] = "",
        technician: Annotated[str, "Assigned technician login name"] = "",
        scheduled_start: Annotated[str, "Scheduled start time (ISO 8601)"] = "",
        scheduled_end: Annotated[str, "Scheduled end time (ISO 8601)"] = "",
    ) -> dict[str, Any]:
        """Create a new change record."""
        change: dict[str, Any] = {"title": title}
        if description:
            change["description"] = description
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
        description: Annotated[str, "Updated description"] = "",
        status: Annotated[str, "New status name"] = "",
        priority: Annotated[str, "New priority name"] = "",
        technician: Annotated[str, "New assigned technician login name"] = "",
    ) -> dict[str, Any]:
        """Update an existing change record."""
        change: dict[str, Any] = {}
        if title:
            change["title"] = title
        if description:
            change["description"] = description
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
    async def add_change_note(
        change_id: Annotated[str, "Change ID"],
        note_text: Annotated[str, "Note content"],
    ) -> dict[str, Any]:
        """Add a note to a change record."""
        async with get_client() as c:
            return await c.post(f"/changes/{change_id}/notes", {"note": {"description": note_text}})

    @app.tool()
    async def list_change_tasks(
        change_id: Annotated[str, "Change ID"],
    ) -> dict[str, Any]:
        """List all tasks associated with a change record."""
        async with get_client() as c:
            return await c.get(f"/changes/{change_id}/tasks")

    @app.tool()
    async def list_pending_approvals(
        change_id: Annotated[str, "Change ID"],
    ) -> dict[str, Any]:
        """List all pending approvals for a change record."""
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
