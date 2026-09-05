"""Super Productivity Local Bridge."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

# The version is declared once, in pyproject.toml, and read back from the
# installed distribution metadata. Duplicating it here as a literal is how the
# package came to report 0.2.0 while shipping as 0.2.1 — three copies (this
# file, pyproject.toml and a test assertion) that had to be bumped together and
# were not.
try:
    __version__ = _version("sp-local-bridge")
except PackageNotFoundError:
    # Imported from a source tree with no installed distribution — during a
    # build, or `python -c` from the repo root. Not a version anyone ships.
    __version__ = "0+unknown"

__all__ = ["__version__"]
