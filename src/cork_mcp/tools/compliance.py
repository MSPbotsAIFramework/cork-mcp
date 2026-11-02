"""Tools over Cork compliance/risk events for a client, plus the static
event-type reference list used to interpret them."""

from __future__ import annotations

from typing import Callable

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from cork_mcp.api_client import CorkClient
from cork_mcp.errors import CorkApiError, invalid_argument, map_api_error, not_configured
from cork_mcp.format import dumps, items_envelope, static_list_envelope
from cork_mcp.observability import log_tool_call, now

HasCredential = Callable[[], bool]
ClientFactory = Callable[[], "CorkClient | None"]

_READ_ONLY = ToolAnnotations(readOnlyHint=True, idempotentHint=True)


def register(mcp: FastMCP, has_credential: HasCredential, get_client: ClientFactory) -> None:
    @mcp.tool(annotations=_READ_ONLY)
    async def cork_get_compliance_events(
        client_uuid: str | None = None,
        show_resolved: bool | None = None,
        at_risk: bool | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> str:
        """List a client's Cork compliance/risk events (type, at-risk, resolved).

        Args:
            client_uuid: Cork client id (required).
            show_resolved: Include resolved events (default excludes them).
            at_risk: Filter to events currently flagged at-risk.
            page: 1-based page number.
            page_size: Items per page (default 50, max 200).
        """
        started = now()
        if not has_credential():
            log_tool_call("cork_get_compliance_events", client_uuid, "not_configured", started)
            return not_configured()
        if not client_uuid:
            log_tool_call("cork_get_compliance_events", None, "invalid_argument", started)
            return invalid_argument("client_uuid is required.")
        try:
            async with get_client() as client:
                payload = await client.list_compliance_events(
                    client_uuid=client_uuid,
                    show_resolved=show_resolved,
                    at_risk=at_risk,
                    page=page,
                    page_size=page_size,
                )
        except CorkApiError as exc:
            envelope = map_api_error(exc)
            log_tool_call(
                "cork_get_compliance_events", client_uuid, exc.status_code or "network_error", started
            )
            return envelope
        log_tool_call("cork_get_compliance_events", client_uuid, "ok", started)
        return dumps(items_envelope(payload))

    @mcp.tool(annotations=_READ_ONLY)
    async def cork_get_compliance_event_types() -> str:
        """List Cork's reference compliance event types (code, description, cure period).

        Static lookup, not client-scoped -- interprets the `event_type`
        field on compliance events.
        """
        started = now()
        if not has_credential():
            log_tool_call("cork_get_compliance_event_types", None, "not_configured", started)
            return not_configured()
        try:
            async with get_client() as client:
                payload = await client.list_compliance_event_types()
        except CorkApiError as exc:
            envelope = map_api_error(exc)
            log_tool_call(
                "cork_get_compliance_event_types", None, exc.status_code or "network_error", started
            )
            return envelope
        log_tool_call("cork_get_compliance_event_types", None, "ok", started)
        return dumps(static_list_envelope(payload))
