# Claude Desktop

## Prerequisites

- [Super Productivity](https://super-productivity.com/) desktop app running with Local REST API enabled (Settings → Misc)
- [Claude Desktop](https://claude.ai/download) installed
- `sp-local-bridge` installed ([Getting Started](../getting-started.md))

## Install Bridge

```sh
git clone https://github.com/CameronBrooks11/super-productivity-local-bridge.git
cd super-productivity-local-bridge
scripts/install.sh
```

## Generate Config

```sh
sp-local-bridge-print-config claude-desktop
```

Example output:

```json
{
  "mcpServers": {
    "super-productivity": {
      "command": "/home/you/.local/bin/sp-local-bridge-mcp",
      "args": []
    }
  }
}
```

The command path will be resolved to your actual installation location. Claude Desktop typically does not inherit shell PATH, so the absolute path is required.

Use `--bare` for a bare command name (only if you've configured Claude Desktop's PATH).

## Add Config

Add the output to your Claude Desktop config file:

| OS      | Path                                                    |
|---------|---------------------------------------------------------|
| Linux   | `~/.config/Claude/claude_desktop_config.json`           |
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json`           |

If the file already exists with other MCP servers, merge the `super-productivity` entry into the existing `mcpServers` object.

## Restart or Reload Host

Restart Claude Desktop completely after editing the config file. There is no hot-reload.

## Verify

```sh
sp-local-bridge-doctor
```

Or ask Claude to check your Super Productivity health — it will invoke the bridge tools if configured correctly.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Tools not showing | Restart Claude Desktop after config edit |
| SP unreachable | Start Super Productivity, enable Local REST API (Settings → Misc) |
| Command path wrong | Re-run `sp-local-bridge-print-config claude-desktop` for current path |
| Config parse error | Validate JSON syntax — check for trailing commas |

See also: [Troubleshooting](../troubleshooting.md)

## Uninstall Cleanup

1. Remove the `super-productivity` entry from `claude_desktop_config.json`
2. Restart Claude Desktop
3. Optionally run `scripts/uninstall.sh` to remove the bridge binary
