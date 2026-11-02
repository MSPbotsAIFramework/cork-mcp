"""TC2 (AC1), TC10 (AC7) for warranties."""

from __future__ import annotations

import httpx
import respx

from tests.conftest import call_tool

BASE_URL = "https://api.corkinc.com/api/v1"


@respx.mock
async def test_get_warranties_returns_coverage_dates(mcp, with_api_key):
    respx.get(f"{BASE_URL}/warranties").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "package_name": "Cyber Shield Pro",
                        "coverage_limit": 1000000,
                        "effective_date": "2026-01-01",
                        "expiry_date": "2027-01-01",
                    }
                ],
                "has_more": False,
            },
        )
    )

    result = await call_tool(mcp, "cork_get_warranties", {"client_uuid": "client-1"})

    package = result["items"][0]
    assert package["package_name"] == "Cyber Shield Pro"
    assert package["effective_date"] == "2026-01-01"
    assert package["expiry_date"] == "2027-01-01"


@respx.mock
async def test_empty_warranty_list_is_not_an_error(mcp, with_api_key):
    respx.get(f"{BASE_URL}/warranties").mock(
        return_value=httpx.Response(200, json={"data": [], "has_more": False})
    )

    result = await call_tool(mcp, "cork_get_warranties", {"client_uuid": "client-1"})

    assert result == {"items": [], "has_more": False}
    assert "error" not in result
