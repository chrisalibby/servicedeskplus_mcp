"""Knowledge base / solutions tools for ServiceDesk Plus."""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client


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
        topic: Annotated[str, "Topic or category name"] = "",
        keywords: Annotated[str, "Comma-separated keywords for search"] = "",
    ) -> dict[str, Any]:
        """Create a new knowledge base solution article."""
        solution: dict[str, Any] = {"title": title, "description": description}
        if topic:
            solution["topic"] = {"name": topic}
        if keywords:
            solution["keywords"] = keywords
        async with get_client() as c:
            return await c.post("/solutions", {"solution": solution})

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
