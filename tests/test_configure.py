"""Tests for the configure command."""

import json
from pathlib import Path

import pytest

from sp_local_bridge.diagnostics.configure import (
    check_host_configured,
    configure_host,
)


@pytest.fixture
def tmp_config_dir(tmp_path, monkeypatch):
    """Patch _resolve_config_path to use tmp_path for all hosts."""
    from sp_local_bridge.diagnostics import configure

    paths = {
        "claude-desktop": tmp_path / "claude" / "config.json",
        "vscode-copilot": tmp_path / "vscode" / "mcp.json",
        "codex": tmp_path / "codex" / "config.toml",
    }

    def _mock_resolve(host: str) -> Path:
        return paths[host]

    monkeypatch.setattr(configure, "_resolve_config_path", _mock_resolve)
    return paths


class TestConfigureHostAdd:
    def test_creates_new_json_config(self, tmp_config_dir):
        result = configure_host("claude-desktop")
        assert result == 0
        config_path = tmp_config_dir["claude-desktop"]
        assert config_path.exists()
        data = json.loads(config_path.read_text())
        assert "super-productivity" in data["mcpServers"]
        assert "command" in data["mcpServers"]["super-productivity"]

    def test_creates_new_vscode_config(self, tmp_config_dir):
        result = configure_host("vscode-copilot")
        assert result == 0
        config_path = tmp_config_dir["vscode-copilot"]
        data = json.loads(config_path.read_text())
        assert "superProductivity" in data["servers"]
        assert data["servers"]["superProductivity"]["type"] == "stdio"

    def test_creates_new_toml_config(self, tmp_config_dir):
        import tomllib

        result = configure_host("codex")
        assert result == 0
        config_path = tmp_config_dir["codex"]
        assert config_path.exists()
        data = tomllib.loads(config_path.read_text())
        assert "superProductivity" in data["mcp_servers"]

    def test_merges_into_existing_json(self, tmp_config_dir):
        config_path = tmp_config_dir["claude-desktop"]
        config_path.parent.mkdir(parents=True, exist_ok=True)
        existing = {"mcpServers": {"other-tool": {"command": "other"}}, "extra": True}
        config_path.write_text(json.dumps(existing))

        result = configure_host("claude-desktop")
        assert result == 0
        data = json.loads(config_path.read_text())
        # Our entry added
        assert "super-productivity" in data["mcpServers"]
        # Existing preserved
        assert "other-tool" in data["mcpServers"]
        assert data["extra"] is True

    def test_idempotent(self, tmp_config_dir):
        configure_host("claude-desktop")
        configure_host("claude-desktop")
        config_path = tmp_config_dir["claude-desktop"]
        data = json.loads(config_path.read_text())
        # Still just one entry for us
        assert len([k for k in data["mcpServers"] if k == "super-productivity"]) == 1

    def test_dry_run_does_not_write(self, tmp_config_dir, capsys):
        result = configure_host("claude-desktop", dry_run=True)
        assert result == 0
        config_path = tmp_config_dir["claude-desktop"]
        assert not config_path.exists()
        captured = capsys.readouterr()
        assert "Would write to:" in captured.out

    def test_unknown_host_returns_error(self, tmp_config_dir):
        result = configure_host("unknown-host")
        assert result == 2


class TestConfigureHostRemove:
    def test_remove_existing_entry(self, tmp_config_dir):
        configure_host("claude-desktop")
        result = configure_host("claude-desktop", remove=True)
        assert result == 0
        config_path = tmp_config_dir["claude-desktop"]
        data = json.loads(config_path.read_text())
        assert "mcpServers" not in data or "super-productivity" not in data.get("mcpServers", {})

    def test_remove_preserves_other_entries(self, tmp_config_dir):
        config_path = tmp_config_dir["claude-desktop"]
        config_path.parent.mkdir(parents=True, exist_ok=True)
        existing = {
            "mcpServers": {
                "super-productivity": {"command": "sp-local-bridge-mcp"},
                "other": {"command": "other"},
            }
        }
        config_path.write_text(json.dumps(existing))

        result = configure_host("claude-desktop", remove=True)
        assert result == 0
        data = json.loads(config_path.read_text())
        assert "other" in data["mcpServers"]
        assert "super-productivity" not in data["mcpServers"]

    def test_remove_nonexistent_file(self, tmp_config_dir):
        result = configure_host("claude-desktop", remove=True)
        assert result == 0  # graceful no-op

    def test_remove_missing_entry(self, tmp_config_dir):
        config_path = tmp_config_dir["claude-desktop"]
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({"mcpServers": {"other": {}}}))

        result = configure_host("claude-desktop", remove=True)
        assert result == 0

    def test_remove_dry_run(self, tmp_config_dir):
        configure_host("claude-desktop")
        result = configure_host("claude-desktop", remove=True, dry_run=True)
        assert result == 0
        # Entry should still be there
        config_path = tmp_config_dir["claude-desktop"]
        data = json.loads(config_path.read_text())
        assert "super-productivity" in data["mcpServers"]


