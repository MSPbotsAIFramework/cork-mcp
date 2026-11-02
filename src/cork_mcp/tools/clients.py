"""Tools over Cork's client roster and per-client Cyber Score history."""

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
    async def cork_get_clients(page: int | None = None, page_size: int | None = None) -> str:
        """List the MSP's Cork-covered clients with warranty status and Cyber Score.

        Args:
            page: 1-based page number.
            page_size: Items per page (default 50, max 200).
        """
        started = now()
        if not has_credential():
            log_tool_call("cork_get_clients", None, "not_configured", started)
            return not_configured()
        try:
            async with get_client() as client:
                payload = await client.list_clients(page=page, page_size=page_size)
        except CorkApiError as exc:
            envelope = map_api_error(exc)
            log_tool_call("cork_get_clients", None, exc.status_code or "network_error", started)
            return envelope
        log_tool_call("cork_get_clients", None, "ok", started)
        return dumps(items_envelope(payload))

    @mcp.tool(annotations=_READ_ONLY)
    async def cork_get_client_score_history(
        client_uuid: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> str:
        """Get a client's Cork Cyber Score history, newest first.

        Args:
            client_uuid: Cork client id (required).
            created_after: ISO-8601 timestamp lower bound.
            created_before: ISO-8601 timestamp upper bound.
            page: 1-based page number.
            page_size: Items per page (default 50, max 200).
        """
        started = now()
        if not has_credential():
            log_tool_call("cork_get_client_score_history", client_uuid, "not_configured", started)
            return not_configured()
        if not client_uuid:
            log_tool_call("cork_get_client_score_history", None, "invalid_argument", started)
            return invalid_argument("client_uuid is required.")
        try:
            async with get_client() as client:
                payload = await client.get_client_score_history(
                    client_uuid=client_uuid,
                    created_after=created_after,
                    created_before=created_before,
                    page=page,
                    page_size=page_size,
                )
        except CorkApiError as exc:
            envelope = map_api_error(exc)
            log_tool_call(
                "cork_get_client_score_history", client_uuid, exc.status_code or "network_error", started
            )
            return envelope
        log_tool_call("cork_get_client_score_history", client_uuid, "ok", started)
        return dumps(items_envelope(payload))
