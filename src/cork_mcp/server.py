"""FastMCP app factory, request-scoped credential middleware, health route.

Per vendor-mcp-development SOP SS1.3/SS3: the server is stateless, reads the
Cork API key only from the `X-Cork-Api-Key` header on each request (never
env/global fallback), and isolates that key in a contextvar so concurrent
requests for different MSP accounts never see each other's credential.
"""

from __future__ import annotations

from contextvars import ContextVar

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from cork_mcp.api_client import CorkClient
from cork_mcp.config import settings
from cork_mcp.tools import clients, compliance, vulnerabilities, warranty

API_KEY_HEADER = "X-Cork-Api-Key"
MCP_PATH = "/mcp"

# Request-scoped only: a ContextVar is isolated per asyncio task, so one
# incoming request's credential is never visible to a concurrently running
# request for a different tenant. This is NOT a module-level secret store.
_api_key_var: ContextVar[str | None] = ContextVar("cork_api_key", default=None)

INSTRUCTIONS = """\
Cork is a cyber-insurance/warranty platform for MSPs. Each MSP has one Cork \
account covering every client it manages. Use these tools to review, for a \
given client, whether they are currently covered (warranty/coverage status), \
how their Cork Cyber Score has trended over time, and what compliance or \
software-vulnerability risk Cork has flagged for them.

Typical flow: call cork_get_clients to find a client's uuid and current \
warranty_status/latest_cyber_score, then use that uuid with \
cork_get_warranties, cork_get_client_score_history, \
cork_get_compliance_events, and/or cork_get_software_vulnerabilities for \
detail. cork_get_compliance_event_types is a static reference list (not \
client-scoped) for interpreting the event_type field on compliance events.

This connector is read-only: it cannot connect, update, or delete a Cork \
integration, and does not return account credentials or invoices.\
"""


def has_credential() -> bool:
    """Cheap check with no side effect -- use before any argument validation
    so a request with neither a credential nor a required argument still
    gets `not_configured` (consistent with HTTP's 401-before-400 ordering),
    without opening an HTTP connection pool that would then go unclosed.
    """
    return bool(_api_key_var.get())


def get_client() -> CorkClient | None:
    """Build a fresh, request-scoped Cork API client, or None if unconfigured.

    Returns a new CorkClient per call -- never cached -- so no tenant's
    credential or derived state can leak into another request. Call only
    after `has_credential()` and all argument validation have passed, since
    this opens an HTTP connection pool the caller must close (`async with`).
    """
    api_key = _api_key_var.get()
    if not api_key:
        return None
    return CorkClient(api_key=api_key, base_url=settings.cork_base_url)


async def _credential_middleware(request: Request, call_next):
    """Gate `/mcp` on the credential header (SOP SS3.2: 401, not 500, and
    never let a request with an empty credential reach Cork), and otherwise
    read it into the contextvar for this request only.

    The tools' own `has_credential()` check is a second, independent layer:
    it is what actually runs when a tool is invoked directly (e.g. in unit
    tests that call `mcp.call_tool` without going through this ASGI app), so
    missing-credential behavior is identical whether or not this HTTP layer
    is in the call path.
    """
    api_key = request.headers.get(API_KEY_HEADER)
    if request.url.path == MCP_PATH and not api_key:
        return JSONResponse(
            {
                "error": {
                    "code": "not_configured",
                    "message": f"Missing required header(s): {API_KEY_HEADER}",
                    "retryable": False,
                }
            },
            status_code=401,
        )
    token = _api_key_var.set(api_key)
    try:
        return await call_next(request)
    finally:
        _api_key_var.reset(token)


async def _health(_request: Request) -> JSONResponse:
    """Pure local liveness probe -- must never depend on Cork's API (SOP SS1.1)."""
    return JSONResponse({"status": "ok"})


def create_mcp() -> FastMCP:
    mcp = FastMCP(
        name="cork-mcp",
        instructions=INSTRUCTIONS,
        host=settings.mcp_http_host,
        port=settings.mcp_http_port,
        stateless_http=True,
        # The server sits behind an internal proxy/gateway, not on localhost,
        # so the default DNS-rebinding Host check would reject it (SOP SS7).
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )

    @mcp.custom_route("/health", methods=["GET"])
    async def health(request: Request) -> JSONResponse:  # noqa: ANN001 - Starlette signature
        return await _health(request)

    clients.register(mcp, has_credential, get_client)
    warranty.register(mcp, has_credential, get_client)
    compliance.register(mcp, has_credential, get_client)
    vulnerabilities.register(mcp, has_credential, get_client)

    return mcp


def create_app() -> Starlette:
    """Build the single ASGI app serving both /health and /mcp.

    Using FastMCP's own `streamable_http_app()` (rather than Mount()-ing it
    under a separate outer Starlette app) means the MCP session manager's
    lifespan is already the app's lifespan -- the Mount() lifespan pitfall
    from SOP SS7 ("Task group is not initialized") does not apply here.
    """
    mcp = create_mcp()
    app = mcp.streamable_http_app()
    app.add_middleware(BaseHTTPMiddleware, dispatch=_credential_middleware)
    return app
