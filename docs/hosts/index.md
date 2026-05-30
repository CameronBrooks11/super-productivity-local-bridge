# Host Setup Guides

Choose your MCP host:

- [VS Code Copilot](./vscode-copilot.md) — recommended for VS Code users
- [Claude Desktop](./claude-desktop.md) — Anthropic's desktop app
- [Codex CLI](./codex.md) — OpenAI's CLI and VS Code extension

## Quick Start (Any Host)

```sh
sp-local-bridge-print-config <host-name>
```

This prints:
1. A config snippet ready to paste
2. The file path where it goes

Then restart the host.

## How It Works

The bridge runs as an MCP server via stdio transport. Your host launches it as a subprocess when it needs to call Super Productivity tools. The bridge then translates MCP tool calls into HTTP requests to the SP Local REST API.

```
MCP Host → stdio → sp-local-bridge-mcp → HTTP → SP Local REST API → Super Productivity
```
