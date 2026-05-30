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
    assert "health" in result.stdout


def test_cli_version():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "0.1.0.dev0" in result.stdout


def test_cli_unknown_command():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "nonsense"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "unknown command" in result.stderr


def test_cli_tasks_add_missing_title():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "tasks", "add"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "requires a title" in result.stderr


def test_cli_tasks_get_missing_id():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "tasks", "get"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "requires a task ID" in result.stderr


def test_cli_health_when_sp_unavailable():
    """health command should fail gracefully when SP is not running.

    Uses an environment variable to point the client at a port with nothing listening,
    ensuring the test is deterministic regardless of whether SP is running on the dev machine.
    """
    import os

    env = os.environ.copy()
    env["SP_BASE_URL"] = "http://127.0.0.1:1"

    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "health"],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert result.returncode == 1
    assert "SP_UNAVAILABLE" in result.stderr
    # No traceback
    assert "Traceback" not in result.stderr
