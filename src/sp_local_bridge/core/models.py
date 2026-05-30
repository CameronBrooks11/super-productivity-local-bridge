"""Core bridge models — request, result, and error shapes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from sp_local_bridge.core.operations import Operation  # noqa: TC001 — needed at runtime for pydantic validation


class BridgeError(BaseModel):
    """Structured error returned by the bridge."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class BridgeResult(BaseModel):
    """Result of a bridge operation."""

    ok: bool
    data: Any = None
    error: BridgeError | None = None

    @classmethod
    def success(cls, data: Any = None) -> BridgeResult:
        return cls(ok=True, data=data)

    @classmethod
    def failure(cls, code: str, message: str, details: dict[str, Any] | None = None) -> BridgeResult:
        return cls(ok=False, error=BridgeError(code=code, message=message, details=details or {}))


class BridgeRequest(BaseModel):
    """A request to execute a bridge operation."""

    operation: Operation
    payload: dict[str, Any] = Field(default_factory=dict)
