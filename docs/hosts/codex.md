# Codex Host Configuration

## Prerequisites

1. [Super Productivity](https://super-productivity.com/) desktop app running with Local REST API enabled (Settings → Misc)
2. `sp-local-bridge` installed (see below)
3. [Codex CLI](https://github.com/openai/codex) installed

## Install

```sh
git clone https://github.com/CameronBrooks11/super-productivity-local-bridge.git
cd super-productivity-local-bridge
scripts/install.sh
```

## Configure Codex

### Option A: CLI command

```sh
codex mcp add superProductivity -- /home/you/.local/bin/sp-local-bridge-mcp
```

### Option B: Edit config.toml

Run:
```sh
sp-local-bridge-print-config codex
```

Output:
```toml
[mcp_servers.superProductivity]
command = "/home/you/.local/bin/sp-local-bridge-mcp"
args = []
```

Add the above to `~/.codex/config.toml` (global) or `.codex/config.toml` (project-scoped, trusted projects only).

If you prefer a bare command name (only works if `~/.local/bin` is on PATH):
```sh
sp-local-bridge-print-config --bare codex
```

## Using Codex in VS Code

When running Codex as a VS Code extension, it uses the same `~/.codex/config.toml` configuration as the CLI. This is separate from VS Code Copilot's `.vscode/mcp.json`. No additional config is needed if you already configured Codex above.

## Verify

```sh
sp-local-bridge-doctor
```

Or in Codex TUI, use `/mcp` to see active servers.

## Troubleshooting

- **SP unreachable**: Ensure Super Productivity is running and Local REST API is enabled in Settings → Misc.
- **Server not starting**: Check that the command path exists and is executable.
- **MCP command path wrong**: Re-run `sp-local-bridge-print-config codex` to get the current absolute path.
