"""Pytest configuration."""

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> Any:
    """Load a JSON fixture file from tests/fixtures/.

    Fixtures suffixed with canonical names (e.g. task-list-ok.json) represent
    observed SP REST API response shapes. Fixtures with qualifiers like
    '-with-details' are synthetic test variants not yet confirmed live.
    """
    return json.loads((FIXTURES_DIR / name).read_text())
