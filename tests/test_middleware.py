"""SOP SS10 minimal set, part 2: health probe, and the credential middleware
gating /mcp (SOP SS1.1, SS3.2).

Uses Starlette's TestClient (not a bare httpx.ASGITransport) because it
drives the ASGI lifespan protocol -- the MCP session manager's task group
(see server.py's create_app docstring on the Mount() lifespan pitfall) is
only initialized once `lifespan.startup` has run.
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from cork_mcp.server import API_KEY_HEADER, create_app

JSON_RPC_TOOLS_LIST = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
STREAMABLE_HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


@pytest.fixture
def client():
    with TestClient(create_app()) as test_client:
        yield test_client


def test_health_returns_ok_without_any_header(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_mcp_without_credential_header_returns_401(client):
    response = client.post("/mcp", json=JSON_RPC_TOOLS_LIST, headers=STREAMABLE_HEADERS)

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "not_configured"
    assert API_KEY_HEADER in body["error"]["message"]


def test_mcp_with_credential_header_is_not_rejected_by_middleware(client):
    headers = {**STREAMABLE_HEADERS, API_KEY_HEADER: "test-key"}

    response = client.post("/mcp", json=JSON_RPC_TOOLS_LIST, headers=headers)

    # Stateless mode accepts a bare tools/list without a prior `initialize`
    # handshake (SOP SS1.3's self-check). A 400 here would mean
    # stateless_http is not actually wired up.
    assert response.status_code == 200
