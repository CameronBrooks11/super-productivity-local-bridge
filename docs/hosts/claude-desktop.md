# Claude Desktop Host Configuration

To use the Super Productivity Local Bridge with Claude Desktop, add the following to your Claude Desktop config file:

**Linux:** `~/.config/Claude/claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

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

Then restart Claude Desktop.

## Prerequisites

1. Super Productivity desktop app running with Local REST API enabled (Settings → Misc)
2. `sp-local-bridge` installed (`uv tool install sp-local-bridge` or from source)
3. Verify with: `sp-local-bridge-doctor`
