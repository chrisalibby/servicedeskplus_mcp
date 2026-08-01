"""Contract and purchase order tools for ServiceDesk Plus."""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from ..client import get_client
from ._util import date_to_epoch_ms, resolve_ref


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
    async def create_contract(
        name: Annotated[str, "Contract name"],
        custom_contract_id: Annotated[str, "Contract ID/reference (mandatory on this instance)"],
        contract_type: Annotated[
            str, "Contract type name, e.g. 'Software', 'Hosted Service' (resolved to {'name': ...})"
        ],
        vendor_id: Annotated[
            str,
            "Vendor ID (numeric — see vendor.id on list_contracts results). Name lookup is "
            "not supported here; pass the numeric id.",
        ],
        from_date: Annotated[str, "Start date (YYYY-MM-DD)"],
        to_date: Annotated[str, "End date (YYYY-MM-DD)"],
        total_price: Annotated[str, "Total contract price"] = "",
    ) -> dict[str, Any]:
        """Create a new contract. name, custom_contract_id, contract_type, vendor_id, from_date,
        and to_date are all mandatory on this instance."""
        contract: dict[str, Any] = {
            "name": name,
            "custom_contract_id": custom_contract_id,
            "type": {"name": contract_type},
            "vendor": {"id": vendor_id},
            "from_date": {"value": date_to_epoch_ms(from_date)},
            "to_date": {"value": date_to_epoch_ms(to_date)},
        }
        if total_price:
            contract["total_price"] = total_price
        async with get_client() as c:
            return await c.post("/contracts", {"contract": contract})

    @app.tool()
    async def update_contract(
        contract_id: Annotated[str, "Contract ID"],
        name: Annotated[str, "Updated name"] = "",
        total_price: Annotated[str, "Updated total price"] = "",
        to_date: Annotated[str, "Updated end date (YYYY-MM-DD)"] = "",
    ) -> dict[str, Any]:
        """Update an existing contract."""
        contract: dict[str, Any] = {}
        if name:
            contract["name"] = name
        if total_price:
            contract["total_price"] = total_price
        if to_date:
            contract["to_date"] = {"value": date_to_epoch_ms(to_date)}
        async with get_client() as c:
            return await c.put(f"/contracts/{contract_id}", {"contract": contract})

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

    @app.tool()
    async def create_purchase_order(
        name: Annotated[str, "Purchase order name"],
        custom_po_id: Annotated[str, "PO ID/reference (mandatory on this instance)"],
        vendor: Annotated[
            str, "Vendor name or numeric ID, e.g. 'CDW' or '12'. Every item's product must "
            "already be associated with this vendor, or the API 400s with "
            "'Product-Vendor association does not exist'.",
        ],
        requested_by: Annotated[
            str, "Requester display name or numeric ID (mandatory on this instance)"
        ],
        items: Annotated[
            list[dict[str, Any]],
            "Line items, e.g. [{'product': 'HP EliteBook 840 G8', 'quantity': 2, "
            "'price': '899.00', 'category': 1}]. 'product' is a name or numeric ID and must "
            "be vendor-associated for the given vendor; 'category' is the numeric purchase "
            "category ID, defaulting to '1' (Assets).",
        ],
        terms: Annotated[str, "Payment terms, e.g. 'NET/30'"] = "",
        comments: Annotated[str, "Comments"] = "",
    ) -> dict[str, Any]:
        """Create a new purchase order. name, custom_po_id, vendor, requested_by, and items
        are all mandatory on this instance. Each item needs product, quantity, price, and
        a category (defaults to '1' — Assets); product must be vendor-associated or the
        API rejects the request."""
        async with get_client() as c:
            vendor_ref = await resolve_ref(c, "/vendors", "vendors", vendor)
            if "error" in vendor_ref:
                return vendor_ref
            resolved_items: list[dict[str, Any]] = []
            for item in items:
                product_ref = await resolve_ref(c, "/products", "products", str(item["product"]))
                if "error" in product_ref:
                    return product_ref
                resolved_items.append(
                    {
                        "product": product_ref,
                        "ordered_quantity": str(item.get("quantity", "1.00")),
                        "price": str(item["price"]),
                        "category": {"id": str(item.get("category", "1"))},
                    }
                )
            purchase_order: dict[str, Any] = {
                "name": name,
                "custom_po_id": custom_po_id,
                "vendor": vendor_ref,
                "requested_by": (
                    {"id": requested_by} if requested_by.isdigit() else {"name": requested_by}
                ),
                "items": resolved_items,
            }
            if terms:
                purchase_order["terms"] = terms
            if comments:
                purchase_order["comments"] = comments
            return await c.post("/purchase_orders", {"purchase_order": purchase_order})

    @app.tool()
    async def update_purchase_order(
        purchase_order_id: Annotated[str, "Purchase order ID"],
        name: Annotated[str, "Updated name"] = "",
        terms: Annotated[str, "Updated payment terms"] = "",
        comments: Annotated[str, "Updated comments"] = "",
    ) -> dict[str, Any]:
        """Update an existing purchase order."""
        purchase_order: dict[str, Any] = {}
        if name:
            purchase_order["name"] = name
        if terms:
            purchase_order["terms"] = terms
        if comments:
            purchase_order["comments"] = comments
        async with get_client() as c:
            return await c.put(
                f"/purchase_orders/{purchase_order_id}", {"purchase_order": purchase_order}
            )
