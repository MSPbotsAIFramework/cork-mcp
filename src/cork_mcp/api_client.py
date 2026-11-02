"""Thin async wrapper around Cork's REST API.

One CorkClient is created per request (see server.py's credential
middleware) and carries that request's own API key -- never a module-level
singleton, so concurrent requests for different MSP accounts never share a
credential (vendor-mcp-development SOP SS3.3/SS3.4).

Endpoint paths and response shapes are taken from a read-only review of the
open-source WYRE-AI/cork-mcp reference implementation (src/client.ts,
src/types.ts) -- see docs/tickets/PRD-21227.md "Current state" and "Tech
design" for the citation. Cork itself publishes no public developer portal.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from cork_mcp.errors import CorkApiError

CONNECT_TIMEOUT_S = 5.0
READ_TIMEOUT_S = 30.0
MAX_RETRY_ATTEMPTS = 3  # 1 initial try + 2 retries, bounded by SOP SS5's 120s total
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def clamp_page_size(page_size: int | None) -> int:
    """Clamp a requested page size into [1, MAX_PAGE_SIZE] (SOP SS2.5)."""
    if page_size is None:
        return DEFAULT_PAGE_SIZE
    return max(1, min(page_size, MAX_PAGE_SIZE))


class CorkClient:
    """Request-scoped client for Cork's REST API.

    Must be constructed (and its underlying httpx.AsyncClient closed) once
    per incoming MCP request -- see server.py's `client_factory`.
    """

    def __init__(self, api_key: str, base_url: str):
        self._http = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(connect=CONNECT_TIMEOUT_S, read=READ_TIMEOUT_S, write=READ_TIMEOUT_S, pool=READ_TIMEOUT_S),
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "CorkClient":
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.aclose()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET `path`, retrying 429/5xx with backoff, raising CorkApiError otherwise."""
        params = {k: v for k, v in (params or {}).items() if v is not None}
        last_error: CorkApiError | None = None
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                response = await self._http.get(path, params=params)
            except httpx.TimeoutException as exc:
                last_error = CorkApiError(f"Timed out calling Cork: {exc}", status_code=None)
                await asyncio.sleep(_backoff_seconds(attempt))
                continue
            except httpx.HTTPError as exc:
                last_error = CorkApiError(f"Network error calling Cork: {exc}", status_code=None)
                await asyncio.sleep(_backoff_seconds(attempt))
                continue

            if response.status_code < 400:
                return response.json()

            if response.status_code in (429, 500, 502, 503, 504) and attempt < MAX_RETRY_ATTEMPTS - 1:
                last_error = CorkApiError(
                    f"Cork returned HTTP {response.status_code}", status_code=response.status_code
                )
                await asyncio.sleep(_retry_after_seconds(response) or _backoff_seconds(attempt))
                continue

            raise CorkApiError(
                f"Cork returned HTTP {response.status_code}", status_code=response.status_code
            )

        assert last_error is not None
        raise last_error

    # -- Endpoints used by tools/, one method per Cork GET endpoint. --------

    async def list_clients(self, *, page: int | None, page_size: int | None) -> dict[str, Any]:
        return await self._get(
            "/clients", {"page": page, "page_size": clamp_page_size(page_size)}
        )

    async def list_warranties(
        self, *, client_uuid: str, page: int | None, page_size: int | None
    ) -> dict[str, Any]:
        return await self._get(
            "/warranties",
            {"client_uuid": client_uuid, "page": page, "page_size": clamp_page_size(page_size)},
        )

    async def get_client_score_history(
        self,
        *,
        client_uuid: str,
        created_after: str | None,
        created_before: str | None,
        page: int | None,
        page_size: int | None,
    ) -> dict[str, Any]:
        return await self._get(
            f"/clients/{client_uuid}/score-history",
            {
                "created_after": created_after,
                "created_before": created_before,
                "page": page,
                "page_size": clamp_page_size(page_size),
            },
        )

    async def list_compliance_events(
        self,
        *,
        client_uuid: str,
        show_resolved: bool | None,
        at_risk: bool | None,
        page: int | None,
        page_size: int | None,
    ) -> dict[str, Any]:
        return await self._get(
            f"/compliance/client/{client_uuid}/events",
            {
                "show_resolved": show_resolved,
                "at_risk": at_risk,
                "page": page,
                "page_size": clamp_page_size(page_size),
            },
        )

    async def list_compliance_event_types(self) -> dict[str, Any]:
        return await self._get("/compliance/event-types")

    async def list_software_vulnerabilities(
        self,
        *,
        client_uuid: str | None,
        minimum_cvss_score: float | None,
        only_known_exploited: bool | None,
        page: int | None,
        page_size: int | None,
    ) -> dict[str, Any]:
        return await self._get(
            "/vulnerabilities/software",
            {
                "client_uuid": client_uuid,
                "minimum_cvss_score": minimum_cvss_score,
                "only_known_exploited": only_known_exploited,
                "page": page,
                "page_size": clamp_page_size(page_size),
            },
        )


def _backoff_seconds(attempt: int) -> float:
    return 0.5 * (2**attempt)


def _retry_after_seconds(response: httpx.Response) -> float | None:
    value = response.headers.get("Retry-After")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
