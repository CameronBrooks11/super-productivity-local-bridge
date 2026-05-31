"""Core bridge service — maps operations to the SP REST client."""

from __future__ import annotations

from typing import Any, ClassVar

from sp_local_bridge.core import errors
from sp_local_bridge.core.models import BridgeRequest, BridgeResult
from sp_local_bridge.core.operations import Operation
from sp_local_bridge.sp_rest.client import SPRestClient

# Fields that the SP REST API recognizes for task creation/update, with their expected types.
# None means the field accepts null (optional clear).
_TASK_FIELD_TYPES: dict[str, tuple[type, ...]] = {
    "title": (str,),
    "notes": (str,),
    "projectId": (str, type(None)),
    "tagIds": (list,),
    "plannedAt": (str, int, type(None)),
    "dueDay": (str, type(None)),
    "dueWithTime": (int, type(None)),
    "isDone": (bool,),
    "timeEstimate": (int,),
    "timeSpent": (int,),
}

# Fields only valid on task.create (not on update)
_CREATE_ONLY_FIELDS = frozenset({"parentId"})

_TASK_WRITABLE_FIELDS = frozenset(_TASK_FIELD_TYPES.keys()) | _CREATE_ONLY_FIELDS

# Valid task list filter fields
_TASK_LIST_FILTERS: dict[str, tuple[type, ...]] = {
    "query": (str,),
    "projectId": (str,),
    "tagId": (str,),
    "includeDone": (bool,),
    "source": (str,),
}

_VALID_SOURCE_VALUES = frozenset({"active", "archived", "all"})


def _validate_id(payload: dict[str, Any]) -> str | None:
    """Validate that payload contains a non-empty string 'id'. Returns the id or None."""
    task_id = payload.get("id")
    if not isinstance(task_id, str) or not task_id.strip():
        return None
    return task_id


def _validate_task_fields(payload: dict[str, Any], *, exclude: frozenset[str] = frozenset()) -> BridgeResult | None:
    """Validate task payload fields and types. Returns a failure BridgeResult if invalid, None if ok."""
    unknown = set(payload.keys()) - _TASK_WRITABLE_FIELDS - exclude
    if unknown:
        return BridgeResult.failure(
            errors.INVALID_INPUT,
            f"Unknown fields: {', '.join(sorted(unknown))}",
        )

    for field, value in payload.items():
        if field in exclude:
            continue
        expected = _TASK_FIELD_TYPES.get(field)
        if expected is None:
            continue
        # Reject bool for int-typed fields (bool is subclass of int in Python)
        if isinstance(value, bool) and bool not in expected:
            type_names = " | ".join(t.__name__ for t in expected)
            return BridgeResult.failure(
                errors.INVALID_INPUT,
                f"Field '{field}' must be {type_names}, got bool",
            )
        if not isinstance(value, expected):
            type_names = " | ".join(t.__name__ for t in expected)
            return BridgeResult.failure(
                errors.INVALID_INPUT,
                f"Field '{field}' must be {type_names}, got {type(value).__name__}",
            )

    # Validate tagIds items are all strings if present
    tag_ids = payload.get("tagIds")
    if isinstance(tag_ids, list) and not all(isinstance(item, str) for item in tag_ids):
        return BridgeResult.failure(errors.INVALID_INPUT, "tagIds must contain only strings")

    # Validate non-negative for time fields
    for time_field in ("timeEstimate", "timeSpent"):
        val = payload.get(time_field)
        if isinstance(val, int) and val < 0:
            return BridgeResult.failure(
                errors.INVALID_INPUT,
                f"Field '{time_field}' must be non-negative (milliseconds), got {val}",
            )

    return None


