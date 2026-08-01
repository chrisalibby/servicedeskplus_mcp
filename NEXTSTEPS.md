# Next Steps

## Current state (as of 2026-08-01)

Integration tested against `sdp.example.com` (Spero Financial SDP on-prem instance).
All unit tests pass (234). Integration tests: 52+ pass (added note get/delete roundtrip
2026-08-01), 2 skip, 3 intermittently blocked by SDP's `POST /changes` rate limit (see Known
Gaps below) — re-run after a pause if those fail.

### Punch-list closeout (2026-08-01, second pass)

- Note get/delete added for requests, problems, and changes (6 tools) — all confirmed live.
- `delete_problem` added — confirmed permanent (no trash sub-route exists for problems here).
- `delete_change`/`restore_change` added — confirmed live (trash+restore round-trip on an
  existing test change). `copy_change` added per docs, unverified live (rate-limit risk).
- `list_closure_codes`/`list_change_types` added — confirmed live. `list_change_risks` skipped
  — 404s "Invalid URL" on this instance.
- `list_pending_approvals` re-probed: still no working flat approvals path on this instance
  across 5 variants tried; docstring updated to steer to `list_change_approval_levels`.
- Remaining gaps are now limited to: known-blocked items below (groups, request-worklog POST,
  CI relationships, change-close workflow), documented platform gaps (drafts/reply-forward,
  @mentions), task sub-depth (dependencies/attachments/worklogs on tasks), topic CRUD beyond
  create, user management writes (requester/technician create/update/delete), and unconfirmed
  cloud-only modules (checklists, request/change maintenance, technician unavailability,
  delegation, space management, custom modules).

### What works

- Full CRUD for requests, problems, changes, assets, workstations
- CMDB: list all CIs (`/cmdb`), get by ID, filter by module type (`cmdb_itservice`, `cmdb_departmentci`, `cmdb_people`, `cmdb_supportgroup`, `cmdb_switchportci`); create/update (module-scoped) and relationship listing
- Notes (add/list/edit), tasks, worklogs, resolution on requests, problems, and changes (feature parity across all three ticket types) — note editing (`update_request_note`/`update_problem_note`/`update_change_note`) added 2026-08-01
- Change approvals (approve/reject)
- Contract create/update/read; purchase order create/update/read (PO writes confirmed live 2026-08-01 — see Known gaps history)
- Asset depreciation fields (`asset_depreciation` nested object) on `create_asset`/`update_asset`, plus `list_depreciation_types` — added 2026-08-01
- Request/problem/change attachments: list, download (`get_request_attachment_content`), and upload (`add_request_attachment`) — added 2026-08-01
- `get_product` lookup, `list_assets` serial-number filter, `list_requests` category/subcategory/item filters, closure-comments length guard on `close_request`, and technician-email resolution (email auto-resolved to ID via `/technicians`, in addition to display name) — added 2026-08-01
- All admin lookup endpoints: statuses, priorities, categories, subcategories, sites, departments, urgencies, technicians, requesters, announcements, products, product types
- Knowledge base: search solutions, get/create articles, list topics
- HTTPS with self-signed cert (`SDP_VERIFY_SSL=false`)
- Multi-portal support via `SDP_PORTAL_ID`
- Readable error messages — SDP's `response_status.messages` text is returned directly instead of raising exceptions
- **Shared HTTP hosting**: `SDP_TRANSPORT=http` runs the server as a streamable-HTTP MCP endpoint with per-connection API keys (`X-SDP-API-Key` header), so one deployment serves every technician with their own credentials. Deploy via Docker (`docker compose up -d --build` — see `DOCKER.md`) or directly as a systemd service (see `SETUP.md`).

### Known gaps on this instance

