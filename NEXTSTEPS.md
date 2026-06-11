# Next Steps

## Current state (as of June 2026)

Integration tested against `sdp.example.com` (Spero Financial SDP on-prem instance).
All unit tests pass (74). Integration tests: 35 pass, 2 skip (see Known Gaps below).

### What works

- Full CRUD for requests, problems, changes, assets, workstations
- CMDB: list all CIs (`/cmdb`), get by ID, filter by module type (`cmdb_itservice`, `cmdb_departmentci`, `cmdb_people`, `cmdb_supportgroup`, `cmdb_switchportci`)
- Notes, tasks, worklogs, resolution on requests
- Change approvals (approve/reject)
- All admin lookup endpoints: statuses, priorities, categories, subcategories, sites, departments, urgencies, technicians, requesters, announcements
- Knowledge base: search solutions, get/create articles, list topics
- HTTPS with self-signed cert (`SDP_VERIFY_SSL=false`)
- Multi-portal support via `SDP_PORTAL_ID`
- Readable error messages — SDP's `response_status.messages` text is returned directly instead of raising exceptions

### Known gaps on this instance

| Gap | Detail |
|---|---|
| **Groups** (`list_groups`) | `/groups` returns 400/404. May require a different endpoint path on this SDP version. |
| **CMDB create/update/relationships** | `POST /cmdb` and `/cmdb/{id}/relationships` return 404. List and get-by-ID work. |
| **`close_change`** | Changes require workflow progression (Requested → In Review → Approved → In Progress → Completed). Direct status PUT is rejected on this instance. The tool is kept for other instances with simpler configurations. |

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
# Expected: 74 passed, 37 deselected
```

### 4. Run integration smoke tests

```bash
pytest tests/integration/test_smoke.py -m integration -v -s
# Expected: 6 passed — also prints statuses, priorities, categories, technicians
```

### 5. Run full integration suite

```bash
pytest tests/integration/ -m integration -v
# Expected: 35 passed, 2 skipped (groups, change_close workflow)
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
- **Attachments** — upload/download files on requests, problems, and changes.
- **Bulk operations** — batch-update multiple tickets in one tool call (e.g. bulk-assign, bulk-close).
- **Change workflow progression** — `close_change` currently blocked by SDP's workflow enforcement. Would need tooling to advance through stages (Requested → In Review → Approved → In Progress → Completed) rather than jumping directly to a terminal state.
