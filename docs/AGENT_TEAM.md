# Agent Team Architecture (🅱️ Shared-Resolve)

## What it is

One DaVinci Resolve instance, multiple specialized MCP servers — one per
"room" of Resolve (Media, Cut, Edit, Fusion, Color, Fairlight, Deliver),
plus a cross-cutting **Director**. Each server exposes only the tools
relevant to its role and gets its own port + auth token. LLM agents
connect to the role they're responsible for — the colorist agent can't
accidentally reach into the media pool; the deliverer agent can't nudge
a color grade.

```
                    ┌──────────────────────────────┐
                    │     DaVinci Resolve (GUI)    │
                    └───────────┬──────────────────┘
                                │ scripting API (single-process)
    ┌────────────────┬──────────┼────────────┬────────────────┐
    │                │          │            │                │
 :8100            :8102       :8105        :8106           :810x
 media            color       deliver      director        …
 agent            agent       agent        agent
```

## Why this shape

- Resolve is single-process and has **one globally active page**. Multi-
  tenant would require N Resolves on N machines. This architecture works
  on a single workstation.
- Native page separation maps naturally to post-production roles — the
  program is literally built as rooms for different work types.
- Per-role token isolation + role-scoped tool surface means a compromised
  colorist agent cannot issue `delete_media` even if it tries.

## Components

| Module | Responsibility |
|--------|----------------|
| `src/roles.py` | Maps role names → tool modules + target page |
| `src/server_factory.py` | Builds a FastMCP instance containing only a role's tools, wrapping each in page-lock + audit + rate-limit + dry-run |
| `src/utils/page_lock.py` | **Intra-process** lock serializing page switches |
| `src/utils/file_lock.py` | **Inter-process** advisory file lock for the page switch (shared across N role-server processes) |
| `src/utils/auth.py` | Bearer token config (shared or per-role) |
| `src/utils/auth_middleware.py` | ASGI middleware enforcing auth; exposes unauthenticated `/health` |
| `src/utils/audit.py` | Append-only JSONL log at `logs/audit.jsonl` |
| `src/utils/dry_run.py` | Short-circuit DESTRUCTIVE tools — describe instead of execute |
| `src/utils/rate_limit.py` | Token-bucket: global + destructive-specific |
| `src/utils/logging_config.py` | Text or JSON logging, selectable via env |
| `src/context.py` | Auto-reconnect to Resolve on COM/bridge death |

## Request lifecycle

```
HTTP request
  └─ BearerAuthMiddleware              (auth; /health bypasses)
      └─ FastMCP streamable-http
          └─ wrapped tool
              ├─ rate-limit check     (reject 429-ish if over budget)
              ├─ dry-run check        (skip if DESTRUCTIVE + dry-run on)
              ├─ ProcessFileLock      (cross-process coordination)
              │   └─ PageLock         (intra-process coordination)
              │       └─ resolve.OpenPage(...) if not already
              │           └─ original tool fn
              └─ audit.write(...)     (always)
```

## Roles and tool counts

| Role      | Port | Page in Resolve | Tools |
|-----------|------|-----------------|-------|
| media     | 8100 | Media           |  58   |
| edit      | 8101 | Edit            |  98   |
| color     | 8102 | Color           |  40   |
| fusion    | 8103 | Fusion          |  10   |
| fairlight | 8104 | Fairlight       |  13   |
| deliver   | 8105 | Deliver         |  20   |
| director  | 8106 | (cross-page)    |  50   |
| full      |  —   | (all)           | 289   |

## Launching the team

### Windows (PowerShell)

```powershell
$env:MCP_AUTH_TOKENS = "color:ctok,deliver:dtok,edit:etok,director:drtok,media:mtok,fusion:ftok,fairlight:latok"
.\scripts\launch-team.ps1
```

### macOS / Linux

```bash
export MCP_AUTH_TOKENS="color:ctok,deliver:dtok,edit:etok,director:drtok,media:mtok,fusion:ftok,fairlight:latok"
./scripts/launch-team.sh
```

### Manually (one role at a time)

```bash
python src/main.py --role color --transport http --port 8102
```

## Client configuration

Each agent's MCP client points at its own URL + token. Example for Claude
Desktop — one entry per agent that gets attached to that agent's system
prompt ("you are the colorist"):

```json
{
  "mcpServers": {
    "resolve-color": {
      "url": "http://127.0.0.1:8102/mcp/",
      "headers": { "Authorization": "Bearer ctok" }
    },
    "resolve-deliver": {
      "url": "http://127.0.0.1:8105/mcp/",
      "headers": { "Authorization": "Bearer dtok" }
    }
  }
}
```

