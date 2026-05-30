"""Core bridge service — maps operations to the SP REST client."""

from __future__ import annotations

from typing import Any, ClassVar

from sp_local_bridge.core import errors
from sp_local_bridge.core.models import BridgeRequest, BridgeResult
from sp_local_bridge.core.operations import Operation
from sp_local_bridge.sp_rest.client import SPRestClient


class BridgeService:
    """Maps core bridge operations to SP REST API calls."""

    def __init__(self, client: SPRestClient | None = None) -> None:
        self._client = client or SPRestClient()

    async def execute(self, request: BridgeRequest) -> BridgeResult:
        """Execute a bridge operation."""
        handler = self._handlers.get(request.operation)
        if handler is None:
            return BridgeResult.failure(
                errors.UNKNOWN_OPERATION,
                f"Unknown operation: {request.operation}",
            )
        return await handler(self, request.payload)

    async def _task_list(self, payload: dict[str, Any]) -> BridgeResult:
        return await self._client.list_tasks()

    async def _task_get(self, payload: dict[str, Any]) -> BridgeResult:
        task_id = payload.get("id")
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id")
        return await self._client.get_task(task_id)

    async def _task_create(self, payload: dict[str, Any]) -> BridgeResult:
        if not payload.get("title"):
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: title")
        return await self._client.create_task(payload)

    async def _task_update(self, payload: dict[str, Any]) -> BridgeResult:
        task_id = payload.get("id")
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id")
        # Pass everything except 'id' as the update body
        update_data = {k: v for k, v in payload.items() if k != "id"}
        return await self._client.update_task(task_id, update_data)

    async def _task_complete(self, payload: dict[str, Any]) -> BridgeResult:
        task_id = payload.get("id")
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id")
        return await self._client.update_task(task_id, {"isDone": True})

    async def _task_uncomplete(self, payload: dict[str, Any]) -> BridgeResult:
        task_id = payload.get("id")
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id")
        return await self._client.update_task(task_id, {"isDone": False})

    async def _task_start(self, payload: dict[str, Any]) -> BridgeResult:
        task_id = payload.get("id")
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id")
        return await self._client.start_task(task_id)

    async def _task_stop_current(self, payload: dict[str, Any]) -> BridgeResult:
        return await self._client.stop_current_task()

    async def _task_archive(self, payload: dict[str, Any]) -> BridgeResult:
        task_id = payload.get("id")
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id")
        return await self._client.archive_task(task_id)

    async def _task_restore(self, payload: dict[str, Any]) -> BridgeResult:
        task_id = payload.get("id")
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id")
        return await self._client.restore_task(task_id)

    async def _project_list(self, payload: dict[str, Any]) -> BridgeResult:
        return await self._client.list_projects()

    async def _tag_list(self, payload: dict[str, Any]) -> BridgeResult:
        return await self._client.list_tags()

    async def _bridge_health(self, payload: dict[str, Any]) -> BridgeResult:
        health = await self._client.health()
        if not health.ok:
            return health
        status = await self._client.status()
        if not status.ok:
            # Health passed but status failed — still report healthy with partial data
            return BridgeResult.success({"health": health.data})
        return BridgeResult.success({"health": health.data, "status": status.data})

    _handlers: ClassVar[dict[Operation, Any]] = {
        Operation.TASK_LIST: _task_list,
        Operation.TASK_GET: _task_get,
        Operation.TASK_CREATE: _task_create,
        Operation.TASK_UPDATE: _task_update,
        Operation.TASK_COMPLETE: _task_complete,
        Operation.TASK_UNCOMPLETE: _task_uncomplete,
        Operation.TASK_START: _task_start,
        Operation.TASK_STOP_CURRENT: _task_stop_current,
        Operation.TASK_ARCHIVE: _task_archive,
        Operation.TASK_RESTORE: _task_restore,
        Operation.PROJECT_LIST: _project_list,
        Operation.TAG_LIST: _tag_list,
        Operation.BRIDGE_HEALTH: _bridge_health,
    }
