"""Tests for the core bridge service."""

import httpx
import pytest
import respx

from sp_local_bridge.core import errors
from sp_local_bridge.core.models import BridgeRequest
from sp_local_bridge.core.operations import Operation
from sp_local_bridge.core.service import BridgeService
from sp_local_bridge.sp_rest.client import SPRestClient

BASE_URL = "http://127.0.0.1:3876"


@pytest.fixture
def service() -> BridgeService:
    return BridgeService(SPRestClient(base_url=BASE_URL))


class TestOperationMapping:
    @respx.mock
    @pytest.mark.asyncio
    async def test_task_list(self, service: BridgeService):
        respx.get(f"{BASE_URL}/tasks").mock(return_value=httpx.Response(200, json=[{"id": "t1", "title": "Do stuff"}]))
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST))
        assert result.ok is True
        assert result.data == [{"id": "t1", "title": "Do stuff"}]

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_get(self, service: BridgeService):
        respx.get(f"{BASE_URL}/tasks/t1").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "t1", "title": "Task"}})
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_GET, payload={"id": "t1"}))
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_create(self, service: BridgeService):
        respx.post(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "new", "title": "Test"}})
        )
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "Test", "projectId": "p1"})
        )
        assert result.ok is True
        assert result.data["title"] == "Test"

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_complete(self, service: BridgeService):
        route = respx.patch(f"{BASE_URL}/tasks/t1").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "t1", "isDone": True}})
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_COMPLETE, payload={"id": "t1"}))
        assert result.ok is True
        # Verify it sent isDone: true
        assert b'"isDone":true' in route.calls[0].request.content

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_uncomplete(self, service: BridgeService):
        route = respx.patch(f"{BASE_URL}/tasks/t1").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "t1", "isDone": False}})
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_UNCOMPLETE, payload={"id": "t1"}))
        assert result.ok is True
        assert b'"isDone":false' in route.calls[0].request.content

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_start(self, service: BridgeService):
        respx.post(f"{BASE_URL}/tasks/t1/start").mock(return_value=httpx.Response(200, json={"ok": True, "data": None}))
        result = await service.execute(BridgeRequest(operation=Operation.TASK_START, payload={"id": "t1"}))
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_stop_current(self, service: BridgeService):
        respx.post(f"{BASE_URL}/task-control/stop").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": None})
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_STOP_CURRENT))
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_archive(self, service: BridgeService):
        respx.post(f"{BASE_URL}/tasks/t1/archive").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": None})
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_ARCHIVE, payload={"id": "t1"}))
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_restore(self, service: BridgeService):
        respx.post(f"{BASE_URL}/tasks/t1/restore").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": None})
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_RESTORE, payload={"id": "t1"}))
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_project_list(self, service: BridgeService):
        respx.get(f"{BASE_URL}/projects").mock(return_value=httpx.Response(200, json=[{"id": "p1"}]))
        result = await service.execute(BridgeRequest(operation=Operation.PROJECT_LIST))
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_tag_list(self, service: BridgeService):
        respx.get(f"{BASE_URL}/tags").mock(return_value=httpx.Response(200, json=[{"id": "tag1"}]))
        result = await service.execute(BridgeRequest(operation=Operation.TAG_LIST))
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_bridge_health(self, service: BridgeService):
        respx.get(f"{BASE_URL}/health").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"status": "up"}})
        )
        respx.get(f"{BASE_URL}/status").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"currentTask": None}})
        )
        result = await service.execute(BridgeRequest(operation=Operation.BRIDGE_HEALTH))
        assert result.ok is True
        assert "health" in result.data
        assert "status" in result.data

    @respx.mock
    @pytest.mark.asyncio
    async def test_bridge_health_degraded(self, service: BridgeService):
        """If /health passes but /status fails, report degraded (not success)."""
        respx.get(f"{BASE_URL}/health").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"server": "up"}})
        )
        respx.get(f"{BASE_URL}/status").mock(
            return_value=httpx.Response(
                503, json={"ok": False, "error": {"code": "APP_NOT_READY", "message": "Not ready"}}
            )
        )
        result = await service.execute(BridgeRequest(operation=Operation.BRIDGE_HEALTH))
        assert result.ok is False
        assert result.error is not None
        assert "degraded" in result.error.message.lower() or "status" in result.error.message.lower()


