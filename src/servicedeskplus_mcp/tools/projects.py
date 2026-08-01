"""Project management tools for ServiceDesk Plus."""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client
from ._util import strip_cdata


def register(app: FastMCP) -> None:
    @app.tool()
    async def list_projects(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
        status: Annotated[str, "Filter by status name"] = "",
        sort_field: Annotated[str, "Field to sort by"] = "created_time",
        sort_order: Annotated[str, "Sort order: 'asc' or 'desc'"] = "desc",
    ) -> dict[str, Any]:
        """List project records with optional filtering. Sorted newest-first by default."""
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
            return await c.get("/projects", params=params)

    @app.tool()
    async def get_project(
        project_id: Annotated[str, "Project record ID"],
    ) -> dict[str, Any]:
        """Get a single project record by ID."""
        async with get_client() as c:
            return await c.get(f"/projects/{project_id}")

    @app.tool()
    async def create_project(
        title: Annotated[str, "Project title"],
        description: Annotated[
            str, "Project description. Raw HTML is supported; do not wrap in CDATA."
        ] = "",
        priority: Annotated[str, "Priority name"] = "",
        project_type: Annotated[str, "Project type, e.g. 'Departmental'"] = "",
        scheduled_start: Annotated[str, "Scheduled start time (ISO 8601)"] = "",
        scheduled_end: Annotated[str, "Scheduled end time (ISO 8601)"] = "",
    ) -> dict[str, Any]:
        """Create a new project record. Only title is mandatory — SDP assigns the default
        template, status, and creator as Project Admin automatically."""
        project: dict[str, Any] = {"title": title}
        if description:
            project["description"] = strip_cdata(description)
        if priority:
            project["priority"] = {"name": priority}
        if project_type:
            project["type"] = {"name": project_type}
        if scheduled_start:
            project["scheduled_start_time"] = {"value": scheduled_start}
        if scheduled_end:
            project["scheduled_end_time"] = {"value": scheduled_end}
        async with get_client() as c:
            return await c.post("/projects", {"project": project})

    @app.tool()
    async def update_project(
        project_id: Annotated[str, "Project ID"],
        title: Annotated[str, "Updated title"] = "",
        description: Annotated[
            str, "Updated description. Raw HTML is supported; do not wrap in CDATA."
        ] = "",
        priority: Annotated[str, "New priority name"] = "",
    ) -> dict[str, Any]:
        """Update an existing project record."""
        project: dict[str, Any] = {}
        if title:
            project["title"] = title
        if description:
            project["description"] = strip_cdata(description)
        if priority:
            project["priority"] = {"name": priority}
        async with get_client() as c:
            return await c.put(f"/projects/{project_id}", {"project": project})

    @app.tool()
    async def delete_project(
        project_id: Annotated[str, "Project ID to delete"],
    ) -> dict[str, Any]:
        """Permanently delete a project record. Note: there is no move_to_trash endpoint
        for projects on this instance (404s) — this is a direct, non-recoverable delete."""
        async with get_client() as c:
            return await c.delete(f"/projects/{project_id}")

    @app.tool()
    async def list_project_milestones(
        project_id: Annotated[str, "Project ID"],
    ) -> dict[str, Any]:
        """List all milestones on a project record."""
        async with get_client() as c:
            return await c.get(f"/projects/{project_id}/milestones")

    @app.tool()
    async def add_project_milestone(
        project_id: Annotated[str, "Project ID"],
        title: Annotated[str, "Milestone title"],
        description: Annotated[str, "Milestone description"] = "",
    ) -> dict[str, Any]:
        """Add a milestone to a project record."""
        milestone: dict[str, Any] = {"title": title}
        if description:
            milestone["description"] = description
        async with get_client() as c:
            return await c.post(f"/projects/{project_id}/milestones", {"milestone": milestone})

    @app.tool()
    async def list_project_tasks(
        project_id: Annotated[str, "Project ID"],
    ) -> dict[str, Any]:
        """List all tasks associated with a project record."""
        async with get_client() as c:
            return await c.get(f"/projects/{project_id}/tasks")

    @app.tool()
    async def add_project_task(
        project_id: Annotated[str, "Project ID"],
        title: Annotated[str, "Task title"],
        description: Annotated[str, "Task description"] = "",
        assigned_to: Annotated[str, "Technician login name to assign task"] = "",
    ) -> dict[str, Any]:
        """Add a task to a project record. Unlike release tasks, stage is not mandatory here."""
        task: dict[str, Any] = {"title": title}
        if description:
            task["description"] = description
        if assigned_to:
            task["owner"] = {"name": assigned_to}
        async with get_client() as c:
            return await c.post(f"/projects/{project_id}/tasks", {"task": task})

    @app.tool()
    async def list_project_members(
        project_id: Annotated[str, "Project ID"],
    ) -> dict[str, Any]:
        """List all members on a project record."""
        async with get_client() as c:
            return await c.get(f"/projects/{project_id}/members")

    @app.tool()
    async def add_project_member(
        project_id: Annotated[str, "Project ID"],
        technician_email: Annotated[str, "Technician email address to add as a member"],
        role: Annotated[
            str, "Member role name, e.g. 'Team Member', 'Project Admin'"
        ] = "Team Member",
    ) -> dict[str, Any]:
        """Add a member to a project record. Note: on this instance `POST
        /projects/{id}/members` with `user.email_id` is broken — it ignores the value
        entirely and always adds the same unrelated technician. This tool works around
        that by resolving the email to a display name via `/users` and submitting
        `user.name` instead, then verifying the member SDP actually added matches the
        requested email. If SDP still adds the wrong person (happens when two accounts
        share a display name), the wrongly-added member is automatically removed and an
        error is returned instead of silently leaving the wrong person on the project."""
        async with get_client() as c:
            lookup = await c.get(
                "/users",
                params={
                    "input_data": json.dumps(
                        {
                            "list_info": {
                                "row_count": 5,
                                "search_criteria": [
                                    {
                                        "field": "email_id",
                                        "condition": "is",
                                        "value": technician_email,
                                    }
                                ],
                            }
                        }
                    )
                },
            )
            if "error" in lookup:
                return {"error": f"User lookup failed: {lookup['error']}"}
            users = lookup.get("users", [])
            if len(users) != 1:
                return {
                    "error": f"Could not uniquely resolve '{technician_email}' to a user "
                    f"(found {len(users)} matches) — refusing to guess to avoid adding "
                    "the wrong person."
                }
            display_name = users[0].get("linked_instance", {}).get("name") or users[0].get(
                "name"
            )
            if not display_name:
                return {"error": f"User record for '{technician_email}' has no display name"}
            member = {"user": {"name": display_name}, "role": {"name": role}}
            result = await c.post(f"/projects/{project_id}/members", {"member": member})
            if "error" in result:
                return result
            added_user = result.get("member", {}).get("user", {})
            if added_user.get("email_id") != technician_email:
                member_id = result.get("member", {}).get("id")
                if member_id:
                    await c.delete(f"/projects/{project_id}/members/{member_id}")
                return {
                    "error": f"SDP added the wrong person (got '{added_user.get('name')}' "
                    f"<{added_user.get('email_id')}>, requested '{technician_email}') — "
                    "this happens when multiple accounts share a display name on this "
                    "instance. The wrongly-added member was removed automatically.",
                    "requested_email": technician_email,
                    "resolved_name": display_name,
                    "wrongly_added": added_user,
                }
            return result

    @app.tool()
    async def remove_project_member(
        project_id: Annotated[str, "Project ID"],
        member_id: Annotated[str, "Member record ID (from list_project_members), not user ID"],
    ) -> dict[str, Any]:
        """Remove a member from a project record."""
        async with get_client() as c:
            return await c.delete(f"/projects/{project_id}/members/{member_id}")

    @app.tool()
    async def list_project_comments(
        project_id: Annotated[str, "Project ID"],
    ) -> dict[str, Any]:
        """List all comments on a project record."""
        async with get_client() as c:
            return await c.get(f"/projects/{project_id}/comments")

    @app.tool()
    async def add_project_comment(
        project_id: Annotated[str, "Project ID"],
        comment_text: Annotated[
            str, "Comment content. Raw HTML is supported; do not wrap in CDATA."
        ],
    ) -> dict[str, Any]:
        """Add a comment to a project record. Note: the field is 'content', not
        'description' — 'description' is rejected with 'Extra key found in JSON'."""
        async with get_client() as c:
            return await c.post(
                f"/projects/{project_id}/comments",
                {"comment": {"content": strip_cdata(comment_text)}},
            )
