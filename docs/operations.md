# Operations Reference

The bridge exposes 16 operations for controlling Super Productivity. These are the stable contract — transport-specific names (MCP tools, CLI subcommands) are adapter details.

Verified against Super Productivity 18.8.0 (commit `24725c9`).

## Call Shape

```text
operation: "task.create"
payload:   { "title": "Review budget", "projectId": "p1" }
```

## Result Shape

```json
{
  "ok": true,
  "data": { ... }
}
```

## Error Shape

```json
{
  "ok": false,
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Resource not found.",
    "details": { "status_code": 404 }
  }
}
```

## Operations

| Operation            | Description                          | Required Payload   |
|----------------------|--------------------------------------|--------------------|
| `task.list`          | List tasks (with optional filters)   | —                  |
| `task.get`           | Get a task by ID                     | `id`               |
| `task.create`        | Create a new task                    | `title`            |
| `task.update`        | Update fields on an existing task    | `id`               |
| `task.complete`      | Mark a task as done                  | `id`               |
| `task.uncomplete`    | Mark a task as not done              | `id`               |
| `task.start`         | Start time tracking for a task       | `id`               |
| `task.stop_current`  | Stop the currently tracked task      | —                  |
| `task.get_current`   | Get the currently tracked task       | —                  |
| `task.set_current`   | Set or clear the current task        | `taskId`           |
| `task.archive`       | Archive a task                       | `id`               |
| `task.restore`       | Restore an archived task             | `id`               |
| `project.list`       | List all projects (with query)       | —                  |
| `tag.list`           | List all tags (with query)           | —                  |
| `status.get`         | Get SP status summary                | —                  |
| `bridge.health`      | Check SP connectivity and status     | —                  |

## Local REST Mapping

| Operation            | HTTP Method | Endpoint              |
|----------------------|-------------|-----------------------|
| `task.list`          | GET         | `/tasks`              |
| `task.get`           | GET         | `/tasks/:id`          |
| `task.create`        | POST        | `/tasks`              |
| `task.update`        | PATCH       | `/tasks/:id`          |
| `task.complete`      | PATCH       | `/tasks/:id` (`{"isDone": true}`)  |
| `task.uncomplete`    | PATCH       | `/tasks/:id` (`{"isDone": false}`) |
| `task.start`         | POST        | `/tasks/:id/start`    |
| `task.stop_current`  | POST        | `/task-control/stop`  |
| `task.get_current`   | GET         | `/task-control/current` |
| `task.set_current`   | POST        | `/task-control/current` |
| `task.archive`       | POST        | `/tasks/:id/archive`  |
| `task.restore`       | POST        | `/tasks/:id/restore`  |
| `project.list`       | GET         | `/projects`           |
| `tag.list`           | GET         | `/tags`               |
| `status.get`         | GET         | `/status`             |
| `bridge.health`      | GET         | `/health` + `/status` |

## Error Codes

| Code                   | Meaning                                              |
|------------------------|------------------------------------------------------|
| `SP_UNAVAILABLE`       | Cannot connect to SP (connection refused, DNS error) |
| `TIMEOUT`              | Request to SP timed out                              |
| `UNKNOWN_OPERATION`    | Operation name not recognized                        |
| `UNSUPPORTED_OPERATION`| Operation recognized but not available               |
| `INVALID_INPUT`        | Payload validation failed                            |
| `TASK_NOT_FOUND`       | Requested task does not exist (HTTP 404)             |
| `PROJECT_NOT_FOUND`    | Requested project does not exist                     |
| `SP_ERROR`             | SP returned an error response                        |
| `INTERNAL_ERROR`       | Unexpected bridge failure                            |

## MCP Tool Names

The MCP adapter maps snake_case tool names to core operations:

| MCP Tool            | Core Operation       |
|---------------------|----------------------|
| `health`            | `bridge.health`      |
| `get_status`        | `status.get`         |
| `list_tasks`        | `task.list`          |
| `get_task`          | `task.get`           |
| `create_task`       | `task.create`        |
| `update_task`       | `task.update`        |
| `complete_task`     | `task.complete`      |
| `uncomplete_task`   | `task.uncomplete`    |
| `start_task`        | `task.start`         |
| `stop_current_task` | `task.stop_current`  |
| `get_current_task`  | `task.get_current`   |
| `set_current_task`  | `task.set_current`   |
| `archive_task`      | `task.archive`       |
| `restore_task`      | `task.restore`       |
| `list_projects`     | `project.list`       |
| `list_tags`         | `tag.list`           |

