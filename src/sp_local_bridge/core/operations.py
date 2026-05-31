"""Core bridge operation definitions."""

from enum import StrEnum


class Operation(StrEnum):
    """All supported bridge operations."""

    TASK_LIST = "task.list"
    TASK_GET = "task.get"
    TASK_CREATE = "task.create"
    TASK_UPDATE = "task.update"
    TASK_COMPLETE = "task.complete"
    TASK_UNCOMPLETE = "task.uncomplete"
    TASK_START = "task.start"
    TASK_STOP_CURRENT = "task.stop_current"
    TASK_ARCHIVE = "task.archive"
    TASK_RESTORE = "task.restore"
    TASK_GET_CURRENT = "task.get_current"
    TASK_SET_CURRENT = "task.set_current"
    PROJECT_LIST = "project.list"
    TAG_LIST = "tag.list"
    STATUS_GET = "status.get"
    BRIDGE_HEALTH = "bridge.health"
