# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project

Super Productivity Local Bridge — a local automation bridge for the Super Productivity desktop app. Uses the SP Local REST API (`http://127.0.0.1:3876`) as the primary app-control path, with MCP as one thin host adapter.

## Stack

- **Python 3.11+** with `uv` for environment/dependency management
- **Pydantic** for models and validation
- **httpx** for the SP Local REST client
- **MCP Python SDK** for the MCP adapter (stdio transport)
- **Ruff** for formatting and linting
- **Pyright** for type checking
- **Pytest** for testing

## Layout

```
src/sp_local_bridge/       Python package (src layout)
  core/                    Core operation models, errors, service
  sp_rest/                 SP Local REST API client
  adapters/                Host adapters (MCP server)
  diagnostics/             Doctor, health checks
  cli.py                   CLI entry point
tests/                     Pytest tests
docs/                      Documentation
```

## Commands

```sh
uv sync                    # Install deps (creates .venv)
uv run ruff format .       # Format
uv run ruff check .        # Lint
uv run pyright             # Type check
uv run pytest              # Test
uv run pytest --cov        # Test with coverage
make check                 # Run all checks (format, lint, types, tests)
```

## Conventions

- All Python code lives under `src/sp_local_bridge/` (src layout).
- Use pydantic BaseModel for data structures crossing boundaries.
- Use `httpx.AsyncClient` for HTTP calls to SP.
- MCP adapter is thin — all logic lives in `core/`.
- No Claude/agent-specific language in tool descriptions or core code.
- Use SP-native camelCase field names at REST boundaries (`projectId`, `tagIds`).
- Type annotations on all public functions.
- Tests in `tests/` mirror `src/` structure.

## Do NOT

- Add runtime deps without discussing (the dep tree is intentionally small).
- Put business logic in the MCP adapter.
- Reference specific AI hosts (Claude, Cursor, etc.) outside `docs/hosts/`.
- Create files named after phases or milestones.
- Commit `.venv/`, `working/`, `refs/`, or build artifacts.
