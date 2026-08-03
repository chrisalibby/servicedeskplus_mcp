# servicedeskplus-mcp — Claude Code Context

## What this project is

An MCP server written in Python (FastMCP) that exposes ManageEngine ServiceDesk Plus On-Premise as tools for AI assistants. Developed for Spero Financial (South Carolina credit union) by Chris Libby.

## Architecture

- **Language:** Python 3.11+, managed with `uv`
- **Framework:** FastMCP (`@mcp.tool()` decorators, stdio transport)
- **HTTP client:** `httpx` async only — never mix in requests/aiohttp
- **Config:** pydantic-settings reading from env / `.env` file
- **Entry point:** `sdp-mcp` console script → `servicedeskplus_mcp.__main__:main`

All tools live in `src/servicedeskplus_mcp/tools/` as `register(app: FastMCP)` functions. `server.py` imports and calls each module's `register()`. The client wrapper is in `client.py` — it returns error dicts on failure rather than raising, so the AI always gets readable output.

## Target SDP instance

- **Host:** `sdp.example.com:443` (HTTPS, self-signed cert) — a generic example; real instance-specific host and credentials live in `CLAUDE.local.md` (gitignored, not tracked in this repo)
- **Config:** `SDP_VERIFY_SSL=false` required for self-signed certs
- **Mandatory create_request fields (typical):** subject, description, requester, category, subcategory — varies by instance configuration
- **API auth:** `Authtoken: {api_key}` header; bodies are `application/x-www-form-urlencoded` with JSON in `input_data` key
- **`delete_request`** moves to trash (recoverable) — does NOT permanently delete

## Testing

```bash
uv run pytest                                      # unit tests (no server)
uv run pytest tests/integration/ -m integration   # live server tests
```

Unit tests use `respx` to mock httpx. Integration tests read real credentials from `.env` — the integration conftest builds its own `Settings` instance directly from `.env` values so it never contaminates the unit test environment.

Integration test status: **191 unit / 53+ integration** (as of 2026-08-01)
- `add_request_worklog`: broken — `POST /requests/{id}/worklogs` returns 400 for all field formats tried. The identical payload shape works fine on `/problems/{id}/worklogs` and `/changes/{id}/worklogs` (confirmed 2026-07-20), so this is specific to the requests endpoint on this instance, not a schema-wide issue. Needs a browser network capture of the SDP UI's own worklog POST to find the working shape.
- CMDB create/update/relationships: fixed 2026-07-20 (see quirks table) — GET-only `/ci` 404s were a stale finding, not the real blocker.
- Groups (`/groups`): confirmed unavailable — hard 404 "Invalid URL" on this instance (not "returns empty", corrected in API_COVERAGE.md 2026-07-20)
- `POST /changes` is rate-limited by SDP ("URL blocked as maximum access limit exceeded") when hit repeatedly — re-run change tests after a pause if they fail with that message

## Known endpoint quirks

