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
        module_type: Annotated[
            str,
            "Filter by module api_plural_name, e.g. 'cmdb_itservice', 'cmdb_departmentci', "
            "'cmdb_people', 'cmdb_supportgroup', 'cmdb_switchportci'",
        ] = "",
    ) -> dict[str, Any]:
        """List CMDB configuration items. Each item includes a 'module' field identifying its type."""  # noqa: E501
        list_info: dict[str, Any] = {
            "start_index": (page - 1) * page_size,
            "row_count": page_size,
        }
        params = {"input_data": json.dumps({"list_info": list_info})}
        path = f"/{module_type}" if module_type else "/cmdb"
        async with get_client() as c:
            return await c.get(path, params=params)

    @app.tool()
    async def get_configuration_item(
        ci_id: Annotated[str, "Configuration item ID"],
    ) -> dict[str, Any]:
        """Get a single configuration item by ID."""
        async with get_client() as c:
            return await c.get(f"/cmdb/{ci_id}")

    @app.tool()
    async def create_configuration_item(
        module_type: Annotated[
            str,
            "Module api_plural_name, e.g. 'cmdb_itservice', 'cmdb_departmentci', "
            "'cmdb_people', 'cmdb_supportgroup', 'cmdb_switchportci'",
        ],
        name: Annotated[str, "CI name"],
        description: Annotated[str, "CI description"] = "",
        state: Annotated[str, "CI state"] = "",
    ) -> dict[str, Any]:
        """Create a new CMDB configuration item. The module is scoped by module_type — the same
        value used to filter list_configuration_items."""
        ci: dict[str, Any] = {"name": name}
        if description:
            ci["description"] = description
        if state:
            ci["state"] = {"name": state}
        async with get_client() as c:
            return await c.post(f"/{module_type}", {module_type: ci})

    @app.tool()
    async def update_configuration_item(
        ci_id: Annotated[str, "CI ID"],
        module_type: Annotated[
            str,
            "Module api_plural_name the CI belongs to, e.g. 'cmdb_itservice' "
            "(see list_configuration_items' module_type filter)",
        ],
        name: Annotated[str, "Updated name"] = "",
        description: Annotated[str, "Updated description"] = "",
        state: Annotated[str, "New state name"] = "",
    ) -> dict[str, Any]:
        """Update an existing configuration item. module_type must match the CI's own module
        (its 'module.api_plural_name' field from get_configuration_item)."""
        ci: dict[str, Any] = {}
        if name:
            ci["name"] = name
        if description:
            ci["description"] = description
        if state:
            ci["state"] = {"name": state}
        async with get_client() as c:
            return await c.put(f"/{module_type}/{ci_id}", {module_type: ci})

    @app.tool()
    async def delete_configuration_item(
        ci_id: Annotated[str, "CI ID to delete"],
        module_type: Annotated[
            str,
            "Module api_plural_name the CI belongs to, e.g. 'cmdb_itservice' "
            "(see list_configuration_items' module_type filter)",
        ],
    ) -> dict[str, Any]:
        """Permanently delete a configuration item. Unlike delete_request, this is NOT
        recoverable. module_type must match the CI's own module."""
        async with get_client() as c:
            return await c.delete(f"/{module_type}/{ci_id}")

    @app.tool()
    async def list_ci_relationships(
        ci_id: Annotated[str, "Configuration item ID"],
    ) -> dict[str, Any]:
        """List all relationships for a configuration item."""
        async with get_client() as c:
            return await c.get(f"/cmdb/{ci_id}/ci_relationships")

    @app.tool()
    async def add_ci_relationship(
        ci_id: Annotated[str, "Source CI ID"],
        related_ci_id: Annotated[str, "Related CI ID"],
        relationship_type: Annotated[
            str,
            "Relationship type, e.g. 'Depends on'. Currently 400s on this instance on the "
            "'api_name' field whether sent as {\"name\": ...} or {\"api_name\": ...} — a "
            "relationship-type lookup endpoint (not yet implemented) is likely needed to "
            "supply a valid identifier.",
        ],
    ) -> dict[str, Any]:
        """Add a relationship between two configuration items.

        Unverified on this instance: POST to /cmdb/{ci_id}/ci_relationships consistently
        returns a generic 400 on the 'api_name' field regardless of relationship_type shape
        tried ({"name": ...} or {"api_name": ...}). Likely needs a relationship-type lookup
        endpoint (not yet implemented) to supply a valid identifier.
        """
        data = {
            "ci_relationship": {
                "relationship_type": {"name": relationship_type},
                "related_ci": {"id": related_ci_id},
            }
        }
        async with get_client() as c:
            return await c.post(f"/cmdb/{ci_id}/ci_relationships", data)
