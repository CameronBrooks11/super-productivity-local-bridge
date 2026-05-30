# Validation

This page documents the manual validation performed against a live Super Productivity instance.

## Install Validation

**Date:** 2026-05-30

Verified:
- Clean install via `scripts/install.sh` succeeds on Linux (Python 3.11, uv 0.11.12)
- All 4 entry points are accessible after install: `sp-local-bridge`, `sp-local-bridge-mcp`, `sp-local-bridge-doctor`, `sp-local-bridge-print-config`
- `--dry-run` mode previews without side effects
- Uninstall script removes all installed binaries
- Reinstall over existing installation works without errors

## Live Integration Test

**Date:** 2026-05-30
**Host:** VS Code Copilot (MCP via `.vscode/mcp.json`)
**SP Version:** Super Productivity desktop app with Local REST API enabled
**Bridge Version:** 0.1.0

### Tools Validated

All 13 MCP tools were invoked successfully against a live SP instance with real user data:

| Tool | Result |
|------|--------|
| `bridge_health` | ✓ Connected, status returned |
| `list_tasks` | ✓ Returned 59 active tasks |
| `get_task` | ✓ Returned full task details |
| `create_task` | ✓ Task created with title, project, tags |
| `update_task` | ✓ Fields updated correctly |
| `complete_task` | ✓ Task marked done |
| `uncomplete_task` | ✓ Task marked not done |
| `start_task` | ✓ Time tracking started |
| `stop_current_task` | ✓ Time tracking stopped |
| `archive_task` | ✓ Task archived |
| `restore_task` | ✓ Task restored from archive |
| `list_projects` | ✓ All projects returned |
| `list_tags` | ✓ All tags returned |

### Failure Recovery

- Stopped SP while bridge was configured → tool calls returned `SP_UNAVAILABLE` error
- Restarted SP → next tool call succeeded without bridge restart
- No manual intervention required for recovery

### Data Cleanup

- Test task created during validation was archived
- Active task count returned to pre-test baseline (59)
- No orphaned or corrupted data observed

### Defects Found

None.

## Scope and Limitations

- Validation was performed manually, not via automated integration tests
- Tested on Linux only (Ubuntu-based)
- Single host validated (VS Code Copilot); Claude Desktop and Codex are config-supported but not live-tested
- SP Local REST API behavior may vary across SP versions
