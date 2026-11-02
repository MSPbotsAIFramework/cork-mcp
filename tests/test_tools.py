"""SOP SS10 minimal set, part 1: tools/list snapshot and error-code mapping.

A changed snapshot here is a signal, not necessarily a bug (SOP SS13: tool
signatures are an external contract) -- but it must be a deliberate,
documented change, not an accident.
"""

from __future__ import annotations

from cork_mcp.errors import CorkApiError, map_api_error

EXPECTED_TOOLS = {
    "cork_get_clients",
    "cork_get_warranties",
    "cork_get_client_score_history",
    "cork_get_compliance_events",
    "cork_get_compliance_event_types",
    "cork_get_software_vulnerabilities",
}


async def test_tools_list_snapshot(mcp):
    tools = await mcp.list_tools()
    names = {t.name for t in tools}

    assert names == EXPECTED_TOOLS
    for tool in tools:
        assert tool.name.startswith("cork_")  # SOP SS2.8: vendor-prefixed names
        assert len(tool.description or "") <= 500  # SOP SS2.2
        # No tool requires client_uuid at the JSON-schema level -- it is
        # validated in business logic instead (see tools/*.py docstrings),
        # so a schema-level validation error never bypasses the structured
        # error envelope (SOP SS4.1).
        assert not (tool.inputSchema.get("required") or [])


def test_error_mapping_covers_the_fixed_vocabulary():
    cases = [
        (401, "unauthorized"),
        (403, "unauthorized"),
        (404, "not_found"),
        (429, "rate_limited"),
        (400, "invalid_argument"),
        (422, "invalid_argument"),
        (500, "upstream_error"),
        (503, "upstream_error"),
        (None, "upstream_error"),  # timeout / connection error
    ]
    for status_code, expected_code in cases:
        envelope = map_api_error(CorkApiError("boom", status_code=status_code))
        assert f'"code":"{expected_code}"' in envelope
