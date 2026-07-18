FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
WORKDIR /app
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim-bookworm
RUN useradd --create-home --uid 1000 sdp
COPY --from=build --chown=sdp:sdp /app/.venv /app/.venv
USER sdp
ENV PATH="/app/.venv/bin:$PATH" \
    SDP_TRANSPORT=http \
    SDP_HTTP_HOST=0.0.0.0 \
    SDP_HTTP_PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import socket; socket.create_connection(('127.0.0.1', 8000), 3)"
ENTRYPOINT ["sdp-mcp"]
