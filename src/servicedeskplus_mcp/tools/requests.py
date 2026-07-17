"""Service request tools for ServiceDesk Plus."""

import json
from datetime import UTC, datetime
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client
from ._util import normalize_id, resolve_ref, strip_cdata


def _date_to_epoch_ms(date_str: str) -> str:
    """Convert YYYY-MM-DD to epoch milliseconds string (UTC midnight)."""
    dt = datetime.fromisoformat(date_str).replace(tzinfo=UTC)
    return str(int(dt.timestamp() * 1000))


def register(app: FastMCP) -> None:
    @app.tool()
    async def list_requests(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
        status: Annotated[
            str, "Filter by status name, e.g. 'Open'. Cannot combine with date filters."
        ] = "",
        technician: Annotated[
            str, "Filter by technician login name. Cannot combine with date filters."
        ] = "",
        opened_after: Annotated[
            str,
            "Return tickets created after this date (YYYY-MM-DD). "
            "Cannot combine with other filters.",
        ] = "",
        opened_before: Annotated[
            str,
            "Return tickets created before this date (YYYY-MM-DD). "
            "Cannot combine with other filters.",
        ] = "",
        due_before: Annotated[
            str,
            "Return tickets due before this date (YYYY-MM-DD). "
            "Cannot combine with other filters.",
        ] = "",
        search: Annotated[
            str,
            "Search request subjects containing this text. Cannot combine with date filters.",
        ] = "",
        sort_field: Annotated[str, "Field to sort by, e.g. 'created_time'"] = "",
        sort_order: Annotated[str, "Sort order: 'asc' or 'desc'"] = "",
    ) -> dict[str, Any]:
        """List service requests with optional filtering. Note: date filters (opened_after, opened_before, due_before) cannot be combined with status, technician, or search filters on this instance."""  # noqa: E501
        list_info: dict[str, Any] = {
            "start_index": (page - 1) * page_size,
            "row_count": page_size,
        }
        if sort_field:
            list_info["sort_field"] = sort_field
        if sort_order:
            list_info["sort_order"] = sort_order
        filters: list[dict[str, str]] = []
        if search:
            filters.append({"field": "subject", "condition": "contains", "value": search})
        if status:
            filters.append({"field": "status.name", "condition": "is", "value": status})
        if technician:
            filters.append({"field": "technician.name", "condition": "is", "value": technician})
        if opened_after:
            ms = _date_to_epoch_ms(opened_after)
            filters.append({"field": "created_time", "condition": "gt", "value": ms})
        if opened_before:
            ms = _date_to_epoch_ms(opened_before)
            filters.append({"field": "created_time", "condition": "lt", "value": ms})
        if due_before:
            ms = _date_to_epoch_ms(due_before)
            filters.append({"field": "due_by_time", "condition": "lt", "value": ms})
        if filters:
            list_info["search_criteria"] = filters
        params = {"input_data": json.dumps({"list_info": list_info})}
        async with get_client() as c:
            return await c.get("/requests", params=params)

    @app.tool()
    async def get_request(
        request_id: Annotated[
            str, "ServiceDesk Plus request ID (prefixes like 'RE-' or '#' are stripped)"
        ],
    ) -> dict[str, Any]:
        """Get a single service request by ID."""
        async with get_client() as c:
            return await c.get(f"/requests/{normalize_id(request_id)}")

    @app.tool()
    async def create_request(
        subject: Annotated[str, "Request subject/title"],
        description: Annotated[
            str, "Detailed description. Raw HTML is supported; do not wrap in CDATA."
        ] = "",
        requester_name: Annotated[str, "Requester's login name or email"] = "",
        category: Annotated[str, "Category name"] = "",
        subcategory: Annotated[str, "Subcategory name (required on some instances)"] = "",
        item: Annotated[str, "Item name (third tier under subcategory)"] = "",
        priority: Annotated[str, "Priority name, e.g. 'High'"] = "",
        urgency: Annotated[
            str,
            "Urgency name or numeric ID (resolved via the urgencies list). NOTE: this "
            "instance rejects urgency on requests in every format (the field is not on the "
            "request form) — leave empty and set priority instead.",
        ] = "",
        site: Annotated[str, "Site name"] = "",
        group: Annotated[str, "Technician group name"] = "",
        technician: Annotated[
            str,
            "Assigned technician display name (e.g. 'Jane Smith'); "
            "email format is not accepted by this instance",
        ] = "",
    ) -> dict[str, Any]:
        """Create a new service request."""
        request: dict[str, Any] = {"subject": subject}
        if description:
            request["description"] = strip_cdata(description)
        if requester_name:
            request["requester"] = {"name": requester_name}
        if category:
            request["category"] = {"name": category}
        if subcategory:
            request["subcategory"] = {"name": subcategory}
        if item:
            request["item"] = {"name": item}
        if priority:
            request["priority"] = {"name": priority}
        if site:
            request["site"] = {"name": site}
        if group:
            request["group"] = {"name": group}
        if technician:
            request["technician"] = {"name": technician}
        async with get_client() as c:
            if urgency:
                ref = await resolve_ref(c, "/urgencies", "urgencies", urgency)
                if "error" in ref:
                    return ref
                request["urgency"] = ref
            return await c.post("/requests", {"request": request})

    @app.tool()
    async def update_request(
        request_id: Annotated[str, "Request ID to update"],
        subject: Annotated[str, "Updated subject"] = "",
        description: Annotated[
            str, "Updated description. Raw HTML is supported; do not wrap in CDATA."
        ] = "",
        status: Annotated[str, "New status name"] = "",
        priority: Annotated[str, "New priority name"] = "",
        category: Annotated[str, "New category name"] = "",
        subcategory: Annotated[
            str,
            "New subcategory name (newly added subcategories may not appear in list results "
            "immediately but work by name here)",
        ] = "",
        item: Annotated[str, "New item name (third tier under subcategory)"] = "",
        technician: Annotated[
            str,
            "New assigned technician display name (e.g. 'Jane Smith'); email format is not "
            "accepted. Assignment fails if category/subcategory are unset — set them in the "
            "same call.",
        ] = "",
        group: Annotated[str, "New group name"] = "",
    ) -> dict[str, Any]:
        """Update fields on an existing service request."""
        request: dict[str, Any] = {}
        if subject:
            request["subject"] = subject
        if description:
            request["description"] = strip_cdata(description)
        if status:
            request["status"] = {"name": status}
        if priority:
            request["priority"] = {"name": priority}
        if category:
            request["category"] = {"name": category}
        if subcategory:
            request["subcategory"] = {"name": subcategory}
        if item:
            request["item"] = {"name": item}
        if technician:
            request["technician"] = {"name": technician}
        if group:
            request["group"] = {"name": group}
        async with get_client() as c:
            return await c.put(f"/requests/{normalize_id(request_id)}", {"request": request})

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
            return await c.put(f"/requests/{normalize_id(request_id)}", {"request": request})

    @app.tool()
    async def delete_request(
        request_id: Annotated[str, "Request ID to move to trash"],
    ) -> dict[str, Any]:
        """Move a service request to trash (recoverable from the SDP Trash view)."""
        async with get_client() as c:
            return await c.delete(f"/requests/{normalize_id(request_id)}/move_to_trash")

    @app.tool()
    async def assign_request(
        request_id: Annotated[str, "Request ID"],
        technician: Annotated[
            str,
            "Technician display name to assign (e.g. 'Jane Smith'); email format is not accepted",
        ],
        group: Annotated[str, "Group name to assign"] = "",
    ) -> dict[str, Any]:
        """Assign a request to a technician and optionally a group. Fails if the request has no category/subcategory — use update_request to set them together with the technician."""  # noqa: E501
        request: dict[str, Any] = {"technician": {"name": technician}}
        if group:
            request["group"] = {"name": group}
        async with get_client() as c:
            return await c.put(f"/requests/{normalize_id(request_id)}", {"request": request})

    @app.tool()
    async def pickup_request(
        request_id: Annotated[str, "Request ID to pick up (assign to the API key owner)"],
    ) -> dict[str, Any]:
        """Pick up a request — assigns it to the technician who owns the API key."""
        async with get_client() as c:
            return await c.put(f"/requests/{normalize_id(request_id)}/pickup", {})

    @app.tool()
    async def add_request_note(
        request_id: Annotated[str, "Request ID"],
        note_text: Annotated[str, "Note content. Raw HTML is supported; do not wrap in CDATA."],
        is_public: Annotated[bool, "Whether the note is visible to the requester"] = False,
    ) -> dict[str, Any]:
        """Add a note to a service request."""
        rid = normalize_id(request_id)
        text = strip_cdata(note_text)
        data = {"note": {"description": text, "show_to_requester": is_public}}
        async with get_client() as c:
            result = await c.post(f"/requests/{rid}/notes", data)
            if not result.get("indeterminate"):
                return result
            verify = await c.get(f"/requests/{rid}/notes")
            if "error" in verify:
                return {**result, "posted": "unknown"}
            notes = verify.get("notes", [])
            posted = any(text in str(n.get("description", "")) for n in notes)
            return {**result, "posted": posted}

    @app.tool()
    async def list_request_notes(
        request_id: Annotated[str, "Request ID"],
    ) -> dict[str, Any]:
        """List all notes on a service request."""
        async with get_client() as c:
            return await c.get(f"/requests/{normalize_id(request_id)}/notes")

    @app.tool()
    async def add_request_worklog(
        request_id: Annotated[str, "Request ID"],
        description: Annotated[str, "Work performed"],
        technician_email: Annotated[str, "Technician email address (e.g. jsmith@spero.financial)"],
        hours: Annotated[int, "Whole hours spent"] = 0,
        minutes: Annotated[int, "Additional minutes spent (0–59)"] = 0,
    ) -> dict[str, Any]:
        """Add a worklog entry to a service request."""
        worklog: dict[str, Any] = {
            "description": description,
            "time_spent": {"hours": hours, "minutes": minutes},
            "owner": {"email_id": technician_email},
        }
        async with get_client() as c:
            return await c.post(
                f"/requests/{normalize_id(request_id)}/worklogs", {"worklog": worklog}
            )

    @app.tool()
    async def list_request_worklogs(
        request_id: Annotated[str, "Request ID"],
    ) -> dict[str, Any]:
        """List all worklog entries for a service request."""
        async with get_client() as c:
            return await c.get(f"/requests/{normalize_id(request_id)}/worklogs")

    @app.tool()
    async def get_request_resolution(
        request_id: Annotated[str, "Request ID"],
    ) -> dict[str, Any]:
        """Get the resolution details for a service request."""
        async with get_client() as c:
            return await c.get(f"/requests/{normalize_id(request_id)}/resolutions")

    @app.tool()
    async def update_request_resolution(
        request_id: Annotated[str, "Request ID"],
        resolution_content: Annotated[
            str, "Resolution description. Raw HTML is supported; do not wrap in CDATA."
        ],
    ) -> dict[str, Any]:
        """Set or update the resolution on a service request."""
        data = {"resolution": {"content": strip_cdata(resolution_content)}}
        async with get_client() as c:
            return await c.put(f"/requests/{normalize_id(request_id)}/resolutions", data)

    @app.tool()
    async def list_request_tasks(
        request_id: Annotated[str, "Request ID"],
    ) -> dict[str, Any]:
        """List all tasks associated with a service request."""
        async with get_client() as c:
            return await c.get(f"/requests/{normalize_id(request_id)}/tasks")

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
            return await c.post(f"/requests/{normalize_id(request_id)}/tasks", {"task": task})
