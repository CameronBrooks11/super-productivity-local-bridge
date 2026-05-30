# Super Productivity Local Bridge

Local automation bridge for [Super Productivity](https://super-productivity.com/) — control tasks, projects, and tags from external tools via MCP, CLI, or any host adapter.

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

## Install

```sh
git clone https://github.com/CameronBrooks11/super-productivity-local-bridge.git
cd super-productivity-local-bridge
scripts/install.sh
```

The install script will:
1. Check prerequisites (Python 3.11+, uv)
2. Install the bridge as a tool (`uv tool install`)
3. Verify all commands are accessible
4. Print next steps

Use `scripts/install.sh --dry-run` to preview without making changes.

### Configure MCP Host

```sh
sp-local-bridge-print-config vscode-copilot   # VS Code Copilot / Codex in VS Code
sp-local-bridge-print-config claude-desktop    # Claude Desktop
sp-local-bridge-print-config codex             # Codex CLI (standalone)
```

This prints a config snippet with the **absolute path** to the MCP server command. Add it to the appropriate config file (path shown in output), then restart the host.

Host guides:
- [VS Code Copilot](docs/hosts/vscode-copilot.md)
- [Claude Desktop](docs/hosts/claude-desktop.md)
- [Codex CLI](docs/hosts/codex.md)

### Verify

```sh
sp-local-bridge-doctor
```

### Uninstall

```sh
scripts/uninstall.sh
```

## CLI Usage

```sh
sp-local-bridge health              # Check SP connectivity
sp-local-bridge tasks list          # List all tasks
sp-local-bridge tasks get <id>      # Get a task by ID
sp-local-bridge tasks add "Title"   # Create a new task
sp-local-bridge projects list       # List all projects
sp-local-bridge tags list           # List all tags
```

## Development

```sh
uv sync                         # Install all deps (creates .venv)
uv run ruff format .            # Format code
uv run ruff check .             # Lint
uv run pyright                  # Type check
uv run pytest                   # Run tests
uv run pytest --cov             # Tests with coverage
make check                      # All checks (format, lint, types, tests, build)
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