class TestValidation:
    @pytest.mark.asyncio
    async def test_unknown_operation(self, service: BridgeService):
        # Bypass pydantic validation by constructing directly
        req = BridgeRequest.model_construct(operation="fake.op", payload={})
        result = await service.execute(req)
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.UNKNOWN_OPERATION

    @pytest.mark.asyncio
    async def test_task_get_missing_id(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_GET, payload={}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "id" in result.error.message

    @pytest.mark.asyncio
    async def test_task_create_missing_title(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_CREATE, payload={}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "title" in result.error.message

    @pytest.mark.asyncio
    async def test_task_complete_missing_id(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_COMPLETE, payload={}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT

    @pytest.mark.asyncio
    async def test_task_create_empty_title(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "  "}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT

    @pytest.mark.asyncio
    async def test_task_create_non_string_title(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": 123}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT

    @pytest.mark.asyncio
    async def test_task_create_unknown_fields_rejected(self, service: BridgeService):
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "OK", "badField": "nope"})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "badField" in result.error.message

    @pytest.mark.asyncio
    async def test_task_create_invalid_tag_ids_type(self, service: BridgeService):
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "OK", "tagIds": "not-a-list"})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT

    @pytest.mark.asyncio
    async def test_task_update_no_fields(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_UPDATE, payload={"id": "t1"}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "No fields" in result.error.message

    @pytest.mark.asyncio
    async def test_task_get_non_string_id(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_GET, payload={"id": 123}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT

    @pytest.mark.asyncio
    async def test_task_create_tag_ids_with_non_string_items(self, service: BridgeService):
        """tagIds=[123] should be rejected (items must be strings)."""
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "OK", "tagIds": [123]})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "tagIds" in result.error.message

    @pytest.mark.asyncio
    async def test_task_create_project_id_non_string(self, service: BridgeService):
        """projectId=123 should be rejected (must be string or null)."""
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "OK", "projectId": 123})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "projectId" in result.error.message

    @pytest.mark.asyncio
    async def test_task_create_rejects_id_field(self, service: BridgeService):
        """task.create should reject payloads containing 'id'."""
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "OK", "id": "custom-id"})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "id" in result.error.message.lower()

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_create_due_with_time_accepts_int(self, service: BridgeService):
        """dueWithTime should accept an integer (Unix ms timestamp)."""
        respx.post(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "new", "title": "OK"}})
        )
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "OK", "dueWithTime": 1717000000000})
        )
        assert result.ok is True

    @pytest.mark.asyncio
    async def test_task_create_due_with_time_rejects_string(self, service: BridgeService):
        """dueWithTime should reject strings (it's a Unix ms timestamp, not ISO string)."""
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "OK", "dueWithTime": "2025-01-01"})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "dueWithTime" in result.error.message

    @pytest.mark.asyncio
    async def test_task_create_due_with_time_rejects_bool(self, service: BridgeService):
        """dueWithTime=True should be rejected (bool is not a valid timestamp)."""
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "OK", "dueWithTime": True})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "dueWithTime" in result.error.message

    @pytest.mark.asyncio
    async def test_task_create_planned_at_rejects_bool(self, service: BridgeService):
        """plannedAt=False should be rejected (bool is not a valid timestamp)."""
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "OK", "plannedAt": False})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "plannedAt" in result.error.message

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_create_parent_id_valid(self, service: BridgeService):
        """parentId with a valid non-empty string should pass validation."""
        respx.post(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "new", "title": "Sub"}})
        )
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "Sub", "parentId": "parent-123"})
        )
        assert result.ok is True

    @pytest.mark.asyncio
    async def test_task_create_parent_id_empty_string_rejected(self, service: BridgeService):
        """parentId must be non-empty string when present."""
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "Sub", "parentId": ""})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "parentId" in result.error.message

    @pytest.mark.asyncio
    async def test_task_create_parent_id_null_rejected(self, service: BridgeService):
        """parentId=None is not valid on create (just omit it)."""
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "Sub", "parentId": None})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT

    @pytest.mark.asyncio
    async def test_task_create_parent_id_rejects_project_id(self, service: BridgeService):
        """Subtasks cannot specify projectId (inherited from parent)."""
        result = await service.execute(
            BridgeRequest(
                operation=Operation.TASK_CREATE,
                payload={"title": "Sub", "parentId": "p1", "projectId": "proj1"},
            )
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "projectId" in result.error.message or "parentId" in result.error.message

    @pytest.mark.asyncio
    async def test_task_create_parent_id_rejects_tag_ids(self, service: BridgeService):
        """Subtasks cannot specify tagIds (inherited from parent)."""
        result = await service.execute(
            BridgeRequest(
                operation=Operation.TASK_CREATE,
                payload={"title": "Sub", "parentId": "p1", "tagIds": ["t1"]},
            )
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT

    @pytest.mark.asyncio
    async def test_task_update_rejects_parent_id(self, service: BridgeService):
        """parentId is not allowed on task.update (upstream rejects it)."""
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_UPDATE, payload={"id": "t1", "parentId": "p1"})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "parentId" in result.error.message


class TestErrorPropagation:
    @respx.mock
    @pytest.mark.asyncio
    async def test_sp_unavailable_propagates(self, service: BridgeService):
        respx.get(f"{BASE_URL}/tasks").mock(side_effect=httpx.ConnectError("refused"))
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.SP_UNAVAILABLE

    @respx.mock
    @pytest.mark.asyncio
    async def test_timeout_propagates(self, service: BridgeService):
        respx.get(f"{BASE_URL}/tasks").mock(side_effect=httpx.ReadTimeout("timeout"))
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.TIMEOUT
