"""Smoke tests — verify the package is importable and minimally functional."""

import sp_local_bridge


def test_version():
    assert sp_local_bridge.__version__ == "0.1.1"


def test_import_core():
    import sp_local_bridge.core  # noqa: F401


def test_import_sp_rest():
    import sp_local_bridge.sp_rest  # noqa: F401


def test_import_adapters():
    import sp_local_bridge.adapters  # noqa: F401


def test_import_diagnostics():
    import sp_local_bridge.diagnostics  # noqa: F401
