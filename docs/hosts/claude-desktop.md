# Claude Desktop Host Configuration

## Prerequisites

1. [Super Productivity](https://super-productivity.com/) desktop app running with Local REST API enabled (Settings → Misc)
2. `sp-local-bridge` installed (see below)

## Install

```sh
# From source
git clone https://github.com/CameronBrooks11/super-productivity-local-bridge.git
cd super-productivity-local-bridge
scripts/install.sh

# Or directly with uv
uv tool install --reinstall --from . sp-local-bridge
```

## Configure Claude Desktop

Run:
```sh
sp-local-bridge-print-config claude-desktop
```

The output will contain an **absolute path** to the MCP server command, which works even if Claude Desktop does not inherit your shell PATH:

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

Add the above to your Claude Desktop config file:

| OS      | Path                                                    |
|---------|---------------------------------------------------------|
| Linux   | `~/.config/Claude/claude_desktop_config.json`           |
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json`           |

Then restart Claude Desktop.

If you prefer a bare command name (only works if `~/.local/bin` is on Claude Desktop's PATH):
```sh
sp-local-bridge-print-config --bare claude-desktop
```

## Verify

```sh
sp-local-bridge-doctor
```

Expected output when everything is working:
```
sp-local-bridge doctor
========================================
  ✓ Python 3.11.x
  ✓ sp-local-bridge 0.1.0
  ✓ MCP SDK available
  ✓ SP reachable at http://127.0.0.1:3876
  ✓ Task API functional (N tasks)
  ✓ MCP server: /path/to/sp-local-bridge-mcp
========================================
All checks passed.
```

## Troubleshooting

- **SP unreachable**: Ensure Super Productivity is running and Local REST API is enabled in Settings → Misc.
- **Claude Desktop doesn't show tools**: Restart Claude Desktop after editing the config file.
- **MCP command path wrong**: Re-run `sp-local-bridge-print-config claude-desktop` — it resolves the absolute path to the installed binary. If you moved or reinstalled, re-generate the config.
