# Changelog

All notable changes to servicedeskplus-mcp are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/); dates are YYYY-MM-DD.

## [0.2.0] — 2026-08-01

API gap-closure release: three new modules (Releases, Projects, Contracts/Purchase Orders writes), full CRUD depth (get/update/delete) on notes/tasks/worklogs across requests/problems/changes, the request approval workflow, permanent-delete support on assets/CIs/problems, merge/summary/associations on requests, and MCP schema resources documenting gnarly write shapes. Tool count grew 68 → 162; unit suite grew 111 → 238.

### Added

- **Releases module** (`tools/releases.py`, 12 tools) — list/get/create/update/close, notes (add/list/edit), tasks (add/list — `stage` mandatory), worklogs (add/list). Confirmed live; only `title` is mandatory to create. `close_release` is permission-gated on this instance (403 for the standard technician role).
- **Projects module** (`tools/projects.py`, 14 tools) — list/get/create/update/delete (permanent, no trash), milestones (add/list), tasks (add/list, no `stage` requirement), members (add/list/remove), comments (add/list, payload key `content` not `description`). Confirmed live.
- **Request approval workflow** — `list_request_approval_levels`, `add_request_approval_level`, `list_request_approvals`, `add_request_approver`, `send_request_approval_notification`, `approve_request`, `reject_request`. Confirmed live end-to-end 2026-08-01 (create → level → approver → notify → approve → trash). `approve_request` 400s "Recommendation mail is not yet sent" until the notification step has run at least once.
- **Purchase order writes** — `create_purchase_order`, `update_purchase_order`. Mandatory fields confirmed live: `name`, `custom_po_id`, `vendor`, `requested_by`, `items` (each needs `product`, `ordered_quantity`, `price`, `category`).
- **Note editing and full note CRUD** — `update_request_note`/`update_problem_note`/`update_change_note` plus `get_*_note`/`delete_*_note` on all three modules, confirmed live.
- **Task and worklog CRUD depth** — `get_*_task`/`update_*_task`/`delete_*_task` and `update_*_worklog`/`delete_*_worklog` across requests, problems, and changes.
- **Request attachments** — `list_request_attachments`, `get_request_attachment_content` (download, base64 or `save_to_path`), `add_request_attachment` (multipart upload). Confirmed live end-to-end (upload → list → download byte-for-byte match → trashed). See CLAUDE.md for the `_download`/`upload` path quirks.
- **Permanent deletes** — `delete_problem`, `delete_change`/`restore_change`, `delete_configuration_item`, `delete_asset` (all confirmed permanent unlike `delete_request`'s trash behavior). `copy_change` added per docs (unverified live — change-create is rate-limited on this instance).
- **Request merge, summary, and associations** — `merge_requests` (confirmed live, **irreversible** — the merged-away request becomes permanently unfetchable), `get_request_summary`, `associate_problem`/`dissociate_problem`, `associate_change`/`dissociate_change` (initiated and caused-by).
- **Solutions** — `update_solution` (incl. approval status via plain field update), `add_solution_attachment`, `create_solution_topic`.
- **Asset depreciation** — `create_asset`/`update_asset` gain `depreciation_type`, `useful_life`, `salvage_value` params (nested `asset_depreciation` object); `list_depreciation_types` added.
- **Admin lookups** — `list_closure_codes`, `list_change_types`.
- **Technician email resolution** — `create_request`/`update_request`/`assign_request` now accept a technician email in addition to display name, resolved to an ID via `/technicians` (shared `resolve_ref` helper).
- **Smaller request/asset gaps** — `get_product` lookup tool, `list_assets` `serial_number` filter, `list_requests` category/subcategory/item filters, and a length guard on `close_request`'s `closure_comments`.
- **MCP schema resources** — `sdp://schema/asset`, `sdp://schema/ci-relationship`, `sdp://schema/purchase-order` document the gnarly nested write shapes for these payloads.
- **Client resilience** — `get_binary`/`post_multipart` for attachments, and optional bodies on DELETE/PUT for endpoints that reject one.

### Fixed

- **`delete_solution`** — root-caused the "Not in trash" 400: the working flow is two-step, `DELETE /solutions/{id}/_move_to_trash` (underscore-prefixed action route, not `/move_to_trash`) followed by `DELETE /solutions/{id}` to purge. Previously undocumented and unresolved; now implemented and confirmed live, including cleanup of three leftover test articles.
- **`add_project_member`** — root-caused a bug where the API ignored the given `email_id` entirely and always added the same unrelated technician regardless of input; a bare `user.id` is also rejected. Fix resolves the email to a unique display name via `/users`, submits `user.name`, then verifies the member SDP actually added matches by email and auto-removes it on mismatch (duplicate display names exist on this instance). Added `remove_project_member`.

### Documentation

- Closed out two punch-list items as documented platform gaps (no code changes): `reply_request`/`forward_request` (the on-prem v3 API's only email-shaped resource, `/requests/{id}/drafts`, saves an unsent draft only — no send/dispatch operation exists) and @mentions/notify-on-notes (no `notify_to`/`mentions` field in the `request_note.html` schema).
- Confirmed unavailable on this on-prem instance: problem approvals (4007 "Invalid URL"), flat `/changes/{id}/approvals` pending-approvals path (5 path variants tried), `/change_risks` (404).
- CLAUDE.md quirks table: corrected the stale "technician params" row to reflect email resolution; added a taxonomy-caching-lag row (newly added categories/subcategories may lag in list results but work by name immediately); added a cross-cutting note tying together instance-config-dependent params (`closure_code`, `urgency`, `show_to_requester`).
- Test counts refreshed across CLAUDE.md/NEXTSTEPS.md/README.md: 238 unit (was 111), 60+ integration.

## [Unreleased] — 2026-07-20

Docker deployment, CMDB/contract write support, and problems/changes feature parity with requests.

### Added

- **Docker deployment** — `Dockerfile`, `docker-compose.yml`, `.dockerignore`, and `DOCKER.md` for running the HTTP transport as a shared container; no credentials baked into the image, each client supplies its own `X-SDP-API-Key`.
- **Problems/changes note, task, and worklog tools** — `list_problem_notes`, `list_problem_tasks`, `add_problem_task`, `list_problem_worklogs`, `add_problem_worklog`, `list_change_notes`, `add_change_task`, `list_change_worklogs`, `add_change_worklog`. Backfills problems and changes to the same coverage requests already had. Confirmed live that the worklog payload shape works fine here — the request-scoped worklog endpoint is the one still broken (see Fixed below).
- **Contract write support** — `create_contract`, `update_contract`. Mandatory fields confirmed live: `name`, `custom_contract_id`, `type`, `vendor` (numeric ID), `from_date`/`to_date`.

### Fixed

- **CMDB create/update/relationships** — previously thought unavailable (404) on this instance; the real issue was the endpoint shape. Create/update are module-scoped (`POST`/`PUT /{module_type}` with body `{module_type: {...}}`, not `/cmdb` with `{"ci": {...}}`), and relationship listing uses `/cmdb/{id}/ci_relationships` (not `/relationships`). All confirmed live and cleaned up after testing. `add_ci_relationship` remains unresolved — it 400s on the `relationship_type` field regardless of shape tried.
- **Groups doc contradiction** — API_COVERAGE.md said `/groups` "returns empty"; confirmed live it's actually a hard 404 "Invalid URL". Corrected to match CLAUDE.md/NEXTSTEPS.md.

### Known limitations (updated)

- `add_request_worklog` is still broken (400 on all formats), but now confirmed to be specific to the requests endpoint — the identical payload works on problems and changes worklogs.
- Purchase order writes deferred — `POST /purchase_orders` requires a mandatory `items` line-item array whose schema wasn't probed live this round.

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
