"""CLI tests."""

import subprocess
import sys


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "sp-local-bridge" in result.stdout


def test_cli_unknown_command():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "nonsense"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "unknown command" in result.stderr


def test_cli_unimplemented_command():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "health"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "not yet implemented" in result.stderr
