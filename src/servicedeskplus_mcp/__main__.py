import sys


def main() -> None:
    from .server import mcp
    mcp.run(transport="stdio")


if __name__ == "__main__":
    sys.exit(main())  # type: ignore[arg-type]