## Payload Fields

Use Super Productivity's native camelCase field names at all REST boundaries.

### `task.create` fields

| Field          | Type                    | Required | Notes                                                |
|----------------|-------------------------|----------|------------------------------------------------------|
| `title`        | `string`                | **yes**  | Non-empty                                            |
| `projectId`    | `string \| null`        | no       | Project to assign                                    |
| `tagIds`       | `string[]`              | no       | Tag IDs to assign                                    |
| `notes`        | `string`                | no       | Task notes                                           |
| `parentId`     | `string`                | no       | Parent task ID (subtask). **Create-only.** Cannot be combined with `projectId` or `tagIds` (subtasks inherit from parent) |
| `plannedAt`    | `string \| int \| null` | no       | Planned date/time (ISO string or Unix ms timestamp)  |
| `dueDay`       | `string \| null`        | no       | Due date (YYYY-MM-DD format)                         |
| `dueWithTime`  | `int \| null`           | no       | Due date+time as Unix millisecond timestamp          |
| `isDone`       | `boolean`               | no       | Completion status                                    |
| `timeEstimate` | `int`                   | no       | Estimated time in milliseconds (≥ 0)                 |
| `timeSpent`    | `int`                   | no       | Time spent in milliseconds (≥ 0). **Absolute replacement**, not additive |

### `task.update` fields

Same as `task.create` except:
- `id` is **required** (identifies the task to update)
- `parentId` is **not allowed** (upstream rejects it on PATCH)
- At least one field besides `id` must be provided

### `task.list` filters

All optional query parameters passed as payload fields:

| Field         | Type      | Notes                                            |
|---------------|-----------|--------------------------------------------------|
| `query`       | `string`  | Search tasks by title substring                  |
| `projectId`   | `string`  | Filter by project ID                             |
| `tagId`       | `string`  | Filter by tag ID                                 |
| `includeDone` | `boolean` | Include completed tasks (default: false)         |
| `source`      | `string`  | `"active"` (default), `"archived"`, or `"all"`   |

### `project.list` / `tag.list` filters

| Field   | Type     | Notes                     |
|---------|----------|---------------------------|
| `query` | `string` | Filter by name substring  |

### `task.set_current` payload

| Field    | Type            | Notes                                        |
|----------|-----------------|----------------------------------------------|
| `taskId` | `string \| null`| **Required.** Task ID to set as current, or `null` to clear. |

### No-payload operations

`task.get_current`, `task.stop_current`, `status.get`, `bridge.health` take no payload.

### ID-only operations

`task.get`, `task.complete`, `task.uncomplete`, `task.start`, `task.archive`, `task.restore` require only `{ "id": "<task-id>" }`.

## Excluded Operations

- `task.delete` — intentionally excluded from v1. Deletion is destructive and irreversible in SP.

## Examples

### Create a task

```json
{
  "operation": "task.create",
  "payload": {
    "title": "Write integration tests",
    "projectId": "project-1",
    "tagIds": ["tag-dev"],
    "notes": "Cover REST client edge cases"
  }
}
```

### Update a task

```json
{
  "operation": "task.update",
  "payload": {
    "id": "task-abc123",
    "title": "Write integration tests (updated)",
    "isDone": true
  }
}
```

### Complete a task

```json
{
  "operation": "task.complete",
  "payload": { "id": "task-abc123" }
}
```

### Archive a task

```json
{
  "operation": "task.archive",
  "payload": { "id": "task-abc123" }
}
```

## Known REST API Gaps

These operations are not available via the SP Local REST API and are candidates for future versions:

- `project.create`
- `tag.create`
- `notification.show`
- Recurring task creation / repeat config

## API Contract Fixtures

Canonical SP REST API response shapes are maintained in [`tests/fixtures/`](https://github.com/CameronBrooks11/super-productivity-local-bridge/tree/main/tests/fixtures). Files without qualifiers (e.g. `task-list-ok.json`) represent observed API responses. Files with qualifiers (e.g. `task-create-error-with-details.json`) are synthetic edge cases.

## MCP Error Semantics

| Condition | MCP behavior |
|-----------|-------------|
| SP returns an error | `CallToolResult(isError=True)` with error code and message |
| SP unreachable / timeout | `CallToolResult(isError=True)` with `SP_UNAVAILABLE` or `TIMEOUT` |
| Payload validation failure | `CallToolResult(isError=True)` with `INVALID_INPUT` |
| Unknown tool name | `CallToolResult(isError=True)` with "Unknown tool: ..." message |
