# VS Code Copilot Host Configuration

## Prerequisites

1. [Super Productivity](https://super-productivity.com/) desktop app running with Local REST API enabled (Settings → Misc)
2. `sp-local-bridge` installed (see below)
3. VS Code with GitHub Copilot Chat extension

## Install

```sh
git clone https://github.com/CameronBrooks11/super-productivity-local-bridge.git
cd super-productivity-local-bridge
scripts/install.sh
```

## Configure VS Code

Run:
```sh
sp-local-bridge-print-config vscode-copilot
```

Output:
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

Add the above to `.vscode/mcp.json` in your workspace (for project-scoped access) or run `MCP: Open User Configuration` from the Command Palette for global access.

VS Code will prompt you to trust the server on first use. Accept the prompt to start the server.

If you prefer a bare command name (only works if `~/.local/bin` is on VS Code's PATH):
```sh
sp-local-bridge-print-config --bare vscode-copilot
```

## Verify

```sh
sp-local-bridge-doctor
```

Or use the MCP tools directly in Copilot Chat — ask it to check Super Productivity health.

## Available Tools

Once configured, Copilot Chat can use 13 tools: `health`, `list_tasks`, `get_task`, `create_task`, `update_task`, `complete_task`, `uncomplete_task`, `start_task`, `stop_current_task`, `archive_task`, `restore_task`, `list_projects`, `list_tags`.

## Troubleshooting

- **Server not starting**: Check the MCP output log — run `MCP: List Servers` from Command Palette, select the server, then "Show Output".
- **SP unreachable**: Ensure Super Productivity is running and Local REST API is enabled in Settings → Misc.
- **Tools not appearing**: Run `MCP: Reset Cached Tools` from the Command Palette, or restart the server.
- **Command not found**: Re-run `sp-local-bridge-print-config vscode-copilot` — it resolves the absolute path to the installed binary.
