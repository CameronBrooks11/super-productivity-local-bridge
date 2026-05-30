"""Tests for the host config generator."""

import json
import subprocess
import sys

import pytest

from sp_local_bridge.diagnostics.host_config import _HOSTS, _print_config


class TestPrintConfig:
    def test_claude_desktop_returns_valid_json(self, capsys: pytest.CaptureFixture[str]):
        exit_code = _print_config("claude-desktop")
        assert exit_code == 0
        output = capsys.readouterr().out
        # First section should be valid JSON
        json_str = output.split("\n\n")[0]
        config = json.loads(json_str)
        assert "mcpServers" in config
        assert "super-productivity" in config["mcpServers"]
        assert config["mcpServers"]["super-productivity"]["command"] == "sp-local-bridge-mcp"

    def test_unknown_host_returns_error(self, capsys: pytest.CaptureFixture[str]):
        exit_code = _print_config("unknown-host")
        assert exit_code == 2
        err = capsys.readouterr().err
        assert "unknown host" in err.lower()

    def test_all_hosts_have_required_keys(self):
        for host, entry in _HOSTS.items():
            assert "config" in entry, f"{host} missing 'config'"
            assert "paths" in entry, f"{host} missing 'paths'"
            paths = entry["paths"]
            assert isinstance(paths, dict)
            assert "linux" in paths, f"{host} missing linux path"
            assert "macos" in paths, f"{host} missing macos path"
            assert "windows" in paths, f"{host} missing windows path"


class TestPrintConfigCLI:
    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "sp_local_bridge.diagnostics.host_config", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Supported hosts" in result.stdout

    def test_no_args_shows_usage(self):
        result = subprocess.run(
            [sys.executable, "-m", "sp_local_bridge.diagnostics.host_config"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "Usage" in result.stdout
