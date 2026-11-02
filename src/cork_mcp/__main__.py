"""Entrypoint: run the Cork MCP server over Streamable HTTP."""

from __future__ import annotations

import logging

import uvicorn

from cork_mcp.config import settings
from cork_mcp.server import create_app


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    uvicorn.run(app, host=settings.mcp_http_host, port=settings.mcp_http_port, log_level="info")


if __name__ == "__main__":
    main()
