"""Tests for the MCP server adapter."""

import json

import httpx
import pytest
import respx
from mcp.types import TextContent

from sp_local_bridge.adapters.mcp_server import _TOOL_MAP, _TOOLS, _result_to_call_result
from sp_local_bridge.core.models import BridgeRequest, BridgeResult
from sp_local_bridge.core.operations import Operation
from sp_local_bridge.core.service import BridgeService
from sp_local_bridge.sp_rest.client import SPRestClient

BASE_URL = "http://127.0.0.1:3876"


class TestToolMap:
    def test_all_operations_have_tools(self):
        """Every core operation should be reachable via an MCP tool."""
        mapped_ops = set(_TOOL_MAP.values())
        for op in Operation:
            assert op in mapped_ops, f"Operation {op} has no MCP tool mapping"

    def test_all_tools_have_definitions(self):
        """Every mapped tool name should have a Tool definition."""
        defined_names = {t.name for t in _TOOLS}
        for tool_name in _TOOL_MAP:
            assert tool_name in defined_names, f"Tool {tool_name} has no definition"

    def test_tool_names_are_snake_case(self):
        """MCP tool names should be snake_case (no dots, no camelCase)."""
        for tool_name in _TOOL_MAP:
            assert "." not in tool_name
            assert tool_name == tool_name.lower()


class TestResultConversion:
    def test_success_result_has_is_error_false(self):
        result = BridgeResult.success({"id": "t1", "title": "Test"})
        call_result = _result_to_call_result(result)
        assert call_result.isError is False
        assert len(call_result.content) == 1
        item = call_result.content[0]
        assert isinstance(item, TextContent)
        content = json.loads(item.text)
        assert content["id"] == "t1"

    def test_failure_result_has_is_error_true(self):
        result = BridgeResult.failure("SP_UNAVAILABLE", "Cannot connect.")
        call_result = _result_to_call_result(result)
        assert call_result.isError is True
        item = call_result.content[0]
        assert isinstance(item, TextContent)
        content = json.loads(item.text)
        assert content["error"] == "SP_UNAVAILABLE"
        assert content["message"] == "Cannot connect."

    def test_failure_with_details_includes_details(self):
        result = BridgeResult.failure("SP_ERROR", "Bad request", {"status_code": 400})
        call_result = _result_to_call_result(result)
        assert call_result.isError is True
        item = call_result.content[0]
        assert isinstance(item, TextContent)
        content = json.loads(item.text)
        assert content["details"]["status_code"] == 400


class TestToolExecution:
    """Integration tests calling through the service via MCP tool mapping."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_tasks_tool(self):
        respx.get(f"{BASE_URL}/tasks").mock(return_value=httpx.Response(200, json=[{"id": "t1", "title": "Task"}]))
        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["list_tasks"]
        request = BridgeRequest(operation=operation, payload={})
        result = await service.execute(request)
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_task_tool(self):
        respx.post(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "new", "title": "Test"}})
        )
        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["create_task"]
        request = BridgeRequest(operation=operation, payload={"title": "Test"})
        result = await service.execute(request)
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_health_tool(self):
        respx.get(f"{BASE_URL}/health").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"server": "up"}})
        )
        respx.get(f"{BASE_URL}/status").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"currentTask": None}})
        )
        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["health"]
        request = BridgeRequest(operation=operation, payload={})
        result = await service.execute(request)
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_sp_error_returns_is_error(self):
        """When SP returns an error, the MCP result should have isError=True."""
        respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(
                503, json={"ok": False, "error": {"code": "APP_NOT_READY", "message": "Not ready"}}
            )
        )
        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["list_tasks"]
        request = BridgeRequest(operation=operation, payload={})
        result = await service.execute(request)
        call_result = _result_to_call_result(result)
        assert call_result.isError is True
        item = call_result.content[0]
        assert isinstance(item, TextContent)
        content = json.loads(item.text)
        assert content["error"] == "APP_NOT_READY"
