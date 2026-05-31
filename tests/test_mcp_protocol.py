"""MCP protocol integration tests.

Tests the actual MCP protocol flow using the SDK's in-memory transport:
initialize → list_tools → call_tool → response. The server is wired to
a real BridgeService backed by mocked HTTP (respx).

Note: These use the SDK's in-memory client/server streams, not the stdio
console script. The protocol semantics are identical; only the transport differs.
"""

import json

import httpx
import pytest
import respx
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import TextContent

from sp_local_bridge.adapters.mcp_server import create_server
from sp_local_bridge.core.models import BridgeRequest
from sp_local_bridge.core.service import BridgeService
from sp_local_bridge.sp_rest.client import SPRestClient

BASE_URL = "http://127.0.0.1:3876"


class TestMCPProtocol:
    """Real MCP protocol tests using in-memory transport.

    These test the full path: MCP client → server session → handler → service → REST mock.
    """

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self):
        """MCP list_tools should return all 13 tool definitions."""
        service = BridgeService(SPRestClient(base_url=BASE_URL))
        server = create_server(service)

        async with create_connected_server_and_client_session(server) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            tool_names = {t.name for t in tools_result.tools}

            assert len(tools_result.tools) == 16
            assert "health" in tool_names
            assert "get_status" in tool_names
            assert "list_tasks" in tool_names
            assert "create_task" in tool_names
            assert "update_task" in tool_names
            assert "get_current_task" in tool_names
            assert "set_current_task" in tool_names
            assert "list_projects" in tool_names
            assert "list_tags" in tool_names

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_list_tasks(self):
        """MCP call_tool('list_tasks') should return task data."""
        respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json=[{"id": "t1", "title": "Task 1"}, {"id": "t2", "title": "Task 2"}])
        )

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        server = create_server(service)

        async with create_connected_server_and_client_session(server) as session:
            await session.initialize()
            result = await session.call_tool("list_tasks", {})

            assert result.isError is False or result.isError is None
            assert len(result.content) >= 1
            item = result.content[0]
            assert isinstance(item, TextContent)
            data = json.loads(item.text)
            # list_tasks returns wrapped in {"result": [...]}
            assert isinstance(data, dict)

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_get_task(self):
        """MCP call_tool('get_task', {id: ...}) returns task data."""
        respx.get(f"{BASE_URL}/tasks/t1").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "t1", "title": "Test Task"}})
        )

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        server = create_server(service)

        async with create_connected_server_and_client_session(server) as session:
            await session.initialize()
            result = await session.call_tool("get_task", {"id": "t1"})

            assert result.isError is False or result.isError is None
            item = result.content[0]
            assert isinstance(item, TextContent)
            data = json.loads(item.text)
            assert data["id"] == "t1"
            assert data["title"] == "Test Task"

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_create_task(self):
        """MCP call_tool('create_task') with valid payload creates a task."""
        respx.post(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "new1", "title": "Created"}})
        )

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        server = create_server(service)

        async with create_connected_server_and_client_session(server) as session:
            await session.initialize()
            result = await session.call_tool("create_task", {"title": "Created", "projectId": "p1"})

            assert result.isError is False or result.isError is None
            item = result.content[0]
            assert isinstance(item, TextContent)
            data = json.loads(item.text)
            assert data["id"] == "new1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_sp_error_sets_is_error(self):
        """When SP returns an error, MCP result has isError=True."""
        respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(
                503, json={"ok": False, "error": {"code": "APP_NOT_READY", "message": "Loading"}}
            )
        )

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        server = create_server(service)

        async with create_connected_server_and_client_session(server) as session:
            await session.initialize()
            result = await session.call_tool("list_tasks", {})

            assert result.isError is True
            item = result.content[0]
            assert isinstance(item, TextContent)
            data = json.loads(item.text)
            assert data["error"] == "APP_NOT_READY"

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_connection_error_sets_is_error(self):
        """When SP is unreachable, MCP result has isError=True."""
        respx.get(f"{BASE_URL}/tasks").mock(side_effect=httpx.ConnectError("refused"))

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        server = create_server(service)

        async with create_connected_server_and_client_session(server) as session:
            await session.initialize()
            result = await session.call_tool("list_tasks", {})

            assert result.isError is True
            item = result.content[0]
            assert isinstance(item, TextContent)
            data = json.loads(item.text)
            assert data["error"] == "SP_UNAVAILABLE"

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool_returns_error(self):
        """Unknown tool name returns isError=True.

        Note: The MCP SDK catches McpError in call_tool handlers and converts
        it to CallToolResult(isError=True) rather than a JSON-RPC protocol error.
        This is an SDK design choice, not a bridge defect.
        """
        service = BridgeService(SPRestClient(base_url=BASE_URL))
        server = create_server(service)

        async with create_connected_server_and_client_session(server) as session:
            await session.initialize()
            result = await session.call_tool("nonexistent_tool", {})
            assert result.isError is True
            # Verify the error message is informative
            item = result.content[0]
            assert isinstance(item, TextContent)
            assert "Unknown tool" in item.text

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_validation_error_through_protocol(self):
        """Payload validation errors propagate correctly through MCP protocol."""
        service = BridgeService(SPRestClient(base_url=BASE_URL))
        server = create_server(service)

        async with create_connected_server_and_client_session(server) as session:
            await session.initialize()
            # list_tasks takes no payload — extra fields should be rejected
            result = await session.call_tool("list_tasks", {"filter": "active"})

            assert result.isError is True
            item = result.content[0]
            assert isinstance(item, TextContent)
            data = json.loads(item.text)
            assert data["error"] == "INVALID_INPUT"

    @respx.mock
    @pytest.mark.asyncio
    async def test_call_tool_health(self):
        """MCP health tool returns connectivity status."""
        respx.get(f"{BASE_URL}/health").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"status": "up"}})
        )
        respx.get(f"{BASE_URL}/status").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"currentTask": None}})
        )

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        server = create_server(service)

        async with create_connected_server_and_client_session(server) as session:
            await session.initialize()
            result = await session.call_tool("health", {})

            assert result.isError is False or result.isError is None
            item = result.content[0]
            assert isinstance(item, TextContent)
            data = json.loads(item.text)
            assert "health" in data
            assert "status" in data


class TestMCPPayloadValidation:
    """Unit tests that verify payload validation through the service layer."""

    @pytest.mark.asyncio
    async def test_list_tasks_rejects_unknown_filter(self):
        """list_tasks should reject unknown filter fields."""
        from sp_local_bridge.adapters.mcp_server import _TOOL_MAP

        service = BridgeService(SPRestClient(base_url=BASE_URL))
        operation = _TOOL_MAP["list_tasks"]
        request = BridgeRequest(operation=operation, payload={"filter": "active"})
        result = await service.execute(request)

        assert result.ok is False
        assert result.error is not None
        assert result.error.code == "INVALID_INPUT"
        assert "filter" in result.error.message.lower()

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
