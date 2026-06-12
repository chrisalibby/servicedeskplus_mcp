import sys


def main() -> None:
    from .config import settings

    if settings.SDP_TRANSPORT == "http":
        import uvicorn

        from .server import create_http_app

        uvicorn.run(
            create_http_app(),
            host=settings.SDP_HTTP_HOST,
            port=settings.SDP_HTTP_PORT,
            proxy_headers=settings.SDP_TRUST_PROXY,
            forwarded_allow_ips="*" if settings.SDP_TRUST_PROXY else None,
        )
    else:
        if not settings.SDP_API_KEY:
            sys.exit("SDP_API_KEY is required for stdio transport")
        from .server import mcp

        mcp.run(transport="stdio")


if __name__ == "__main__":
    sys.exit(main())  # type: ignore[arg-type]
