"""Contract and purchase order tools for ServiceDesk Plus."""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client


async def _paged_list(path: str, page: int, page_size: int) -> dict[str, Any]:
    list_info: dict[str, Any] = {
        "start_index": (page - 1) * page_size,
        "row_count": page_size,
    }
    params = {"input_data": json.dumps({"list_info": list_info})}
    async with get_client() as c:
        return await c.get(path, params=params)


def register(app: FastMCP) -> None:
    @app.tool()
    async def list_contracts(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List contracts (vendor, type, dates, total price)."""
        return await _paged_list("/contracts", page, page_size)

    @app.tool()
    async def get_contract(
        contract_id: Annotated[str, "Contract ID"],
    ) -> dict[str, Any]:
        """Get a single contract by ID."""
        async with get_client() as c:
            return await c.get(f"/contracts/{contract_id}")

    @app.tool()
    async def list_purchase_orders(
        page: Annotated[int, "Page number (1-based)"] = 1,
        page_size: Annotated[int, "Results per page (max 100)"] = 25,
    ) -> dict[str, Any]:
        """List purchase orders (vendor, owner, totals, status)."""
        return await _paged_list("/purchase_orders", page, page_size)

    @app.tool()
    async def get_purchase_order(
        purchase_order_id: Annotated[str, "Purchase order ID"],
    ) -> dict[str, Any]:
        """Get a single purchase order by ID."""
        async with get_client() as c:
            return await c.get(f"/purchase_orders/{purchase_order_id}")
