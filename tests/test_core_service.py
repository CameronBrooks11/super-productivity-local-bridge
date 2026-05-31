"""Tests for the core bridge service."""

import httpx
import pytest
import respx

from sp_local_bridge.core import errors
from sp_local_bridge.core.models import BridgeRequest
from sp_local_bridge.core.operations import Operation
from sp_local_bridge.core.service import BridgeService
from sp_local_bridge.sp_rest.client import SPRestClient
from tests.conftest import load_fixture

BASE_URL = "http://127.0.0.1:3876"


@pytest.fixture
def service() -> BridgeService:
    return BridgeService(SPRestClient(base_url=BASE_URL))


class TestOperationMapping:
    @respx.mock
    @pytest.mark.asyncio
    async def test_task_list(self, service: BridgeService):
        respx.get(f"{BASE_URL}/tasks").mock(return_value=httpx.Response(200, json=load_fixture("task-list-ok.json")))
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST))
        assert result.ok is True
        assert result.data == load_fixture("task-list-ok.json")

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_get(self, service: BridgeService):
        fixture = load_fixture("task-create-ok.json")
        respx.get(f"{BASE_URL}/tasks/t1").mock(return_value=httpx.Response(200, json=fixture))
        result = await service.execute(BridgeRequest(operation=Operation.TASK_GET, payload={"id": "t1"}))
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_create(self, service: BridgeService):
        respx.post(f"{BASE_URL}/tasks").mock(return_value=httpx.Response(200, json=load_fixture("task-create-ok.json")))
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "Test", "projectId": "p1"})
        )
        assert result.ok is True
        assert result.data["title"] == "Write integration tests"

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_complete(self, service: BridgeService):
        route = respx.patch(f"{BASE_URL}/tasks/t1").mock(
            return_value=httpx.Response(200, json=load_fixture("task-update-ok.json"))
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
        respx.get(f"{BASE_URL}/projects").mock(
            return_value=httpx.Response(200, json=load_fixture("project-list-ok.json"))
        )
        result = await service.execute(BridgeRequest(operation=Operation.PROJECT_LIST))
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_tag_list(self, service: BridgeService):
        respx.get(f"{BASE_URL}/tags").mock(return_value=httpx.Response(200, json=load_fixture("tag-list-ok.json")))
        result = await service.execute(BridgeRequest(operation=Operation.TAG_LIST))
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_bridge_health(self, service: BridgeService):
        respx.get(f"{BASE_URL}/health").mock(return_value=httpx.Response(200, json=load_fixture("health-ok.json")))
        respx.get(f"{BASE_URL}/status").mock(return_value=httpx.Response(200, json=load_fixture("status-ok.json")))
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


class TestTaskListFilters:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_with_query_filter(self, service: BridgeService):
        route = respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json=load_fixture("task-list-ok.json"))
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST, payload={"query": "budget"}))
        assert result.ok is True
        assert route.calls[0].request.url.params["query"] == "budget"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_with_project_id_filter(self, service: BridgeService):
        route = respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json=load_fixture("task-list-ok.json"))
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST, payload={"projectId": "proj-1"}))
        assert result.ok is True
        assert route.calls[0].request.url.params["projectId"] == "proj-1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_with_tag_id_filter(self, service: BridgeService):
        route = respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json=load_fixture("task-list-ok.json"))
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST, payload={"tagId": "TODAY"}))
        assert result.ok is True
        assert route.calls[0].request.url.params["tagId"] == "TODAY"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_with_include_done(self, service: BridgeService):
        route = respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json=load_fixture("task-list-ok.json"))
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST, payload={"includeDone": True}))
        assert result.ok is True
        assert route.calls[0].request.url.params["includeDone"] == "true"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_with_source_archived(self, service: BridgeService):
        route = respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json=load_fixture("task-list-ok.json"))
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST, payload={"source": "archived"}))
        assert result.ok is True
        assert route.calls[0].request.url.params["source"] == "archived"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_with_source_all(self, service: BridgeService):
        route = respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json=load_fixture("task-list-ok.json"))
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST, payload={"source": "all"}))
        assert result.ok is True
        assert route.calls[0].request.url.params["source"] == "all"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_no_filters_no_params(self, service: BridgeService):
        route = respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json=load_fixture("task-list-ok.json"))
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST))
        assert result.ok is True
        assert str(route.calls[0].request.url) == f"{BASE_URL}/tasks"

    @pytest.mark.asyncio
    async def test_rejects_unknown_filter(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST, payload={"badFilter": "x"}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "badFilter" in result.error.message

    @pytest.mark.asyncio
    async def test_rejects_invalid_source_value(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST, payload={"source": "invalid"}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "source" in result.error.message

    @pytest.mark.asyncio
    async def test_rejects_non_string_query(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST, payload={"query": 123}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "query" in result.error.message

    @pytest.mark.asyncio
    async def test_rejects_non_bool_include_done(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST, payload={"includeDone": "yes"}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "includeDone" in result.error.message


class TestProjectTagSearch:
    @respx.mock
    @pytest.mark.asyncio
    async def test_project_list_with_query(self, service: BridgeService):
        route = respx.get(f"{BASE_URL}/projects").mock(
            return_value=httpx.Response(200, json=load_fixture("project-list-ok.json"))
        )
        result = await service.execute(BridgeRequest(operation=Operation.PROJECT_LIST, payload={"query": "work"}))
        assert result.ok is True
        assert route.calls[0].request.url.params["query"] == "work"

    @respx.mock
    @pytest.mark.asyncio
    async def test_tag_list_with_query(self, service: BridgeService):
        route = respx.get(f"{BASE_URL}/tags").mock(
            return_value=httpx.Response(200, json=load_fixture("tag-list-ok.json"))
        )
        result = await service.execute(BridgeRequest(operation=Operation.TAG_LIST, payload={"query": "urgent"}))
        assert result.ok is True
        assert route.calls[0].request.url.params["query"] == "urgent"

    @pytest.mark.asyncio
    async def test_project_list_rejects_unknown_filter(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.PROJECT_LIST, payload={"badField": "x"}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT

    @pytest.mark.asyncio
    async def test_tag_list_rejects_unknown_filter(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TAG_LIST, payload={"source": "all"}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT

    @pytest.mark.asyncio
    async def test_project_list_rejects_non_string_query(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.PROJECT_LIST, payload={"query": 42}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT


class TestTimeFields:
    @respx.mock
    @pytest.mark.asyncio
    async def test_create_with_time_estimate(self, service: BridgeService):
        route = respx.post(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "new", "title": "OK"}})
        )
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "OK", "timeEstimate": 3600000})
        )
        assert result.ok is True
        import json as json_mod

        body = json_mod.loads(route.calls[0].request.content)
        assert body["timeEstimate"] == 3600000

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_with_time_spent(self, service: BridgeService):
        route = respx.patch(f"{BASE_URL}/tasks/t1").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "t1"}})
        )
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_UPDATE, payload={"id": "t1", "timeSpent": 1800000})
        )
        assert result.ok is True
        import json as json_mod

        body = json_mod.loads(route.calls[0].request.content)
        assert body["timeSpent"] == 1800000

    @pytest.mark.asyncio
    async def test_rejects_negative_time_estimate(self, service: BridgeService):
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "OK", "timeEstimate": -1})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "timeEstimate" in result.error.message

    @pytest.mark.asyncio
    async def test_rejects_negative_time_spent(self, service: BridgeService):
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_UPDATE, payload={"id": "t1", "timeSpent": -100})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "timeSpent" in result.error.message

    @pytest.mark.asyncio
    async def test_rejects_bool_for_time_estimate(self, service: BridgeService):
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "OK", "timeEstimate": True})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "timeEstimate" in result.error.message

    @pytest.mark.asyncio
    async def test_rejects_string_for_time_spent(self, service: BridgeService):
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_UPDATE, payload={"id": "t1", "timeSpent": "1h"})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "timeSpent" in result.error.message


