"""TC7, TC8, TC9 (AC5, AC6): credential and argument validation across tools."""

from __future__ import annotations

import httpx
import pytest
import respx

from tests.conftest import ALL_TOOLS, CLIENT_SCOPED_TOOLS, MINIMAL_ARGS, call_tool

BASE_URL = "https://api.corkinc.com/api/v1"


@respx.mock
@pytest.mark.parametrize("tool_name", ALL_TOOLS)
async def test_upstream_401_maps_to_unauthorized_for_every_tool(mcp, with_api_key, tool_name):
    respx.route(url__regex=rf"{BASE_URL}/.*").mock(return_value=httpx.Response(401, json={"message": "no"}))

    result = await call_tool(mcp, tool_name, MINIMAL_ARGS[tool_name])

    assert result["error"]["code"] == "unauthorized"
    assert result["error"]["retryable"] is False


@respx.mock
@pytest.mark.parametrize("tool_name", ALL_TOOLS)
async def test_missing_credential_header_short_circuits_every_tool(mcp, no_api_key, tool_name):
    # No respx route is registered: if the tool attempted an outbound call,
    # respx would raise instead of silently succeeding, failing this test.
    result = await call_tool(mcp, tool_name, MINIMAL_ARGS[tool_name])

    assert result["error"]["code"] == "not_configured"


@respx.mock
@pytest.mark.parametrize("tool_name", CLIENT_SCOPED_TOOLS)
async def test_missing_client_uuid_short_circuits_client_scoped_tools(mcp, with_api_key, tool_name):
    # No respx route is registered: a call reaching Cork would raise here.
    result = await call_tool(mcp, tool_name, {})

    assert result["error"]["code"] == "invalid_argument"
