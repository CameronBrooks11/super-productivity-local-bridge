"""Tests for the install/uninstall scripts."""

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
