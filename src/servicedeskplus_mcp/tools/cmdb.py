"""CMDB / Configuration Item tools for ServiceDesk Plus."""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client


def register(app: FastMCP) -> None:
    @app.tool()
    async def list_configuration_items(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
        ci_type: Annotated[str, "Filter by CI type name"] = "",
    ) -> dict[str, Any]:
        """List CMDB configuration items."""
        list_info: dict[str, Any] = {
            "start_index": (page - 1) * page_size,
            "row_count": page_size,
        }
        if ci_type:
            list_info["search_criteria"] = [
                {"field": "ci_type.name", "condition": "is", "value": ci_type}
            ]
        params = {"input_data": json.dumps({"list_info": list_info})}
        async with get_client() as c:
            return await c.get("/ci", params=params)

    @app.tool()
    async def get_configuration_item(
        ci_id: Annotated[str, "Configuration item ID"],
    ) -> dict[str, Any]:
        """Get a single configuration item by ID."""
        async with get_client() as c:
            return await c.get(f"/ci/{ci_id}")

    @app.tool()
    async def create_configuration_item(
        name: Annotated[str, "CI name"],
        ci_type: Annotated[str, "CI type name"],
        description: Annotated[str, "CI description"] = "",
        state: Annotated[str, "CI state"] = "",
    ) -> dict[str, Any]:
        """Create a new CMDB configuration item."""
        ci: dict[str, Any] = {
            "name": name,
            "ci_type": {"name": ci_type},
        }
        if description:
            ci["description"] = description
        if state:
            ci["state"] = {"name": state}
        async with get_client() as c:
            return await c.post("/ci", {"ci": ci})

    @app.tool()
    async def update_configuration_item(
        ci_id: Annotated[str, "CI ID"],
        name: Annotated[str, "Updated name"] = "",
        description: Annotated[str, "Updated description"] = "",
        state: Annotated[str, "New state name"] = "",
    ) -> dict[str, Any]:
        """Update an existing configuration item."""
        ci: dict[str, Any] = {}
        if name:
            ci["name"] = name
        if description:
            ci["description"] = description
        if state:
            ci["state"] = {"name": state}
        async with get_client() as c:
            return await c.put(f"/ci/{ci_id}", {"ci": ci})

    @app.tool()
    async def list_ci_relationships(
        ci_id: Annotated[str, "Configuration item ID"],
    ) -> dict[str, Any]:
        """List all relationships for a configuration item."""
        async with get_client() as c:
            return await c.get(f"/ci/{ci_id}/relationships")

    @app.tool()
    async def add_ci_relationship(
        ci_id: Annotated[str, "Source CI ID"],
        related_ci_id: Annotated[str, "Related CI ID"],
        relationship_type: Annotated[str, "Relationship type, e.g. 'Depends on'"],
    ) -> dict[str, Any]:
        """Add a relationship between two configuration items."""
        data = {
            "relationship": {
                "relationship_type": {"name": relationship_type},
                "related_ci": {"id": related_ci_id},
            }
        }
        async with get_client() as c:
            return await c.post(f"/ci/{ci_id}/relationships", data)
