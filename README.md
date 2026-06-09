# servicedeskplus-mcp

An MCP (Model Context Protocol) server that exposes ManageEngine ServiceDesk Plus On-Premise as tools for AI assistants. Connect Claude Desktop, Claude Code, or any MCP-compatible client to your SDP instance and manage requests, problems, changes, assets, and knowledge base articles through natural language.

## Features

- **Service Requests** — list, create, update, close, trash, assign, pick up, add notes/tasks, manage resolutions
- **Problems** — list, create, update, close, add notes
- **Changes** — list, create, update, close, add notes/tasks, manage approvals (approve/reject)
- **Assets** — list, create, update assets and workstations
- **CMDB** — list, create, update configuration items; manage CI relationships *(availability depends on your SDP license)*
- **Knowledge Base** — search solutions, get/create articles, list topics
- **Admin lookups** — requesters, technicians, sites, categories, subcategories, priorities, statuses, urgencies, departments, announcements

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

## Tool Reference

### Service Requests (`tools/requests.py`)

| Tool | Description |
|---|---|
| `list_requests` | List requests with optional status/technician filters and pagination |
| `get_request` | Get a single request by ID |
| `create_request` | Create a new service request (supports subcategory) |
| `update_request` | Update fields on an existing request |
| `close_request` | Close a request; closure code is optional |
| `delete_request` | Move a request to trash (recoverable from SDP Trash view) |
| `assign_request` | Assign a request to a technician and/or group |
| `pickup_request` | Pick up a request (assign to the API key owner) |
| `add_request_note` | Add a public or private note |
| `list_request_notes` | List all notes on a request |
| `add_request_worklog` | Log time worked on a request |
| `list_request_worklogs` | List all worklog entries |
| `get_request_resolution` | Get the current resolution |
| `update_request_resolution` | Set or update the resolution |
| `list_request_tasks` | List tasks associated with a request |
| `add_request_task` | Add a task to a request |

### Problems (`tools/problems.py`)

| Tool | Description |
|---|---|
| `list_problems` | List problems with optional status filter |
| `get_problem` | Get a single problem by ID |
| `create_problem` | Create a new problem record |
| `update_problem` | Update an existing problem |
| `close_problem` | Close a problem |
| `add_problem_note` | Add a note to a problem |

### Changes (`tools/changes.py`)

| Tool | Description |
|---|---|
| `list_changes` | List changes with optional status filter |
| `get_change` | Get a single change by ID |
| `create_change` | Create a new change record |
| `update_change` | Update an existing change |
| `close_change` | Close a change |
| `add_change_note` | Add a note to a change |
| `list_change_tasks` | List tasks on a change |
| `list_pending_approvals` | List pending approvals for a change |
| `approve_change` | Approve a pending change approval |
| `reject_change` | Reject a pending change approval |

### Assets (`tools/assets.py`)

| Tool | Description |
|---|---|
| `list_assets` | List assets with optional type/state filters |
| `get_asset` | Get a single asset by ID |
| `create_asset` | Create a new asset record |
| `update_asset` | Update an existing asset |
| `list_workstations` | List workstation assets |
| `get_workstation` | Get a single workstation by ID |

### CMDB (`tools/cmdb.py`)

| Tool | Description |
|---|---|
| `list_configuration_items` | List CIs with optional type filter |
| `get_configuration_item` | Get a single CI by ID |
| `create_configuration_item` | Create a new CI |
| `update_configuration_item` | Update an existing CI |
| `list_ci_relationships` | List relationships for a CI |
| `add_ci_relationship` | Add a relationship between two CIs |

### Knowledge Base (`tools/solutions.py`)

| Tool | Description |
|---|---|
| `search_solutions` | Search solutions by keyword |
| `get_solution` | Get a single solution article by ID |
| `create_solution` | Create a new solution article |
| `list_solution_topics` | List all knowledge base topics |

### Admin Lookups (`tools/admin.py`)

| Tool | Description |
|---|---|
| `list_requesters` | List all requesters |
| `get_requester` | Get a requester by ID |
| `list_technicians` | List all technicians |
| `get_technician` | Get a technician by ID |
| `list_groups` | List technician groups |
| `list_sites` | List all sites |
| `list_categories` | List request categories |
| `list_priorities` | List priority levels |
| `list_statuses` | List request statuses |
| `list_urgencies` | List urgency levels |
| `list_departments` | List all departments |
| `list_announcements` | List active announcements |

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
```

### Run integration tests (requires live SDP in `.env`)

```bash
uv run pytest tests/integration/ -m integration -v
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

## Known Limitations

These were discovered during integration testing against a real on-prem instance:

| Area | Status | Notes |
|---|---|---|
| Worklogs | Broken | `POST /requests/{id}/worklogs` rejects all field formats with 400. Time entry is enabled in SDP Admin but the API contract is unclear. To debug: open a ticket, add a time entry in the UI, capture the request in browser DevTools. |
| Groups (`list_groups`) | May 404 | `/groups` endpoint returns 404 or 400 on some instances. |
| CMDB (`list_configuration_items`) | May be unavailable | `/ci` returns 400/404 on instances without CMDB licensed or enabled. |
| Closure codes | Optional | `close_request` works without a closure code; include one only if your instance requires it. |
| `delete_request` | Trash only | Moves to SDP Trash (recoverable). There is no permanently-delete tool. |

## Roadmap

- **Resolve worklog API** — capture browser network traffic to determine correct field format for on-prem v14
- **Cloud / OAuth2 support** — SDP Cloud uses OAuth2; planned as next major feature
- **Attachments** — upload and download file attachments on requests, problems, and changes
- **Bulk operations** — batch-update multiple records in a single tool call
- **Date range filters** — `list_requests` filtered by open date, due date, etc.

## License

MIT — see [LICENSE](LICENSE) for details.
