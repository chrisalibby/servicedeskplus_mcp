# Docker deployment

Run the SDP MCP server as a shared HTTP service so teammates can use it without installing Python, uv, or anything else. One container serves everyone — each user connects with their own SDP technician API key via the `X-SDP-API-Key` header, so actions are attributed to them and no credentials are baked into the image.

## How it works

- `Dockerfile` builds a slim image and bakes in `SDP_TRANSPORT=http`, `SDP_HTTP_HOST=0.0.0.0`, and `SDP_HTTP_PORT=8000` so the container always comes up as an HTTP MCP server on port 8000.
- `docker-compose.yml` sets the connection details for your SDP server and publishes that port. It deliberately does **not** set `SDP_API_KEY` — see [Why no server-side API key](#why-no-server-side-api-key) below.

## Configure `docker-compose.yml`

Every setting the container reads comes from `src/servicedeskplus_mcp/config.py`. Edit the `environment:` block before building:

```yaml
services:
  sdp-mcp:
    build: .
    image: servicedeskplus-mcp:latest
    ports:
      - "8000:8000"
    environment:
      SDP_SERVER: sdp.example.com
      SDP_PORT: "443"
      SDP_VERIFY_SSL: "false"
      SDP_TIMEOUT: "60"
      # No SDP_API_KEY — each client sends X-SDP-API-Key
    restart: unless-stopped
```

| Variable | Where it goes | Purpose |
|---|---|---|
| `SDP_SERVER` | `environment:` in `docker-compose.yml` | Hostname (or IP) of your ServiceDesk Plus server. Replace `sdp.example.com` with your real instance's hostname. |
| `SDP_PORT` | same | Port SDP listens on. Use `443` for HTTPS (the normal case) or `8080` for a plain-HTTP on-prem install. |
| `SDP_VERIFY_SSL` | same | Set `"false"` if your SDP instance uses a self-signed or internal-CA certificate (common for on-prem). Leave `"true"` (or omit) for a publicly trusted cert. |
| `SDP_TIMEOUT` | same | Per-request timeout in seconds against the SDP API. `60` is a safe default for slower on-prem instances. |
| `SDP_PORTAL_ID` | same, only if needed | Portal name for multi-portal SDP setups. Omit unless your instance requires it. |
| `SDP_API_KEY` | **not set** | See below — deliberately left out of the container config. |
| `SDP_TRANSPORT` | baked into `Dockerfile` | Already `http` in the image; don't override unless you have a reason to run stdio in a container (you don't). |
| `SDP_HTTP_HOST` | baked into `Dockerfile` | `0.0.0.0` so the server is reachable from outside the container's network namespace. Leave as-is. |
| `SDP_HTTP_PORT` | baked into `Dockerfile` | `8000` internally. To expose the server on a different host port, change the **left** side of `ports:` (see [Port mapping](#port-mapping)) rather than this value. |
| `SDP_TRUST_PROXY` | add to `environment:` once fronted by a proxy | Set `"true"` after putting Caddy/nginx in front (see [TLS](#tls--reverse-proxy)) so `X-Forwarded-*` headers are honored. |

### Why no server-side API key

`SDP_API_KEY` is intentionally absent from `docker-compose.yml`. If it were set, any client that forgot to send its own `X-SDP-API-Key` header would silently fall back to that key and act as the wrong technician in SDP's audit logs — a quiet, hard-to-catch mistake. Leaving it unset makes a misconfigured client fail loudly instead of acting under someone else's identity.

Each technician generates their own key in SDP (**Admin → Technicians → their account → Generate API key**, or **My Profile → API Key** for their own account) and supplies it per-connection — see [Client setup](#client-setup-teammates--no-installs-needed).

## Build and run

```bash
docker compose up -d --build
```

This builds the image from `Dockerfile` and starts it detached. Rebuild/restart after any config or code change with the same command.

Check it came up clean:

```bash
docker compose ps
docker compose logs -f sdp-mcp
```

## Port mapping

The container always listens on `8000` internally (`SDP_HTTP_PORT` in the `Dockerfile`). `docker-compose.yml`'s `ports:` list maps that to the host:

```yaml
ports:
  - "8000:8000"   # host:container — change the first number to publish on a different host port
```

Only the host-side number needs to change; the container side should stay `8000` to match `SDP_HTTP_PORT`.

## Verify / health check

The image ships a `HEALTHCHECK` that confirms the server is accepting TCP connections on port 8000:

```bash
docker inspect --format='{{.State.Health.Status}}' $(docker compose ps -q sdp-mcp)
# expect: healthy
```

For an end-to-end check, add a client (below) and list tools, or hit the endpoint directly:

```bash
curl -i http://localhost:8000/mcp
```

Any HTTP response (even a 4xx from a missing session) means the process is up and routing; a connection refused means the container isn't running or the port mapping is wrong.

## Client setup (teammates — no installs needed)

Each technician first generates their own API key in SDP: **Admin → Technicians → \<their account\> → Generate API key**.

### Claude Code

```bash
claude mcp add --transport http sdp http://<host>:8000/mcp --header "X-SDP-API-Key: <their-key>"
```

### Claude Desktop / other MCP clients

Add a streamable HTTP MCP server:

- URL: `http://<host>:8000/mcp` (or `https://...` once a reverse proxy is in front — see below)
- Header: `X-SDP-API-Key: <their-key>`

## TLS / reverse proxy guidance

The container itself only speaks plain HTTP on port 8000 and shouldn't be exposed to an untrusted network as-is — API keys travel in a request header, so anything between client and container needs to be trusted or encrypted.

- **Internal network only** — if every client already reaches the container over a trusted VPN/LAN at `http://<host>:8000/mcp`, this works without further changes, but headers travel in cleartext on that network.
- **Reverse proxy with TLS (recommended)** — put Caddy or nginx in front of the published port and terminate TLS there:

  ```
  # Caddyfile
  mcp.yourdomain.example {
      reverse_proxy 127.0.0.1:8000
  }
  ```

  ```nginx
  # nginx
  server {
      listen 443 ssl;
      server_name mcp.yourdomain.example;
      ssl_certificate     /path/to/cert.pem;
      ssl_certificate_key /path/to/key.pem;

      location / {
          proxy_pass         http://127.0.0.1:8000;
          proxy_set_header   Host $host;
          proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header   X-Forwarded-Proto $scheme;
          proxy_buffering    off;
          proxy_read_timeout 3600s;
      }
  }
  ```

  `proxy_buffering off` and a long `proxy_read_timeout` are required — MCP uses long-lived streaming connections that stall under default proxy buffering. When adding a proxy, also set `SDP_TRUST_PROXY: "true"` in `docker-compose.yml`'s `environment:` block, and have clients connect to the proxy's `https://` URL instead of the container's port directly.

## Updating

```bash
git pull
docker compose up -d --build
```

`--build` rebuilds the image with any code or dependency changes; `up -d` recreates the container from the new image using the existing `docker-compose.yml` configuration. Clean up old images afterward with `docker image prune` if needed.
