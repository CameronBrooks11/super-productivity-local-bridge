"""Smoke tests — verify the package is importable and minimally functional."""

import tomllib
from importlib.metadata import version
from pathlib import Path

import sp_local_bridge


def test_version_comes_from_distribution_metadata():
    """__version__ must be read, not restated.

    A literal here is a second source of truth: the package once reported
    0.2.0 while shipping as 0.2.1 because this assertion, the module constant
    and pyproject.toml all had to be bumped together.
    """
    assert sp_local_bridge.__version__ == version("sp-local-bridge")
    assert sp_local_bridge.__version__ != "0+unknown"


def test_version_matches_pyproject():
    """pyproject.toml is the single declaration; nothing may drift from it."""
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if not pyproject.exists():  # installed-only test run
        return
    declared = tomllib.loads(pyproject.read_text())["project"]["version"]
    assert sp_local_bridge.__version__ == declared


def test_import_core():
    import sp_local_bridge.core  # noqa: F401


def test_import_sp_rest():
    import sp_local_bridge.sp_rest  # noqa: F401


def test_import_adapters():
    import sp_local_bridge.adapters  # noqa: F401


def test_import_diagnostics():
    import sp_local_bridge.diagnostics  # noqa: F401
