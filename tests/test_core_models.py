"""Tests for core models."""

import pytest
from pydantic import ValidationError

from sp_local_bridge.core.models import BridgeError, BridgeRequest, BridgeResult
from sp_local_bridge.core.operations import Operation


class TestBridgeRequest:
    def test_valid_request(self):
        req = BridgeRequest(operation=Operation.TASK_LIST)
        assert req.operation == Operation.TASK_LIST
        assert req.payload == {}

    def test_request_with_payload(self):
        req = BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": "Test"})
        assert req.payload == {"title": "Test"}

    def test_invalid_operation_rejected(self):
        with pytest.raises(ValidationError):
            BridgeRequest(operation="not.a.real.op")  # type: ignore[arg-type]


class TestBridgeResult:
    def test_success(self):
        result = BridgeResult.success({"id": "abc"})
        assert result.ok is True
        assert result.data == {"id": "abc"}
        assert result.error is None

    def test_success_no_data(self):
        result = BridgeResult.success()
        assert result.ok is True
        assert result.data is None

    def test_failure(self):
        result = BridgeResult.failure("SP_UNAVAILABLE", "Cannot connect.")
        assert result.ok is False
        assert result.data is None
        assert result.error is not None
        assert result.error.code == "SP_UNAVAILABLE"
        assert result.error.message == "Cannot connect."

    def test_failure_with_details(self):
        result = BridgeResult.failure("SP_ERROR", "Bad", {"status_code": 500})
        assert result.error is not None
        assert result.error.details == {"status_code": 500}


class TestBridgeError:
    def test_error_model(self):
        err = BridgeError(code="TIMEOUT", message="Timed out.")
        assert err.code == "TIMEOUT"
        assert err.details == {}


class TestOperation:
    def test_all_operations_are_dot_namespaced(self):
        for op in Operation:
            assert "." in op.value

    def test_operation_from_string(self):
        assert Operation("task.list") == Operation.TASK_LIST