A token tied to a role is **rejected** by a server serving a different
role (cross-role protection in `BearerAuthMiddleware`).

## Safety layers

1. **Tool annotations.** Every tool carries `READ_ONLY` / `SAFE_WRITE` /
   `DESTRUCTIVE`. MCP-aware clients (Claude Desktop, etc.) gate
   destructive calls behind a confirmation.
2. **Role isolation.** Only tools relevant to the role are exposed.
3. **Token isolation.** Per-role Bearer tokens; cross-role reuse rejected.
4. **Rate limiting.** Global: `MCP_RATE_ALL=10`/s. Destructive:
   `MCP_RATE_DESTRUCTIVE=0.5`/s (one every two seconds). Disable with
   `MCP_RATE_DISABLED=1`.
5. **Dry-run.** `MCP_DRY_RUN=1` (process-wide) or
   `MCP_DRY_RUN_ROLES=color,deliver` (selective) short-circuits
   destructive tools — they describe what they'd do, no change is made.
6. **Audit log.** JSONL at `logs/audit.jsonl` — every call logs
   `(timestamp, role, tool, destructive, dry_run, args_hash, duration, ok, error)`.
   Override with `MCP_AUDIT_LOG=/path/audit.jsonl`.
7. **Cross-process page lock.** `ProcessFileLock` via
   `%TEMP%/davinci-resolve-mcp.page.lock` serializes page switches across
   all role-server processes.
8. **Auto-reconnect.** If Resolve crashes/restarts, `context.get_resolve()`
   transparently reconnects on next tool call (rate-limited to one
   attempt per 5s).

## Environment variables

| Var | Meaning | Default |
|---|---|---|
| `MCP_TRANSPORT` | `stdio` or `http` | `stdio` |
| `MCP_HOST` | HTTP bind address | `127.0.0.1` |
| `MCP_PORT` | HTTP port | `8100` |
| `MCP_AUTH_TOKEN` | Shared bearer token (all roles) | — |
| `MCP_AUTH_TOKENS` | `role1:tok1,role2:tok2` — per-role tokens | — |
| `MCP_DRY_RUN` | `1` = skip destructive execution | `0` |
| `MCP_DRY_RUN_ROLES` | `role1,role2` dry-run selectively | — |
| `MCP_RATE_ALL` | Global tool rate limit (req/s) | `10` |
| `MCP_RATE_DESTRUCTIVE` | Destructive-tool rate limit (req/s) | `0.5` |
| `MCP_RATE_DISABLED` | `1` = disable rate limiter | `0` |
| `MCP_AUDIT_LOG` | Path to audit JSONL | `logs/audit.jsonl` |
| `MCP_LOG_JSON` | `1` = JSON log format | `0` |
| `MCP_DISABLE_FILE_LOCK` | `1` = disable cross-process file lock | `0` |

## Observability

- `GET /health` — unauthenticated liveness (200 OK, `{"status":"ok"}`).
- `resolve://health` MCP resource (authenticated) — reports role list,
  Resolve connection, active page, in-process page-lock state.
- `logs/audit.jsonl` — append-only audit trail.
- Structured JSON logging via `MCP_LOG_JSON=1`.

## Known limitations

- **No cross-process reconnect coordination.** If Resolve crashes, each
  role-server reconnects independently. Harmless but logged repeatedly.
- **File lock is advisory only.** A third-party MCP server touching
  Resolve would bypass it. Within this codebase, all entry points go
  through `page_lock.acquire_page` → `process_file_lock.acquire`.
- **No audit log rotation built in.** Use `logrotate` / Windows Task
  Scheduler. The log is append-safe and line-atomic.
- **No metrics endpoint.** Prometheus-style metrics are not yet exposed.
  Audit log can be grepped in the meantime.

## Tests

```bash
pytest tests/unit/                        # 137 tests, no Resolve needed
pytest tests/unit/test_roles_and_factory.py
pytest tests/unit/test_auth_middleware.py
pytest tests/unit/test_new_infra.py

# Live integration tests (require running DaVinci Resolve):
pytest tests/integration/test_agent_team_live.py -v -m live
```

## Request tracing

Each HTTP request gets a correlation ID — either the caller's
`X-Request-ID` header or a freshly generated UUID4. The ID appears in:

- The response headers (so clients can grep logs for their call).
- Every `audit.jsonl` entry produced by that request (`request_id` field).
- Every structured log line emitted during the request (JSON mode).

This makes post-mortem debugging across 7 concurrent servers tractable.

