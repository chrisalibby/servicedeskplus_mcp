"""Service request tools for ServiceDesk Plus."""

import base64
import json
from pathlib import Path
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import SDPClient, get_client
from ._util import date_to_epoch_ms, normalize_id, resolve_ref, strip_cdata


async def _technician_ref(client: SDPClient, technician: str) -> dict[str, Any]:
    if "@" not in technician:
        return {"name": technician}
    return await resolve_ref(
        client, "/technicians", "technicians", technician, name_field="email_id"
    )


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
        category: Annotated[
            str, "Filter by category name. Cannot combine with date filters."
        ] = "",
        subcategory: Annotated[
            str, "Filter by subcategory name. Cannot combine with date filters."
        ] = "",
        item: Annotated[
            str, "Filter by item name (third tier). Cannot combine with date filters."
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
        if category:
            filters.append({"field": "category.name", "condition": "is", "value": category})
        if subcategory:
            filters.append({"field": "subcategory.name", "condition": "is", "value": subcategory})
        if item:
            filters.append({"field": "item.name", "condition": "is", "value": item})
        if opened_after:
            ms = date_to_epoch_ms(opened_after)
            filters.append({"field": "created_time", "condition": "gt", "value": ms})
        if opened_before:
            ms = date_to_epoch_ms(opened_before)
            filters.append({"field": "created_time", "condition": "lt", "value": ms})
        if due_before:
            ms = date_to_epoch_ms(due_before)
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
            "Assigned technician display name (e.g. 'Jane Smith') or email "
            "(resolved to an ID via the technician list)",
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
        async with get_client() as c:
            if technician:
                tech = await _technician_ref(c, technician)
                if "error" in tech:
                    return tech
                request["technician"] = tech
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
            "New assigned technician display name (e.g. 'Jane Smith') or email (resolved to "
            "an ID via the technician list). Assignment fails if category/subcategory are "
            "unset — set them in the same call.",
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
        if group:
            request["group"] = {"name": group}
        async with get_client() as c:
            if technician:
                tech = await _technician_ref(c, technician)
                if "error" in tech:
                    return tech
                request["technician"] = tech
            return await c.put(f"/requests/{normalize_id(request_id)}", {"request": request})

    @app.tool()
    async def close_request(
        request_id: Annotated[str, "Request ID to close"],
        closure_code: Annotated[str, "Closure code name (optional — omit if not configured)"] = "",
        closure_comments: Annotated[
            str,
            "Comments explaining closure (max 250 characters on this instance — "
            "put longer detail in a note via add_request_note)",
        ] = "",
    ) -> dict[str, Any]:
        """Close a service request."""
        if len(closure_comments) > 250:
            return {
                "error": f"closure_comments is {len(closure_comments)} characters; this "
                "instance rejects closure comments over ~250 characters. Shorten the "
                "comment and add the full detail as a note via add_request_note instead."
            }
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
    async def merge_requests(
        request_id: Annotated[str, "Parent request ID that other requests will be merged into"],
        merge_request_ids: Annotated[
            list[str], "IDs of the requests to merge into request_id"
        ],
    ) -> dict[str, Any]:
        """Merge one or more requests into a parent request. Irreversible — merged requests are consumed by the parent and can no longer be fetched with get_request; their description/conversation is copied into the parent."""  # noqa: E501
        rid = normalize_id(request_id)
        merges = [{"id": normalize_id(m)} for m in merge_request_ids]
        async with get_client() as c:
            return await c.put(f"/requests/{rid}/merge_requests", {"merge_requests": merges})

    @app.tool()
    async def get_request_summary(
        request_id: Annotated[str, "Request ID"],
    ) -> dict[str, Any]:
        """Get summary counts for a request: tasks, notes, purchase orders, checklists, and linked requests."""  # noqa: E501
        async with get_client() as c:
            return await c.get(f"/requests/{normalize_id(request_id)}/summary")

    @app.tool()
    async def associate_problem(
        request_id: Annotated[str, "Request ID"],
        problem_id: Annotated[str, "Problem ID to associate with the request"],
    ) -> dict[str, Any]:
        """Associate a problem with a request."""
        rid = normalize_id(request_id)
        pid = normalize_id(problem_id)
        data = {"request_problem_association": {"problem": {"id": pid}}}
        async with get_client() as c:
            return await c.post(f"/requests/{rid}/problem", data)

    @app.tool()
    async def dissociate_problem(
        request_id: Annotated[str, "Request ID"],
        problem_id: Annotated[str, "Problem ID currently associated with the request"],
    ) -> dict[str, Any]:
        """Remove a problem association from a request."""
        rid = normalize_id(request_id)
        pid = normalize_id(problem_id)
        data = {"request_problem_association": {"problem": {"id": pid}}}
        async with get_client() as c:
            return await c.delete(f"/requests/{rid}/problem", data)

    @app.tool()
    async def associate_change(
        request_id: Annotated[str, "Request ID"],
        change_id: Annotated[str, "Change ID to associate with the request"],
        association_type: Annotated[
            str,
            "'initiated' if the request initiated the change, 'caused_by' if the "
            "change caused the request",
        ],
    ) -> dict[str, Any]:
        """Associate a change with a request, either as initiated by the request or as the cause of the request."""  # noqa: E501
        rid = normalize_id(request_id)
        cid = normalize_id(change_id)
        if association_type not in ("initiated", "caused_by"):
            return {"error": "association_type must be 'initiated' or 'caused_by'"}
        key = (
            "request_initiated_change"
            if association_type == "initiated"
            else "request_caused_by_change"
        )
        data = {key: {"change": {"id": cid}}}
        async with get_client() as c:
            return await c.post(f"/requests/{rid}/{key}", data)

    @app.tool()
    async def dissociate_change(
        request_id: Annotated[str, "Request ID"],
        change_id: Annotated[str, "Change ID currently associated with the request"],
        association_type: Annotated[
            str,
            "'initiated' if the request initiated the change, 'caused_by' if the "
            "change caused the request",
        ],
    ) -> dict[str, Any]:
        """Remove a change association from a request."""
        rid = normalize_id(request_id)
        cid = normalize_id(change_id)
        if association_type not in ("initiated", "caused_by"):
            return {"error": "association_type must be 'initiated' or 'caused_by'"}
        key = (
            "request_initiated_change"
            if association_type == "initiated"
            else "request_caused_by_change"
        )
        data = {key: {"change": {"id": cid}}}
        async with get_client() as c:
            return await c.delete(f"/requests/{rid}/{key}", data)

    @app.tool()
    async def assign_request(
        request_id: Annotated[str, "Request ID"],
        technician: Annotated[
            str,
            "Technician display name to assign (e.g. 'Jane Smith') or email "
            "(resolved to an ID via the technician list)",
        ],
        group: Annotated[str, "Group name to assign"] = "",
    ) -> dict[str, Any]:
        """Assign a request to a technician and optionally a group. Fails if the request has no category/subcategory — use update_request to set them together with the technician."""  # noqa: E501
        request: dict[str, Any] = {}
        if group:
            request["group"] = {"name": group}
        async with get_client() as c:
            tech = await _technician_ref(c, technician)
            if "error" in tech:
                return tech
            request["technician"] = tech
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
    async def update_request_note(
        request_id: Annotated[str, "Request ID"],
        note_id: Annotated[str, "Note ID"],
        note_text: Annotated[str, "New note content. Raw HTML is supported; do not wrap in CDATA."],
    ) -> dict[str, Any]:
        """Edit an existing note on a service request."""
        rid = normalize_id(request_id)
        data = {"note": {"description": strip_cdata(note_text)}}
        async with get_client() as c:
            return await c.put(f"/requests/{rid}/notes/{note_id}", data)

    @app.tool()
    async def get_request_note(
        request_id: Annotated[str, "Request ID"],
        note_id: Annotated[str, "Note ID"],
    ) -> dict[str, Any]:
        """Get a single note on a service request."""
        rid = normalize_id(request_id)
        async with get_client() as c:
            return await c.get(f"/requests/{rid}/notes/{note_id}")

    @app.tool()
    async def delete_request_note(
        request_id: Annotated[str, "Request ID"],
        note_id: Annotated[str, "Note ID"],
    ) -> dict[str, Any]:
        """Delete a note from a service request. This is a permanent delete."""
        rid = normalize_id(request_id)
        async with get_client() as c:
            return await c.delete(f"/requests/{rid}/notes/{note_id}")

    @app.tool()
    async def add_request_worklog(
        request_id: Annotated[str, "Request ID"],
        description: Annotated[str, "Work performed"],
        technician_email: Annotated[str, "Technician email address (e.g. jsmith@example.com)"],
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
    async def update_request_worklog(
        request_id: Annotated[str, "Request ID"],
        worklog_id: Annotated[str, "Worklog ID"],
        description: Annotated[str, "Updated work performed"] = "",
        hours: Annotated[int, "Updated whole hours spent (omit to leave unchanged)"] = -1,
        minutes: Annotated[int, "Updated additional minutes spent (0–59)"] = -1,
    ) -> dict[str, Any]:
        """Edit an existing worklog entry on a service request. Shape verified live against
        problems/changes worklogs (identical sub-resource); requests-side PUT is unverified
        on this instance since add_request_worklog (POST) itself is broken here."""
        worklog: dict[str, Any] = {}
        if description:
            worklog["description"] = description
        if hours >= 0 or minutes >= 0:
            worklog["time_spent"] = {
                "hours": hours if hours >= 0 else 0,
                "minutes": minutes if minutes >= 0 else 0,
            }
        rid = normalize_id(request_id)
        async with get_client() as c:
            return await c.put(f"/requests/{rid}/worklogs/{worklog_id}", {"worklog": worklog})

    @app.tool()
    async def delete_request_worklog(
        request_id: Annotated[str, "Request ID"],
        worklog_id: Annotated[str, "Worklog ID"],
    ) -> dict[str, Any]:
        """Delete a worklog entry from a service request. Permanent delete. Shape verified
        live against problems/changes worklogs; requests-side DELETE is unverified on this
        instance since add_request_worklog (POST) itself is broken here."""
        rid = normalize_id(request_id)
        async with get_client() as c:
            return await c.delete(f"/requests/{rid}/worklogs/{worklog_id}")

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

    @app.tool()
    async def get_request_task(
        request_id: Annotated[str, "Request ID"],
        task_id: Annotated[str, "Task ID"],
    ) -> dict[str, Any]:
        """Get a single task on a service request."""
        rid = normalize_id(request_id)
        async with get_client() as c:
            return await c.get(f"/requests/{rid}/tasks/{task_id}")

    @app.tool()
    async def update_request_task(
        request_id: Annotated[str, "Request ID"],
        task_id: Annotated[str, "Task ID"],
        title: Annotated[str, "Updated task title"] = "",
        description: Annotated[str, "Updated task description"] = "",
        assigned_to: Annotated[str, "New technician login name to assign task"] = "",
        status: Annotated[str, "New task status name, e.g. 'Open', 'Closed'"] = "",
    ) -> dict[str, Any]:
        """Update a task on a service request."""
        task: dict[str, Any] = {}
        if title:
            task["title"] = title
        if description:
            task["description"] = description
        if assigned_to:
            task["owner"] = {"name": assigned_to}
        if status:
            task["status"] = {"name": status}
        rid = normalize_id(request_id)
        async with get_client() as c:
            return await c.put(f"/requests/{rid}/tasks/{task_id}", {"task": task})

    @app.tool()
    async def delete_request_task(
        request_id: Annotated[str, "Request ID"],
        task_id: Annotated[str, "Task ID"],
    ) -> dict[str, Any]:
        """Delete a task from a service request. This is a permanent delete."""
        rid = normalize_id(request_id)
        async with get_client() as c:
            return await c.delete(f"/requests/{rid}/tasks/{task_id}")

    @app.tool()
    async def list_request_approval_levels(
        request_id: Annotated[str, "Request ID"],
    ) -> dict[str, Any]:
        """List approval levels configured on a service request."""
        async with get_client() as c:
            return await c.get(f"/requests/{normalize_id(request_id)}/approval_levels")

    @app.tool()
    async def add_request_approval_level(
        request_id: Annotated[str, "Request ID"],
        approver: Annotated[
            str,
            "Email or display name of the first approver on this level (SDP requires at "
            "least one approver to create a level — 'Approvers are unavailable' otherwise). "
            "CAUTION: this and send_request_approval_notification can email the named "
            "person — use only your own technician account for testing.",
        ],
    ) -> dict[str, Any]:
        """Add an approval level to a service request with an initial approver."""
        rid = normalize_id(request_id)
        ref = {"email_id": approver} if "@" in approver else {"name": approver}
        data = {"approval_level": {"approvals": [{"approver": ref}]}}
        async with get_client() as c:
            return await c.post(f"/requests/{rid}/approval_levels", data)

    @app.tool()
    async def list_request_approvals(
        request_id: Annotated[str, "Request ID"],
        level_id: Annotated[str, "Approval level ID (from list_request_approval_levels)"],
    ) -> dict[str, Any]:
        """List approvers/approvals for a specific approval level on a service request."""
        rid = normalize_id(request_id)
        async with get_client() as c:
            return await c.get(f"/requests/{rid}/approval_levels/{level_id}/approvals")

    @app.tool()
    async def add_request_approver(
        request_id: Annotated[str, "Request ID"],
        level_id: Annotated[str, "Approval level ID"],
        approver: Annotated[
            str,
            "Email or display name of the approver to add. CAUTION: sends a real email "
            "once send_request_approval_notification is called — use only your own "
            "technician account for testing.",
        ],
        comments: Annotated[str, "Optional comments"] = "",
    ) -> dict[str, Any]:
        """Add an additional approver to an existing approval level on a service request."""
        rid = normalize_id(request_id)
        ref = {"email_id": approver} if "@" in approver else {"name": approver}
        approval: dict[str, Any] = {"approver": ref}
        if comments:
            approval["comments"] = comments
        async with get_client() as c:
            return await c.post(
                f"/requests/{rid}/approval_levels/{level_id}/approvals", {"approval": approval}
            )

    @app.tool()
    async def send_request_approval_notification(
        request_id: Annotated[str, "Request ID"],
        level_id: Annotated[str, "Approval level ID"],
        approval_id: Annotated[str, "Approval ID (from list_request_approvals)"],
    ) -> dict[str, Any]:
        """Send the approval-request notification email to an approver. Required before
        approve_request/reject_request will succeed — SDP rejects those with 'Recommendation
        mail is not yet sent' until this has run. CAUTION: sends a real email to whoever is
        set as the approver — confirm the approver is correct before calling this."""
        rid = normalize_id(request_id)
        async with get_client() as c:
            content = await c.get(
                f"/requests/{rid}/approval_levels/{level_id}/approvals/get_notification_content"
            )
            if "error" in content:
                return content
            notification = content.get("notification", {})
            data = {"approval": {"notification": notification}}
            return await c.put(
                f"/requests/{rid}/approval_levels/{level_id}/approvals/send_notification"
                f"?ids={approval_id}",
                data,
            )

    @app.tool()
    async def approve_request(
        request_id: Annotated[str, "Request ID"],
        level_id: Annotated[str, "Approval level ID"],
        approval_id: Annotated[str, "Approval ID"],
        comments: Annotated[str, "Approval comments"] = "",
    ) -> dict[str, Any]:
        """Approve a pending approval on a service request. The approval notification must
        have been sent first via send_request_approval_notification."""
        rid = normalize_id(request_id)
        data: dict[str, Any] = {"approval": {"comments": comments} if comments else {}}
        async with get_client() as c:
            return await c.put(
                f"/requests/{rid}/approval_levels/{level_id}/approvals/{approval_id}/_approve",
                data,
            )

    @app.tool()
    async def reject_request(
        request_id: Annotated[str, "Request ID"],
        level_id: Annotated[str, "Approval level ID"],
        approval_id: Annotated[str, "Approval ID"],
        comments: Annotated[str, "Rejection reason"] = "",
    ) -> dict[str, Any]:
        """Reject a pending approval on a service request. The approval notification must
        have been sent first via send_request_approval_notification."""
        rid = normalize_id(request_id)
        data: dict[str, Any] = {"approval": {"comments": comments} if comments else {}}
        async with get_client() as c:
            return await c.put(
                f"/requests/{rid}/approval_levels/{level_id}/approvals/{approval_id}/_reject",
                data,
            )

    @app.tool()
    async def list_request_attachments(
        request_id: Annotated[str, "Request ID"],
    ) -> dict[str, Any]:
        """List attachments on a service request, including each attachment's ID, name, content type, and size."""  # noqa: E501
        async with get_client() as c:
            return await c.get(f"/requests/{normalize_id(request_id)}/attachments")

    @app.tool()
    async def get_request_attachment_content(
        request_id: Annotated[str, "Request ID"],
        attachment_id: Annotated[str, "Attachment ID (from list_request_attachments)"],
        save_to_path: Annotated[
            str,
            "If set, write the file to this local path and omit base64 content from the "
            "response (returns 'saved_to' instead). Leave empty to get base64 content inline.",
        ] = "",
    ) -> dict[str, Any]:
        """Download an attachment's raw content from a service request."""
        rid = normalize_id(request_id)
        async with get_client() as c:
            result = await c.get_binary(f"/requests/{rid}/attachments/{attachment_id}/_download")
            if "error" in result:
                return result
            content: bytes = result["content"]
            content_type: str = result["content_type"]
            if save_to_path:
                Path(save_to_path).write_bytes(content)
                return {
                    "saved_to": save_to_path,
                    "content_type": content_type,
                    "size": len(content),
                }
            return {
                "content_type": content_type,
                "size": len(content),
                "content_base64": base64.b64encode(content).decode("ascii"),
            }

    @app.tool()
    async def add_request_attachment(
        request_id: Annotated[str, "Request ID"],
        file_path: Annotated[str, "Local path to the file to upload"],
        description: Annotated[str, "Optional description for the attachment"] = "",
    ) -> dict[str, Any]:
        """Upload a local file as an attachment on a service request."""
        rid = normalize_id(request_id)
        path = Path(file_path)
        content = path.read_bytes()
        files = {"input_file": (path.name, content, "application/octet-stream")}
        params = {"description": description} if description else None
        async with get_client() as c:
            return await c.post_multipart(f"/requests/{rid}/upload", files, params)
