"""TC1, TC4, TC11 (AC1, AC2, AC8)."""

from __future__ import annotations

import httpx
import respx

from tests.conftest import call_tool

BASE_URL = "https://api.corkinc.com/api/v1"


@respx.mock
async def test_get_clients_returns_warranty_status_and_score(mcp, with_api_key):
    respx.get(f"{BASE_URL}/clients").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"uuid": "client-1", "name": "Acme MSP", "warranty_status": "active", "latest_cyber_score": 782},
                    {"uuid": "client-2", "name": "Beta MSP", "warranty_status": "lapsed", "latest_cyber_score": 410},
                ],
                "has_more": False,
            },
        )
    )

    result = await call_tool(mcp, "cork_get_clients")

    assert result["items"][0]["warranty_status"] == "active"
    assert result["items"][0]["latest_cyber_score"] == 782
    assert result["items"][1]["warranty_status"] == "lapsed"
    assert result["items"][1]["latest_cyber_score"] == 410


@respx.mock
async def test_get_client_score_history_preserves_order(mcp, with_api_key):
    entries = [
        {"score": 782, "created_at": "2026-10-01T00:00:00Z"},
        {"score": 760, "created_at": "2026-09-01T00:00:00Z"},
        {"score": 745, "created_at": "2026-08-01T00:00:00Z"},
    ]
    respx.get(f"{BASE_URL}/clients/client-1/score-history").mock(
        return_value=httpx.Response(200, json={"data": entries, "has_more": False})
    )

    result = await call_tool(mcp, "cork_get_client_score_history", {"client_uuid": "client-1"})

    assert result["items"] == entries


@respx.mock
async def test_page_size_is_clamped_and_has_more_is_surfaced(mcp, with_api_key):
    route = respx.get(f"{BASE_URL}/clients").mock(
        return_value=httpx.Response(200, json={"data": [{"uuid": "client-1"}], "has_more": True})
    )

    result = await call_tool(mcp, "cork_get_clients", {"page_size": 500})

    sent_page_size = route.calls.last.request.url.params.get("page_size")
    assert sent_page_size == "200"
    assert result["has_more"] is True
