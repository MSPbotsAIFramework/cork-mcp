"""Shared test fixtures.

Tools are exercised through `mcp.call_tool`, the same path the Gateway uses,
rather than calling the decorated functions directly -- that way the tests
also catch schema-level mistakes (e.g. a required arg the JSON schema would
reject before our own validation runs).
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from cork_mcp import server

TEST_API_KEY = "test-cork-api-key"


@pytest.fixture
def mcp():
    return server.create_mcp()


@pytest.fixture
def with_api_key():
    """Simulate the credential middleware having set the contextvar."""
    token = server._api_key_var.set(TEST_API_KEY)
    try:
        yield TEST_API_KEY
    finally:
        server._api_key_var.reset(token)


@pytest.fixture
def no_api_key():
    """Simulate a request with no X-Cork-Api-Key header at all."""
    token = server._api_key_var.set(None)
    try:
        yield
    finally:
        server._api_key_var.reset(token)


async def call_tool(mcp, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call a tool and parse its (always-JSON-string) result."""
    content, _ = await mcp.call_tool(name, arguments or {})
    return json.loads(content[0].text)


CLIENT_SCOPED_TOOLS = [
    "cork_get_warranties",
    "cork_get_client_score_history",
    "cork_get_compliance_events",
]

ALL_TOOLS = [
    "cork_get_clients",
    "cork_get_warranties",
    "cork_get_client_score_history",
    "cork_get_compliance_events",
    "cork_get_compliance_event_types",
    "cork_get_software_vulnerabilities",
]

# Minimal valid arguments for tools with a client_uuid-shaped requirement,
# used by tests that are not about that argument itself.
MINIMAL_ARGS = {
    "cork_get_clients": {},
    "cork_get_warranties": {"client_uuid": "client-1"},
    "cork_get_client_score_history": {"client_uuid": "client-1"},
    "cork_get_compliance_events": {"client_uuid": "client-1"},
    "cork_get_compliance_event_types": {},
    "cork_get_software_vulnerabilities": {},
}
