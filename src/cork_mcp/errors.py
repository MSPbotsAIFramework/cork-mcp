"""Structured error envelope shared by every tool.

Every tool returns a JSON string. On failure that string is this envelope,
never a raised exception -- see vendor-mcp-development SOP SS4.
"""

from __future__ import annotations

import json

# Fixed, finite error-code vocabulary (SOP SS4.2). Do not invent new codes.
NOT_CONFIGURED = "not_configured"
UNAUTHORIZED = "unauthorized"
NOT_FOUND = "not_found"
INVALID_ARGUMENT = "invalid_argument"
RATE_LIMITED = "rate_limited"
UPSTREAM_ERROR = "upstream_error"

_RETRYABLE_CODES = {RATE_LIMITED, UPSTREAM_ERROR}


def error_envelope(code: str, message: str, *, retryable: bool | None = None) -> str:
    """Build the fixed JSON error envelope as a compact string.

    `retryable` defaults to the SOP table's value for `code` if not given.
    """
    if retryable is None:
        retryable = code in _RETRYABLE_CODES
    return json.dumps(
        {"error": {"code": code, "message": message, "retryable": retryable}},
        separators=(",", ":"),
        ensure_ascii=False,
    )


def not_configured(message: str = "The X-Cork-Api-Key header is missing.") -> str:
    return error_envelope(NOT_CONFIGURED, message)


def invalid_argument(message: str) -> str:
    return error_envelope(INVALID_ARGUMENT, message)


class CorkApiError(Exception):
    """Raised by api_client on any non-2xx response or network failure.

    `status_code` is None for timeouts/connection errors (mapped to
    upstream_error); otherwise it is the HTTP status Cork returned.
    """

    def __init__(self, message: str, *, status_code: int | None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def map_api_error(exc: CorkApiError) -> str:
    """Map a CorkApiError to the fixed error envelope (SOP SS4.2 table)."""
    status = exc.status_code
    if status == 401 or status == 403:
        return error_envelope(UNAUTHORIZED, "Cork rejected the API key.")
    if status == 404:
        return error_envelope(NOT_FOUND, exc.message)
    if status == 429:
        return error_envelope(RATE_LIMITED, "Cork rate-limited this request.")
    if status is not None and 400 <= status < 500:
        return error_envelope(INVALID_ARGUMENT, exc.message)
    # 5xx, None (timeout/connection error), or anything else unexpected.
    return error_envelope(UPSTREAM_ERROR, exc.message)
