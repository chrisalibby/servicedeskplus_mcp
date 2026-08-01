"""Reference resources documenting gnarly nested write shapes for ServiceDesk Plus."""

from mcp.server.fastmcp import FastMCP

_ASSET_SCHEMA = """# Asset write shape

`POST /assets` and `PUT /assets/{id}` both take `{"asset": {...}}`.

```json
{
  "asset": {
    "name": "LAPTOP-042",
    "serial_number": "CNU1234ABC",
    "product": {"id": "1001"},
    "product_type": {"id": "12"},
    "vendor": {"name": "CDW"},
    "site": {"name": "Main Branch"},
    "department": {"name": "IT"},
    "used_by": {"name": "jdoe"},
    "asset_depreciation": {
      "depreciation_type": {"id": "1"},
      "useful_life": "36",
      "salvage_value": "100.00"
    }
  }
}
```

Field relationships:
- `product` drives most defaults; `product_type` is usually inferred from it but can be set
  explicitly. Both accept a name or numeric ID from `create_asset`/`update_asset` tool params —
  names are resolved to `{"id": ...}` via `/products` and `/product_types`.
- `asset_depreciation.depreciation_type` ids on this instance: `1` = Straight Line,
  `2` = Declining Balance, `3` = Sum Of The Years Digit, `4` = Double Declining Balance
  (confirmed live 2026-08-01; use `list_depreciation_types` to verify).
- The read-only `is_asset_depreciation` flag stays `false` even after setting
  `asset_depreciation` — sending it explicitly 400s with "Extra key found in JSON", so it is
  never sent.
- `depreciation_percent` also 400s ("Invalid Input" on `depreciation_detail`) and is not exposed.
- `serial_number` filters in `list_assets` are exact-match only.
"""

_CI_RELATIONSHIP_SCHEMA = """# CMDB configuration item write shape and relationships

CI create/update are module-scoped: `POST /{module_type}` and `PUT /{module_type}/{ci_id}`,
body keyed by the module_type itself (NOT `/cmdb` with `{"ci": {...}}` — that 400s with
"Extra key found in JSON").

```json
{
  "cmdb_itservice": {
    "name": "Core Banking Platform",
    "description": "Primary teller/member-facing platform",
    "state": {"name": "In Production"}
  }
}
```

Valid `module_type` values (`api_plural_name`): `cmdb_itservice`, `cmdb_departmentci`,
`cmdb_people`, `cmdb_supportgroup`, `cmdb_switchportci`. `list_configuration_items` and
`get_configuration_item` read through the generic `/cmdb` (or `/{module_type}`) path and each
returned item carries its own `module.api_plural_name` — pass that same value back in as
`module_type` on update.

## ci_relationships

`GET /cmdb/{ci_id}/ci_relationships` (not `/relationships`) lists existing relationships and is
confirmed working. The write side is not:

```json
{
  "ci_relationship": {
    "relationship_type": {"name": "Depends on"},
    "related_ci": {"id": "2002"}
  }
}
```

`POST /cmdb/{ci_id}/ci_relationships` with this shape 400s on the `api_name` field regardless
of whether `relationship_type` is sent as `{"name": ...}` or `{"api_name": ...}`. This likely
needs a relationship-type lookup endpoint (not yet found/implemented) to supply a valid
identifier — `add_ci_relationship` remains unverified on this instance.
"""

_PURCHASE_ORDER_SCHEMA = """# Purchase order write shape

`POST /purchase_orders` and `PUT /purchase_orders/{id}` take `{"purchase_order": {...}}`.

```json
{
  "purchase_order": {
    "name": "Q3 Laptop Refresh",
    "custom_po_id": "PO-2026-014",
    "vendor": {"id": "12"},
    "requested_by": {"name": "jdoe"},
    "items": [
      {
        "product": {"id": "1001"},
        "ordered_quantity": "2.00",
        "price": "899.00",
        "category": {"id": "1"}
      }
    ],
    "terms": "NET/30",
    "comments": "Replacing end-of-life fleet"
  }
}
```

Mandatory fields (confirmed live 2026-08-01): `name`, `custom_po_id`, `vendor`, `requested_by`,
`items`. Each item needs `product`, `ordered_quantity`, `price`; `category` is a numeric
purchase category ID and defaults to `1` (Assets) when omitted.

Vendor-product association requirement: every line item's `product` must already be associated
with the PO's `vendor`, or the API rejects the whole request with "Product-Vendor association
does not exist" — there is no bypass. Resolve both `vendor` and each `product` from name to ID
via `/vendors` and `/products` before posting.

`DELETE /purchase_orders/{id}` works (like contracts), unlike requests/problems/changes which
only move to trash.
"""


def register(app: FastMCP) -> None:
    @app.resource("sdp://schema/asset")
    def asset_schema() -> str:
        return _ASSET_SCHEMA

    @app.resource("sdp://schema/ci-relationship")
    def ci_relationship_schema() -> str:
        return _CI_RELATIONSHIP_SCHEMA

    @app.resource("sdp://schema/purchase-order")
    def purchase_order_schema() -> str:
        return _PURCHASE_ORDER_SCHEMA
