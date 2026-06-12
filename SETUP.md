# Technician Setup Guide — ServiceDesk Plus MCP

This guide covers two deployment options:

- **Local install** — each technician installs the server on their own machine (Steps 1–6 below)
- **Shared server** — an admin runs one central instance; technicians only need to configure Claude Desktop ([jump to Shared Server Setup](#shared-server-setup))

Both options preserve per-user API keys so activity in ServiceDesk Plus is attributed correctly.

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

## Step 6 — Verify

In Claude Desktop, start a new conversation and type:

> List my open ServiceDesk Plus tickets.

Claude should call the `list_requests` tool and return your open tickets. If you see an error about the server, check that you are on the Spero network or VPN.

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

### Admin: server-side setup

**1. Install on the server**

Follow Steps 1–2 of the local install on the server host (clone the repo, `pip install -e .`).

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

Each technician gets their SDP API key (Step 3 of the local install guide) and adds this to their
Claude Desktop config instead of the local-command version:

**Config file location:**

- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "servicedeskplus": {
      "url": "https://mcp.yourdomain.local/mcp",
      "headers": {
        "X-SDP-Api-Key": "<paste your key here>"
      }
    }
  }
}
```

Replace the URL with your actual server hostname, and `<paste your key here>` with your SDP API
key. Save the file and restart Claude Desktop.

> **Network requirement:** Claude Desktop must be able to reach the server. If it is hosted on the
> Spero internal network, you must be on-site or connected to VPN.

---

## What Claude can do with this integration

- Create, update, close, and look up service requests
- Add notes and log work time on tickets
- List open/assigned tickets, filter by date or status
- Search the knowledge base
- Look up requesters, technicians, categories, and subcategories
- View CMDB configuration items (IT services, devices, support groups)
- Create and manage problem and change records
