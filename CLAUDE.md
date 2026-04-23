# CLAUDE.md

## Project Overview

DaVinci Resolve MCP Server — Python-based Model Context Protocol (MCP) server that exposes DaVinci Resolve's scripting API as tools for AI assistants (Cursor, Claude Desktop, etc.).

Two deployment modes:

- **Single-agent stdio (legacy):** one process, all tools, stdio transport.
- **Agent team over HTTP (🅱️ Shared-Resolve):** N processes, one per role
  (media / edit / color / fusion / fairlight / deliver / director), each
  on its own port with its own Bearer token. See `docs/AGENT_TEAM.md`.

## Quick Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
pip install -r requirements-dev.txt   # pytest + plugins

# Run single-agent stdio (legacy)
python src/main.py                       # all tools
python src/main.py --role full           # same thing
python src/main.py --role edit           # edit-page only
python src/main.py --debug

# Run one role over HTTP
python src/main.py --role color --transport http --port 8102

# Launch the full 7-role team
# Windows:
.\scripts\launch-team.ps1
# macOS/Linux:
./scripts/launch-team.sh

# Tests
pytest tests/unit/ -v                    # 137 tests, no Resolve needed
pytest tests/integration/ -v -m live     # Live tests (needs Resolve running)
pytest tests/ --cov=src --cov-report=html
```

## Architecture

```
AI Assistants (one per role) ──[HTTP + Bearer]──┐
                                                │
                                         auth middleware  (/health bypasses)
                                                │
                                         FastMCP (role-scoped tools only)
                                                │
                                  wrapper: rate-limit → dry-run → page-lock → audit
                                                │
                                        src/tools/<role>.py
                                                │
                                         src/api/*.py
                                                │
                                         src/context.py  (auto-reconnect)
                                                │
                                        DaVinciResolveScript
                                                │
                                       DaVinci Resolve (single GUI process)
```

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `src/api/` | Low-level API wrappers: timeline, media, color, delivery, fairlight, fusion, gallery, keyframe, export, ai_director, semantic_detector, llm_client |
| `src/tools/` | MCP tool layer: media, timeline, project, color, delivery, navigation, fairlight, fusion, media_storage |
| `src/utils/` | safety, page_lock, file_lock, auth, auth_middleware, audit, dry_run, rate_limit, logging_config, resolve_connection, platform, error_handling, object_inspection, project_properties, app_control, cloud_operations, layout_presets |
| `src/roles.py` | Role definitions (media/edit/color/fusion/fairlight/deliver/director/full) |
| `src/server_factory.py` | Builds a role-scoped FastMCP and wraps tools with page-lock + audit + rate-limit + dry-run |
| `tests/unit/` | 137 unit tests with mocks (no DaVinci required) |
| `tests/integration/` | Integration tests (requires running DaVinci Resolve) |
| `scripts/` | `launch-team.ps1`, `launch-team.sh`, setup scripts |
| `config/` | MCP config templates for Cursor/Claude Desktop |
| `docs/` | API reference, features, changelog, `AGENT_TEAM.md` |
| `logs/` | `audit.jsonl` — append-only tool-call audit trail |

## Code Conventions

- Tools: `@mcp.tool(annotations=READ_ONLY|SAFE_WRITE|DESTRUCTIVE)` from `src/utils/safety.py`
- Resources: `@mcp.resource("resolve://...")`
- Global state via singleton in `src/context.py` — `get_resolve()` auto-reconnects on bridge death
- API functions in `src/api/` wrap DaVinci scripting calls, return strings/dicts/lists
- Type hints used throughout
- Roles defined in `src/roles.py`; add a tool module to a role's `tool_modules` set to expose it
- No linter/formatter currently configured

## Safety

Every tool is annotated with one of three presets from `src/utils/safety.py`:

- `READ_ONLY` — pure getters, idempotent, never mutates
- `SAFE_WRITE` — mutates state but doesn't destroy data
- `DESTRUCTIVE` — deletes / overwrites / closes; MCP clients gate behind confirmation

Layered protection:
1. Tool annotations (client-side gating)
2. Role isolation (tool surface restricted per role)
3. Token isolation (per-role Bearer tokens, cross-role rejected)
4. Rate limiting (`MCP_RATE_ALL`=10/s, `MCP_RATE_DESTRUCTIVE`=0.5/s)
5. Dry-run mode (`MCP_DRY_RUN=1` or `MCP_DRY_RUN_ROLES=color,deliver`)
6. Audit log (`logs/audit.jsonl`, one JSON record per call)
7. Cross-process file lock (serializes page switches across role servers)

## Testing

- **Framework:** pytest with `asyncio_mode=auto`
- **Config:** `pytest.ini`
- **Mocks:** `tests/conftest.py` — MockResolve, MockProject, MockTimeline, etc.
- **New infra tests:** `test_roles_and_factory.py`, `test_auth_middleware.py`, `test_new_infra.py`
- **CI:** GitHub Actions on Python 3.10 / 3.11, runs `pytest tests/`

## Environment variables (HTTP mode)

| Var | Meaning |
|---|---|
| `MCP_TRANSPORT` | `stdio` or `http` |
| `MCP_HOST` / `MCP_PORT` | HTTP bind |
| `MCP_AUTH_TOKEN` | Shared bearer token |
| `MCP_AUTH_TOKENS` | `role1:tok1,role2:tok2` |
| `MCP_DRY_RUN` / `MCP_DRY_RUN_ROLES` | Dry-run gating |
| `MCP_RATE_ALL` / `MCP_RATE_DESTRUCTIVE` / `MCP_RATE_DISABLED` | Rate limiter |
| `MCP_AUDIT_LOG` | Path to audit JSONL (default `logs/audit.jsonl`) |
| `MCP_LOG_JSON` | `1` → JSON log output |
| `MCP_DISABLE_FILE_LOCK` | `1` → disable cross-process page lock |

## Remaining Issues

### Medium
- No Prometheus/metrics endpoint (audit.jsonl covers post-hoc analysis)
- No idempotency-key support for destructive tools (retry-safe `import_media`)

### Low
- Test coverage ~45%, many api/* modules still without direct tests
- No linter/formatter configured (black, flake8, mypy)
- No audit-log rotation (rely on external logrotate)
