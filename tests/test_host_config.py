"""Tests for the host config generator."""

import json
import subprocess
import sys
import tomllib

import pytest

from sp_local_bridge.diagnostics.host_config import (
    _HOSTS,
    _build_config,
    _format_toml_config,
    _print_config,
    _resolve_mcp_command,
)


class TestResolveMcpCommand:
    def test_resolves_to_string(self):
        result = _resolve_mcp_command()
        assert isinstance(result, str)
        assert "sp-local-bridge-mcp" in result

    def test_resolves_absolute_when_on_path(self):
        """If installed, should resolve to an absolute path."""
        result = _resolve_mcp_command()
        # In dev environment with uv sync, should find it
        if result != "sp-local-bridge-mcp":
            assert result.startswith("/")


class TestBuildConfig:
    def test_bare_mode_uses_command_name(self):
        config = _build_config("claude-desktop", absolute=False)
        cmd = config["mcpServers"]["super-productivity"]["command"]
        assert cmd == "sp-local-bridge-mcp"

    def test_absolute_mode_resolves_path(self):
        config = _build_config("claude-desktop", absolute=True)
        cmd = config["mcpServers"]["super-productivity"]["command"]
        # Should be either absolute or fallback bare name
        assert "sp-local-bridge-mcp" in cmd

    def test_vscode_copilot_bare_mode(self):
        config = _build_config("vscode-copilot", absolute=False)
        cmd = config["servers"]["superProductivity"]["command"]
        assert cmd == "sp-local-bridge-mcp"
        assert config["servers"]["superProductivity"]["type"] == "stdio"

    def test_vscode_copilot_absolute_mode(self):
        config = _build_config("vscode-copilot", absolute=True)
        cmd = config["servers"]["superProductivity"]["command"]
        assert "sp-local-bridge-mcp" in cmd

    def test_codex_bare_mode(self):
        config = _build_config("codex", absolute=False)
        cmd = config["mcp_servers"]["superProductivity"]["command"]
        assert cmd == "sp-local-bridge-mcp"

    def test_codex_absolute_mode(self):
        config = _build_config("codex", absolute=True)
        cmd = config["mcp_servers"]["superProductivity"]["command"]
        assert "sp-local-bridge-mcp" in cmd


class TestPrintConfig:
    def test_claude_desktop_returns_valid_json(self, capsys: pytest.CaptureFixture[str]):
        exit_code = _print_config("claude-desktop", absolute=False)
        assert exit_code == 0
        output = capsys.readouterr().out
        # First section should be valid JSON
        json_str = output.split("\n\n")[0]
        config = json.loads(json_str)
        assert "mcpServers" in config
        assert "super-productivity" in config["mcpServers"]
        assert config["mcpServers"]["super-productivity"]["command"] == "sp-local-bridge-mcp"

    def test_absolute_mode_outputs_valid_json(self, capsys: pytest.CaptureFixture[str]):
        exit_code = _print_config("claude-desktop", absolute=True)
        assert exit_code == 0
        output = capsys.readouterr().out
        json_str = output.split("\n\n")[0]
        config = json.loads(json_str)
        assert "mcpServers" in config
        # Command should contain the mcp substring regardless of resolution
        cmd = config["mcpServers"]["super-productivity"]["command"]
        assert "sp-local-bridge-mcp" in cmd

    def test_unknown_host_returns_error(self, capsys: pytest.CaptureFixture[str]):
        exit_code = _print_config("unknown-host")
        assert exit_code == 2
        err = capsys.readouterr().err
        assert "unknown host" in err.lower()

    def test_codex_outputs_toml(self, capsys: pytest.CaptureFixture[str]):
        exit_code = _print_config("codex", absolute=False)
        assert exit_code == 0
        output = capsys.readouterr().out
        # Parse the TOML section (everything before the blank-line separator)
        toml_str = output.split("\n\n")[0]
        parsed = tomllib.loads(toml_str)
        assert "mcp_servers" in parsed
        assert "superProductivity" in parsed["mcp_servers"]
        assert parsed["mcp_servers"]["superProductivity"]["command"] == "sp-local-bridge-mcp"

    def test_vscode_copilot_outputs_valid_json(self, capsys: pytest.CaptureFixture[str]):
        exit_code = _print_config("vscode-copilot", absolute=False)
        assert exit_code == 0
        output = capsys.readouterr().out
        json_str = output.split("\n\n")[0]
        config = json.loads(json_str)
        assert "servers" in config
        assert config["servers"]["superProductivity"]["type"] == "stdio"
        assert config["servers"]["superProductivity"]["command"] == "sp-local-bridge-mcp"

    def test_all_hosts_have_required_keys(self):
        for host, entry in _HOSTS.items():
            assert "config_template" in entry, f"{host} missing 'config_template'"
            assert "paths" in entry, f"{host} missing 'paths'"
            paths = entry["paths"]
            assert isinstance(paths, dict)
            assert "linux" in paths, f"{host} missing linux path"
            assert "macos" in paths, f"{host} missing macos path"
            assert "windows" in paths, f"{host} missing windows path"


class TestTomlEscaping:
    def test_windows_path_produces_valid_toml(self):
        """Windows paths with backslashes must not break TOML parsing."""
        config = {
            "mcp_servers": {"superProductivity": {"command": r"C:\Users\Me\bin\sp-local-bridge-mcp.exe", "args": []}}
        }
        toml_str = _format_toml_config(config)
        parsed = tomllib.loads(toml_str)
        assert parsed["mcp_servers"]["superProductivity"]["command"] == r"C:\Users\Me\bin\sp-local-bridge-mcp.exe"

    def test_unix_path_produces_valid_toml(self):
        config = {
            "mcp_servers": {"superProductivity": {"command": "/home/user/.local/bin/sp-local-bridge-mcp", "args": []}}
        }
        toml_str = _format_toml_config(config)
        parsed = tomllib.loads(toml_str)
        assert parsed["mcp_servers"]["superProductivity"]["command"] == "/home/user/.local/bin/sp-local-bridge-mcp"

    def test_path_with_spaces_produces_valid_toml(self):
        config = {"mcp_servers": {"test": {"command": "/opt/my tools/bin/sp-local-bridge-mcp", "args": ["--flag"]}}}
        toml_str = _format_toml_config(config)
        parsed = tomllib.loads(toml_str)
        assert parsed["mcp_servers"]["test"]["command"] == "/opt/my tools/bin/sp-local-bridge-mcp"
        assert parsed["mcp_servers"]["test"]["args"] == ["--flag"]


class TestPrintConfigCLI:
    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "sp_local_bridge.diagnostics.host_config", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Supported hosts" in result.stdout
        assert "--absolute" in result.stdout

    def test_no_args_shows_usage(self):
        result = subprocess.run(
            [sys.executable, "-m", "sp_local_bridge.diagnostics.host_config"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "Usage" in result.stdout

    def test_bare_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "sp_local_bridge.diagnostics.host_config", "--bare", "claude-desktop"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        config = json.loads(result.stdout.split("\n\n")[0])
        assert config["mcpServers"]["super-productivity"]["command"] == "sp-local-bridge-mcp"
