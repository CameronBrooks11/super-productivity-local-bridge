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
uv tool install --from . sp-local-bridge
```

## Configure Claude Desktop

Run:
```sh
sp-local-bridge-print-config claude-desktop
```

Output:
```json
{
  "mcpServers": {
    "super-productivity": {
      "command": "sp-local-bridge-mcp",
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
- **sp-local-bridge-mcp not found**: Ensure `~/.local/bin` is on your PATH, or reinstall with `scripts/install.sh`.
- **Claude Desktop doesn't show tools**: Restart Claude Desktop after editing the config file.
