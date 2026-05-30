"""MCP server adapter — maps MCP tool calls to core bridge operations."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent, Tool

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

# Tool definitions with input schemas
_TOOLS: list[Tool] = [
    Tool(
        name="health",
        description="Check connectivity to the Super Productivity desktop app.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="list_tasks",
        description="List all tasks.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_task",
        description="Get a task by its ID.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Task ID."}},
            "required": ["id"],
        },
    ),
    Tool(
        name="create_task",
        description="Create a new task. Accepts title, optional projectId, tagIds, notes, parentId.",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title."},
                "projectId": {"type": "string", "description": "Project ID to assign."},
                "tagIds": {"type": "array", "items": {"type": "string"}, "description": "Tag IDs to assign."},
                "notes": {"type": "string", "description": "Task notes."},
                "parentId": {"type": "string", "description": "Parent task ID for subtasks."},
            },
            "required": ["title"],
        },
    ),
    Tool(
        name="update_task",
        description="Update an existing task by ID. Pass fields to change.",
        inputSchema={
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Task ID."},
                "title": {"type": "string", "description": "New title."},
                "notes": {"type": "string", "description": "New notes."},
                "projectId": {"type": "string", "description": "New project ID."},
                "tagIds": {"type": "array", "items": {"type": "string"}, "description": "New tag IDs."},
            },
            "required": ["id"],
        },
    ),
    Tool(
        name="complete_task",
        description="Mark a task as done.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Task ID."}},
            "required": ["id"],
        },
    ),
    Tool(
        name="uncomplete_task",
        description="Mark a task as not done.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Task ID."}},
            "required": ["id"],
        },
    ),
    Tool(
        name="start_task",
        description="Start time tracking for a task.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Task ID."}},
            "required": ["id"],
        },
    ),
    Tool(
        name="stop_current_task",
        description="Stop the currently tracked task.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="archive_task",
        description="Archive a task by ID.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Task ID."}},
            "required": ["id"],
        },
    ),
    Tool(
        name="restore_task",
        description="Restore an archived task by ID.",
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Task ID."}},
            "required": ["id"],
        },
    ),
    Tool(
        name="list_projects",
        description="List all projects.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="list_tags",
        description="List all tags.",
        inputSchema={"type": "object", "properties": {}},
    ),
]


def _result_to_call_result(result: BridgeResult) -> CallToolResult:
    """Convert a BridgeResult to an MCP CallToolResult with proper isError semantics."""
    if result.ok:
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


async def _serve() -> None:
    """Run the MCP stdio server."""
    service = BridgeService(SPRestClient())
    server = Server("sp-local-bridge")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return _TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> CallToolResult:
        operation = _TOOL_MAP.get(name)
        if operation is None:
            # Unknown tool is a protocol-level error — raise so MCP SDK returns isError=True
            raise ValueError(f"Unknown tool: {name}")

        payload = arguments or {}
        request = BridgeRequest(operation=operation, payload=payload)
        result = await service.execute(request)
        return _result_to_call_result(result)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    """Run the MCP stdio server."""
    try:
        asyncio.run(_serve())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"sp-local-bridge-mcp: {exc}", file=sys.stderr)
        sys.exit(1)
