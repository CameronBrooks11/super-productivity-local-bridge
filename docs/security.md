# Security

## Scope

Super Productivity Local Bridge is a **local automation tool with write access** to your Super Productivity data. It can:

- Create tasks
- Update task fields (title, notes, project, tags, due date)
- Mark tasks complete or incomplete
- Start and stop task time tracking
- Archive and restore tasks
- List tasks, projects, and tags

## What It Cannot Do

- **Delete tasks** — `task.delete` is intentionally excluded from v0.1
- **Access network resources** — all communication is to `127.0.0.1:3876`
- **Modify SP settings** — the bridge only uses data endpoints
- **Send data externally** — no telemetry, no cloud, no outbound connections

## Network Exposure

The bridge communicates exclusively with the Super Productivity Local REST API at `http://127.0.0.1:3876`. This API is provided by the SP desktop app and listens only on localhost.

**Do not expose the SP Local REST API over a network.** It has no authentication and grants full read/write access to your task data.

## MCP Host Access

When you configure an MCP host (VS Code Copilot, Claude Desktop, Codex, etc.) to use this bridge, you are granting that host the ability to invoke all 13 bridge operations. Be mindful of:

- Which hosts you configure
- What prompts or agents have access to the MCP tools
- Whether the host has auto-approval or requires confirmation for tool calls

## Recommendations

1. **Back up your Super Productivity data** before heavy or experimental automation use
2. **Review tool calls** — if your MCP host supports confirmation prompts, enable them initially
3. **Use `--dry-run`** during install to verify what will be installed before committing
4. **Run `sp-local-bridge-doctor`** after setup to confirm the bridge is correctly connected
5. **Remove host config** if you stop using the bridge — stale configs may cause host startup errors

## Blast Radius

If something goes wrong:

- Tasks may be created, modified, or archived unexpectedly
- Time tracking may be started or stopped
- No tasks will be deleted (not supported)
- SP's built-in undo and archive/restore can recover most changes
- SP's automatic backups provide additional safety net
