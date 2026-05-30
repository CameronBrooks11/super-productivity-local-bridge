# VS Code Copilot

## Prerequisites

- [Super Productivity](https://super-productivity.com/) desktop app running with Local REST API enabled (Settings → Misc)
- [VS Code](https://code.visualstudio.com/) with GitHub Copilot Chat extension
- `sp-local-bridge` installed ([Getting Started](../getting-started.md))

## Install Bridge

```sh
git clone https://github.com/CameronBrooks11/super-productivity-local-bridge.git
cd super-productivity-local-bridge
scripts/install.sh
```

## Generate Config

```sh
sp-local-bridge-print-config vscode-copilot
```

Example output:

```json
{
  "servers": {
    "superProductivity": {
      "type": "stdio",
      "command": "/home/you/.local/bin/sp-local-bridge-mcp",
      "args": []
    }
  }
}
```

The command path will be resolved to your actual installation location.

Use `--bare` for a bare command name (only works if `~/.local/bin` is on VS Code's PATH).

## Add Config

Add the output to one of:

- **Workspace:** `.vscode/mcp.json` in your project root
- **Global:** Command Palette → `MCP: Open User Configuration`

## Restart or Reload Host

VS Code will detect the new config automatically. If prompted, trust the MCP server.

If tools don't appear, run `MCP: Reset Cached Tools` from the Command Palette or restart VS Code.

## Verify

```sh
sp-local-bridge-doctor
```

Or ask Copilot Chat to check Super Productivity health — it will invoke the `bridge_health` tool.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Server not starting | Run `MCP: List Servers` → select server → "Show Output" for logs |
| SP unreachable | Start Super Productivity, enable Local REST API (Settings → Misc) |
| Tools not appearing | `MCP: Reset Cached Tools` or restart VS Code |
| Command not found | Re-run `sp-local-bridge-print-config vscode-copilot` for absolute path |

See also: [Troubleshooting](../troubleshooting.md)

## Uninstall Cleanup

1. Remove the `superProductivity` entry from `.vscode/mcp.json` or user settings
2. Optionally run `scripts/uninstall.sh` to remove the bridge binary
