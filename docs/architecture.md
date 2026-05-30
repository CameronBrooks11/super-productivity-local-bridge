# Architecture

## Design

```
MCP client / CLI / agent host
        ↓
    host adapter (thin)
        ↓
    core operations
        ↓
  SP Local REST API (http://127.0.0.1:3876)
        ↓
  Super Productivity desktop app
```

The bridge uses Super Productivity's Local REST API as the primary app-control path. MCP is one thin adapter. The core operation layer is host-agnostic.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| App control | SP Local REST API | Built-in desktop control surface; no plugin required |
| Core models | Pydantic | Already a transitive dep of `mcp`; validation + serialization |
| HTTP client | httpx | Async, already transitive dep of `mcp` |
| MCP adapter | Low-level `Server` | Full protocol control; business logic stays in `core/` |
| Field naming | camelCase at REST boundaries | Match SP-native field names (`projectId`, `tagIds`) |
| Operation naming | `task.create` (dot-namespaced) | Host-agnostic; MCP adapter maps to `create_task` |
| `task.delete` | Excluded | Destructive; deferred until confirmation UX is designed |
| Plugin fallback | Deferred | Only needed for operations the REST API cannot support |

## Boundaries

```
src/sp_local_bridge/
├── core/           Core operation models, errors, service (no transport knowledge)
├── sp_rest/        SP Local REST API client (httpx, translates HTTP to core errors)
├── adapters/       Host adapters (MCP server — thin, maps tools to operations)
└── diagnostics/    Doctor, host config generator (user-facing CLI utilities)
```

Rules:
- No MCP imports inside `core/` or `sp_rest/`
- No host-specific language in core operation descriptions
- Adapter declares tools and maps calls to core service — no business logic
- All SP communication goes through `sp_rest/client.py`
