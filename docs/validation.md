# Validation

This page documents the manual validation performed against a live Super Productivity instance.

## Install Validation

**Date:** 2026-05-30

Verified:
- Clean install via `scripts/install.sh` succeeds on Linux (Python 3.11, uv 0.11.12)
- All 5 entry points are accessible after install: `sp-local-bridge`, `sp-local-bridge-mcp`, `sp-local-bridge-doctor`, `sp-local-bridge-print-config`, `sp-local-bridge-configure`
- `--dry-run` mode previews without side effects
- Uninstall script removes all installed binaries
- Reinstall over existing installation works without errors

## Live Integration Test

**Date:** 2026-05-30
**Host:** VS Code Copilot (MCP via `.vscode/mcp.json`)
**SP Version:** Super Productivity desktop app with Local REST API enabled
**Bridge Version:** 0.1.1

### Tools Validated

All 13 MCP tools were invoked successfully against a live SP instance with real user data:

| Tool | Result |
|------|--------|
| `health` | ✓ Connected, status returned |
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

## v0.2.0 Live Integration Test

**Date:** 2026-05-31
**Host:** CLI + Python API (direct invocation against live SP)
**SP Version:** Super Productivity 18.8.0 desktop app with Local REST API enabled
**Bridge Version:** 0.2.0

### New Operations Validated

| Operation | Method | Result |
|-----------|--------|--------|
| `status.get` | CLI `status` | ✓ Returned currentTask, currentTaskId, taskCount |
| `task.get_current` (idle) | CLI `tasks current` | ✓ Returned `null` when no task active |
| `task.set_current` (set) | CLI `tasks set-current <id>` | ✓ Task set as current, verified via `tasks current` |
| `task.get_current` (active) | CLI `tasks current` | ✓ Returned full task object with correct ID/title |
| `status.get` (active) | CLI `status` | ✓ Reflected active task with timeSpentOnDay |
| `task.set_current` (clear) | CLI `tasks clear-current` | ✓ Cleared current task, verified via `tasks current` → `null` |

### Filter Operations Validated

| Filter | Method | Result |
|--------|--------|--------|
| `task.list --query "Test"` | CLI | ✓ Returned 3 matching tasks (substring match) |
| `task.list --include-done` | CLI | ✓ Returned 50 tasks (34 done + 16 active) |
| `task.list --source archived` | CLI | ✓ Returned 0 (no archived tasks) |
| `task.list --source all` | CLI | ✓ Returned 16 tasks |
| `task.list --project-id <full-id>` | CLI | ✓ Returned 1 task in specified project |
| `task.list --project-id <id> --include-done` | CLI | ✓ Combined filters work |
| `project.list --query "Bio"` | CLI | ✓ Returned 1 matching project |
| `tag.list --query "TODAY"` | CLI | ✓ Returned 1 matching tag |

### Time Fields Validated

| Operation | Result |
|-----------|--------|
| `task.create` with `timeEstimate: 3600000` | ✓ Created, timeEstimate persisted |
| `task.update` with `timeSpent: 1800000` | ✓ Updated, timeSpent persisted |
| `task.get` after update | ✓ Both timeEstimate=3600000 and timeSpent=1800000 returned |

### CLI Error Handling Validated

| Scenario | Result |
|----------|--------|
| Unknown flag (`--sorce`) | ✓ Exit 2, "Unknown flag" error |
| Missing flag value (`--source` with no arg) | ✓ Exit 2, "requires a value" error |
| Invalid flag on projects (`--source all`) | ✓ Exit 2, "Unknown flag" error |
| Missing required arg (`tasks set-current`) | ✓ Exit 2, "requires a task ID" error |

### Data Cleanup

- Test task `JLGFI87ZU-vF9BfkkdyUP` created and archived after validation
- Active task count unchanged (50 pre/post)
- Current task cleared; no tracking state left behind

### Defects Found

None.

## Scope and Limitations

- Validation was performed manually, not via automated integration tests
- Tested on Linux only (Ubuntu-based)
- Single host validated (VS Code Copilot); Claude Desktop and Codex are config-supported but not live-tested
- SP Local REST API behavior may vary across SP versions
