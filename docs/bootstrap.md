# Project Bootstrap

Documents the bootstrap process, decisions, and validation results for the initial project scaffold.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Python version | 3.11+ | MCP SDK requires >=3.10; 3.11 gives better typing and pathlib |
| Package manager | uv | Fast, lockfile-based, recommended by MCP SDK docs |
| Build backend | hatchling | Lightweight, src-layout native |
| Formatter | ruff format | Single tool for format+lint, fast |
| Linter | ruff check | Replaces flake8/isort/pyupgrade/bugbear in one binary |
| Type checker | pyright | Standard mode, catches real errors without excessive strictness |
| Test runner | pytest | Industry standard, minimal config |
| Coverage | pytest-cov | Integrated with pytest, reports missing lines |
| Pre-commit | pre-commit + ruff hooks | Catches formatting/lint before commit |
| CI | GitHub Actions | Matrix across 3.11/3.12/3.13 |
| Dependency updates | Dependabot | Weekly checks for pip and actions |
| Source layout | `src/sp_local_bridge/` | Prevents accidental imports from project root |

## Files Created

```
pyproject.toml                 Project metadata, deps, tool config
.python-version                Pin to 3.11
uv.lock                        Reproducible dependency lockfile
Makefile                       Standard dev commands
.editorconfig                  Editor defaults (indent, EOL, charset)
.gitignore                     Python/uv/IDE/working exclusions
.pre-commit-config.yaml        Pre-commit hooks (whitespace, ruff)
.github/workflows/ci.yml       CI pipeline
.github/dependabot.yml         Dependency update config
AGENTS.md                      Canonical agent instructions
CLAUDE.md                      Pointer to AGENTS.md
README.md                      Project overview and dev commands
docs/hosts/claude-desktop.md   Claude Desktop host config
src/sp_local_bridge/           Python package structure
tests/test_smoke.py            Import smoke tests
tests/test_cli.py              CLI invocation test
```

## Package Structure

```
src/sp_local_bridge/
├── __init__.py          Package root, exports __version__
├── __main__.py          python -m entry point
├── cli.py               CLI entry point
├── core/                Core operations (models, errors, service)
├── sp_rest/             SP Local REST API client
├── adapters/            Host adapters (MCP server)
└── diagnostics/         Doctor, health checks
```

## Commands

```sh
# Bootstrap from scratch
uv sync

# Individual checks
uv run ruff format --check .   # Format check
uv run ruff check .            # Lint
uv run pyright                 # Type check
uv run pytest                  # Tests
uv run pytest --cov            # Tests + coverage

# All checks in one command
make check

# Pre-commit
uv run pre-commit install
uv run pre-commit run --all-files
```

## Validation Results

```
$ uv run ruff format --check .
12 files already formatted

$ uv run ruff check .
All checks passed!

$ uv run pyright
0 errors, 0 warnings, 0 informations

$ uv run pytest
8 passed in 0.06s

$ uv run pre-commit run --all-files
trim trailing whitespace .................... Passed
fix end of files ............................ Passed
check yaml .................................. Passed
check toml .................................. Passed
check for added large files ................. Passed
check for merge conflicts ................... Passed
debug statements (python) ................... Passed
ruff format ................................. Passed
ruff ........................................ Passed
```

## Policy

- Generated files (`uv.lock`): committed but never manually edited
- Local environments (`.venv/`): never committed
- Secrets (`.env`): never committed
- Build artifacts (`dist/`): never committed
- Working/planning files (`working/`): gitignored, local only
- Reference repos (`refs/`): gitignored, local only
