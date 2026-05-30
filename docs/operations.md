# Core Operations v1

The durable bridge contract. Transport-specific schemas (MCP tool names, CLI subcommands) are adapter details.

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

| Operation         | Description                          | Required Payload   |
|-------------------|--------------------------------------|--------------------|
| `task.list`       | List all tasks                       | —                  |
| `task.get`        | Get a task by ID                     | `id`               |
| `task.create`     | Create a new task                    | `title`            |
| `task.update`     | Update fields on an existing task    | `id`               |
| `task.complete`   | Mark a task as done                  | `id`               |
| `task.uncomplete` | Mark a task as not done              | `id`               |
| `task.start`      | Start time tracking for a task       | `id`               |
| `task.stop_current` | Stop the currently tracked task    | —                  |
| `task.archive`    | Archive a task                       | `id`               |
| `task.restore`    | Restore an archived task             | `id`               |
| `project.list`    | List all projects                    | —                  |
| `tag.list`        | List all tags                        | —                  |
| `bridge.health`   | Check SP connectivity and status     | —                  |

## Local REST Mapping

| Operation           | HTTP Method | Endpoint              |
|---------------------|-------------|-----------------------|
| `task.list`         | GET         | `/tasks`              |
| `task.get`          | GET         | `/tasks/:id`          |
| `task.create`       | POST        | `/tasks`              |
| `task.update`       | PATCH       | `/tasks/:id`          |
| `task.complete`     | PATCH       | `/tasks/:id` (`{"isDone": true}`)  |
| `task.uncomplete`   | PATCH       | `/tasks/:id` (`{"isDone": false}`) |
| `task.start`        | POST        | `/tasks/:id/start`    |
| `task.stop_current` | POST        | `/task-control/stop`  |
| `task.archive`      | POST        | `/tasks/:id/archive`  |
| `task.restore`      | POST        | `/tasks/:id/restore`  |
| `project.list`      | GET         | `/projects`           |
| `tag.list`          | GET         | `/tags`               |
| `bridge.health`     | GET         | `/health` + `/status` |

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

| MCP Tool            | Core Operation      |
|---------------------|---------------------|
| `health`            | `bridge.health`     |
| `list_tasks`        | `task.list`         |
| `get_task`          | `task.get`          |
| `create_task`       | `task.create`       |
| `update_task`       | `task.update`       |
| `complete_task`     | `task.complete`     |
| `uncomplete_task`   | `task.uncomplete`   |
| `start_task`        | `task.start`        |
| `stop_current_task` | `task.stop_current` |
| `archive_task`      | `task.archive`      |
| `restore_task`      | `task.restore`      |
| `list_projects`     | `project.list`      |
| `list_tags`         | `tag.list`          |

## Payload Fields

Use Super Productivity's native camelCase field names at all REST boundaries:

- `projectId` — project association
- `tagIds` — tag associations (array)
- `parentId` — parent task for subtasks
- `plannedAt` — planned date/time
- `dueDay` — due date (date only)
- `dueWithTime` — due with specific time
- `isDone` — completion status

## Excluded Operations

- `task.delete` — intentionally excluded from v1. Deletion is destructive and deferred until explicit destructive-tool semantics are designed.

## Known REST Gaps

These operations are not available via the Local REST API and are candidates for a future PluginAPI fallback:

- `project.create`
- `tag.create`
- `notification.show`
- Recurring task creation / repeat config
