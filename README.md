# cork-mcp

MCP server for [Cork](https://corkinc.com), a cyber-insurance/warranty platform for MSPs. Gives an Agent read-only access to a client's Cork warranty/coverage status, Cyber Score history, and compliance/vulnerability data.

- **Transport**: MCP Streamable HTTP (`POST /mcp`), stateless.
- **Stack**: Python 3.12, FastMCP, httpx.
- **License**: Internal MSPbots connector; not published.

<div align="center">

## MSPbots Connector

**The MCP Gateway built for MSPs: visible, controlled, and your data stays where it belongs.**

[**Get started at connect.mspbots.ai →**](https://connect.mspbots.ai)

</div>

---

MSPbots Connector gives your AI clients one MCP URL to reach your entire MSP stack (RMM, PSA, documentation, security, finance), and gives you control over who can call which tool and a record of everything that was called.

**Hosted service: [connect.mspbots.ai](https://connect.mspbots.ai)** · Free to use.

### Why Connector

![MSPbots Connector](https://stgoss.mspbots.ai/files/mcp/mspbots-mcp.png)

| | |
|---|---|
| **Visible** | Every tool call is logged: who, which vendor, when. Usage dashboard, CSV export, SIEM streaming. |
| **Controlled** | Role-based, per-tool allowlist. Deny by default. |
| **Protected** | Credentials encrypted per record. AI clients never see your vendor passwords or tokens. |
| **MSP-native** | Built for the MSP stack only: RMM, PSA, documentation, security, finance. |

### Quick start

1. **Sign up** at [connect.mspbots.ai](https://connect.mspbots.ai).
2. **Connect your vendors.** Pick from 150+ connectors and authorize each one on the vendor's own page, or bring your own API keys. No extra vendor accounts needed.
3. **Set access.** Create roles and decide which tools each role may call. Nothing is allowed until you allow it.
4. **Add your MCP URL to your AI client.** Copy the URL from your Connector dashboard into Claude, ChatGPT, Cursor, VS Code, Gemini, Codex, or any MCP-capable client.
5. **Ask your AI to do real work**, and watch every call appear in the audit log.

### Features

**Unified gateway**
- One MCP URL for all your AI clients
- 150+ connectors across the MSP stack
- Custom MCP servers supported, free
- Authorization happens on each vendor's own page; the AI never sees passwords or tokens
- Bring your own credentials: use the vendor API keys you already have
- Multiple accounts per app; connect once, reuse across AI clients
- Tool search: finds the right action for the task
- One sign-in; vendor credentials are injected behind the scenes and OAuth tokens refresh automatically

**Visibility**
- Audit log for every tool call (who, which vendor, when)
- Usage dashboard: call volume, top vendors, error rate, per-user activity
- Export audit logs to CSV, or stream to Loki, Graylog, or LogScale (SIEM)
- Optional recording of tool arguments and result summaries (off by default, enabled per organization)

**Control**
- Per-role, per-tool allowlist, deny by default
- owner / admin / member roles
- SCIM provisioning with Entra ID, Okta, JumpCloud, and Google Workspace

**Security**
- Credentials encrypted one record at a time (AES-256-GCM, per-record key)
- AI clients authenticate with OAuth 2.1 + PKCE
- Vendor responses are scanned for prompt-injection patterns and returned as structured data. This is one layer of defense, not a guarantee against every attack.
- Static egress IP for customer firewall and API allowlisting

### Pricing

**Free.**

Links: [connect.mspbots.ai](https://connect.mspbots.ai) · [mspbots.ai](https://mspbots.ai)

---

## Authentication headers

| Header | Required | Meaning | Where to get it |
|---|---|---|---|
| `X-Cork-Api-Key` | Yes | Bearer API key generated in Cork's Admin UI (Settings -> API). Scoped to the whole MSP account, not to individual clients. | Cork portal -> Settings -> API |

Credentials are read only from this request header, never from an environment variable or config file, and are never logged or persisted (see `src/cork_mcp/server.py`).

## Tools

All 6 tools are read-only.

| Tool | Description |
|---|---|
| `cork_get_clients` | List the MSP's Cork-covered clients with warranty status and Cyber Score. |
| `cork_get_warranties` | List a client's active Cork cyber-warranty packages and coverage dates. |
| `cork_get_client_score_history` | Get a client's Cork Cyber Score history, newest first. |
| `cork_get_compliance_events` | List a client's Cork compliance/risk events (type, at-risk, resolved). |
| `cork_get_compliance_event_types` | List Cork's reference compliance event types (code, description, cure period). |
| `cork_get_software_vulnerabilities` | List software vulnerabilities (CVE, CVSS/EPSS scores, known-exploited flag). |

Every client-scoped tool requires `client_uuid` except `cork_get_software_vulnerabilities`, where Cork's own API allows an account-wide query (see `docs/tickets/PRD-21227.md` "Data & API contract" for why this is a documented exception).

Out of scope for this version (no write/provisioning tools, no credential or bulk-export endpoints, no invoices/distributor/installer tooling) -- see `docs/tickets/PRD-21227.md` "Product design -> Non-goals".

## Errors

Every tool returns a JSON string. On failure it is this fixed envelope, never a raised exception:

```json
{"error": {"code": "unauthorized", "message": "Cork rejected the API key", "retryable": false}}
```

`code` is one of: `not_configured`, `unauthorized`, `not_found`, `invalid_argument`, `rate_limited`, `upstream_error`.

## Local development

```bash
uv sync
uv run pytest
uv run python -m cork_mcp   # serves on 0.0.0.0:8080
```

Smoke-test with a real or placeholder key:

```bash
curl -s http://localhost:8080/health

curl -s -X POST http://localhost:8080/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'X-Cork-Api-Key: test-key' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Build the production image:

```bash
docker build --platform linux/amd64 -t cork-mcp:dev .
```
