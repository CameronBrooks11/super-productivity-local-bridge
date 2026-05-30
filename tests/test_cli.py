"""CLI tests."""

import subprocess
import sys


def test_cli_runs():
    result = subprocess.run(
        [sys.executable, "-m", "sp_local_bridge"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "sp-local-bridge" in result.stdout