def _validate_task_list_filters(payload: dict[str, Any]) -> tuple[BridgeResult | None, dict[str, str]]:
    """Validate task list filter payload. Returns (error, params_dict)."""
    unknown = set(payload.keys()) - set(_TASK_LIST_FILTERS.keys())
    if unknown:
        return (
            BridgeResult.failure(
                errors.INVALID_INPUT,
                f"Unknown filter fields: {', '.join(sorted(unknown))}",
            ),
            {},
        )

    for field, value in payload.items():
        expected = _TASK_LIST_FILTERS[field]
        if not isinstance(value, expected):
            type_names = " | ".join(t.__name__ for t in expected)
            return (
                BridgeResult.failure(
                    errors.INVALID_INPUT,
                    f"Filter '{field}' must be {type_names}, got {type(value).__name__}",
                ),
                {},
            )

    source = payload.get("source")
    if source is not None and source not in _VALID_SOURCE_VALUES:
        return (
            BridgeResult.failure(
                errors.INVALID_INPUT,
                f"Filter 'source' must be one of: {', '.join(sorted(_VALID_SOURCE_VALUES))}",
            ),
            {},
        )

    # Build query params dict (string values for httpx)
    params: dict[str, str] = {}
    for field, value in payload.items():
        if isinstance(value, bool):
            params[field] = "true" if value else "false"
        else:
            params[field] = str(value)

    return None, params


def _validate_no_payload(payload: dict[str, Any]) -> BridgeResult | None:
    """Reject unexpected fields on no-payload operations."""
    if payload:
        return BridgeResult.failure(
            errors.INVALID_INPUT,
            f"This operation takes no payload, got: {', '.join(sorted(payload.keys()))}",
        )
    return None


