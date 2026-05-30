"""Tests for the install/uninstall scripts and installed behavior."""

import json
import os
import subprocess
import tempfile

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
INSTALL_SCRIPT = os.path.join(SCRIPTS_DIR, "install.sh")
UNINSTALL_SCRIPT = os.path.join(SCRIPTS_DIR, "uninstall.sh")


class TestInstallScript:
    def test_dry_run_exits_zero(self):
        """--dry-run should succeed without side effects."""
        result = subprocess.run(
            [INSTALL_SCRIPT, "--dry-run"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "dry-run" in result.stdout.lower()

    def test_help_flag(self):
        result = subprocess.run(
            [INSTALL_SCRIPT, "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Prerequisites" in result.stdout

    def test_install_with_bad_path_exits_nonzero(self):
        """If commands are installed to a dir NOT on PATH, script should exit 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool_dir = os.path.join(tmpdir, "tools")
            bin_dir = os.path.join(tmpdir, "bin")
            os.makedirs(tool_dir, exist_ok=True)
            os.makedirs(bin_dir, exist_ok=True)

            # Run install with a custom tool bin dir that's NOT on PATH
            env = os.environ.copy()
            env["UV_TOOL_DIR"] = tool_dir
            env["UV_TOOL_BIN_DIR"] = bin_dir
            # Restrict PATH to not include our custom bin dir
            env["PATH"] = os.environ.get("PATH", "/usr/bin:/bin")

            result = subprocess.run(
                [INSTALL_SCRIPT],
                capture_output=True,
                text=True,
                env=env,
            )
            # Should exit non-zero because bin_dir is not on PATH
            assert result.returncode != 0
            assert "not" in result.stderr.lower() and "path" in result.stderr.lower()


class TestInstalledBehavior:
    """Tests that verify the INSTALLED commands behave correctly.

    These run the installed executables (from uv tool install) in a temp
    directory with PATH stripped, proving absolute-path invocation and
    sibling resolution work.
    """

    def test_installed_print_config_has_bare_flag(self):
        """Installed sp-local-bridge-print-config must support --bare."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool_dir = os.path.join(tmpdir, "tools")
            bin_dir = os.path.join(tmpdir, "bin")
            os.makedirs(tool_dir, exist_ok=True)
            os.makedirs(bin_dir, exist_ok=True)

            env = os.environ.copy()
            env["UV_TOOL_DIR"] = tool_dir
            env["UV_TOOL_BIN_DIR"] = bin_dir
            # Keep PATH for uv access during install
            env["PATH"] = os.environ.get("PATH", "/usr/bin:/bin")

            # Install to temp dir
            repo_dir = os.path.dirname(SCRIPTS_DIR)
            install_result = subprocess.run(
                ["uv", "tool", "install", "--reinstall", "--from", repo_dir, "sp-local-bridge"],
                capture_output=True,
                text=True,
                env=env,
            )
            assert install_result.returncode == 0, f"Install failed: {install_result.stderr}"

            config_cmd = os.path.join(bin_dir, "sp-local-bridge-print-config")
            assert os.path.isfile(config_cmd), f"print-config not found at {config_cmd}"

            # Verify --bare flag exists in help
            help_result = subprocess.run(
                [config_cmd, "--help"],
                capture_output=True,
                text=True,
                env={"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "/tmp")},
            )
            assert help_result.returncode == 0
            assert "--bare" in help_result.stdout, "Installed code is stale: --bare missing from help"

    def test_installed_print_config_resolves_absolute_path(self):
        """Invoked by absolute path with PATH stripped, config must contain absolute mcp path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool_dir = os.path.join(tmpdir, "tools")
            bin_dir = os.path.join(tmpdir, "bin")
            os.makedirs(tool_dir, exist_ok=True)
            os.makedirs(bin_dir, exist_ok=True)

            env = os.environ.copy()
            env["UV_TOOL_DIR"] = tool_dir
            env["UV_TOOL_BIN_DIR"] = bin_dir
            env["PATH"] = os.environ.get("PATH", "/usr/bin:/bin")

            # Install to temp dir
            repo_dir = os.path.dirname(SCRIPTS_DIR)
            install_result = subprocess.run(
                ["uv", "tool", "install", "--reinstall", "--from", repo_dir, "sp-local-bridge"],
                capture_output=True,
                text=True,
                env=env,
            )
            assert install_result.returncode == 0, f"Install failed: {install_result.stderr}"

            config_cmd = os.path.join(bin_dir, "sp-local-bridge-print-config")

            # Run with PATH stripped — only system bins available
            stripped_env = {
                "PATH": "/usr/bin:/bin",
                "HOME": os.environ.get("HOME", "/tmp"),
            }
            result = subprocess.run(
                [config_cmd, "claude-desktop"],
                capture_output=True,
                text=True,
                env=stripped_env,
            )
            assert result.returncode == 0, f"print-config failed: {result.stderr}"

            # Parse the JSON output (first block before blank line)
            json_str = result.stdout.split("\n\n")[0]
            config = json.loads(json_str)
            cmd = config["mcpServers"]["super-productivity"]["command"]

            # Must be an absolute path, not bare "sp-local-bridge-mcp"
            assert os.path.isabs(cmd), f"Expected absolute path, got: {cmd}"
            assert cmd.endswith("sp-local-bridge-mcp")
            assert os.path.isfile(cmd), f"Resolved path does not exist: {cmd}"

    def test_installed_version_matches_source(self):
        """Installed sp-local-bridge --version must match source version."""
        from sp_local_bridge import __version__

        with tempfile.TemporaryDirectory() as tmpdir:
            tool_dir = os.path.join(tmpdir, "tools")
            bin_dir = os.path.join(tmpdir, "bin")
            os.makedirs(tool_dir, exist_ok=True)
            os.makedirs(bin_dir, exist_ok=True)

            env = os.environ.copy()
            env["UV_TOOL_DIR"] = tool_dir
            env["UV_TOOL_BIN_DIR"] = bin_dir
            env["PATH"] = os.environ.get("PATH", "/usr/bin:/bin")

            repo_dir = os.path.dirname(SCRIPTS_DIR)
            install_result = subprocess.run(
                ["uv", "tool", "install", "--reinstall", "--from", repo_dir, "sp-local-bridge"],
                capture_output=True,
                text=True,
                env=env,
            )
            assert install_result.returncode == 0, f"Install failed: {install_result.stderr}"

            cli_cmd = os.path.join(bin_dir, "sp-local-bridge")
            result = subprocess.run(
                [cli_cmd, "--version"],
                capture_output=True,
                text=True,
                env={"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "/tmp")},
            )
            assert result.returncode == 0
            assert __version__ in result.stdout.strip()


class TestUninstallScript:
    def test_dry_run_exits_zero(self):
        """--dry-run should succeed without side effects."""
        result = subprocess.run(
            [UNINSTALL_SCRIPT, "--dry-run"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "dry-run" in result.stdout.lower()

    def test_help_flag(self):
        result = subprocess.run(
            [UNINSTALL_SCRIPT, "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Uninstall" in result.stdout
