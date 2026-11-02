"""TC6 (AC4), TC10 (AC7) for software vulnerabilities."""

from __future__ import annotations

import httpx
import respx

from tests.conftest import call_tool

BASE_URL = "https://api.corkinc.com/api/v1"


@respx.mock
async def test_get_software_vulnerabilities_returns_cve_fields(mcp, with_api_key):
    respx.get(f"{BASE_URL}/vulnerabilities/software").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "cve_id": "CVE-2026-12345",
                        "cvss_score": 9.8,
                        "epss_score": 0.94,
                        "known_exploited": True,
                        "affected_software": "Acme VPN Client 3.2",
                    }
                ],
                "has_more": False,
            },
        )
    )

    result = await call_tool(mcp, "cork_get_software_vulnerabilities", {"client_uuid": "client-1"})

    cve = result["items"][0]
    assert cve["cvss_score"] == 9.8
    assert cve["epss_score"] == 0.94
    assert cve["known_exploited"] is True


@respx.mock
async def test_empty_vulnerability_list_is_not_an_error(mcp, with_api_key):
    respx.get(f"{BASE_URL}/vulnerabilities/software").mock(
        return_value=httpx.Response(200, json={"data": [], "has_more": False})
    )

    result = await call_tool(mcp, "cork_get_software_vulnerabilities", {"client_uuid": "client-1"})

    assert result == {"items": [], "has_more": False}
    assert "error" not in result
