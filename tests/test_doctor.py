"""Tests for the bridge doctor diagnostic tool."""

import httpx
import pytest
import respx

from sp_local_bridge.diagnostics.doctor import _Check, _print_report, _run_checks

BASE_URL = "http://127.0.0.1:3876"


class TestDoctorChecks:
    @respx.mock
    @pytest.mark.asyncio
    async def test_checks_pass_when_sp_healthy(self):
        """Doctor should report all checks passed when SP is responsive."""
        respx.get(f"{BASE_URL}/health").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"status": "up"}})
        )
        respx.get(f"{BASE_URL}/status").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"currentTask": None}})
        )
        respx.get(f"{BASE_URL}/tasks").mock(return_value=httpx.Response(200, json=[{"id": "t1", "title": "Task"}]))

        checks = await _run_checks()

        # Find SP connectivity check
        sp_check = next((c for c in checks if c.name == "sp_connectivity"), None)
        assert sp_check is not None
        assert sp_check.passed is True

        # Find task API check
        task_check = next((c for c in checks if c.name == "sp_tasks"), None)
        assert task_check is not None
        assert task_check.passed is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_checks_fail_when_sp_unavailable(self):
        """Doctor should report failure when SP is unreachable."""
        respx.get(f"{BASE_URL}/health").mock(side_effect=httpx.ConnectError("refused"))
        respx.get(f"{BASE_URL}/status").mock(side_effect=httpx.ConnectError("refused"))

        checks = await _run_checks()

        sp_check = next((c for c in checks if c.name == "sp_connectivity"), None)
        assert sp_check is not None
        assert sp_check.passed is False

        # Task check should not run if health failed
        task_check = next((c for c in checks if c.name == "sp_tasks"), None)
        assert task_check is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_always_checks_python_and_version(self):
        """Doctor always checks python version and bridge version."""
        respx.get(f"{BASE_URL}/health").mock(side_effect=httpx.ConnectError("refused"))
        respx.get(f"{BASE_URL}/status").mock(side_effect=httpx.ConnectError("refused"))

        checks = await _run_checks()

        py_check = next((c for c in checks if c.name == "python_version"), None)
        assert py_check is not None
        assert py_check.passed is True

        ver_check = next((c for c in checks if c.name == "bridge_version"), None)
        assert ver_check is not None
        assert ver_check.passed is True


class TestDoctorReport:
    def test_report_all_passed(self, capsys):
        checks = [
            _Check("test1", True, "Check 1 OK"),
            _Check("test2", True, "Check 2 OK"),
        ]
        result = _print_report(checks)
        assert result is True
        captured = capsys.readouterr()
        assert "All checks passed" in captured.out

    def test_report_some_failed(self, capsys):
        checks = [
            _Check("test1", True, "Check 1 OK"),
            _Check("test2", False, "Check 2 FAILED", "Fix this"),
        ]
        result = _print_report(checks)
        assert result is False
        captured = capsys.readouterr()
        assert "1 check(s) failed" in captured.out
        assert "Fix this" in captured.out
