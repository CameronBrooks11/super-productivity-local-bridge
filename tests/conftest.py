"""Pytest configuration."""

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> Any:
    """Load a JSON fixture file from tests/fixtures/.

    This is the canonical source of truth for SP REST API response shapes.
    Update these files when the SP app changes its API contract.
    """
    return json.loads((FIXTURES_DIR / name).read_text())
