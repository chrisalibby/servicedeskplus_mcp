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

- **Host:** `sdp.example.com:443` (HTTPS, self-signed cert)
- **Config:** `SDP_VERIFY_SSL=false` required
- **Mandatory create_request fields:** subject, description, requester, category, subcategory
- **API auth:** `Authtoken: {api_key}` header; bodies are `application/x-www-form-urlencoded` with JSON in `input_data` key
- **`delete_request`** moves to trash (recoverable) — does NOT permanently delete

## Testing

```bash
uv run pytest                                      # unit tests (no server)
uv run pytest tests/integration/ -m integration   # live server tests
```

Unit tests use `respx` to mock httpx. Integration tests read real credentials from `.env` — the integration conftest builds its own `Settings` instance directly from `.env` values so it never contaminates the unit test environment.

Integration test status: **25 pass, 3 skip**
- Worklogs: broken — all field formats return 400; needs browser network capture to debug
- CMDB (`/ci`): unavailable on this instance
- Groups (`/groups`): unavailable on this instance

## Known endpoint quirks

| Tool | Quirk |
|---|---|
| `list_solution_topics` | Uses `/topics` endpoint, not `/solution_topics` |
| `delete_request` | `DELETE /requests/{id}/move_to_trash` only — no permanent delete |
| `close_request` | Omit `closure_code` unless explicitly configured; including it causes 400 on this instance |
| `add_request_worklog` | Skipped — `POST /requests/{id}/worklogs` rejects all tested formats |

## Code style

- No comments unless the why is non-obvious
- No docstrings beyond the one-line tool description (used by MCP)
- ruff + pyright must pass clean before committing
- No Co-Authored-By trailers in commits — author is Chris Libby only
- Commits: `git commit -m "..."` with no attribution lines
