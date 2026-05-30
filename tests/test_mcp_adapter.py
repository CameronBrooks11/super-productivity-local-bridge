"""Tests for the MCP server adapter."""

import json

import httpx
import pytest
import respx
from mcp.types import CallToolResult, TextContent

from sp_local_bridge.adapters.mcp_server import (
    _TOOL_MAP,
    _TOOLS,
    _result_to_call_result,
    _result_to_structured,
)
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


class TestToolAnnotations:
    """Every tool should have annotations declared."""

    def test_all_tools_have_annotations(self):
        for tool in _TOOLS:
            assert tool.annotations is not None, f"Tool {tool.name} missing annotations"

    def test_read_tools_are_read_only(self):
        read_tools = {"health", "list_tasks", "get_task", "list_projects", "list_tags"}
        for tool in _TOOLS:
            if tool.name in read_tools:
                assert tool.annotations is not None
                assert tool.annotations.readOnlyHint is True, f"{tool.name} should be readOnly"
                assert tool.annotations.destructiveHint is False

    def test_mutating_tools_are_not_read_only(self):
        mutating_tools = {"create_task", "update_task", "complete_task", "start_task", "stop_current_task"}
        for tool in _TOOLS:
            if tool.name in mutating_tools:
                assert tool.annotations is not None
                assert tool.annotations.readOnlyHint is False, f"{tool.name} should not be readOnly"


class TestStructuredContent:
    """Test _result_to_structured returns proper types."""

    def test_success_dict_returns_dict(self):
        result = BridgeResult.success({"id": "t1", "title": "Test"})
        out = _result_to_structured(result)
        assert isinstance(out, dict)
        assert out["id"] == "t1"

    def test_success_list_returns_wrapped_dict(self):
        result = BridgeResult.success([{"id": "t1"}, {"id": "t2"}])
        out = _result_to_structured(result)
        assert isinstance(out, dict)
        assert "result" in out
        assert len(out["result"]) == 2

    def test_failure_returns_call_tool_result_with_is_error(self):
        result = BridgeResult.failure("SP_UNAVAILABLE", "Cannot connect")
        out = _result_to_structured(result)
        assert isinstance(out, CallToolResult)
        assert out.isError is True
