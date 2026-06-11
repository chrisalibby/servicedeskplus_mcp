# Technician Setup Guide — ServiceDesk Plus MCP

This guide gets the SDP MCP server running in Claude Desktop on a Windows machine at Spero Financial.
Each technician follows these steps once and uses their own API key.

---

## Prerequisites

- Python 3.11 or later — download from https://www.python.org/downloads/
- Git — download from https://git-scm.com/
- Claude Desktop — download from https://claude.ai/download
- Network access to `sdp.example.com` (must be on-site or VPN)

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

If Windows says the command is not found, add your Python Scripts folder to PATH:
`C:\Users\<you>\AppData\Roaming\Python\Python3xx\Scripts`

## Step 3 — Get your SDP API key

1. Log in to ServiceDesk Plus at https://sdp.example.com
2. Click your name (top-right) → **My Profile**
3. Scroll to **API Key** → click **Generate** if none exists
4. Copy the key — you will not see it again

## Step 4 — Create your `.env` file

In the `servicedeskplus_mcp` folder, create a file named `.env` (no extension):

```
SDP_SERVER=sdp.example.com
SDP_PORT=443
SDP_API_KEY=<paste your key here>
SDP_PORTAL_ID=
SDP_TIMEOUT=30
SDP_VERIFY_SSL=false
```

Keep this file private — it contains your API key.

## Step 5 — Configure Claude Desktop

Open Claude Desktop → **Settings** → **Developer** → **Edit Config**.

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

> **Note:** If `sdp-mcp` is not on your PATH, use the full path instead:
> `"command": "C:\\Users\\<you>\\AppData\\Roaming\\Python\\Python313\\Scripts\\sdp-mcp.exe"`

## Step 6 — Verify

In Claude Desktop, start a new conversation and type:

> List my open ServiceDesk Plus tickets.

Claude should call the `list_requests` tool and return your open tickets. If you see an error about the server, check that you are on the Spero network or VPN.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `sdp-mcp: command not found` | Add Python Scripts to your PATH (see Step 2) |
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
