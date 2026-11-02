"""Shared JSON formatting for tool results (SOP SS2.5 token-economy rules)."""

from __future__ import annotations

import json
from typing import Any

MAX_RESULT_CHARS = 20_000


def dumps(payload: Any) -> str:
    """Compact, non-ASCII-escaped JSON. Never use indent=2 -- it wastes tokens."""
    text = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    if len(text) <= MAX_RESULT_CHARS:
        return text
    # Oversized payload: truncate the item list (if present) and say so,
    # rather than returning a payload the caller cannot fit in context.
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        truncated = dict(payload)
        items = truncated["items"]
        while items and len(json.dumps(truncated, separators=(",", ":"), ensure_ascii=False)) > MAX_RESULT_CHARS:
            items.pop()
        truncated["has_more"] = True
        truncated["truncated"] = True
        return json.dumps(truncated, separators=(",", ":"), ensure_ascii=False)
    return text[:MAX_RESULT_CHARS]


def items_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Cork list response (`{"data": [...], "has_more": ...}`)
    into the connector's consistent `{"items": [...], "has_more": ...}`
    shape. Item fields are passed through unchanged (SOP SS2.5: trim only
    the envelope, not fields the ticket's AC asks the agent to see).
    """
    return {"items": payload.get("data", []), "has_more": bool(payload.get("has_more", False))}


def static_list_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    """Shape for non-paginated static reference data (no `has_more`)."""
    return {"items": payload.get("data", [])}
