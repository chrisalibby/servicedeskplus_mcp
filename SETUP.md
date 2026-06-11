# Technician Setup Guide — ServiceDesk Plus MCP

This guide gets the SDP MCP server running in Claude Desktop at Spero Financial.
Each technician follows these steps once and uses their own API key.

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

## What Claude can do with this integration

- Create, update, close, and look up service requests
- Add notes and log work time on tickets
- List open/assigned tickets, filter by date or status
- Search the knowledge base
- Look up requesters, technicians, categories, and subcategories
- View CMDB configuration items (IT services, devices, support groups)
- Create and manage problem and change records