def _validate_id_only(payload: dict[str, Any]) -> BridgeResult | None:
    """Reject unexpected fields on id-only operations (only 'id' allowed)."""
    extra = set(payload.keys()) - {"id"}
    if extra:
        return BridgeResult.failure(
            errors.INVALID_INPUT,
            f"This operation only accepts 'id', got extra: {', '.join(sorted(extra))}",
        )
    return None


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
        err, params = _validate_task_list_filters(payload)
        if err:
            return err
        return await self._client.list_tasks(params or None)

    async def _task_get(self, payload: dict[str, Any]) -> BridgeResult:
        err = _validate_id_only(payload)
        if err:
            return err
        task_id = _validate_id(payload)
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id (non-empty string)")
        return await self._client.get_task(task_id)

    async def _task_create(self, payload: dict[str, Any]) -> BridgeResult:
        title = payload.get("title")
        if not isinstance(title, str) or not title.strip():
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: title (non-empty string)")
        if "id" in payload:
            return BridgeResult.failure(errors.INVALID_INPUT, "Field 'id' is not allowed on task.create")
        validation_err = _validate_task_fields(payload)
        if validation_err:
            return validation_err
        # parentId: must be non-empty string when present; rejects projectId/tagIds for subtasks
        if "parentId" in payload:
            parent_id = payload["parentId"]
            if not isinstance(parent_id, str) or not parent_id.strip():
                return BridgeResult.failure(errors.INVALID_INPUT, "Field 'parentId' must be a non-empty string")
            if "projectId" in payload or "tagIds" in payload:
                return BridgeResult.failure(
                    errors.INVALID_INPUT,
                    "Cannot set projectId or tagIds when parentId is specified (subtasks inherit from parent)",
                )
        return await self._client.create_task(payload)

    async def _task_update(self, payload: dict[str, Any]) -> BridgeResult:
        task_id = _validate_id(payload)
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id (non-empty string)")
        update_data = {k: v for k, v in payload.items() if k != "id"}
        if not update_data:
            return BridgeResult.failure(errors.INVALID_INPUT, "No fields to update")
        # parentId is not allowed on update (upstream rejects it)
        if "parentId" in update_data:
            return BridgeResult.failure(errors.INVALID_INPUT, "Field 'parentId' is not allowed on task.update")
        validation_err = _validate_task_fields(update_data)
        if validation_err:
            return validation_err
        return await self._client.update_task(task_id, update_data)

    async def _task_complete(self, payload: dict[str, Any]) -> BridgeResult:
        err = _validate_id_only(payload)
        if err:
            return err
        task_id = _validate_id(payload)
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id (non-empty string)")
        return await self._client.update_task(task_id, {"isDone": True})

    async def _task_uncomplete(self, payload: dict[str, Any]) -> BridgeResult:
        err = _validate_id_only(payload)
        if err:
            return err
        task_id = _validate_id(payload)
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id (non-empty string)")
        return await self._client.update_task(task_id, {"isDone": False})

    async def _task_start(self, payload: dict[str, Any]) -> BridgeResult:
        err = _validate_id_only(payload)
        if err:
            return err
        task_id = _validate_id(payload)
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id (non-empty string)")
        return await self._client.start_task(task_id)

    async def _task_stop_current(self, payload: dict[str, Any]) -> BridgeResult:
        err = _validate_no_payload(payload)
        if err:
            return err
        return await self._client.stop_current_task()

    async def _task_archive(self, payload: dict[str, Any]) -> BridgeResult:
        err = _validate_id_only(payload)
        if err:
            return err
        task_id = _validate_id(payload)
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id (non-empty string)")
        return await self._client.archive_task(task_id)

    async def _task_restore(self, payload: dict[str, Any]) -> BridgeResult:
        err = _validate_id_only(payload)
        if err:
            return err
        task_id = _validate_id(payload)
        if not task_id:
            return BridgeResult.failure(errors.INVALID_INPUT, "Missing required field: id (non-empty string)")
        return await self._client.restore_task(task_id)

    async def _project_list(self, payload: dict[str, Any]) -> BridgeResult:
        unknown = set(payload.keys()) - {"query"}
        if unknown:
            return BridgeResult.failure(
                errors.INVALID_INPUT,
                f"Unknown filter fields: {', '.join(sorted(unknown))}",
            )
        if "query" in payload and not isinstance(payload["query"], str):
            return BridgeResult.failure(errors.INVALID_INPUT, "Filter 'query' must be str")
        params = {"query": payload["query"]} if "query" in payload else None
        return await self._client.list_projects(params)

    async def _tag_list(self, payload: dict[str, Any]) -> BridgeResult:
        unknown = set(payload.keys()) - {"query"}
        if unknown:
            return BridgeResult.failure(
                errors.INVALID_INPUT,
                f"Unknown filter fields: {', '.join(sorted(unknown))}",
            )
        if "query" in payload and not isinstance(payload["query"], str):
            return BridgeResult.failure(errors.INVALID_INPUT, "Filter 'query' must be str")
        params = {"query": payload["query"]} if "query" in payload else None
        return await self._client.list_tags(params)

    async def _task_get_current(self, payload: dict[str, Any]) -> BridgeResult:
        err = _validate_no_payload(payload)
        if err:
            return err
        return await self._client.get_current_task()

    async def _task_set_current(self, payload: dict[str, Any]) -> BridgeResult:
        if "taskId" not in payload:
            return BridgeResult.failure(
                errors.INVALID_INPUT,
                "Field 'taskId' is required (string to set, null to clear)",
            )
        extra = set(payload.keys()) - {"taskId"}
        if extra:
            return BridgeResult.failure(
                errors.INVALID_INPUT,
                f"This operation only accepts 'taskId', got extra: {', '.join(sorted(extra))}",
            )
        task_id = payload["taskId"]
        if task_id is not None and (not isinstance(task_id, str) or not task_id.strip()):
            return BridgeResult.failure(
                errors.INVALID_INPUT,
                "Field 'taskId' must be a non-empty string or null (to clear)",
            )
        return await self._client.set_current_task(task_id)

    async def _status_get(self, payload: dict[str, Any]) -> BridgeResult:
        err = _validate_no_payload(payload)
        if err:
            return err
        return await self._client.status()

    async def _bridge_health(self, payload: dict[str, Any]) -> BridgeResult:
        err = _validate_no_payload(payload)
        if err:
            return err
        health = await self._client.health()
        if not health.ok:
            return health
        status = await self._client.status()
        if not status.ok:
            # Health endpoint passed but status failed — report degraded
            assert status.error is not None
            return BridgeResult.failure(
                errors.SP_ERROR,
                "SP is reachable but status check failed.",
                {"health": health.data, "status_error": status.error.code},
            )
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
        Operation.TASK_GET_CURRENT: _task_get_current,
        Operation.TASK_SET_CURRENT: _task_set_current,
        Operation.PROJECT_LIST: _project_list,
        Operation.TAG_LIST: _tag_list,
        Operation.STATUS_GET: _status_get,
        Operation.BRIDGE_HEALTH: _bridge_health,
    }