| Gap | Detail |
|---|---|
| **Groups** (`list_groups`) | `/groups` returns a hard 404 "Invalid URL" — confirmed unavailable on this instance (2026-07-20), not an endpoint-path issue. |
| **`add_request_worklog`** | `POST /requests/{id}/worklogs` returns 400 for all field formats tried, specifically on the requests endpoint — the identical payload works on problems and changes worklogs (confirmed 2026-07-20). Needs a browser network capture of the SDP UI's own request-worklog POST. |
| **`add_ci_relationship`** | `POST /cmdb/{id}/ci_relationships` 400s on the `api_name` field regardless of `relationship_type` shape tried — likely needs a relationship-type lookup endpoint (not implemented). List/get/create/update on CMDB all work (fixed 2026-07-20 — see CLAUDE.md). |
| **`close_change`** | Changes require workflow progression (Requested → In Review → Approved → In Progress → Completed). Direct status PUT is rejected on this instance. The tool is kept for other instances with simpler configurations. |
| **`reply_request`/`forward_request`** | Not supported by the on-prem v3 REST API — the only email-shaped resource (`/requests/{id}/drafts`) only saves an unsent draft, no send/dispatch operation exists. Documented platform gap, closed out 2026-08-01 (see Future development below). |
| **@mentions on notes** | Not supported by the API — `request_note.html` schema has no `notify_to`/`mentions` field. Documented platform gap, closed out 2026-08-01 (see Future development below). |

### Instance-specific configuration (Spero Financial)

- **Server:** `sdp.example.com:443` (HTTPS, self-signed cert)
- **SSL:** `SDP_VERIFY_SSL=false`
- **Mandatory fields on `create_request`:** subject, description, requester, category, subcategory
- **Mandatory field values that work:** category=`User Administration`, subcategory=`Password Reset` (or other valid combos — run `list_categories` and `list_subcategories` tools to get the full list)
- **Statuses:** Open, Assigned, In Progress, Onhold, Resolved, Closed, Waiting for Requester, Waiting for Vendor/3rd Party, Waiting for Internal, Waiting for Approval, Follow Up, Backlog, Cancelled, Budget Review
- **Priorities:** Low, Normal, Medium, High
- **`delete_request`:** moves to SDP Trash (recoverable). No permanent delete tool exists.

---

## Picking this back up on a new machine

### 1. Clone and install

```bash
git clone https://github.com/chrisalibby/servicedeskplus_mcp.git
cd servicedeskplus_mcp
```

With `uv` (preferred for dev):
```bash
uv sync --extra dev
```

With standard `pip`:
```bash
pip install -e ".[dev]"
```

### 2. Create your `.env`

```bash
cp .env.example .env
```

Edit `.env`:

```
SDP_SERVER=sdp.example.com
SDP_PORT=443
SDP_API_KEY=<generate from your SDP profile — Admin > My Profile > API Key>
SDP_PORTAL_ID=
SDP_TIMEOUT=30
SDP_VERIFY_SSL=false
```

### 3. Verify unit tests pass

```bash
pytest
# or: uv run pytest
# Expected: 146 passed, 53 deselected
```

### 4. Run integration smoke tests

```bash
pytest tests/integration/test_smoke.py -m integration -v -s
# Expected: 6 passed — also prints statuses, priorities, categories, technicians
```

### 5. Run full integration suite

```bash
pytest tests/integration/ -m integration -v
# Expected: 51+ passed, 2 skipped (groups, change_close workflow) — the 3 change-creation
# tests may transiently fail with SDP's "URL blocked as maximum access limit exceeded"
# if POST /changes has been hit repeatedly; re-run after a pause
```

---

## Recommended next work

### Immediate (before team rollout)

1. **Distribute `SETUP.md`** — send to each technician. They follow the guide independently; each generates their own SDP API key so actions are attributed correctly in audit logs.

2. **Clean up SDP debug records** — two records were created during development and left open:
   - Change **#89** ("[DEBUG] change probe") — close or delete via SDP UI
   - Worklog on request **#47202** (description: "probe") — delete via the worklog section on that ticket

### If issues come up during rollout

