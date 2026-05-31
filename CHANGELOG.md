# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] — 2026-05-31

### Added

- `sp-local-bridge-configure` command for auto-writing MCP config to host files
- Agent setup skill (`skills/sp-local-bridge-setup/`) for guided installation
- Regression tests for TOML preservation, doctor parse-error handling, uninstall ordering

### Fixed

- TOML auto-config: surgical write now only touches `[mcp_servers.superProductivity]`, preserving all other file content including inline tables, env maps, and numbers
- TOML auto-config: malformed existing TOML fails closed (error code 1) instead of silently appending
- TOML auto-config: removal now deletes descendant tables (e.g. `[mcp_servers.superProductivity.env]`)
- Doctor: malformed host config produces a failed diagnostic check instead of crashing or false-passing
- Uninstall: host config cleanup runs before package removal; failures are surfaced clearly

## [0.1.0] — 2026-05-30

### Added

- Core operation layer with 13 operations: `task.list`, `task.get`, `task.create`, `task.update`, `task.complete`, `task.uncomplete`, `task.start`, `task.stop_current`, `task.archive`, `task.restore`, `project.list`, `tag.list`, `bridge.health`
- SP Local REST API client with full envelope parsing, timeout handling, and error translation
- MCP adapter with tool annotations, structured content, and complete input schemas
- CLI with `health`, `tasks`, `projects`, `tags` subcommands
- Doctor command (`sp-local-bridge-doctor`) for bridge health diagnostics
- Host config generator (`sp-local-bridge-print-config`) for MCP host setup
- Install/uninstall scripts with `--dry-run` support
- CI pipeline (GitHub Actions) with Python 3.11/3.12/3.13 matrix
- 135+ tests covering core validation, REST translation, MCP protocol, and diagnostics
- Documentation: operations reference, host setup guides

### Notes

- Plugin fallback (file-spool bridge) is deferred — all operations use the Local REST API
- Requires Super Productivity desktop app with Local REST API enabled (Settings → Misc)
