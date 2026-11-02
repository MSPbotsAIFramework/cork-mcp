# PRD-21227 · Code review

## Round 1 · 2026-11-02 · reviewed dev/PRD-21227 @ 686525a (base main @ 6ee3c0d)

Verdict: approved

### Scope

New repo `MSPbotsAIFramework/cork-mcp`, single commit range `6ee3c0d...686525a` (33 files, +2729/-1, all new). No prior code to preserve; nothing out of scope was touched.

### Independent verification performed

- `uv sync` then `uv run pytest -v` on the synced branch: **29 passed**, matching the `[DEV]` stub and `docs/tickets/PRD-21227.ac.json`.
- `grep -rnP '[\x{4e00}-\x{9fff}]'` (excl. `.git`/`.venv`): clean, no Chinese.
- `git log -p 6ee3c0d..686525a | grep -Ei '(token|secret|api[_-]?key|password|bearer)\s*[=:]'` filtered for placeholders: clean.
- Live HTTP smoke (`uv run python -m cork_mcp`): `GET /health` → `200 {"status":"ok"}`; `POST /mcp tools/list` without `initialize` and without `X-Cork-Api-Key` → `401 {"error":{"code":"not_configured",...}}`; with the header → `200`, 6 tools listed, names and schemas match the tech design's tool list; `tools/call cork_get_warranties {}` with the header present → `200`, `isError:false`, body `{"error":{"code":"invalid_argument","message":"client_uuid is required."}}` — matches the Self-test claim exactly.
- README "MSPbots Connector" section byte-diffed against `~/.claude/skills/vendor-mcp-development/reference/readme-connector-section.md`: identical.
- `docker build`: not run (this machine also has no permission on `/var/run/docker.sock`, same constraint the dev leg hit). Dockerfile read: standard multi-stage build, non-root `app` user in the production stage, `curl` installed for the `HEALTHCHECK`, `EXPOSE 8080`, matches SOP §8 template. INT deploy pipeline builds it as part of `mcppub register`.

### Findings

No must-fix findings.

1. [suggestion] No `LICENSE` file. `vendor-mcp-development/SKILL.md` ("仓库归属规则", rule 3) says self-built MCP repos should carry Apache-2.0 with copyright `MSPbots.ai`; this is not enforced by the §14 checklist and has no functional impact, but the connector should pick one up on a follow-up commit.
2. [suggestion] `docs/tickets/PRD-21227.md` "Change list" describes `src/cork_mcp/__main__.py` as a "stdio/HTTP transport entrypoint (`MCP_TRANSPORT` env var...)"; the actual `__main__.py` only runs the Streamable HTTP server via `uvicorn.run(...)`, with no stdio mode or `MCP_TRANSPORT` switch. This is a design-doc wording mismatch, not a functional gap — the platform contract only requires Streamable HTTP (SOP §14 checklist item 1), and the simpler HTTP-only implementation is correct for this connector's actual deployment target.
3. Acknowledged, not a finding: `cork_get_software_vulnerabilities`'s `client_uuid` is left optional at both the Cork-API and this repo's JSON-schema/validation layer, per the tech design's documented exception (Cork's own endpoint allows an account-wide query on this one path). The design itself flags that MSPbots-facing enforcement belongs at a call-site layer outside this repo (gateway/policy), which this ticket cannot reach — this is correctly surfaced in the tech design, the tool docstring, and the README, not silently left out.

### Checklist cross-check (SOP §14)

Independently re-walked the full checklist in `docs/tickets/PRD-21227.md` "SOP SS14 checklist self-check" against the code; every item checked there was verified true during this review (listed above where it mattered; the remaining items — timeouts, retry/backoff, error vocabulary, tool count/prefix/description length, pagination defaults/caps, compact JSON with truncation, read-only annotations — were read directly in `api_client.py`, `errors.py`, `format.py`, and the `tools/*.py` files and match the design).

### Fixes

N/A — no must-fix items from this round.

---
Status: frozen @ 686525a (this round adds only this review file; no source change)
