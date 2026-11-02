"""Minimal structured logging for tool calls (SOP SS6).

Logs the tool name, the client_uuid (never the API key), the outcome, and
elapsed time. No response bodies -- compliance/vulnerability data is
sensitive and must not land in logs.
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger("cork_mcp")


def now() -> float:
    return time.monotonic()


def log_tool_call(tool_name: str, client_uuid: str | None, outcome: str, started_at: float) -> None:
    """`outcome` is "ok" or an error `code` from errors.py (e.g. "unauthorized")."""
    elapsed_ms = round((time.monotonic() - started_at) * 1000, 1)
    logger.info(
        "cork_mcp_tool_call",
        extra={
            "tool": tool_name,
            "client_uuid": client_uuid,
            "outcome": outcome,
            "elapsed_ms": elapsed_ms,
        },
    )