| Tool | Quirk |
|---|---|
| `list_solution_topics`, `create_solution_topic` | Uses `/topics` endpoint, not `/solution_topics` |
| `create_solution` | `topic` is mandatory on this instance — 400 "Value not provided" when omitted, unlike the field being optional on other instances |
| `update_solution` approval | No working `_approve`/`_reject` action sub-route — those paths 400 with "Value not provided" regardless of payload shape tried. Set `approval_status: {"name": "Approved"/"UnApproved"}` via a plain `PUT /solutions/{id}` instead (confirmed live 2026-08-01) — `update_solution` exposes this as an `approval_status` param. `_publish`/`_submit_for_approval` 404 — cloud-only. |
| `delete_solution` | Resolved 2026-08-01: bare `DELETE /solutions/{id}` 400s "Not in trash" because it's a two-step flow — `DELETE /solutions/{id}/_move_to_trash` first (sets `deleted_time`), then `DELETE /solutions/{id}` purges it. `move_to_trash`/`/trash`/`/movetotrash` sub-routes all 404; the working route is underscore-prefixed like other action endpoints (`_publish`, `_approve`). `delete_solution` now performs both steps. Test articles 144–146 deleted live via this flow. |
| `add_solution_attachment` | `PUT /solutions/{id}/upload` (same pattern as request attachments) — `POST /solutions/{id}/attachments` 404s. |
| `delete_request` | `DELETE /requests/{id}/move_to_trash` only — no permanent delete |
| `close_request` | Omit `closure_code` unless explicitly configured; including it causes 400 on this instance |
| `add_request_worklog` | `time_spent` must be `{"hours": N, "minutes": N}`; owner is required as `{"email_id": "user@domain"}` |
| `list_requests` date filters | `opened_after`/`opened_before`/`due_before` cannot be combined with each other or with `status`/`technician` — SDP returns 400 on multi-criteria arrays containing date fields |
| `add_problem_note`, `add_change_note` | `show_to_requester` is rejected — these endpoints don't support it (unlike request notes) |
| `close_change` | Status transitions on changes require workflow progression; direct PUT to terminal status is rejected on this instance |
| `merge_requests` | `PUT /requests/{id}/merge_requests`, body `{"merge_requests": [{"id": ...}, ...]}` — confirmed live 2026-08-01. Irreversible: merged requests become permanently unfetchable (`GET` 404s naming the parent) and there is no un-merge. |
| `associate_problem`/`associate_change` | POST bodies must wrap the target in a named key matching the endpoint (`request_problem_association`, `request_initiated_change`, `request_caused_by_change`) — a bare `{"problem": {...}}`/`{"change": {...}}` 400s with "Extra key found in JSON" |
| `dissociate_problem`/`dissociate_change` | `DELETE` to the same association path, but a bodyless `DELETE` 500s ("Internal Error") on this instance — must resend the same wrapped body used to associate. Confirmed reversible live 2026-08-01 for problem, initiated-change, and caused-by-change associations. |
| Change note GET | `GET /changes/{id}/notes` omits `description` from list items — only the POST response includes it |
| `update_request_note`, `update_problem_note`, `update_change_note` | Note editing confirmed live (2026-08-01): `PUT /{requests,problems,changes}/{id}/notes/{note_id}` with `{"note": {"description": ...}}` returns 200 and updates `last_updated_time`/`last_updated_by` immediately, on all three modules. |
| `list_configuration_items` | Uses `/cmdb` (not `/ci`) for list/get. Filter by `module_type` using `api_plural_name` values: `cmdb_itservice`, `cmdb_departmentci`, `cmdb_people`, `cmdb_supportgroup`, `cmdb_switchportci`. |
| `create_configuration_item`, `update_configuration_item` | Module-scoped: `POST/PUT /{module_type}` with body `{module_type: {...}}` — NOT `/cmdb` with `{"ci": {...}}` (that shape 400s with "Extra key found in JSON"). `update_configuration_item` and both tools now take a required `module_type` param. |
| `list_ci_relationships` | `GET /cmdb/{ci_id}/ci_relationships` (not `/relationships`) — confirmed working. |
| `add_ci_relationship` | Still unresolved: `POST /cmdb/{ci_id}/ci_relationships` 400s on the `api_name` field regardless of whether `relationship_type` is sent as `{"name": ...}` or `{"api_name": ...}`. Likely needs a relationship-type lookup endpoint (not implemented) to get a valid identifier. |
| `add_problem_worklog`, `add_change_worklog`, `add_problem_task`, `add_change_task` | Same payload shape as `add_request_worklog`/`add_request_task` — confirmed working live (2026-07-20), unlike the request-scoped worklog endpoint. |
| `create_request` urgency | Rejected in EVERY format (name and ID, on create and PUT) — the urgency field is not on the request form on this instance; all live requests have `urgency: null`. Set priority instead. |
| `create_asset` | Flat `asset_type` key is rejected (`"Extra key found in JSON"`). Real schema uses nested `product: {"id": ...}` (+ optional `product_type: {"id": ...}`). Names are resolved to IDs via `/products` / `/product_types` (both confirmed live). |
| `list_assets` filters | Filter asset type on `product_type.name` (not `asset_type.name`). Null-check filter `{"field": "product_type", "condition": "is", "values": []}` is accepted (no 400); unconfirmed whether it matches, since all live assets have a product_type. |
| `create_asset`/`update_asset` depreciation | Nested `asset_depreciation: {depreciation_type: {"id"}, useful_life, salvage_value}` (confirmed live 2026-08-01, both POST and PUT). `depreciation_type` names resolved via new `/depreciation_types` endpoint (Straight Line=1, Declining Balance=2, Sum Of The Years Digit=3, Double Declining Balance=4). Read-only `is_asset_depreciation` flag stays `false` even after setting `asset_depreciation` — sending it on write 400s (`"Extra key found in JSON"`), so it's not exposed as a tool param. `depreciation_percent` also 400s (`"Invalid Input"` on `depreciation_detail`) — not exposed. |
| CDATA in descriptions | Wrapping HTML in `<![CDATA[...]]>` leaks a stray `]]>` into rendered output. Raw HTML works fine. All description/note/resolution tools strip CDATA wrappers before sending. |
| `list_changes` sort | Instance default returns oldest-first (2020 changes on page 1). Tool defaults to `sort_field=created_time`, `sort_order=desc`. |
| Contracts / POs | `/contracts` and `/purchase_orders` confirmed live (2026-07-17). |
| `delete_project` | No `move_to_trash` endpoint for projects on this instance (404s "Invalid URL") — `DELETE /projects/{id}` is a direct, permanent delete, unlike requests/problems/changes. |
| `add_project_comment` | Payload key is `content`, not `description` — `description` 400s "Extra key found in JSON". |
| `add_project_member` | Root cause confirmed 2026-08-01: `POST /projects/{id}/members` with `user.email_id` is broken on this instance — the value is ignored entirely and SDP always adds the same unrelated technician, regardless of which email is sent. Bare `user.id` (numeric, either the technician-list id or the `linked_instance.id`) is rejected outright with 400 "Invalid Input" on the `user` field. Only `user.name` is accepted and correctly resolves in the common case, but is unsafe alone when two accounts share a display name (found live: a second account sharing the same display name sat ahead of the correct account in whatever SDP matches on, so name-only lookup silently added the wrong one). Fix: `add_project_member` now resolves `technician_email` to a display name via `/users` (refusing if the email doesn't resolve to exactly one user), submits `user.name`, then verifies the member SDP actually added has a matching `email_id`; on mismatch it auto-removes the wrongly-added member via `DELETE /projects/{id}/members/{member_id}` and returns an error instead of silently leaving the wrong person on the project. Added `remove_project_member` (`DELETE /projects/{id}/members/{member_id}`, confirmed live) alongside it. |
| `create_contract` | Mandatory fields confirmed live (2026-07-20): `name`, `custom_contract_id`, `type` (name), `vendor` (numeric id), `from_date`/`to_date` (epoch ms). `DELETE /contracts/{id}` works, unlike requests/problems/changes. |
| Purchase order writes | Confirmed live (2026-08-01) via `create_purchase_order`/`update_purchase_order`. Mandatory: `name`, `custom_po_id`, `vendor` (id), `requested_by` (id or name), `items` (each needs `product` id, `ordered_quantity`, `price`, `category` — numeric purchase category id, defaults to `1` = Assets). Product must be vendor-associated or `POST` 400s with "Product-Vendor association does not exist". `DELETE /purchase_orders/{id}` works, like contracts. |
| Request IDs | Tools strip non-numeric prefixes (`RE-`, `#`) from `request_id` before calling the API. |
| Technician params | Display name (e.g. 'Jane Smith') passes through as `{"name": ...}`. Email is now also accepted (confirmed 2026-08-01) — `create_request`/`update_request`/`assign_request` auto-resolve it to a technician ID via `/technicians` (`email_id` lookup, shared `resolve_ref` helper). Assignment still fails if category/subcategory are unset — set them in the same `update_request` call. |
| Taxonomy caching lag (categories/subcategories) | Newly added subcategories (and, by the same mechanism, categories) may not appear immediately in `list_categories`/`list_subcategories` results — SDP-side caching lag — but they work by name in `create_request`/`update_request` right away. Don't treat an absent list entry as proof the value is invalid. |
| Write timeouts | POST/PUT/DELETE timeouts return `indeterminate: true` — the write may have landed; verify before retrying. `add_request_note` auto-verifies and returns `posted: true/false/"unknown"`. GETs retry twice automatically. |
| `restore_change` | `PUT /changes/{id}/restore_from_trash` rejects any `input_data` body ("Extra parameter(s) not allowed") — must be sent as a bare PUT with no body at all, unlike every other write endpoint in this codebase. `SDPClient.put` now accepts `data=None` for this. |
| `delete_change` | `DELETE /changes/{id}/move_to_trash` — recoverable, same pattern as `delete_request`; confirmed live 2026-08-01 by trashing and restoring an existing test change. |
| `delete_problem` | `DELETE /problems/{id}` is permanent — `PUT /problems/{id}/restore_from_trash` 404s "Invalid URL" (no trash sub-route exists for problems on this instance, unlike requests/changes). |
| `list_pending_approvals` (changes) | `GET /changes/{id}/approvals` returns 4007 "Invalid URL" — re-confirmed 2026-08-01 across 5 path variants (`approvals`, `change_approvals`, `approvers`, `approval`, `approval_levels`). No working flat path exists on this instance; use `list_change_approval_levels` instead. |
| `list_change_risks` | `/change_risks` 404s "Invalid URL" on this instance — not implemented as a tool. `/closure_codes` and `/change_types` both work (200) and are implemented. |
| `create_release` | Only `title` is mandatory — SDP auto-assigns the default template ("General Template") and workflow ("General Release Workflow"). Unlike changes, no other field is required. |
| `delete_asset` | `DELETE /assets/{id}` confirmed live 2026-08-01 — unlike `delete_request`, this is a PERMANENT delete (no trash/recovery). |
| `delete_configuration_item` | `DELETE /{module_type}/{id}` confirmed live 2026-08-01 — same `module_type`-scoped path as create/update. PERMANENT delete, no trash/recovery. |
| `get_request_task`/`update_request_task`/`delete_request_task`, `get_problem_task`/`update_problem_task`/`delete_problem_task`, `get_change_task`/`update_change_task`/`delete_change_task` | `GET/PUT/DELETE /{module}/{id}/tasks/{task_id}` confirmed live 2026-08-01 on all three modules. Task `status` on PUT takes a free-form status name (e.g. `{"status": {"name": "Closed"}}`) and transitions immediately — no workflow gating like `close_change` has on the parent record. `owner` on PUT uses `{"name": ...}` like `add_*_task`. Delete is permanent. |
| `update_request_worklog`/`delete_request_worklog` | `PUT/DELETE /requests/{id}/worklogs/{worklog_id}` — shape verified live against the identical worklog sub-resource on problems/changes (see below); requests-side PUT/DELETE itself is unverified on this instance since `add_request_worklog` (POST) is broken here. A single existing worklog was found on a live request during probing and used only for a read-only GET-shape check — it was not mutated, since it belongs to a real user's real ticket. |
| `update_problem_worklog`/`delete_problem_worklog`, `update_change_worklog`/`delete_change_worklog` | `PUT/DELETE /{module}/{id}/worklogs/{worklog_id}` confirmed live 2026-08-01 on problems and changes. `PUT` body is `{"worklog": {"description": ..., "time_spent": {"hours", "minutes"}}}` — both fields optional, only sent if provided. |
| `add_release_task` | `stage` is mandatory (`{"id": "2"}` for Planning, etc.) — SDP 400s "Value not provided" without it. Changes/problems tasks don't require this. |
| `close_release` | `PUT /releases/{id}/_close` with `{"status": "completed", "comment": ...}` per on-prem docs — 403s "User does not have this permission" for the standard technician account tested on this instance; may need an elevated role. |
| `list_release_notes` | Unlike change notes, the GET list response includes `description` on each item (change notes omit it from the list). |
| `delete_release`-equivalent | `DELETE /releases/{id}/move_to_trash` confirmed working (recoverable), same pattern as `delete_request`. No dedicated MCP tool wired up for it. |
| Instance-config-dependent params | Some tool params reflect this SDP instance's configuration, not a payload bug — if a write 400s naming one of these fields, check instance config before re-probing the shape: `closure_code` on `close_request` (400s unless closure codes are configured), `urgency` on `create_request`/`update_request` (not on the request form here at all), and `show_to_requester` on `add_problem_note`/`add_change_note` (rejected — request notes support it, problem/change notes don't). |
| `reply_request` / `forward_request` | Not supported by the on-prem v3 REST API — platform gap, confirmed 2026-08-01. `POST /requests/{id}/drafts` (docs: `requests/request_draft.html`) has a reply/forward-shaped schema (`to`, `cc`, `bcc`, `subject`, `description`, `type: "reply"`) but only **saves an unsent draft** — no send/dispatch/notify operation exists anywhere under Requests in the docs. Not implemented; see API_COVERAGE.md for detail. |
| `list_request_attachments`, `get_request_attachment_content` | Confirmed live 2026-08-01. `GET /requests/{id}/attachments` returns each attachment's `id`, `name`, `content_type`, `size.value`. Download is `GET /requests/{id}/attachments/{attachment_id}/_download` (note the leading underscore in `_download` — not `/download`) and returns raw bytes with `content-type: application/x-download` regardless of the file's real MIME type; use the list response's `content_type`/`name` for that. `get_request_attachment_content` base64-encodes the bytes into `content_base64` by default, or writes to `save_to_path` if provided (response then omits the base64 and returns `saved_to` instead). |
| `add_request_attachment` | Upload is `PUT /requests/{id}/upload` — NOT `POST /requests/{id}/attachments` (that path is GET-only; POST to it 404s bare, with no JSON body). Multipart field name is `input_file` (not `filename`/`file`), no `input_data` part needed. Optional description goes in a `?description=` query param, not the multipart body. Confirmed live 2026-08-01 (upload → list → download byte-for-byte match → trashed). Matches ManageEngine's on-prem "v3 attachment API changes" admin-guide pattern — the cloud (sdpondemand) API uses a different `POST .../uploads` shape with field `filename`; don't use that here. |
| `add_request_approval_level` | Full round-trip confirmed live 2026-08-01 (create → level+approver → notify → approve → trash). Must include at least one approver in the same POST — `{"approval_level": {}}` 400s "Approvers are unavailable". The documented `level` (int) field is rejected as read-only on this instance (`"Read only field cannot be edited"`); SDP assigns the level number itself. Approver is a nested `approvals: [{"approver": {...}}]` array, not a top-level field. |
| `send_request_approval_notification` | Body key is `{"approval": {"notification": {...}}}` — the cloud-docs shape `{"notification": {...}}` (no `approval` wrapper) 400s "Extra key found in JSON" on this instance. `approve_request`/`reject_request` 400 with "Recommendation mail is not yet sent" until this has been called at least once for that approval. Sends a real email to whoever is set as the approver — only ever point this at your own technician account when testing. |
| `list_change_approval_levels` | Endpoint path is valid (`GET /changes/{id}/approval_levels`, distinct from the existing `list_pending_approvals` path `/changes/{id}/approvals`) but returns 4004 "Internal Error" on all 3 live changes probed 2026-08-01 — all three have no approval levels ever configured (`has_approvals: false` in `/changes/{id}/approval_levels/approval_summary`). Unverified whether it works once a level exists; not fixable without creating a change, which is rate-limited on this instance. |
| `list_pending_approvals` (existing tool) | Re-checked 2026-08-01 while probing change approvals: `GET /changes/{id}/approvals` now returns 4007 "Invalid URL" against 3 live changes, vs. `approve_change`/`reject_change`'s `PUT` to the same path family which are documented as working. Flagging as a possible regression on this instance — not fixed in this round (out of scope), but worth re-verifying before relying on `list_pending_approvals` for a real approval flow. |
| Problem approvals | Confirmed unavailable on this on-prem instance 2026-08-01: `GET /problems/{id}/approval_levels` and `GET /problems/{id}/approvals` both return 4007 "Invalid URL" (tested against problem id 41) — the URL itself is rejected, not a permissions/empty-data response. Cloud docs claim parity with Changes; this on-prem version doesn't have it. Not implemented. |

## Code style

- No comments unless the why is non-obvious
- No docstrings beyond the one-line tool description (used by MCP)
- ruff + pyright must pass clean before committing
- No Co-Authored-By trailers in commits — author is Chris Libby only
- Commits: `git commit -m "..."` with no attribution lines
