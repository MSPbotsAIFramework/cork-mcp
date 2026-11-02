"""Tool over a client's active Cork warranty/coverage packages."""

from __future__ import annotations

from typing import Callable

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from cork_mcp.api_client import CorkClient
from cork_mcp.errors import CorkApiError, invalid_argument, map_api_error, not_configured
from cork_mcp.format import dumps, items_envelope
from cork_mcp.observability import log_tool_call, now

HasCredential = Callable[[], bool]
ClientFactory = Callable[[], "CorkClient | None"]

_READ_ONLY = ToolAnnotations(readOnlyHint=True, idempotentHint=True)


def register(mcp: FastMCP, has_credential: HasCredential, get_client: ClientFactory) -> None:
    @mcp.tool(annotations=_READ_ONLY)
    async def cork_get_warranties(
        client_uuid: str | None = None, page: int | None = None, page_size: int | None = None
    ) -> str:
        """List a client's active Cork cyber-warranty packages and coverage dates.

        Args:
            client_uuid: Cork client id (required).
            page: 1-based page number.
            page_size: Items per page (default 50, max 200).
        """
        started = now()
        if not has_credential():
            log_tool_call("cork_get_warranties", client_uuid, "not_configured", started)
            return not_configured()
        if not client_uuid:
            log_tool_call("cork_get_warranties", None, "invalid_argument", started)
            return invalid_argument("client_uuid is required.")
        try:
            async with get_client() as client:
                payload = await client.list_warranties(client_uuid=client_uuid, page=page, page_size=page_size)
        except CorkApiError as exc:
            envelope = map_api_error(exc)
            log_tool_call("cork_get_warranties", client_uuid, exc.status_code or "network_error", started)
            return envelope
        log_tool_call("cork_get_warranties", client_uuid, "ok", started)
        return dumps(items_envelope(payload))
