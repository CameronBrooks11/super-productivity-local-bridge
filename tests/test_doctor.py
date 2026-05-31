"""Tests for the bridge doctor diagnostic tool."""

import json
from pathlib import Path

import httpx
import pytest
import respx

from sp_local_bridge.diagnostics.doctor import _Check, _print_report, _run_checks

BASE_URL = "http://127.0.0.1:3876"


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """Ensure SP_BASE_URL is not set so doctor uses the default base URL."""
    monkeypatch.delenv("SP_BASE_URL", raising=False)


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


class TestDoctorHostConfigChecks:
    @respx.mock
    @pytest.mark.asyncio
    async def test_host_config_check_when_configured(self, tmp_path, monkeypatch):
        """Doctor reports configured hosts."""
        from sp_local_bridge.diagnostics import configure

        # Mock SP as reachable
        respx.get(f"{BASE_URL}/health").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"status": "up"}})
        )
        respx.get(f"{BASE_URL}/status").mock(
            return_value=httpx.Response(200, json={"ok": True, "data": {"currentTask": None}})
        )
        respx.get(f"{BASE_URL}/tasks").mock(return_value=httpx.Response(200, json=[]))

        # Create a fake configured host
        config_path = tmp_path / "claude" / "config.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(json.dumps({"mcpServers": {"super-productivity": {"command": "x"}}}))

        def _mock_resolve(host: str) -> Path:
            paths = {
                "claude-desktop": config_path,
                "vscode-copilot": tmp_path / "vscode" / "mcp.json",
                "codex": tmp_path / "codex" / "config.toml",
            }
            return paths[host]

        monkeypatch.setattr(configure, "_resolve_config_path", _mock_resolve)

        checks = await _run_checks()
        host_check = next((c for c in checks if c.name == "host_config"), None)
        assert host_check is not None
        assert host_check.passed is True
        assert "claude-desktop" in host_check.message

    @respx.mock
    @pytest.mark.asyncio
    async def test_host_config_check_when_none_configured(self, tmp_path, monkeypatch):
        """Doctor reports no hosts configured."""
        from sp_local_bridge.diagnostics import configure

        respx.get(f"{BASE_URL}/health").mock(side_effect=httpx.ConnectError("refused"))
        respx.get(f"{BASE_URL}/status").mock(side_effect=httpx.ConnectError("refused"))

        # All paths point to nonexistent files
        def _mock_resolve(host: str) -> Path:
            return tmp_path / "nonexistent" / f"{host}.json"

        monkeypatch.setattr(configure, "_resolve_config_path", _mock_resolve)

        checks = await _run_checks()
        host_check = next((c for c in checks if c.name == "host_config"), None)
        assert host_check is not None
        assert host_check.passed is True  # advisory, not a failure
        assert "sp-local-bridge-configure" in host_check.detail