- **"Cannot connect to SDP"** — technician is not on VPN or on-site. `sdp.example.com` is not externally accessible.
- **"Invalid API key"** — technician needs to regenerate in SDP → My Profile → API Key.
- **`sdp-mcp` not found** — Python Scripts folder not on PATH. Full path workaround is in `SETUP.md`.
- **Claude Desktop shows no tools** — restart Claude Desktop after saving the config file.

### Future development (not urgent)

- **Cloud / OAuth2 support** — SDP Cloud uses OAuth2 instead of API key auth; planned if Spero ever migrates to cloud.
- ~~**Attachments**~~ — done 2026-08-01: `list_request_attachments`, `get_request_attachment_content` (download), `add_request_attachment` (upload) confirmed live end-to-end (upload → list → download byte-for-byte match → trashed). See CLAUDE.md quirks table for the `_download`/`upload` path details.
- ~~**Purchase order writes**~~ — done 2026-08-01: `create_purchase_order`/`update_purchase_order` confirmed live; mandatory `items` line-item schema resolved (`product`, `ordered_quantity`, `price`, `category`).
- **CMDB relationship writes** — `add_ci_relationship` still 400s on `relationship_type` regardless of shape tried; likely needs a relationship-type lookup endpoint that doesn't exist yet.
- **Bulk operations** — batch-update multiple tickets in one tool call (e.g. bulk-assign, bulk-close).
- **Change workflow progression** — `close_change` currently blocked by SDP's workflow enforcement. Would need tooling to advance through stages (Requested → In Review → Approved → In Progress → Completed) rather than jumping directly to a terminal state.
- ~~**Releases module**~~ — done 2026-08-01: `/releases` confirmed live (returns 200, not the 404 `/groups` gets). Built `releases.py` with 12 tools (list/get/create/update/close + notes/tasks/worklogs), mirroring changes.py. Only `title` is mandatory to create. `close_release` (`PUT /releases/{id}/_close`) 403s "User does not have this permission" for the standard technician role on this instance — implemented per docs but not verified end-to-end here. `add_release_task` requires `stage: {"id": ...}` or SDP 400s "Value not provided" (changes/problems don't require this).
- ~~**Projects module**~~ — done 2026-08-01: `/projects` confirmed live. Built `projects.py` with 13 tools (list/get/create/update/delete + milestones/tasks/members/comments add+list), mirroring releases.py. Only `title` is mandatory to create. No `move_to_trash` endpoint for projects on this instance (404s) — `delete_project` is a direct, permanent delete. Comment payload key is `content`, not `description` (400s "Extra key found in JSON"). `add_project_member` resolved a given `email_id` to a different technician than requested in one live test — root cause unconfirmed, flagged in the tool docstring. Task creation on projects, unlike releases, does not require `stage`.
- **@mentions / notify-technician on notes (punch-list #15)** — closed out 2026-08-01: not supported by the API. `requests/request_note.html` in the on-prem v3 docs (`manageengine.com/products/service-desk/sdpop-v3-api/`) documents only `description`, `show_to_requester`, `mark_first_response`, and `add_to_linked_requests` on the note POST schema — no `notify_to`, `mentions`, or `email_ids_to_notify` field exists. No live probe was performed since the docs showed no plausible field to try. No code changes made.
- **`reply_request` / `forward_request` (punch-list #11)** — closed out 2026-08-01: not supported by the on-prem v3 REST API. The only email-shaped resource under Requests is `requests/request_draft.html` (`POST/GET/DELETE /requests/{id}/drafts`), and its own description says it "save[s] a email notification content as draft" — there is no send/dispatch/notify operation on that page or anywhere else in the Requests section of the docs (confirmed against the full rendered nav: `request.html`, `request_draft.html`, `request_note.html`, `request_task.html`, `archive_request.html`). Implementing `reply_request`/`forward_request` on the draft endpoint would create an unsent draft while claiming to have sent an email, so it was not built. No live probe was attempted (the docs already rule out a send capability). Revisit if ManageEngine adds a dispatch endpoint in a future release.
