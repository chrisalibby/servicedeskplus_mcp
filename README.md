# servicedeskplus-mcp

An MCP (Model Context Protocol) server that exposes ManageEngine ServiceDesk Plus On-Premise as tools for AI assistants. Connect Claude Desktop, Claude Code, or any MCP-compatible client to your SDP instance and manage requests, problems, changes, assets, CMDB, and knowledge base articles through natural language.

## Features

- **Service Requests** — list, create, update, close, delete, assign, pick up, add notes/worklogs/tasks, manage resolutions
- **Problems** — list, create, update, close, add notes
- **Changes** — list, create, update, close, add notes/tasks, manage approvals (approve/reject)
- **Assets** — list, create, update assets and workstations
- **CMDB** — list, create, update configuration items; manage CI relationships
- **Knowledge Base** — search solutions, get/create articles, list topics
- **Admin lookups** — requesters, technicians, groups, sites, categories, priorities, statuses, urgencies, departments, announcements

## Requirements

- Python 3.11 or later
- ManageEngine ServiceDesk Plus On-Premise **v14+** (API v3)
- An SDP API key (see below)

## Installation

### With uv (recommended)

```bash
uv tool install servicedeskplus-mcp
```

### With pip

```bash
pip install servicedeskplus-mcp
```

### From source

```bash
git clone https://github.com/clibby/servicedeskplus-mcp.git
cd servicedeskplus-mcp
uv sync
```

## Generating an API Key

1. Log in to ServiceDesk Plus as an administrator.
2. Navigate to **Admin** → **Users** → **Technicians**.
3. Open the technician record you want to use for API access.
4. Click **Generate** next to the API Key field.
5. Copy the key and set it as `SDP_API_KEY` in your environment (see Configuration below).

## Configuration

The server reads configuration from environment variables. Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `SDP_SERVER` | yes | `localhost` | Hostname or IP of your SDP server |
| `SDP_PORT` | no | `8080` | HTTP port SDP listens on |
| `SDP_API_KEY` | yes | — | API key generated in SDP Admin |
| `SDP_PORTAL_ID` | no | `` | Portal ID for multi-portal setups |
| `SDP_TIMEOUT` | no | `30` | Request timeout in seconds |

## Claude Desktop Configuration

Add this to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "servicedeskplus": {
      "command": "sdp-mcp",
      "env": {
        "SDP_SERVER": "your-sdp-server.example.com",
        "SDP_PORT": "8080",
        "SDP_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

If you installed from source with `uv`:

```json
{
  "mcpServers": {
    "servicedeskplus": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/servicedeskplus-mcp", "sdp-mcp"],
      "env": {
        "SDP_SERVER": "your-sdp-server.example.com",
        "SDP_API_KEY": "your-api-key-here"
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
      "command": "sdp-mcp",
      "env": {
        "SDP_SERVER": "your-sdp-server.example.com",
        "SDP_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Tool Reference

### Service Requests (`tools/requests.py`)

| Tool | Description |
|---|---|
| `list_requests` | List requests with optional status/technician filters |
| `get_request` | Get a single request by ID |
| `create_request` | Create a new service request |
| `update_request` | Update fields on an existing request |
| `close_request` | Close a request with closure code and comments |
| `delete_request` | Permanently delete a request |
| `assign_request` | Assign a request to a technician/group |
| `pickup_request` | Pick up a request (assign to API key owner) |
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
git clone https://github.com/clibby/servicedeskplus-mcp.git
cd servicedeskplus-mcp
uv sync --extra dev
cp .env.example .env
# edit .env with your SDP credentials
```

### Run tests

```bash
uv run pytest
```

### Lint

```bash
uv run ruff check src tests
uv run ruff format --check src tests
```

### Type check

```bash
uv run pyright
```

### Run the server locally

```bash
uv run sdp-mcp
# or
uv run python -m servicedeskplus_mcp
```

### Integration tests

The unit test suite uses `respx` to mock httpx — no real SDP instance needed. For manual integration testing against the ManageEngine demo instance:

1. Go to `demo.servicedeskplus.com` and log in as `admin` / `administrator`.
2. Generate an API key under **Admin → Technicians**.
3. Set `SDP_SERVER=demo.servicedeskplus.com SDP_PORT=443` (or the appropriate port) and `SDP_API_KEY=<key>` in your `.env`.
4. Run `uv run sdp-mcp` and point your MCP client at it.

## Roadmap

- **Cloud/OAuth2 support** — ManageEngine ServiceDesk Plus Cloud uses OAuth2 rather than API key auth. This is planned as the next major feature.
- **Attachments** — Upload and download file attachments on requests, problems, and changes.
- **Bulk operations** — Batch-update multiple records in a single tool call.
- **Webhooks / SSE** — Subscribe to SDP events and surface them as MCP notifications.

## License

MIT — see [LICENSE](LICENSE) for details.
