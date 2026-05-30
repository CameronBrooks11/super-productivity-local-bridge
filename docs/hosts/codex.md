# Codex

## Prerequisites

- [Super Productivity](https://super-productivity.com/) desktop app running with Local REST API enabled (Settings → Misc)
- [Codex CLI](https://github.com/openai/codex) installed
- `sp-local-bridge` installed ([Getting Started](../getting-started.md))

## Install Bridge

```sh
git clone https://github.com/CameronBrooks11/super-productivity-local-bridge.git
cd super-productivity-local-bridge
scripts/install.sh
```

## Generate Config

```sh
sp-local-bridge-print-config codex
```

Example output:

```toml
[mcp_servers.superProductivity]
command = '/home/you/.local/bin/sp-local-bridge-mcp'
args = []
```

The command path will be resolved to your actual installation location.

Use `--bare` for a bare command name (only works if `~/.local/bin` is on PATH).

### Alternative: CLI command

```sh
codex mcp add superProductivity -- /home/you/.local/bin/sp-local-bridge-mcp
```

Replace the path with the actual output from `sp-local-bridge-print-config codex`.

## Add Config

Add the output to your Codex config file:

- **Global:** `~/.codex/config.toml`
- **Project-scoped:** `.codex/config.toml` (trusted projects only)

Both Codex CLI and the Codex VS Code extension read from these same files. This is separate from VS Code Copilot's `.vscode/mcp.json`.

## Restart or Reload Host

If using Codex CLI, the new config is picked up on next invocation. No restart needed.

If using the Codex VS Code extension, restart the extension or reload VS Code.

## Verify

```sh
sp-local-bridge-doctor
```

Or in the Codex TUI, use `/mcp` to see active servers.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| SP unreachable | Start Super Productivity, enable Local REST API (Settings → Misc) |
| Server not starting | Verify command path exists and is executable |
| Command path wrong | Re-run `sp-local-bridge-print-config codex` for current path |
| TOML parse error | Ensure quotes and brackets are correct in config.toml |

See also: [Troubleshooting](../troubleshooting.md)

## Uninstall Cleanup

1. Remove the `[mcp_servers.superProductivity]` section from `~/.codex/config.toml`
2. Optionally run `scripts/uninstall.sh` to remove the bridge binary
