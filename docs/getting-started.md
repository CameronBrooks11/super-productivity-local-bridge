# Getting Started

Install the bridge, configure your MCP host, and verify everything works.

## Prerequisites

- [Super Productivity](https://super-productivity.com/) desktop app with **Local REST API enabled** (Settings → Sync & Export → Local REST API)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Install

```sh
git clone https://github.com/CameronBrooks11/super-productivity-local-bridge.git
cd super-productivity-local-bridge
scripts/install.sh
```

The script checks prerequisites, installs the bridge via `uv tool install`, registers the setup skill, and verifies all commands are accessible.

Use `--dry-run` to preview without making changes. Use `--verbose` to see detailed output.

### From a release artifact

If a [release](https://github.com/CameronBrooks11/super-productivity-local-bridge/releases) is available, you can install the wheel directly:

```sh
uv tool install https://github.com/CameronBrooks11/super-productivity-local-bridge/releases/download/v0.2.0/sp_local_bridge-0.2.0-py3-none-any.whl
```

Note: release installs provide CLI tools but not the setup skill or install/uninstall scripts. Clone the repo if you want the full experience.

## Configure an MCP Host

Generate a config snippet for your host:

```sh
sp-local-bridge-print-config vscode-copilot   # VS Code Copilot
sp-local-bridge-print-config claude-desktop    # Claude Desktop
sp-local-bridge-print-config codex             # Codex CLI
```

The output includes:
1. A config snippet with the **absolute path** to the MCP server command
2. The file path where you should add it

Paste the snippet into the indicated config file, then restart your host.

Use `--bare` if you want the bare command name instead of an absolute path (only works if `~/.local/bin` is on PATH).

See [Host Setup Guides](./hosts/) for detailed per-host instructions.

## Verify

Run the doctor command to check connectivity:

```sh
sp-local-bridge-doctor
```

This checks:
- Bridge installation integrity
- Super Productivity is running
- Local REST API is responding
- MCP server can start

## CLI Usage

The bridge also provides a direct CLI:

```sh
sp-local-bridge health              # Check SP connectivity
sp-local-bridge status              # Get SP app status
sp-local-bridge tasks list          # List all tasks
sp-local-bridge tasks list --query "budget" --include-done
sp-local-bridge tasks get <id>      # Get a task by ID
sp-local-bridge tasks add "Title"   # Create a new task
sp-local-bridge tasks current       # Get currently tracked task
sp-local-bridge tasks set-current <id>   # Set current task
sp-local-bridge tasks clear-current      # Clear current task
sp-local-bridge projects list       # List all projects
sp-local-bridge projects list --query "work"
sp-local-bridge tags list           # List all tags
```

See [Operations Reference](./operations.md) for the full list of filters and payload fields.

## Uninstall

```sh
scripts/uninstall.sh
```

This removes the bridge binary and cleans up the uv tool installation. You will need to manually remove any host config snippets you added.

## Next Steps

- [Operations Reference](./operations.md) — full list of available operations and their payloads
- [Architecture](./architecture.md) — how the bridge is structured
- [Troubleshooting](./troubleshooting.md) — common issues and fixes
