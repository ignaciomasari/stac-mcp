"""Entry point for running the STAC MCP server as ``python -m stac_mcp``."""

import argparse

from stac_mcp.server import app


def main() -> None:
    """Launch the STAC MCP server CLI."""
    parser = argparse.ArgumentParser(description="STAC MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind (for sse/http transport)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind (for sse/http transport)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        app.run()
    else:
        app.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
