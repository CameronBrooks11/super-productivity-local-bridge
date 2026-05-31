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
