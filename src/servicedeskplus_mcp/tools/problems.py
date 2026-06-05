"""Problem management tools for ServiceDesk Plus."""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client


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
        description: Annotated[str, "Problem description"] = "",
        priority: Annotated[str, "Priority name"] = "",
        technician: Annotated[str, "Assigned technician login name"] = "",
    ) -> dict[str, Any]:
        """Create a new problem record."""
        problem: dict[str, Any] = {"title": title}
        if description:
            problem["description"] = description
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
        description: Annotated[str, "Updated description"] = "",
        status: Annotated[str, "New status name"] = "",
        priority: Annotated[str, "New priority name"] = "",
        technician: Annotated[str, "New assigned technician login name"] = "",
    ) -> dict[str, Any]:
        """Update an existing problem record."""
        problem: dict[str, Any] = {}
        if title:
            problem["title"] = title
        if description:
            problem["description"] = description
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
    async def add_problem_note(
        problem_id: Annotated[str, "Problem ID"],
        note_text: Annotated[str, "Note content"],
        is_public: Annotated[bool, "Visible to requester?"] = False,
    ) -> dict[str, Any]:
        """Add a note to a problem record."""
        data = {"note": {"description": note_text, "show_to_requester": is_public}}
        async with get_client() as c:
            return await c.post(f"/problems/{problem_id}/notes", data)
