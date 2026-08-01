# servicedeskplus-mcp

An MCP (Model Context Protocol) server that exposes ManageEngine ServiceDesk Plus On-Premise as tools for AI assistants. Connect Claude Desktop, Claude Code, or any MCP-compatible client to your SDP instance and manage requests, problems, changes, assets, and knowledge base articles through natural language.

## Features

162 tools across eleven modules:

- **Service Requests** — full CRUD, close/assign/pick up/merge (irreversible)/summary; notes (add/list/get/edit/delete); tasks (add/list/get/update/delete); worklogs (add/list/update/delete); resolution get/update; attachments (list/download/upload); approval workflow (add level + approver, send notification, approve/reject); problem and change associations (initiated/caused-by)
- **Problems** — full CRUD + permanent delete; notes (add/list/get/edit/delete); tasks (add/list/get/update/delete); worklogs (add/list/update/delete)
- **Changes** — full CRUD + trash/restore/copy; notes, tasks, worklogs (same shape as requests); approve/reject; approval level listing
- **Releases** — list/get/create/update/close; notes, tasks (stage required), worklogs
- **Projects** — list/get/create/update/delete; milestones; tasks; member management (add/list/remove, with email-to-name verification); comments
- **Assets** — full CRUD (delete is permanent) including depreciation fields (`depreciation_type`, `useful_life`, `salvage_value`) and `list_depreciation_types`; workstations (list/get)
- **CMDB** — list/get/create/update/delete configuration items (module-scoped); list CI relationships *(adding relationships is unresolved on this instance — see Known limitations)*
- **Knowledge Base (Solutions)** — search, get, create (topic required), update, two-step delete (trash then purge), approval status via update, attachment upload, topic create/list
- **Contracts** — list/get/create/update
- **Purchase Orders** — full CRUD (list/get/create/update)
- **Admin lookups** — requesters, technicians, sites, categories, subcategories, priorities, statuses, urgencies, departments, announcements, products, product types, closure codes, change types, depreciation types

### MCP schema resources

Three `sdp://schema/...` resources document write shapes that are easy to get wrong (nested objects, nonstandard payload keys): `sdp://schema/asset`, `sdp://schema/ci-relationship`, `sdp://schema/purchase-order`.

### Known limitations

See [API_COVERAGE.md](API_COVERAGE.md) and [NEXTSTEPS.md](NEXTSTEPS.md) for the full per-module breakdown. Notable gaps:

- `add_request_worklog` — the POST is broken on the requests endpoint on some on-prem instances (the identical payload works fine on problems and changes); confirmed on the Spero instance.
- `add_ci_relationship` — 400s on the relationship-type field regardless of shape tried; likely needs a relationship-type lookup endpoint that doesn't exist yet.
- `close_change` — direct status transitions are rejected where the instance enforces workflow progression (Requested → In Review → Approved → In Progress → Completed).
- No email send API — the on-prem v3 REST API can only save an unsent draft reply/forward (`/requests/{id}/drafts`); there is no dispatch/send operation, so `reply_request`/`forward_request` were not built.
- No @mentions — the note schema has no `notify_to`/`mentions` field.

## Requirements

- Python 3.11 or later
- ManageEngine ServiceDesk Plus On-Premise **v14+** (API v3)
- An SDP API key — each technician generates their own (see below)

## Installation

### From source with uv (recommended for development)

```bash
git clone https://github.com/chrisalibby/servicedeskplus_mcp.git
cd servicedeskplus_mcp
uv sync --extra dev
cp .env.example .env
# edit .env — see Configuration below
```

### With uv tool install

```bash
uv tool install git+https://github.com/chrisalibby/servicedeskplus_mcp.git
```

## Generating an API Key

Each technician generates their own key — actions taken through the MCP server appear in SDP audit logs under their account.

1. Log in to ServiceDesk Plus as yourself.
2. Click your **profile / avatar** in the top-right corner.
3. Select **My Profile** (or **Edit Profile**).
4. Scroll to the **API Key** section and click **Generate**.
5. Copy the key into `SDP_API_KEY` in your `.env`.

> If the API Key section is not visible, ask an admin to enable API access for your technician role under **Admin → Technician Roles**.

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `SDP_SERVER` | yes | `localhost` | Hostname or IP of your SDP server |
| `SDP_PORT` | no | `8080` | Port — use `443` for HTTPS |
| `SDP_API_KEY` | yes | — | Your personal API key |
| `SDP_PORTAL_ID` | no | `` | Portal name for multi-portal setups |
| `SDP_TIMEOUT` | no | `30` | Request timeout in seconds |
| `SDP_VERIFY_SSL` | no | `true` | Set `false` for self-signed certificates |

