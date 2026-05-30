# Super Productivity Local Bridge

[![CI](https://github.com/CameronBrooks11/super-productivity-local-bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/CameronBrooks11/super-productivity-local-bridge/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Control [Super Productivity](https://super-productivity.com/) tasks, projects, and tags from MCP hosts, CLI, and local automation tools — all through the desktop app's Local REST API.

## Why

Super Productivity is a great task manager. This bridge lets AI coding agents and automation scripts interact with it programmatically — creating tasks, tracking work, and managing projects without leaving your workflow.

Everything runs locally on `127.0.0.1:3876`. No cloud. No accounts. No data leaves your machine.

## Features

- **13 operations** — list/get/create/update/complete/start/stop/archive/restore tasks, list projects, list tags, health check
- **MCP adapter** — works with VS Code Copilot, Claude Desktop, Codex CLI, and any MCP-compatible host
- **CLI** — direct command-line access to all operations
- **Host config generator** — prints ready-to-paste config with absolute paths for each supported host
- **Doctor command** — diagnoses connectivity and configuration issues

## Install

```sh
git clone https://github.com/CameronBrooks11/super-productivity-local-bridge.git
cd super-productivity-local-bridge
scripts/install.sh
```

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). Use `--dry-run` to preview.

## Configure an MCP Host

```sh
sp-local-bridge-print-config vscode-copilot   # VS Code Copilot
sp-local-bridge-print-config claude-desktop    # Claude Desktop
sp-local-bridge-print-config codex             # Codex CLI
```

Add the printed snippet to the config file shown in the output, then restart the host.

See the [host setup guides](https://cameronbrooks11.github.io/super-productivity-local-bridge/hosts/) for detailed instructions.

## Verify

```sh
sp-local-bridge-doctor
```

## Safety

This bridge has **write access** to your Super Productivity data (create, update, complete, archive tasks). It talks only to localhost. `task.delete` is intentionally excluded. Back up your SP data before heavy automation use.

See [Security](https://cameronbrooks11.github.io/super-productivity-local-bridge/security) for the full risk profile.

## Documentation

Full docs: [cameronbrooks11.github.io/super-productivity-local-bridge](https://cameronbrooks11.github.io/super-productivity-local-bridge/)

- [Getting Started](https://cameronbrooks11.github.io/super-productivity-local-bridge/getting-started)
- [Operations Reference](https://cameronbrooks11.github.io/super-productivity-local-bridge/operations)
- [Architecture](https://cameronbrooks11.github.io/super-productivity-local-bridge/architecture)
- [Troubleshooting](https://cameronbrooks11.github.io/super-productivity-local-bridge/troubleshooting)

## Development

```sh
uv sync                     # Install deps
make check                  # Format, lint, typecheck, test, build
uv run pytest --cov         # Tests with coverage
uv run pre-commit install   # Git hooks
```

## License

[MIT](LICENSE)
