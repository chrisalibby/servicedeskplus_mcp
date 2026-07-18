# Docker deployment

Run the SDP MCP server as a shared HTTP service so teammates can use it without installing Python, uv, or anything else. One container serves everyone — each user connects with their own SDP technician API key via the `X-SDP-API-Key` header, so actions are attributed to them and no credentials are baked into the image.

## Build & run

```bash
docker compose up -d --build
```

The container listens on port 8000 and connects to `sdp.example.com:443` (see `docker-compose.yml` to change).

## Client setup (teammates — no installs needed)

Each technician first generates their own API key in SDP: **Admin → Technicians → \<their account\> → Generate API key**.

### Claude Code

```bash
claude mcp add --transport http sdp http://<host>:8000/mcp --header "X-SDP-API-Key: <their-key>"
```

### Claude Desktop / other MCP clients

Add a streamable HTTP MCP server:

- URL: `http://<host>:8000/mcp`
- Header: `X-SDP-API-Key: <their-key>`

## Security notes

- **Do not set `SDP_API_KEY` on the container.** If it's set, clients that omit the header silently fall back to that key and act as the wrong technician. Leaving it unset makes misconfigured clients fail loudly.
- Host on the internal network only — the SDP instance is internal anyway.
- API keys travel in request headers. If traffic crosses anything untrusted, put TLS in front (reverse proxy) and set `SDP_TRUST_PROXY=true`.
- `SDP_VERIFY_SSL=false` is required for the self-signed skynet certificate.
