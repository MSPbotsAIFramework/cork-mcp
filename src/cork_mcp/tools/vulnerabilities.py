"""Tool over Cork's software-vulnerability (CVE) data.

Unlike the other client-scoped tools, `client_uuid` here is optional at the
Cork-API level (Cork allows an account-wide query on this one endpoint) --
see docs/tickets/PRD-21227.md "Data & API contract" for why this is a
documented exception rather than an oversight, and the review-item flag on
enforcing it as effectively required at the MSPbots call-site layer.
"""

from __future__ import annotations

from typing import Callable

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from cork_mcp.api_client import CorkClient
from cork_mcp.errors import CorkApiError, map_api_error, not_configured
from cork_mcp.format import dumps, items_envelope
from cork_mcp.observability import log_tool_call, now

HasCredential = Callable[[], bool]
ClientFactory = Callable[[], "CorkClient | None"]

_READ_ONLY = ToolAnnotations(readOnlyHint=True, idempotentHint=True)


def register(mcp: FastMCP, has_credential: HasCredential, get_client: ClientFactory) -> None:
    @mcp.tool(annotations=_READ_ONLY)
    async def cork_get_software_vulnerabilities(
        client_uuid: str | None = None,
        minimum_cvss_score: float | None = None,
        only_known_exploited: bool | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> str:
        """List software vulnerabilities (CVE, CVSS/EPSS scores, known-exploited flag).

        Args:
            client_uuid: Cork client id. Omit only for an account-wide
                rollup; prefer scoping to one client.
            minimum_cvss_score: Only CVEs at or above this score.
            only_known_exploited: Only CVEs flagged as known-exploited.
            page: 1-based page number.
            page_size: Items per page (default 50, max 200).
        """
        started = now()
        if not has_credential():
            log_tool_call("cork_get_software_vulnerabilities", client_uuid, "not_configured", started)
            return not_configured()
        try:
            async with get_client() as client:
                payload = await client.list_software_vulnerabilities(
                    client_uuid=client_uuid,
                    minimum_cvss_score=minimum_cvss_score,
                    only_known_exploited=only_known_exploited,
                    page=page,
                    page_size=page_size,
                )
        except CorkApiError as exc:
            envelope = map_api_error(exc)
            log_tool_call(
                "cork_get_software_vulnerabilities",
                client_uuid,
                exc.status_code or "network_error",
                started,
            )
            return envelope
        log_tool_call("cork_get_software_vulnerabilities", client_uuid, "ok", started)
        return dumps(items_envelope(payload))
