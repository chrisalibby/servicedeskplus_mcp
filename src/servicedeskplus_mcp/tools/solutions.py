"""Knowledge base / solutions tools for ServiceDesk Plus."""

import json
from pathlib import Path
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client
from ._util import strip_cdata


def register(app: FastMCP) -> None:
    @app.tool()
    async def search_solutions(
        query: Annotated[str, "Search keyword or phrase"],
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """Search the knowledge base for solutions matching a query."""
        list_info: dict[str, Any] = {
            "start_index": (page - 1) * page_size,
            "row_count": page_size,
            "search_criteria": [{"field": "title", "condition": "contains", "value": query}],
        }
        params = {"input_data": json.dumps({"list_info": list_info})}
        async with get_client() as c:
            return await c.get("/solutions", params=params)

    @app.tool()
    async def get_solution(
        solution_id: Annotated[str, "Solution/article ID"],
    ) -> dict[str, Any]:
        """Get a single knowledge base solution by ID."""
        async with get_client() as c:
            return await c.get(f"/solutions/{solution_id}")

    @app.tool()
    async def create_solution(
        title: Annotated[str, "Solution title"],
        description: Annotated[str, "Solution content / resolution steps"],
        topic: Annotated[
            str, "Topic or category name — mandatory on this instance (rejected with "
            "'Value not provided' otherwise)"
        ],
        keywords: Annotated[str, "Comma-separated keywords for search"] = "",
    ) -> dict[str, Any]:
        """Create a new knowledge base solution article. topic is mandatory on this instance."""
        solution: dict[str, Any] = {
            "title": title,
            "description": strip_cdata(description),
            "topic": {"name": topic},
        }
        if keywords:
            solution["keywords"] = keywords
        async with get_client() as c:
            return await c.post("/solutions", {"solution": solution})

    @app.tool()
    async def update_solution(
        solution_id: Annotated[str, "Solution/article ID"],
        title: Annotated[str, "Updated title"] = "",
        description: Annotated[
            str, "Updated content. Raw HTML is supported; do not wrap in CDATA."
        ] = "",
        topic: Annotated[str, "Topic or category name"] = "",
        keywords: Annotated[str, "Comma-separated keywords for search"] = "",
        approval_status: Annotated[
            str,
            "Approve or reject the solution: 'Approved' or 'UnApproved'. There is no separate "
            "approve/reject action endpoint on this instance — set it here.",
        ] = "",
    ) -> dict[str, Any]:
        """Update an existing knowledge base solution article, including approving/rejecting it."""
        solution: dict[str, Any] = {}
        if title:
            solution["title"] = title
        if description:
            solution["description"] = strip_cdata(description)
        if topic:
            solution["topic"] = {"name": topic}
        if keywords:
            solution["keywords"] = keywords
        if approval_status:
            solution["approval_status"] = {"name": approval_status}
        async with get_client() as c:
            return await c.put(f"/solutions/{solution_id}", {"solution": solution})

    @app.tool()
    async def delete_solution(
        solution_id: Annotated[str, "Solution/article ID to delete"],
    ) -> dict[str, Any]:
        """Delete a knowledge base solution article. Unlike requests, this instance has no
        working move-to-trash sub-route for solutions — a direct DELETE consistently returns
        'Not in trash', so deletion may require moving the article to trash from the SDP UI
        first. Confirm the result before relying on this in automation."""
        async with get_client() as c:
            return await c.delete(f"/solutions/{solution_id}")

    @app.tool()
    async def add_solution_attachment(
        solution_id: Annotated[str, "Solution/article ID"],
        file_path: Annotated[str, "Local path to the file to upload"],
        description: Annotated[str, "Optional description for the attachment"] = "",
    ) -> dict[str, Any]:
        """Upload a local file as an attachment on a knowledge base solution."""
        path = Path(file_path)
        content = path.read_bytes()
        files = {"input_file": (path.name, content, "application/octet-stream")}
        params = {"description": description} if description else None
        async with get_client() as c:
            return await c.post_multipart(f"/solutions/{solution_id}/upload", files, params)

    @app.tool()
    async def list_solution_topics(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List all knowledge base topics/categories."""
        list_info: dict[str, Any] = {
            "start_index": (page - 1) * page_size,
            "row_count": page_size,
        }
        params = {"input_data": json.dumps({"list_info": list_info})}
        async with get_client() as c:
            return await c.get("/topics", params=params)

    @app.tool()
    async def create_solution_topic(
        name: Annotated[str, "Topic/category name"],
        parent_topic_id: Annotated[str, "Parent topic ID, to create a sub-topic"] = "",
    ) -> dict[str, Any]:
        """Create a new knowledge base topic/category."""
        topic: dict[str, Any] = {"name": name}
        if parent_topic_id:
            topic["parent"] = {"id": parent_topic_id}
        async with get_client() as c:
            return await c.post("/topics", {"topic": topic})
