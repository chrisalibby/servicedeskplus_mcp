"""Asset and workstation tools for ServiceDesk Plus."""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client
from ._util import resolve_ref


def register(app: FastMCP) -> None:
    @app.tool()
    async def list_assets(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
        asset_type: Annotated[str, "Filter by product type name, e.g. 'Laptop'"] = "",
        state: Annotated[str, "Filter by state, e.g. 'In Use'"] = "",
        missing_product_type: Annotated[
            bool, "Return only assets with no product type set"
        ] = False,
        sort_field: Annotated[str, "Field to sort by, e.g. 'created_time'"] = "",
        sort_order: Annotated[str, "Sort order: 'asc' or 'desc'"] = "",
    ) -> dict[str, Any]:
        """List assets with optional filtering."""
        list_info: dict[str, Any] = {
            "start_index": (page - 1) * page_size,
            "row_count": page_size,
        }
        if sort_field:
            list_info["sort_field"] = sort_field
        if sort_order:
            list_info["sort_order"] = sort_order
        filters: list[dict[str, Any]] = []
        if asset_type:
            filters.append({"field": "product_type.name", "condition": "is", "value": asset_type})
        if state:
            filters.append({"field": "asset_state", "condition": "is", "value": state})
        if missing_product_type:
            filters.append({"field": "product_type", "condition": "is", "values": []})
        if filters:
            list_info["search_criteria"] = filters
        params = {"input_data": json.dumps({"list_info": list_info})}
        async with get_client() as c:
            return await c.get("/assets", params=params)

    @app.tool()
    async def get_asset(
        asset_id: Annotated[str, "Asset ID"],
    ) -> dict[str, Any]:
        """Get a single asset by ID."""
        async with get_client() as c:
            return await c.get(f"/assets/{asset_id}")

    @app.tool()
    async def create_asset(
        name: Annotated[str, "Asset name or tag"],
        product: Annotated[
            str,
            "Product name or numeric ID (e.g. 'HP EliteBook 840 G8'). "
            "Use list_products to browse.",
        ],
        product_type: Annotated[
            str,
            "Product type name or numeric ID (e.g. 'Laptop'). Usually inferred from the "
            "product; use list_product_types to browse.",
        ] = "",
        serial_number: Annotated[str, "Serial number"] = "",
        vendor: Annotated[str, "Vendor/manufacturer name"] = "",
        site: Annotated[str, "Site name"] = "",
        department: Annotated[str, "Department name"] = "",
        assigned_to: Annotated[str, "User login name the asset is assigned to"] = "",
    ) -> dict[str, Any]:
        """Create a new asset record."""
        asset: dict[str, Any] = {"name": name}
        if serial_number:
            asset["serial_number"] = serial_number
        if vendor:
            asset["vendor"] = {"name": vendor}
        if site:
            asset["site"] = {"name": site}
        if department:
            asset["department"] = {"name": department}
        if assigned_to:
            asset["used_by"] = {"name": assigned_to}
        async with get_client() as c:
            ref = await resolve_ref(c, "/products", "products", product)
            if "error" in ref:
                return ref
            asset["product"] = ref
            if product_type:
                pt_ref = await resolve_ref(c, "/product_types", "product_types", product_type)
                if "error" in pt_ref:
                    return pt_ref
                asset["product_type"] = pt_ref
            return await c.post("/assets", {"asset": asset})

    @app.tool()
    async def update_asset(
        asset_id: Annotated[str, "Asset ID"],
        name: Annotated[str, "Updated name"] = "",
        state: Annotated[str, "New asset state"] = "",
        assigned_to: Annotated[str, "New user login name"] = "",
        site: Annotated[str, "New site name"] = "",
        department: Annotated[str, "New department name"] = "",
    ) -> dict[str, Any]:
        """Update an existing asset record."""
        asset: dict[str, Any] = {}
        if name:
            asset["name"] = name
        if state:
            asset["asset_state"] = state
        if assigned_to:
            asset["used_by"] = {"name": assigned_to}
        if site:
            asset["site"] = {"name": site}
        if department:
            asset["department"] = {"name": department}
        async with get_client() as c:
            return await c.put(f"/assets/{asset_id}", {"asset": asset})

    @app.tool()
    async def list_workstations(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List workstation assets."""
        list_info: dict[str, Any] = {
            "start_index": (page - 1) * page_size,
            "row_count": page_size,
        }
        params = {"input_data": json.dumps({"list_info": list_info})}
        async with get_client() as c:
            return await c.get("/workstations", params=params)

    @app.tool()
    async def get_workstation(
        workstation_id: Annotated[str, "Workstation ID"],
    ) -> dict[str, Any]:
        """Get a single workstation record by ID."""
        async with get_client() as c:
            return await c.get(f"/workstations/{workstation_id}")