class TestCheckHostConfigured:
    def test_configured_returns_true(self, tmp_config_dir):
        configure_host("claude-desktop")
        assert check_host_configured("claude-desktop") is True

    def test_not_configured_returns_false(self, tmp_config_dir):
        assert check_host_configured("claude-desktop") is False

    def test_unknown_host_returns_false(self, tmp_config_dir):
        assert check_host_configured("unknown") is False


class TestTomlPreservation:
    def test_preserves_existing_toml_settings(self, tmp_config_dir):
        """Codex configure must not delete unrelated user config."""
        import tomllib

        config_path = tmp_config_dir["codex"]
        config_path.parent.mkdir(parents=True, exist_ok=True)
        # Pre-existing config with settings outside mcp_servers
        existing_content = """\
[model]
name = "gpt-4o"

[history]
persistence = true
save_on_exit = true

[mcp_servers.other_tool]
command = '/usr/bin/other-tool'
args = []
"""
        config_path.write_text(existing_content)

        result = configure_host("codex")
        assert result == 0

        written = config_path.read_text()
        data = tomllib.loads(written)

        # Our entry is present
        assert "superProductivity" in data["mcp_servers"]
        # Other MCP server preserved
        assert "other_tool" in data["mcp_servers"]
        # Unrelated sections preserved
        assert data["model"]["name"] == "gpt-4o"
        assert data["history"]["persistence"] is True
        assert data["history"]["save_on_exit"] is True

    def test_toml_backup_created(self, tmp_config_dir):
        """Configure creates a .bak file before writing."""
        config_path = tmp_config_dir["codex"]
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("[mcp_servers.old]\ncommand = 'old'\n")

        configure_host("codex")

        backup = config_path.with_suffix(".toml.bak")
        assert backup.exists()
        assert "old" in backup.read_text()

    def test_json_backup_created(self, tmp_config_dir):
        """Configure creates a .bak file for JSON hosts too."""
        config_path = tmp_config_dir["claude-desktop"]
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({"mcpServers": {}}))

        configure_host("claude-desktop")

        backup = config_path.with_suffix(".json.bak")
        assert backup.exists()

    def test_parse_error_returns_friendly_message(self, tmp_config_dir, capsys):
        """Malformed JSON should not traceback — returns error code 1."""
        config_path = tmp_config_dir["claude-desktop"]
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("{invalid json content!!!")

        result = configure_host("claude-desktop")
        assert result == 1
        captured = capsys.readouterr()
        assert "cannot parse" in captured.err
        assert "Manual repair" in captured.err

    def test_preserves_complex_toml_values(self, tmp_config_dir):
        """Inline tables, numbers, and env maps in other entries must survive."""
        import tomllib

        config_path = tmp_config_dir["codex"]
        config_path.parent.mkdir(parents=True, exist_ok=True)
        existing_content = """\
[model]
name = "gpt-4o"
temperature = 0.7

[mcp_servers.complex_tool]
command = '/usr/bin/complex'
args = ['--verbose']
env = { TOKEN = "secret123", DEBUG = "1" }
timeout = 30
"""
        config_path.write_text(existing_content)

        result = configure_host("codex")
        assert result == 0

        written = config_path.read_text()
        data = tomllib.loads(written)

        # Our entry is present
        assert "superProductivity" in data["mcp_servers"]
        # Complex tool with inline table preserved
        assert data["mcp_servers"]["complex_tool"]["env"]["TOKEN"] == "secret123"
        assert data["mcp_servers"]["complex_tool"]["env"]["DEBUG"] == "1"
        assert data["mcp_servers"]["complex_tool"]["timeout"] == 30
        # Model section preserved with number
        assert data["model"]["temperature"] == 0.7

    def test_remove_preserves_other_toml_entries(self, tmp_config_dir):
        """Remove only deletes our entry, preserves complex sibling entries."""
        import tomllib

        config_path = tmp_config_dir["codex"]
        config_path.parent.mkdir(parents=True, exist_ok=True)
        existing_content = """\
[model]
name = "gpt-4o"

[mcp_servers.superProductivity]
command = '/home/user/.local/bin/sp-local-bridge-mcp'
args = []

[mcp_servers.other_tool]
command = '/usr/bin/other'
env = { API_KEY = "abc" }
"""
        config_path.write_text(existing_content)

        result = configure_host("codex", remove=True)
        assert result == 0

        written = config_path.read_text()
        data = tomllib.loads(written)

        # Our entry removed
        assert "superProductivity" not in data.get("mcp_servers", {})
        # Other tool preserved with complex value
        assert data["mcp_servers"]["other_tool"]["env"]["API_KEY"] == "abc"
        # Model section preserved
        assert data["model"]["name"] == "gpt-4o"
