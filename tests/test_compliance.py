"""TC5 (AC3), TC10 (AC7) for compliance events."""

from __future__ import annotations

import httpx
import respx

from tests.conftest import call_tool

BASE_URL = "https://api.corkinc.com/api/v1"


@respx.mock
async def test_get_compliance_events_returns_event_fields(mcp, with_api_key):
    respx.get(f"{BASE_URL}/compliance/client/client-1/events").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "event_type": "mfa_missing",
                        "at_risk": True,
                        "resolved": False,
                        "created_at": "2026-10-20T00:00:00Z",
                    }
                ],
                "has_more": False,
            },
        )
    )

    result = await call_tool(mcp, "cork_get_compliance_events", {"client_uuid": "client-1"})

    event = result["items"][0]
    assert event["event_type"] == "mfa_missing"
    assert event["at_risk"] is True
    assert event["resolved"] is False


@respx.mock
async def test_empty_events_list_is_not_an_error(mcp, with_api_key):
    respx.get(f"{BASE_URL}/compliance/client/client-1/events").mock(
        return_value=httpx.Response(200, json={"data": [], "has_more": False})
    )

    result = await call_tool(mcp, "cork_get_compliance_events", {"client_uuid": "client-1"})

    assert result == {"items": [], "has_more": False}
    assert "error" not in result
