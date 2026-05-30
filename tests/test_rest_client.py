"""Tests for the SP REST client."""

import httpx
import pytest
import respx

from sp_local_bridge.core import errors
from sp_local_bridge.sp_rest.client import SPRestClient

BASE_URL = "http://127.0.0.1:3876"


@pytest.fixture
def client() -> SPRestClient:
    return SPRestClient(base_url=BASE_URL)


class TestResponseTranslation:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success_envelope(self, client: SPRestClient):
        respx.get(f"{BASE_URL}/health").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"status": "up"}})
        )
        result = await client.health()
        assert result.ok is True
        assert result.data == {"status": "up"}

    @respx.mock
    @pytest.mark.asyncio
    async def test_error_envelope(self, client: SPRestClient):
        respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(500, json={"ok": False, "error": "Internal failure"})
        )
        result = await client.list_tasks()
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.SP_ERROR
        assert "Internal failure" in result.error.message

    @respx.mock
    @pytest.mark.asyncio
    async def test_404_returns_not_found(self, client: SPRestClient):
        respx.get(f"{BASE_URL}/tasks/nonexistent").mock(return_value=httpx.Response(404))
        result = await client.get_task("nonexistent")
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.TASK_NOT_FOUND

    @respx.mock
    @pytest.mark.asyncio
    async def test_non_envelope_success(self, client: SPRestClient):
        """SP may return raw JSON arrays/objects without envelope."""
        respx.get(f"{BASE_URL}/tasks").mock(return_value=httpx.Response(200, json=[{"id": "1", "title": "Task"}]))
        result = await client.list_tasks()
        assert result.ok is True
        assert result.data == [{"id": "1", "title": "Task"}]


class TestConnectionErrors:
    @respx.mock
    @pytest.mark.asyncio
    async def test_connection_refused(self, client: SPRestClient):
        respx.get(f"{BASE_URL}/health").mock(side_effect=httpx.ConnectError("Connection refused"))
        result = await client.health()
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.SP_UNAVAILABLE

    @respx.mock
    @pytest.mark.asyncio
    async def test_timeout(self, client: SPRestClient):
        respx.get(f"{BASE_URL}/health").mock(side_effect=httpx.ReadTimeout("Timeout"))
        result = await client.health()
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == errors.TIMEOUT


class TestClientMethods:
    @respx.mock
    @pytest.mark.asyncio
    async def test_create_task(self, client: SPRestClient):
        route = respx.post(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "new-1", "title": "Hello"}})
        )
        result = await client.create_task({"title": "Hello", "projectId": "p1"})
        assert result.ok is True
        assert result.data == {"id": "new-1", "title": "Hello"}
        # Verify the request body preserved camelCase fields
        import json

        sent = json.loads(route.calls[0].request.content)
        assert sent == {"title": "Hello", "projectId": "p1"}

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_task(self, client: SPRestClient):
        respx.patch(f"{BASE_URL}/tasks/t1").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"id": "t1", "isDone": True}})
        )
        result = await client.update_task("t1", {"isDone": True})
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_start_task(self, client: SPRestClient):
        respx.post(f"{BASE_URL}/tasks/t1/start").mock(return_value=httpx.Response(200, json={"ok": True, "data": None}))
        result = await client.start_task("t1")
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_stop_current_task(self, client: SPRestClient):
        respx.post(f"{BASE_URL}/task-control/stop").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": None})
        )
        result = await client.stop_current_task()
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_archive_task(self, client: SPRestClient):
        respx.post(f"{BASE_URL}/tasks/t1/archive").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": None})
        )
        result = await client.archive_task("t1")
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_restore_task(self, client: SPRestClient):
        respx.post(f"{BASE_URL}/tasks/t1/restore").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": None})
        )
        result = await client.restore_task("t1")
        assert result.ok is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_projects(self, client: SPRestClient):
        respx.get(f"{BASE_URL}/projects").mock(
            return_value=httpx.Response(200, json=[{"id": "p1", "title": "Project"}])
        )
        result = await client.list_projects()
        assert result.ok is True
        assert result.data == [{"id": "p1", "title": "Project"}]

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_tags(self, client: SPRestClient):
        respx.get(f"{BASE_URL}/tags").mock(return_value=httpx.Response(200, json=[{"id": "tag1", "name": "urgent"}]))
        result = await client.list_tags()
        assert result.ok is True
