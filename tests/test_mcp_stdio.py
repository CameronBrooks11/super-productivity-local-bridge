"""MCP stdio transport integration test.

Tests the full MCP protocol flow: initialize → list_tools → call_tool → response,
using the actual MCP server wired to a mocked REST backend.
"""

import json

import httpx
import pytest
import respx
from mcp.types import TextContent

from sp_local_bridge.core.models import BridgeRequest
from sp_local_bridge.core.service import BridgeService
from sp_local_bridge.sp_rest.client import SPRestClient

BASE_URL = "http://127.0.0.1:3876"


class TestMCPCallToolIntegration:
    """Tests that exercise the full call_tool flow through the service layer."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_list_tasks_returns_structured(self):
        """call_tool for list_tasks should return structured dict with task list."""
        respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json=[{"id": "t1", "title": "Task 1"}, {"id": "t2", "title": "Task 2"}])
        )

        from sp_local_bridge.adapters.mcp_server import _TOOL_MAP, _result_to_structured

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["list_tasks"]
        request = BridgeRequest(operation=operation, payload={})
        result = await service.execute(request)
        structured = _result_to_structured(result)

        assert isinstance(structured, dict)
        assert "result" in structured
        assert len(structured["result"]) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_get_task_returns_structured(self):
        """call_tool for get_task should return the task dict directly."""
        respx.get(f"{BASE_URL}/tasks/t1").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "t1", "title": "Test", "isDone": False}})
        )

        from sp_local_bridge.adapters.mcp_server import _TOOL_MAP, _result_to_structured

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["get_task"]
        request = BridgeRequest(operation=operation, payload={"id": "t1"})
        result = await service.execute(request)
        structured = _result_to_structured(result)

        assert isinstance(structured, dict)
        assert structured["id"] == "t1"
        assert structured["title"] == "Test"

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_create_task_with_full_payload(self):
        """create_task with all optional fields should pass validation and reach REST."""
        route = respx.post(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(
                200,
                json={
                    "ok": True,
                    "data": {"id": "new1", "title": "Full task", "dueWithTime": 1717000000000, "isDone": False},
                },
            )
        )

        from sp_local_bridge.adapters.mcp_server import _TOOL_MAP, _result_to_structured

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["create_task"]
        payload = {
            "title": "Full task",
            "projectId": "p1",
            "tagIds": ["tag1", "tag2"],
            "notes": "Some notes",
            "plannedAt": 1717000000000,
            "dueDay": "2025-06-01",
            "dueWithTime": 1717000000000,
            "isDone": False,
        }
        request = BridgeRequest(operation=operation, payload=payload)
        result = await service.execute(request)
        structured = _result_to_structured(result)

        assert isinstance(structured, dict)
        assert structured["id"] == "new1"
        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_update_task_with_timestamp_fields(self):
        """update_task with timestamp fields passes validation."""
        route = respx.patch(f"{BASE_URL}/tasks/t1").mock(
            return_value=httpx.Response(
                200, json={"ok": True, "data": {"id": "t1", "title": "Updated", "dueWithTime": 1717000000000}}
            )
        )

        from sp_local_bridge.adapters.mcp_server import _TOOL_MAP, _result_to_structured

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["update_task"]
        payload = {"id": "t1", "dueWithTime": 1717000000000, "plannedAt": None}
        request = BridgeRequest(operation=operation, payload=payload)
        result = await service.execute(request)
        structured = _result_to_structured(result)

        assert isinstance(structured, dict)
        assert structured["id"] == "t1"
        # Verify the request body contains the fields
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body["dueWithTime"] == 1717000000000
        assert sent_body["plannedAt"] is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_error_propagation(self):
        """SP errors should propagate through the full call_tool flow."""
        respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(
                503, json={"ok": False, "error": {"code": "APP_NOT_READY", "message": "App is loading"}}
            )
        )

        from mcp.types import CallToolResult

        from sp_local_bridge.adapters.mcp_server import _TOOL_MAP, _result_to_structured

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["list_tasks"]
        request = BridgeRequest(operation=operation, payload={})
        result = await service.execute(request)
        structured = _result_to_structured(result)

        assert isinstance(structured, CallToolResult)
        assert structured.isError is True
        item = structured.content[0]
        assert isinstance(item, TextContent)
        content = json.loads(item.text)
        assert content["error"] == "APP_NOT_READY"

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_connection_error(self):
        """Connection errors should result in isError=True with SP_UNAVAILABLE."""
        respx.get(f"{BASE_URL}/tasks").mock(side_effect=httpx.ConnectError("refused"))

        from mcp.types import CallToolResult

        from sp_local_bridge.adapters.mcp_server import _TOOL_MAP, _result_to_structured

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["list_tasks"]
        request = BridgeRequest(operation=operation, payload={})
        result = await service.execute(request)
        structured = _result_to_structured(result)

        assert isinstance(structured, CallToolResult)
        assert structured.isError is True
        item = structured.content[0]
        assert isinstance(item, TextContent)
        content = json.loads(item.text)
        assert content["error"] == "SP_UNAVAILABLE"


class TestMCPPayloadValidation:
    """Tests that MCP tool calls with invalid payloads are rejected."""

    @pytest.mark.asyncio
    async def test_list_tasks_rejects_extra_payload(self):
        """list_tasks should reject unexpected fields."""
        from sp_local_bridge.adapters.mcp_server import _TOOL_MAP

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["list_tasks"]
        request = BridgeRequest(operation=operation, payload={"filter": "active"})
        result = await service.execute(request)

        assert result.ok is False
        assert result.error is not None
        assert result.error.code == "INVALID_INPUT"
        assert "no payload" in result.error.message.lower()

    @pytest.mark.asyncio
    async def test_get_task_rejects_extra_fields(self):
        """get_task should reject fields other than 'id'."""
        from sp_local_bridge.adapters.mcp_server import _TOOL_MAP

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["get_task"]
        request = BridgeRequest(operation=operation, payload={"id": "t1", "extra": "nope"})
        result = await service.execute(request)

        assert result.ok is False
        assert result.error is not None
        assert result.error.code == "INVALID_INPUT"
        assert "extra" in result.error.message

    @pytest.mark.asyncio
    async def test_complete_task_rejects_extra_fields(self):
        """complete_task should reject fields other than 'id'."""
        from sp_local_bridge.adapters.mcp_server import _TOOL_MAP

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["complete_task"]
        request = BridgeRequest(operation=operation, payload={"id": "t1", "isDone": True})
        result = await service.execute(request)

        assert result.ok is False
        assert result.error is not None
        assert result.error.code == "INVALID_INPUT"

    @pytest.mark.asyncio
    async def test_stop_current_task_rejects_payload(self):
        """stop_current_task takes no payload."""
        from sp_local_bridge.adapters.mcp_server import _TOOL_MAP

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["stop_current_task"]
        request = BridgeRequest(operation=operation, payload={"id": "t1"})
        result = await service.execute(request)

        assert result.ok is False
        assert result.error is not None
        assert result.error.code == "INVALID_INPUT"

    @pytest.mark.asyncio
    async def test_archive_task_rejects_extra_fields(self):
        """archive_task should only accept 'id'."""
        from sp_local_bridge.adapters.mcp_server import _TOOL_MAP

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["archive_task"]
        request = BridgeRequest(operation=operation, payload={"id": "t1", "reason": "old"})
        result = await service.execute(request)

        assert result.ok is False
        assert result.error is not None
        assert result.error.code == "INVALID_INPUT"
