# Changelog

All notable changes to servicedeskplus-mcp are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/); dates are YYYY-MM-DD.

## [Unreleased] — 2026-07-17

Real-world usage punch list: fixes and gaps surfaced by production use against the Spero SDP instance.

### Fixed

- **`create_asset` completely rebuilt** — the flat `asset_type` key was rejected by the API on every call (`"Extra key found in JSON"`), which previously forced an Excel bulk-import workaround. The tool now sends the real schema: nested `product: {"id": ...}` plus optional `product_type: {"id": ...}`. Product and product type accept either a name (resolved against the live catalog, with close-match suggestions on failure) or a numeric ID. Verified end-to-end against the live instance.
- **`list_assets` asset type filter** — now filters on `product_type.name` instead of the nonexistent `asset_type.name`, matching the real asset schema.
- **`list_changes` sort order** — instance default returned oldest-first (changes from 2020 on page 1). Now defaults to `created_time` descending; `sort_field`/`sort_order` params exposed.
- **CDATA artifacts in rendered HTML** — wrapping HTML in `<![CDATA[...]]>` leaked a stray `]]>` into rendered descriptions. All description/note/resolution fields across requests, changes, and problems now strip CDATA wrappers before sending; param descriptions state that raw HTML is supported directly.
- **Urgency on `create_request`** — investigated live in every format (name and ID, on create and follow-up PUT): the Spero instance rejects urgency unconditionally because the field is not on the request form (all live requests have `urgency: null`). Documented as an instance limitation; the param description now directs users to set priority instead. An integration test locks in the quirk and will flag if the instance ever starts accepting it.

### Added

- **Timeout resilience / duplicate-write protection** (`client.py`):
  - Per-phase `httpx.Timeout` (connect 10s, read/write `SDP_TIMEOUT`, pool 10s); `SDP_TIMEOUT` default raised 30s → 60s.
  - GETs retry up to 2 extra attempts with backoff on timeout/connect errors (idempotent).
  - POST/PUT/DELETE never auto-retry; on timeout they return `indeterminate: true` with a warning that the write may have landed — verify before retrying to avoid duplicates.
  - `add_request_note` verifies after an indeterminate POST by re-fetching the notes list, returning `posted: true`, `posted: false`, or `posted: "unknown"`.
- **Contracts + Purchase Orders module** (`tools/contracts.py`) — `list_contracts`, `get_contract`, `list_purchase_orders`, `get_purchase_order`. Both endpoints confirmed live on the Spero instance. Read-only this round.
- **Product catalog lookups** (`tools/admin.py`) — `list_products` (with name / product type filters) and `list_product_types`, closing the "no way to list asset types" gap.
- **`list_requests` subject search** — `search` param (contains match on subject). Cannot be combined with date filters (existing instance quirk).
- **`list_assets` `missing_product_type` filter** — SDP null-check convention (`condition: "is"`, empty `values`); syntax accepted by the live instance.
- **Sort params** — `sort_field` / `sort_order` on `list_requests`, `list_assets`, and `list_changes`.
- **Request ID normalization** — request tools strip non-numeric prefixes (`RE-`, `#`) from `request_id` before calling the API.
- **Shared helpers** (`tools/_util.py`) — `strip_cdata`, `normalize_id`, and `resolve_ref` (name → ID resolution with exact-then-contains matching and client-side verification).
- Unit tests for all of the above (111 total) and a live integration suite for the punch list (`tests/integration/test_punchlist.py`); integration status 46 pass / 2 skip.

### Documentation

- CLAUDE.md quirks table expanded with nine entries: urgency unsupported, create_asset schema, product_type filters, CDATA, change sort default, contracts/PO availability, ID normalization, technician name format, and write-timeout semantics. Noted that SDP rate-limits repeated `POST /changes`.
- API_COVERAGE.md updated: products, product types, contracts, and purchase orders now covered — 72 tools total.
- Docstring/param-description clarifications: technician params take display names (email format rejected); assignment fails when category/subcategory are unset (set them in the same `update_request` call); newly added subcategories may not appear in list results immediately but work by name.

## [0.1.0] — 2026-06-17

Initial development cycle.

### Added

- MCP server (FastMCP, stdio transport) exposing ServiceDesk Plus On-Premise API v3: requests (CRUD, notes, worklogs, resolution, tasks, assign/pickup), problems, changes (incl. approvals), assets/workstations, CMDB, solutions, and admin lookups — 66 tools at cycle end (2026-06-05 through 2026-06-17).
- HTTP transport mode with per-connection API key support (`X-SDP-API-Key` header) alongside stdio (2026-06-12).
- Integration test suite against the live Spero instance; unit suite with respx mocks.
- Cross-platform setup (macOS/Windows) and handoff documentation (SETUP.md, NEXTSTEPS.md, API_COVERAGE.md).

### Fixed

- On-prem compatibility: error handling returns readable dicts instead of raising; subcategory support on create/update; endpoint corrections (`/topics`, `/cmdb`); date filter single-criterion limitation; `delete_request` moves to trash only, matching technician UI behavior (2026-06-09 through 2026-06-11).

### Known limitations

- `add_request_worklog` returns 400 in all field formats on the Spero instance — needs a browser network capture to debug.
- `/groups` and CMDB create/update/relationships unavailable on the Spero instance.
