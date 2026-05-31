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
    assert "0.2.0" in result.stdout


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


# --- New command argument validation tests ---


def test_cli_tasks_set_current_missing_id():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "tasks", "set-current"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "requires a task ID" in result.stderr


def test_cli_tasks_unknown_subcommand():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "tasks", "bogus"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "unknown tasks subcommand" in result.stderr


def test_cli_projects_unknown_subcommand():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "projects", "bogus"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "unknown projects subcommand" in result.stderr


def test_cli_tags_unknown_subcommand():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "tags", "bogus"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "unknown tags subcommand" in result.stderr


# --- CLI flag parsing error tests ---


def test_cli_tasks_list_unknown_flag():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "tasks", "list", "--sorce", "all"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "Unknown flag" in result.stderr


def test_cli_tasks_list_flag_missing_value():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "tasks", "list", "--source"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "requires a value" in result.stderr


def test_cli_projects_list_rejects_task_flags():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "projects", "list", "--source", "all"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "Unknown flag" in result.stderr


def test_cli_tags_list_rejects_task_flags():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "tags", "list", "--include-done"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "Unknown flag" in result.stderr


def test_cli_tasks_list_bare_arg_rejected():
    """Positional arguments without -- prefix are rejected."""
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", "tasks", "list", "stray"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "Unexpected argument" in result.stderr


# --- Status / current task commands reach execution (fail with SP_UNAVAILABLE) ---


def _run_cli_unavailable(*args: str) -> subprocess.CompletedProcess[str]:
    """Run CLI pointed at a dead port to test command dispatch."""
    import os

    env = os.environ.copy()
    env["SP_BASE_URL"] = "http://127.0.0.1:1"
    return subprocess.run(
        [sys.executable, "-m", "sp_local_bridge", *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


def test_cli_status_dispatches():
    result = _run_cli_unavailable("status")
    assert result.returncode == 1
    assert "SP_UNAVAILABLE" in result.stderr


def test_cli_tasks_current_dispatches():
    result = _run_cli_unavailable("tasks", "current")
    assert result.returncode == 1
    assert "SP_UNAVAILABLE" in result.stderr


def test_cli_tasks_clear_current_dispatches():
    result = _run_cli_unavailable("tasks", "clear-current")
    assert result.returncode == 1
    assert "SP_UNAVAILABLE" in result.stderr


def test_cli_tasks_list_with_valid_flags_dispatches():
    result = _run_cli_unavailable("tasks", "list", "--query", "budget", "--include-done")
    assert result.returncode == 1
    assert "SP_UNAVAILABLE" in result.stderr
