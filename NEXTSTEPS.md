# Next Steps

## Current state (as of June 2026)

Integration tested against `sdp.example.com` (Spero Financial SDP on-prem instance).
All unit tests pass (73). Integration tests: 25 pass, 3 skip (see Known Gaps below).

### What works

- Full CRUD for requests, problems, changes, assets, workstations
- Notes, tasks, resolution on requests
- Change approvals (approve/reject)
- All admin lookup endpoints: statuses, priorities, categories, subcategories, sites, departments, urgencies, technicians, requesters, announcements
- Knowledge base: search solutions, get/create articles, list topics
- HTTPS with self-signed cert (`SDP_VERIFY_SSL=false`)
- Multi-portal support via `SDP_PORTAL_ID`
- Readable error messages — SDP's `response_status.messages` text is returned directly instead of raising exceptions

### Known gaps on this instance

| Gap | Detail |
|---|---|
| **Worklogs** | `POST /requests/{id}/worklogs` returns 400 for all field formats tried. Time entry is enabled in SDP Admin. To debug: create a ticket, add a time entry in the UI, open browser DevTools → Network, filter for `worklogs`, copy the successful POST as cURL. That will show the exact payload SDP expects. |
| **Groups** (`list_groups`) | `/groups` returns 400/404. May require a different endpoint path on this SDP version. |
| **CMDB** (`list_configuration_items`) | `/ci` returns 400. CMDB may not be licensed or the endpoint path may differ on this version. |

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
uv sync --extra dev
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
uv run pytest
# Expected: 73 passed, 28 deselected
```

### 4. Run integration smoke tests

```bash
uv run pytest tests/integration/test_smoke.py -m integration -v -s
# Expected: 6 passed — also prints statuses, priorities, categories, technicians
```

### 5. Run full integration suite

```bash
uv run pytest tests/integration/ -m integration -v
# Expected: 25 passed, 3 skipped (worklogs, CMDB, groups)
```

---

## Recommended next work

1. **Resolve worklogs** — highest value unresolved item. Capture a real worklog POST from the browser as described above. Update `add_request_worklog` and its skip marker in `tests/integration/test_requests.py`.

2. **Date range filters on `list_requests`** — technicians frequently need "tickets opened this week" or "overdue items". Add `opened_after`, `opened_before`, `due_before` parameters using SDP's `search_criteria` date condition format.

3. **`list_subcategories` tool** — subcategories are fetched in integration tests directly but there's no MCP tool exposed for them. Add to `admin.py` so an AI can look up valid subcategory names before creating a request.

4. **Write tests for problems and changes** — `test_remaining_modules.py` only reads; add create/update/close round-trips matching the pattern in `test_requests.py`.

5. **Claude Desktop / Claude Code setup at Spero** — once the server is stable, configure it in the team's Claude Desktop config pointing at `sdp.example.com`. Each technician uses their own API key.

6. **CMDB investigation** — check whether CMDB is enabled in SDP Admin and whether the API path differs on this version.
