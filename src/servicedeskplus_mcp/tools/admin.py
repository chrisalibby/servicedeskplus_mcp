"""Admin / lookup tools for ServiceDesk Plus."""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client


async def _paged_list(
    path: str,
    page: int,
    page_size: int,
    filters: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    list_info: dict[str, Any] = {
        "start_index": (page - 1) * page_size,
        "row_count": page_size,
    }
    if filters:
        list_info["search_criteria"] = filters
    params = {"input_data": json.dumps({"list_info": list_info})}
    async with get_client() as c:
        return await c.get(path, params=params)


def register(app: FastMCP) -> None:
    @app.tool()
    async def list_requesters(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List all requesters (end users)."""
        return await _paged_list("/requesters", page, page_size)

    @app.tool()
    async def get_requester(
        requester_id: Annotated[str, "Requester ID"],
    ) -> dict[str, Any]:
        """Get a single requester by ID."""
        async with get_client() as c:
            return await c.get(f"/requesters/{requester_id}")

    @app.tool()
    async def list_technicians(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List all technicians."""
        return await _paged_list("/technicians", page, page_size)

    @app.tool()
    async def get_technician(
        technician_id: Annotated[str, "Technician ID"],
    ) -> dict[str, Any]:
        """Get a single technician by ID."""
        async with get_client() as c:
            return await c.get(f"/technicians/{technician_id}")

    @app.tool()
    async def list_groups(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List all technician groups."""
        return await _paged_list("/groups", page, page_size)

    @app.tool()
    async def list_sites(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List all sites."""
        return await _paged_list("/sites", page, page_size)

    @app.tool()
    async def list_categories(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List all request categories."""
        return await _paged_list("/categories", page, page_size)

    @app.tool()
    async def list_subcategories(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 100,
    ) -> dict[str, Any]:
        """List all request subcategories (includes parent category name)."""
        return await _paged_list("/subcategories", page, page_size)

    @app.tool()
    async def list_items(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 100,
    ) -> dict[str, Any]:
        """List all request items (includes parent subcategory and category names)."""
        return await _paged_list("/items", page, page_size)

    @app.tool()
    async def list_priorities(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List all priority levels."""
        return await _paged_list("/priorities", page, page_size)

    @app.tool()
    async def list_statuses(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List all request statuses."""
        return await _paged_list("/statuses", page, page_size)

    @app.tool()
    async def list_urgencies(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List all urgency levels."""
        return await _paged_list("/urgencies", page, page_size)

    @app.tool()
    async def list_products(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
        product_type: Annotated[str, "Filter by product type name, e.g. 'Laptop'"] = "",
        name: Annotated[str, "Filter by product name (contains match)"] = "",
    ) -> dict[str, Any]:
        """List products from the asset product catalog."""
        filters: list[dict[str, str]] = []
        if product_type:
            filters.append(
                {"field": "product_type.name", "condition": "contains", "value": product_type}
            )
        if name:
            filters.append({"field": "name", "condition": "contains", "value": name})
        return await _paged_list("/products", page, page_size, filters)

    @app.tool()
    async def list_product_types(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 100,
    ) -> dict[str, Any]:
        """List all asset product types (e.g. Laptop, Workstation, UPS)."""
        return await _paged_list("/product_types", page, page_size)

    @app.tool()
    async def list_departments(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List all departments."""
        return await _paged_list("/departments", page, page_size)

    @app.tool()
    async def list_announcements(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List all active announcements."""
        return await _paged_list("/announcements", page, page_size)