**HTTPS / self-signed certificates:** If your SDP runs on port 443 with an internal CA or self-signed cert, set `SDP_PORT=443` and `SDP_VERIFY_SSL=false`.

**Instance-specific mandatory fields:** Some SDP instances require `category`, `subcategory`, `description`, and `requester` on every new request. If `create_request` returns an error like *"Please fill the mandatory fields"*, use those parameters. The tool will return the SDP error text directly rather than raising an exception, so the message is always readable.

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "servicedeskplus": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/servicedeskplus_mcp", "sdp-mcp"],
      "env": {
        "SDP_SERVER": "your-sdp-server.example.com",
        "SDP_PORT": "443",
        "SDP_API_KEY": "your-api-key-here",
        "SDP_VERIFY_SSL": "false"
      }
    }
  }
}
```

## Claude Code Configuration

Add to your project or global `.claude/settings.json`:

```json
{
  "mcpServers": {
    "servicedeskplus": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/servicedeskplus_mcp", "sdp-mcp"],
      "env": {
        "SDP_SERVER": "your-sdp-server.example.com",
        "SDP_PORT": "443",
        "SDP_API_KEY": "your-api-key-here",
        "SDP_VERIFY_SSL": "false"
      }
    }
  }
}
```

## Deployment

Three ways to run this server, in increasing order of centralization:

1. **Local stdio, per-technician** (default) — each technician clones the repo and runs `sdp-mcp` locally via `stdio` transport, with their own `SDP_API_KEY` in `.env`. See [SETUP.md](SETUP.md).
2. **Shared HTTP server** — one host runs `sdp-mcp` with `SDP_TRANSPORT=http` (streamable-HTTP, via `uvicorn`). `SDP_API_KEY` is left unset on the server; each client supplies their own key in an `X-SDP-API-Key` header, so actions are still attributed per-technician in SDP's audit logs. Put a reverse proxy (Caddy/nginx) in front for TLS — see [SETUP.md](SETUP.md#shared-server-setup).
3. **Docker / docker-compose** — same shared-HTTP model, containerized. `docker compose up -d --build` builds the image (see `Dockerfile`) and starts it on port 8000 per `docker-compose.yml`; no Python/uv install needed on the host. See [DOCKER.md](DOCKER.md).

Relevant env vars (see `config.py`): `SDP_TRANSPORT` (`stdio`/`http`), `SDP_HTTP_HOST`, `SDP_HTTP_PORT`, `SDP_TRUST_PROXY`.

## Documentation

- [SETUP.md](SETUP.md) — step-by-step technician and admin setup for all three deployment modes
- [USAGE.md](USAGE.md) — practical prompt guide for technicians using this through Claude
- [API_COVERAGE.md](API_COVERAGE.md) — authoritative per-module table of every SDP REST API operation vs. MCP tool coverage
- [CHANGELOG.md](CHANGELOG.md) — release history
- [NEXTSTEPS.md](NEXTSTEPS.md) — current state, known gaps, and future work

## Development

### Setup

```bash
git clone https://github.com/chrisalibby/servicedeskplus_mcp.git
cd servicedeskplus_mcp
uv sync --extra dev
cp .env.example .env
# edit .env with your credentials
```

### Run unit tests (no server needed)

```bash
uv run pytest
# Expected: 238 passed
```

### Run integration tests (requires live SDP in `.env`)

```bash
uv run pytest tests/integration/ -m integration -v
# Expected: 60+ passed (a handful may transiently fail if SDP's POST /changes
# rate limit has been hit recently — re-run after a pause)
```

### Lint and type check

```bash
uv run ruff check src tests
uv run pyright
```

### Run the server

```bash
uv run sdp-mcp
# or
uv run python -m servicedeskplus_mcp
```

## Roadmap

See [NEXTSTEPS.md](NEXTSTEPS.md) for the full list. Highlights:

- **Cloud / OAuth2 support** — SDP Cloud uses OAuth2 instead of API key auth; planned if the target instance ever migrates to cloud
- **CMDB relationship writes** — `add_ci_relationship` still unresolved
- **Bulk operations** — batch-update multiple records in a single tool call
- **Change workflow progression** — tooling to advance a change through its workflow stages so `close_change` can succeed on instances that enforce it

## License

MIT — see [LICENSE](LICENSE) for details.
