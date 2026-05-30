# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- 115+ tests covering core validation, REST translation, MCP protocol, and diagnostics
- REST fixture examples for all supported operations
- Documentation: operations reference, host setup guides

### Notes

- Plugin fallback (file-spool bridge) is deferred — all operations use the Local REST API
- Requires Super Productivity desktop app with Local REST API enabled (Settings → Misc)
