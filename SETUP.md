# Technician Setup Guide — ServiceDesk Plus MCP

This guide covers three deployment options:

- **Local install** — each technician installs the server on their own machine (Steps 1–6 below)
- **Shared server** — an admin runs one central instance directly with Python ([jump to Shared Server Setup](#shared-server-setup))
- **Docker** — an admin runs the same shared-server setup in a container, no Python install needed on the host ([see DOCKER.md](DOCKER.md))

All three preserve per-user API keys so activity in ServiceDesk Plus is attributed correctly.

---

## Prerequisites

- **Python 3.11 or later**
  - Mac: download from <https://www.python.org/downloads/> or `brew install python`
  - Windows: download from <https://www.python.org/downloads/> — check **"Add Python to PATH"** during install
- **Git**
  - Mac: `xcode-select --install` or `brew install git`
  - Windows: download from <https://git-scm.com/>
- **Claude Desktop** — download from <https://claude.ai/download>
- **Network access to `sdp.example.com`** — must be on-site or VPN

---

## Step 1 — Clone the repo

```
git clone https://github.com/chrisalibby/servicedeskplus_mcp.git
cd servicedeskplus_mcp
```

## Step 2 — Install dependencies

With `uv` (preferred):

```
uv sync --extra dev
```

Or with plain `pip`:

```
pip install -e .
```

This installs the `sdp-mcp` command. Verify it appears:

```
sdp-mcp --help
```

If the command is not found, your Python Scripts directory is not on your PATH.

**Mac** — find the path with:

```sh
python3 -m site --user-base
```

Add `<that path>/bin` to your shell profile (`~/.zshrc` or `~/.bash_profile`):

```sh
export PATH="$HOME/Library/Python/3.x/bin:$PATH"
```

Reload with `source ~/.zshrc`, then retry `sdp-mcp --help`.

**Windows** — the Scripts folder is typically:

```
C:\Users\<you>\AppData\Roaming\Python\Python3xx\Scripts
```

Add it to your PATH via **System Properties → Environment Variables**, then open a new terminal and retry.

## Step 3 — Get your SDP API key

1. Log in to ServiceDesk Plus at <https://sdp.example.com>
2. Click your name (top-right) → **My Profile**
3. Scroll to **API Key** → click **Generate** if none exists
4. Copy the key — you will not see it again

## Step 4 — Create your `.env` file

In the `servicedeskplus_mcp` folder, create a file named `.env`:

```dotenv
SDP_SERVER=sdp.example.com
SDP_PORT=443
SDP_API_KEY=<paste your key here>
SDP_PORTAL_ID=
SDP_TIMEOUT=30
SDP_VERIFY_SSL=false
```

Keep this file private — it contains your API key.

> **Windows tip:** File Explorer hides extensions by default. Name the file `.env` in Notepad by choosing **Save as type: All Files** and typing `.env` as the filename.

## Step 5 — Configure Claude Desktop

Open Claude Desktop → **Settings** → **Developer** → **Edit Config**.

The config file location:

- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add the following entry inside the `mcpServers` object:

```json
{
  "mcpServers": {
    "servicedeskplus": {
      "command": "sdp-mcp",
      "env": {
        "SDP_SERVER": "sdp.example.com",
        "SDP_PORT": "443",
        "SDP_API_KEY": "<paste your key here>",
        "SDP_VERIFY_SSL": "false",
        "SDP_TIMEOUT": "30"
      }
    }
  }
}
```

Replace `<paste your key here>` with your actual API key. Save the file, then **restart Claude Desktop**.

> **If `sdp-mcp` is not on your PATH**, use the full path as the `"command"` value instead. On Mac, run `which sdp-mcp` in Terminal to find it. On Windows, run `where sdp-mcp` in Command Prompt and use backslashes: `"C:\\Users\\<you>\\...\\sdp-mcp.exe"`.

**Alternative — run from a cloned repo with uv** (no install step; useful for development):

```json
{
  "mcpServers": {
    "servicedeskplus": {
      "command": "uv",
      "args": ["run", "--project", "/Users/<you>/Projects/servicedeskplus_mcp", "sdp-mcp"],
      "env": {
        "SDP_SERVER": "sdp.example.com",
        "SDP_PORT": "443",
        "SDP_API_KEY": "<paste your key here>",
        "SDP_VERIFY_SSL": "false",
        "SDP_TIMEOUT": "30"
      }
    }
  }
}
```

> **Use an absolute path** for `--project` (and for `"command"` if `uv` isn't on Claude Desktop's PATH — run `which uv` to find it, e.g. `/opt/homebrew/bin/uv`). Claude Desktop launches the command without a shell, so `~` is **not** expanded — `"~/Projects/..."` fails with `Project directory does not exist`.

## Step 6 — Verify

In Claude Desktop, start a new conversation and type:

> List my open ServiceDesk Plus tickets.

Claude should call the `list_requests` tool and return your open tickets. If you see an error about the server, check that you are on the internal network or VPN.

### Optional — verify the test suite

If you cloned for development rather than just running the server:

```bash
uv run pytest
# Expected: 238 passed
```

Integration tests require a real `.env` and hit the live SDP instance:

```bash
uv run pytest tests/integration/ -m integration -v
# Expected: 60+ passed (a few change-creation tests may transiently fail if SDP's
# POST /changes rate limit was hit recently — re-run after a pause)
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `sdp-mcp: command not found` | Add the Python Scripts directory to your PATH (see Step 2) |
| `Cannot connect to SDP` | Make sure you are on-site or connected to VPN |
| `Invalid API key` | Regenerate your key in SDP → My Profile |
| `SSL certificate error` | Confirm `SDP_VERIFY_SSL=false` is set |
| Claude Desktop shows no tools | Restart Claude Desktop after saving the config |

---

## Shared Server Setup

This option runs one instance of the MCP server on an internal host. Technicians point Claude
Desktop at a URL instead of running a local command — no Python, no cloning, nothing to install
on their machines.

> **Prefer Docker?** If you'd rather not install Python/uv on the host at all, see
> [DOCKER.md](DOCKER.md) — it covers the same shared-server model (`SDP_TRANSPORT=http`,
> per-connection `X-SDP-API-Key`) via `docker compose up -d --build`. In short: the `Dockerfile`
> builds a slim image with the `sdp-mcp` entrypoint already set to `SDP_TRANSPORT=http` /
> `SDP_HTTP_HOST=0.0.0.0` / `SDP_HTTP_PORT=8000`; `docker-compose.yml` sets `SDP_SERVER`,
> `SDP_PORT`, `SDP_VERIFY_SSL`, and `SDP_TIMEOUT` for `sdp.example.com` and deliberately
> **omits `SDP_API_KEY`** so every client must supply its own `X-SDP-API-Key` header. The compose
> file does not include a reverse proxy or TLS termination — the same Caddy/nginx guidance below
> (step 4) applies in front of the container's published port 8000, exactly as it would for a
> bare Python process. The technician-side Claude Desktop/Claude Code config below is identical
> either way; only the admin's server-side setup differs.

### Admin: server-side setup

**1. Install on the server**

Follow Steps 1–2 of the local install on the server host (clone the repo, then `uv sync --extra dev` or `pip install -e .`).

**2. Create the server `.env`**

```dotenv
SDP_SERVER=sdp.example.com
SDP_PORT=443
SDP_VERIFY_SSL=false
SDP_TIMEOUT=30
SDP_TRANSPORT=http
SDP_HTTP_HOST=127.0.0.1
SDP_HTTP_PORT=8000
SDP_TRUST_PROXY=true
```

`SDP_API_KEY` is intentionally omitted — each user supplies their own via Claude Desktop.

**3. Run the server**

For a quick test:

```sh
sdp-mcp
```

For a persistent background process (Linux/Mac):

```sh
nohup sdp-mcp >> /var/log/sdp-mcp.log 2>&1 &
```

Or use a systemd unit file (`/etc/systemd/system/sdp-mcp.service`):

```ini
[Unit]
Description=ServiceDesk Plus MCP Server
After=network.target

[Service]
ExecStart=/usr/local/bin/sdp-mcp
WorkingDirectory=/opt/servicedeskplus_mcp
EnvironmentFile=/opt/servicedeskplus_mcp/.env
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start: `systemctl enable --now sdp-mcp`

**4. Configure a reverse proxy (required for HTTPS)**

The server binds to `127.0.0.1:8000` only — do **not** expose this port externally. Put Caddy or
nginx in front to handle TLS.

> **Caddy** (`/etc/caddy/Caddyfile`):
>
> ```
> mcp.yourdomain.local {
>     reverse_proxy 127.0.0.1:8000
> }
> ```
>
> Caddy provisions TLS automatically and passes the required forwarding headers.

> **nginx** (`/etc/nginx/sites-available/sdp-mcp`):
>
> ```nginx
> server {
>     listen 443 ssl;
>     server_name mcp.yourdomain.local;
>     ssl_certificate     /path/to/cert.pem;
>     ssl_certificate_key /path/to/key.pem;
>
>     location / {
>         proxy_pass         http://127.0.0.1:8000;
>         proxy_set_header   Host $host;
>         proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
>         proxy_set_header   X-Forwarded-Proto $scheme;
>         proxy_buffering    off;
>         proxy_read_timeout 3600s;
>     }
> }
> ```
>
> `proxy_buffering off` and the extended `proxy_read_timeout` are required — MCP uses long-lived
> streaming connections that will stall under nginx's default buffering settings.

Reload your proxy after saving the config.

---

### Technician: Claude Desktop config

Claude Desktop's `claude_desktop_config.json` does **not** support a remote HTTP server declared
directly as `"url"` + `"headers"` — that shape is silently rejected ("Some MCP servers could not
be loaded", entry skipped) in current versions. Remote servers with custom auth headers are only
supported through the in-app **Settings → Connectors → Add custom connector** UI, and that UI has
had its own bugs around headers being silently ignored. The reliable option is to bridge through
[`mcp-remote`](https://www.npmjs.com/package/mcp-remote), a local stdio-to-HTTP proxy that Claude
Desktop launches like any other local command, forwarding your header to the real server underneath.

Each technician gets their SDP API key (Step 3 of the local install guide) and adds this to their
Claude Desktop config instead of the local-command version. Requires Node.js/`npx` on the
technician's machine.

**Config file location:**

- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Mac/Linux:**

```json
{
  "mcpServers": {
    "servicedeskplus": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.yourdomain.local/mcp",
        "--header",
        "X-SDP-Api-Key: <paste your key here>"
      ]
    }
  }
}
```

**Windows:** plain `"command": "npx"` fails here — when Node.js is installed at the default
`C:\Program Files\nodejs`, Claude Desktop resolves `npx` to that absolute path and hands it to
`cmd.exe` unquoted, which splits on the space and fails with `'C:\Program' is not recognized as an
internal or external command`. Wrap it in `cmd /c` so `cmd.exe`'s own PATH lookup finds `npx`
instead of Claude Desktop pre-resolving a space-containing path:

```json
{
  "mcpServers": {
    "servicedeskplus": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "mcp-remote",
        "https://mcp.yourdomain.local/mcp",
        "--header",
        "X-SDP-Api-Key: <paste your key here>"
      ]
    }
  }
}
```

Replace the URL with your actual server hostname, and `<paste your key here>` with your SDP API
key. Save the file and fully quit/relaunch Claude Desktop (not just close the window).

**Claude Code CLI** can point at the same remote server directly, without `mcp-remote`, since it
supports HTTP transport with custom headers natively:

```bash
claude mcp add --transport http servicedeskplus https://mcp.yourdomain.local/mcp \
  --header "X-SDP-Api-Key: <paste your key here>"
```

> **Network requirement:** the client must be able to reach the server. If it is hosted on the
> internal network, you must be on-site or connected to VPN.

---

## What Claude can do with this integration

This server exposes 162 tools covering requests, problems, changes, releases, projects, assets,
CMDB, the knowledge base, contracts, purchase orders, and admin lookups — full lifecycles
(notes, tasks, worklogs, attachments, approvals) on the ticket-shaped modules, not just basic
CRUD. For the practical, prompt-oriented version of "what can I ask for", see
**[USAGE.md](USAGE.md)**. For the exhaustive per-endpoint breakdown, see
[API_COVERAGE.md](API_COVERAGE.md).
