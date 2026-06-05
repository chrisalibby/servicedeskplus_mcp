# Next Steps — Real Integration Testing

## What's needed to run integration tests against a live SDP instance

### 1. Connection details (`.env`)

```
SDP_SERVER=        # hostname or IP of your SDP server
SDP_PORT=          # usually 8080 (HTTP) or 443 (HTTPS — needs client change)
SDP_PORTAL_ID=     # only if multi-portal; leave blank for default portal
SDP_API_KEY=       # see step 2
```

### 2. API key

Admin → Users → Technicians → open the technician record → Generate API Key.

Minimum permissions required: read/write on Requests, read on Assets, Workstations,
and the lookup lists (Categories, Priorities, Statuses, etc.).

### 3. Known IDs and names from your instance

Integration tests need real record IDs — nothing is hard-coded. Provide:

- One existing **request ID** (to test `get_request`, `add_request_note`, etc.)
- One existing **asset ID** and/or **workstation ID**
- The exact **status names** your instance uses (SDP allows renaming — "Open" might
  be "New" or "Active" depending on your configuration)
- At least one **technician login name** for assignment and filter tests
- One **category name** and one **priority name** for create/update tests

### 4. Test isolation decision

Integration tests will create real records. Choose one environment:

| Option | Pros | Cons |
|---|---|---|
| **Demo instance** (`demo.servicedeskplus.com`, `admin`/`administrator`) | No setup, no cleanup concerns | Resets periodically; shared with other users |
| **Dev/staging SDP install** | Isolated, persistent | Requires a second install |
| **Production with test requester** | No extra infrastructure | Risk of polluting real data; not recommended |

The demo instance is the fastest path to a first integration run.

---

## What gets built once the above is provided

A `tests/integration/` suite with `pytest -m integration` (skipped by default in CI)
that:

- Reads connection config from `.env`
- Skips gracefully if the server is unreachable
- Creates any records it needs, then cleans them up after each test
- Covers the full CRUD cycle for requests and assets against real SDP responses
