# Super Productivity Local Bridge

Local automation bridge for [Super Productivity](https://super-productivity.com/) — control tasks, projects, and tags from external tools.

## Architecture

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

The bridge uses the Super Productivity Local REST API as the primary app-control path. MCP is one thin adapter. The core operation layer is host-agnostic.

## Prerequisites

- [Super Productivity](https://super-productivity.com/) desktop app with Local REST API enabled (Settings → Misc)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Quick Start

```sh
# Clone
git clone https://github.com/CameronBrooks11/super-productivity-local-bridge.git
cd super-productivity-local-bridge

# Install
uv sync

# Verify install
uv run sp-local-bridge --help

# Check SP connectivity (requires SP desktop app with Local REST API enabled)
uv run sp-local-bridge health

# List tasks
uv run sp-local-bridge tasks list

# Create a task
uv run sp-local-bridge tasks add "Review budget"

# List projects
uv run sp-local-bridge projects list
```

## Development

```sh
uv sync                         # Install all deps (creates .venv)
uv run ruff format .            # Format code
uv run ruff check .             # Lint
uv run pyright                  # Type check
uv run pytest                   # Run tests
uv run pytest --cov             # Tests with coverage
make check                      # All checks (format, lint, types, tests)
```

### Pre-commit hooks

```sh
uv run pre-commit install       # Install git hooks
uv run pre-commit run --all-files  # Run manually
```

## Project Status

**0.1.0** — core operations, REST client, CLI, MCP adapter, doctor, and host config generator functional. Requires SP desktop app with Local REST API enabled.

## License

[MIT](LICENSE)
