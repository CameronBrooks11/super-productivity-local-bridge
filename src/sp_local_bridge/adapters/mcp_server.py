"""MCP server adapter — maps MCP tool calls to core bridge operations."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import INVALID_PARAMS, CallToolResult, ErrorData, TextContent, Tool, ToolAnnotations

from sp_local_bridge.core.models import BridgeRequest, BridgeResult
from sp_local_bridge.core.operations import Operation
from sp_local_bridge.core.service import BridgeService
from sp_local_bridge.sp_rest.client import SPRestClient

# MCP tool name → core operation mapping
_TOOL_MAP: dict[str, Operation] = {
    "health": Operation.BRIDGE_HEALTH,
    "list_tasks": Operation.TASK_LIST,
    "get_task": Operation.TASK_GET,
    "create_task": Operation.TASK_CREATE,
    "update_task": Operation.TASK_UPDATE,
    "complete_task": Operation.TASK_COMPLETE,
    "uncomplete_task": Operation.TASK_UNCOMPLETE,
    "start_task": Operation.TASK_START,
    "stop_current_task": Operation.TASK_STOP_CURRENT,
    "archive_task": Operation.TASK_ARCHIVE,
    "restore_task": Operation.TASK_RESTORE,
    "list_projects": Operation.PROJECT_LIST,
    "list_tags": Operation.TAG_LIST,
}

# Annotation presets
_READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
_MUTATING = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)
_IDEMPOTENT_MUTATING = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False
)

# Tool definitions with input schemas and annotations
_TOOLS: list[Tool] = [
    Tool(
        name="health",
        description="Check connectivity to the Super Productivity desktop app.",
        inputSchema={"type": "object", "properties": {}},
        annotations=_READ_ONLY,
    ),
    Tool(
        name="list_tasks",
        description="List all tasks.",
        inputSchema={"type": "object", "properties": {}},
        annotations=_READ_ONLY,
    ),
    Tool(
        name="get_task",
        description="Get a task by its ID.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Task ID."}},
            "required": ["id"],
        },
        annotations=_READ_ONLY,
    ),
    Tool(
        name="create_task",
        description="Create a new task with a title and optional fields (see schema).",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title."},
                "projectId": {"type": ["string", "null"], "description": "Project ID to assign."},
                "tagIds": {"type": "array", "items": {"type": "string"}, "description": "Tag IDs to assign."},
                "notes": {"type": "string", "description": "Task notes."},
                "parentId": {
                    "type": "string",
                    "description": "Parent task ID for subtasks. Cannot be combined with projectId or tagIds.",
                },
                "plannedAt": {
                    "type": ["integer", "string", "null"],
                    "description": "Planned date/time (Unix ms timestamp, ISO string, or null to clear).",
                },
                "dueDay": {"type": ["string", "null"], "description": "Due date (YYYY-MM-DD or null to clear)."},
                "dueWithTime": {
                    "type": ["integer", "null"],
                    "description": "Due date+time as Unix ms timestamp, or null to clear.",
                },
                "isDone": {"type": "boolean", "description": "Completion status."},
            },
            "required": ["title"],
        },
        annotations=_MUTATING,
    ),
    Tool(
        name="update_task",
        description="Update an existing task by ID. Pass only the fields to change.",
        inputSchema={
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Task ID."},
                "title": {"type": "string", "description": "New title."},
                "notes": {"type": "string", "description": "New notes."},
                "projectId": {"type": ["string", "null"], "description": "New project ID or null to clear."},
                "tagIds": {"type": "array", "items": {"type": "string"}, "description": "New tag IDs."},
                "plannedAt": {
                    "type": ["integer", "string", "null"],
                    "description": "Planned date/time (Unix ms timestamp, ISO string, or null to clear).",
                },
                "dueDay": {"type": ["string", "null"], "description": "Due date (YYYY-MM-DD or null to clear)."},
                "dueWithTime": {
                    "type": ["integer", "null"],
                    "description": "Due date+time as Unix ms timestamp, or null to clear.",
                },
                "isDone": {"type": "boolean", "description": "Completion status."},
            },
            "required": ["id"],
        },
        annotations=_MUTATING,
    ),
    Tool(
        name="complete_task",
        description="Mark a task as done.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Task ID."}},
            "required": ["id"],
        },
        annotations=_IDEMPOTENT_MUTATING,
    ),
    Tool(
        name="uncomplete_task",
        description="Mark a task as not done.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Task ID."}},
            "required": ["id"],
        },
        annotations=_IDEMPOTENT_MUTATING,
    ),
    Tool(
        name="start_task",
        description="Start time tracking for a task.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Task ID."}},
            "required": ["id"],
        },
        annotations=_MUTATING,
    ),
    Tool(
        name="stop_current_task",
        description="Stop the currently tracked task.",
        inputSchema={"type": "object", "properties": {}},
        annotations=_MUTATING,
    ),
    Tool(
        name="archive_task",
        description="Archive a task by ID.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Task ID."}},
            "required": ["id"],
        },
        annotations=_MUTATING,
    ),
    Tool(
        name="restore_task",
        description="Restore an archived task by ID.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Task ID."}},
            "required": ["id"],
        },
        annotations=_MUTATING,
    ),
    Tool(
        name="list_projects",
        description="List all projects.",
        inputSchema={"type": "object", "properties": {}},
        annotations=_READ_ONLY,
    ),
    Tool(
        name="list_tags",
        description="List all tags.",
        inputSchema={"type": "object", "properties": {}},
        annotations=_READ_ONLY,
    ),
]


def _result_to_call_result(result: BridgeResult) -> CallToolResult:
    """Convert a BridgeResult to an MCP CallToolResult with proper isError semantics."""
    if result.ok:
        # Return structured data as JSON text content
        text = json.dumps(result.data, indent=2, default=str)
        return CallToolResult(content=[TextContent(type="text", text=text)], isError=False)
    else:
        assert result.error is not None
        error_payload: dict[str, Any] = {
            "error": result.error.code,
            "message": result.error.message,
        }
        if result.error.details:
            error_payload["details"] = result.error.details
        text = json.dumps(error_payload, indent=2)
        return CallToolResult(content=[TextContent(type="text", text=text)], isError=True)


def _result_to_structured(result: BridgeResult) -> dict[str, Any] | CallToolResult:
    """Convert a BridgeResult to structured content (dict) or CallToolResult for errors.

    The MCP SDK handles dict returns by placing them in structuredContent and
    generating a JSON text fallback in content automatically.
    For errors, we return a CallToolResult with isError=True since structured
    content doesn't support error signaling.
    """
    if result.ok:
        # Return dict — SDK puts it in structuredContent + generates text fallback
        if isinstance(result.data, dict):
            return result.data
        # For non-dict data (lists, None), wrap in a dict
        return {"result": result.data}
    else:
        assert result.error is not None
        error_payload: dict[str, Any] = {
            "error": result.error.code,
            "message": result.error.message,
        }
        if result.error.details:
            error_payload["details"] = result.error.details
        text = json.dumps(error_payload, indent=2)
        return CallToolResult(content=[TextContent(type="text", text=text)], isError=True)


async def _serve() -> None:
    """Run the MCP stdio server."""
    base_url = os.environ.get("SP_BASE_URL")
    client = SPRestClient(base_url=base_url) if base_url else SPRestClient()
    service = BridgeService(client)
    server = create_server(service)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def create_server(service: BridgeService | None = None) -> Server:
    """Create and configure the MCP server. Useful for testing."""
    if service is None:
        service = BridgeService(SPRestClient())
    server = Server("sp-local-bridge")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return _TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> dict[str, Any] | CallToolResult:
        operation = _TOOL_MAP.get(name)
        if operation is None:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Unknown tool: {name}"))

        payload = arguments or {}
        request = BridgeRequest(operation=operation, payload=payload)
        result = await service.execute(request)
        return _result_to_structured(result)

    return server


def main() -> None:
    """Run the MCP stdio server."""
    try:
        asyncio.run(_serve())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"sp-local-bridge-mcp: {exc}", file=sys.stderr)
        sys.exit(1)