class TestCurrentTask:
    @respx.mock
    @pytest.mark.asyncio
    async def test_get_current_task(self, service: BridgeService):
        respx.get(f"{BASE_URL}/task-control/current").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "t1", "title": "Active"}})
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_GET_CURRENT))
        assert result.ok is True
        assert result.data["id"] == "t1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_current_task_idle(self, service: BridgeService):
        respx.get(f"{BASE_URL}/task-control/current").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": None})
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_GET_CURRENT))
        assert result.ok is True
        assert result.data is None

    @pytest.mark.asyncio
    async def test_get_current_rejects_payload(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_GET_CURRENT, payload={"extra": "bad"}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT

    @respx.mock
    @pytest.mark.asyncio
    async def test_set_current_task(self, service: BridgeService):
        route = respx.post(f"{BASE_URL}/task-control/current").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": None})
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_SET_CURRENT, payload={"taskId": "t1"}))
        assert result.ok is True
        import json as json_mod

        body = json_mod.loads(route.calls[0].request.content)
        assert body["taskId"] == "t1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_set_current_task_clear(self, service: BridgeService):
        route = respx.post(f"{BASE_URL}/task-control/current").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": None})
        )
        result = await service.execute(BridgeRequest(operation=Operation.TASK_SET_CURRENT, payload={"taskId": None}))
        assert result.ok is True
        import json as json_mod

        body = json_mod.loads(route.calls[0].request.content)
        assert body["taskId"] is None

    @pytest.mark.asyncio
    async def test_set_current_task_no_payload(self, service: BridgeService):
        """set_current with empty payload should be rejected (taskId required)."""
        result = await service.execute(BridgeRequest(operation=Operation.TASK_SET_CURRENT))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
        assert "taskId" in result.error.message

    @pytest.mark.asyncio
    async def test_set_current_rejects_empty_string(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_SET_CURRENT, payload={"taskId": ""}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT

    @pytest.mark.asyncio
    async def test_set_current_rejects_non_string(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.TASK_SET_CURRENT, payload={"taskId": 123}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT

    @pytest.mark.asyncio
    async def test_set_current_rejects_extra_fields(self, service: BridgeService):
        result = await service.execute(
            BridgeRequest(operation=Operation.TASK_SET_CURRENT, payload={"taskId": "t1", "extra": "bad"})
        )
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT


class TestStatusGet:
    @respx.mock
    @pytest.mark.asyncio
    async def test_status_get(self, service: BridgeService):
        respx.get(f"{BASE_URL}/status").mock(return_value=httpx.Response(200, json=load_fixture("status-ok.json")))
        result = await service.execute(BridgeRequest(operation=Operation.STATUS_GET))
        assert result.ok is True
        assert "currentTask" in result.data

    @pytest.mark.asyncio
    async def test_status_get_rejects_payload(self, service: BridgeService):
        result = await service.execute(BridgeRequest(operation=Operation.STATUS_GET, payload={"extra": "bad"}))
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.INVALID_INPUT
