"""Service request tools for ServiceDesk Plus."""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client


def register(app: FastMCP) -> None:
    @app.tool()
    async def list_requests(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
        status: Annotated[str, "Filter by status name, e.g. 'Open'"] = "",
        technician: Annotated[str, "Filter by technician login name"] = "",
    ) -> dict[str, Any]:
        """List service requests with optional filtering."""
        list_info: dict[str, Any] = {
            "start_index": (page - 1) * page_size,
            "row_count": page_size,
        }
        filters: list[dict[str, str]] = []
        if status:
            filters.append({"field": "status.name", "condition": "is", "value": status})
        if technician:
            filters.append({"field": "technician.name", "condition": "is", "value": technician})
        if filters:
            list_info["search_criteria"] = filters
        params = {"input_data": json.dumps({"list_info": list_info})}
        async with get_client() as c:
            return await c.get("/requests", params=params)

    @app.tool()
    async def get_request(
        request_id: Annotated[str, "ServiceDesk Plus request ID"],
    ) -> dict[str, Any]:
        """Get a single service request by ID."""
        async with get_client() as c:
            return await c.get(f"/requests/{request_id}")

    @app.tool()
    async def create_request(
        subject: Annotated[str, "Request subject/title"],
        description: Annotated[str, "Detailed description"] = "",
        requester_name: Annotated[str, "Requester's login name or email"] = "",
        category: Annotated[str, "Category name"] = "",
        subcategory: Annotated[str, "Subcategory name (required on some instances)"] = "",
        priority: Annotated[str, "Priority name, e.g. 'High'"] = "",
        urgency: Annotated[str, "Urgency name"] = "",
        site: Annotated[str, "Site name"] = "",
        group: Annotated[str, "Technician group name"] = "",
        technician: Annotated[str, "Assigned technician login name"] = "",
    ) -> dict[str, Any]:
        """Create a new service request."""
        request: dict[str, Any] = {"subject": subject}
        if description:
            request["description"] = description
        if requester_name:
            request["requester"] = {"name": requester_name}
        if category:
            request["category"] = {"name": category}
        if subcategory:
            request["subcategory"] = {"name": subcategory}
        if priority:
            request["priority"] = {"name": priority}
        if urgency:
            request["urgency"] = {"name": urgency}
        if site:
            request["site"] = {"name": site}
        if group:
            request["group"] = {"name": group}
        if technician:
            request["technician"] = {"name": technician}
        async with get_client() as c:
            return await c.post("/requests", {"request": request})

    @app.tool()
    async def update_request(
        request_id: Annotated[str, "Request ID to update"],
        subject: Annotated[str, "Updated subject"] = "",
        description: Annotated[str, "Updated description"] = "",
        status: Annotated[str, "New status name"] = "",
        priority: Annotated[str, "New priority name"] = "",
        category: Annotated[str, "New category name"] = "",
        subcategory: Annotated[str, "New subcategory name"] = "",
        technician: Annotated[str, "New assigned technician login name"] = "",
        group: Annotated[str, "New group name"] = "",
    ) -> dict[str, Any]:
        """Update fields on an existing service request."""
        request: dict[str, Any] = {}
        if subject:
            request["subject"] = subject
        if description:
            request["description"] = description
        if status:
            request["status"] = {"name": status}
        if priority:
            request["priority"] = {"name": priority}
        if category:
            request["category"] = {"name": category}
        if subcategory:
            request["subcategory"] = {"name": subcategory}
        if technician:
            request["technician"] = {"name": technician}
        if group:
            request["group"] = {"name": group}
        async with get_client() as c:
            return await c.put(f"/requests/{request_id}", {"request": request})

    @app.tool()
    async def close_request(
        request_id: Annotated[str, "Request ID to close"],
        closure_code: Annotated[str, "Closure code name (optional — omit if not configured)"] = "",
        closure_comments: Annotated[str, "Comments explaining closure"] = "",
    ) -> dict[str, Any]:
        """Close a service request."""
        request: dict[str, Any] = {"status": {"name": "Closed"}}
        if closure_code or closure_comments:
            request["closure_info"] = {
                "closure_code": {"name": closure_code} if closure_code else {},
                "closure_comments": closure_comments,
            }
        async with get_client() as c:
            return await c.put(f"/requests/{request_id}", {"request": request})

    @app.tool()
    async def delete_request(
        request_id: Annotated[str, "Request ID to move to trash"],
    ) -> dict[str, Any]:
        """Move a service request to trash (recoverable from the SDP Trash view)."""
        async with get_client() as c:
            return await c.delete(f"/requests/{request_id}/move_to_trash")

    @app.tool()
    async def assign_request(
        request_id: Annotated[str, "Request ID"],
        technician: Annotated[str, "Technician login name to assign"],
        group: Annotated[str, "Group name to assign"] = "",
    ) -> dict[str, Any]:
        """Assign a request to a technician and optionally a group."""
        request: dict[str, Any] = {"technician": {"name": technician}}
        if group:
            request["group"] = {"name": group}
        async with get_client() as c:
            return await c.put(f"/requests/{request_id}", {"request": request})

    @app.tool()
    async def pickup_request(
        request_id: Annotated[str, "Request ID to pick up (assign to the API key owner)"],
    ) -> dict[str, Any]:
        """Pick up a request — assigns it to the technician who owns the API key."""
        async with get_client() as c:
            return await c.put(f"/requests/{request_id}/pickup", {})

    @app.tool()
    async def add_request_note(
        request_id: Annotated[str, "Request ID"],
        note_text: Annotated[str, "Note content"],
        is_public: Annotated[bool, "Whether the note is visible to the requester"] = False,
    ) -> dict[str, Any]:
        """Add a note to a service request."""
        data = {"note": {"description": note_text, "show_to_requester": is_public}}
        async with get_client() as c:
            return await c.post(f"/requests/{request_id}/notes", data)

    @app.tool()
    async def list_request_notes(
        request_id: Annotated[str, "Request ID"],
    ) -> dict[str, Any]:
        """List all notes on a service request."""
        async with get_client() as c:
            return await c.get(f"/requests/{request_id}/notes")

    @app.tool()
    async def add_request_worklog(
        request_id: Annotated[str, "Request ID"],
        description: Annotated[str, "Work performed"],
        hours: Annotated[float, "Hours spent (decimal)"] = 0.0,
        technician: Annotated[str, "Technician login name"] = "",
    ) -> dict[str, Any]:
        """Add a worklog entry to a service request."""
        worklog: dict[str, Any] = {
            "description": description,
            "time_spent": int(hours * 60),
        }
        if technician:
            worklog["technician"] = {"name": technician}
        async with get_client() as c:
            return await c.post(f"/requests/{request_id}/worklogs", {"worklog": worklog})

    @app.tool()
    async def list_request_worklogs(
        request_id: Annotated[str, "Request ID"],
    ) -> dict[str, Any]:
        """List all worklog entries for a service request."""
        async with get_client() as c:
            return await c.get(f"/requests/{request_id}/worklogs")

    @app.tool()
    async def get_request_resolution(
        request_id: Annotated[str, "Request ID"],
    ) -> dict[str, Any]:
        """Get the resolution details for a service request."""
        async with get_client() as c:
            return await c.get(f"/requests/{request_id}/resolutions")

    @app.tool()
    async def update_request_resolution(
        request_id: Annotated[str, "Request ID"],
        resolution_content: Annotated[str, "Resolution description"],
    ) -> dict[str, Any]:
        """Set or update the resolution on a service request."""
        data = {"resolution": {"content": resolution_content}}
        async with get_client() as c:
            return await c.put(f"/requests/{request_id}/resolutions", data)

    @app.tool()
    async def list_request_tasks(
        request_id: Annotated[str, "Request ID"],
    ) -> dict[str, Any]:
        """List all tasks associated with a service request."""
        async with get_client() as c:
            return await c.get(f"/requests/{request_id}/tasks")

    @app.tool()
    async def add_request_task(
        request_id: Annotated[str, "Request ID"],
        title: Annotated[str, "Task title"],
        description: Annotated[str, "Task description"] = "",
        assigned_to: Annotated[str, "Technician login name to assign task"] = "",
    ) -> dict[str, Any]:
        """Add a task to a service request."""
        task: dict[str, Any] = {"title": title}
        if description:
            task["description"] = description
        if assigned_to:
            task["owner"] = {"name": assigned_to}
        async with get_client() as c:
            return await c.post(f"/requests/{request_id}/tasks", {"task": task})
