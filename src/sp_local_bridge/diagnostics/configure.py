"""Write MCP host configuration — merge our entry into host config files."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
import tempfile
from pathlib import Path

from sp_local_bridge.diagnostics.host_config import _HOSTS, _build_config, _format_toml_config

# Concrete writable paths per host (no "(workspace) or ..." ambiguity)
_WRITABLE_PATHS: dict[str, dict[str, str]] = {
    "claude-desktop": {
        "linux": "~/.config/Claude/claude_desktop_config.json",
        "macos": "~/Library/Application Support/Claude/claude_desktop_config.json",
        "windows": "%APPDATA%/Claude/claude_desktop_config.json",
    },
    "vscode-copilot": {
        "linux": "~/.config/Code/User/mcp.json",
        "macos": "~/Library/Application Support/Code/User/mcp.json",
        "windows": "%APPDATA%/Code/User/mcp.json",
    },
    "codex": {
        "linux": "~/.codex/config.toml",
        "macos": "~/.codex/config.toml",
        "windows": "~/.codex/config.toml",
    },
}

# Keys we merge into (top-level key containing server entries)
_SERVER_KEYS: dict[str, str] = {
    "claude-desktop": "mcpServers",
    "vscode-copilot": "servers",
    "codex": "mcp_servers",
}

# Our server entry name per host
_ENTRY_NAMES: dict[str, str] = {
    "claude-desktop": "super-productivity",
    "vscode-copilot": "superProductivity",
    "codex": "superProductivity",
}


def _detect_platform() -> str:
    """Detect current platform as linux/macos/windows."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "linux"


def _resolve_config_path(host: str) -> Path:
    """Resolve the writable config file path for a host on this platform."""
    plat = _detect_platform()
    raw = _WRITABLE_PATHS[host][plat]
    return Path(os.path.expandvars(os.path.expanduser(raw)))


def _read_json(path: Path) -> dict:
    """Read existing JSON config or return empty dict."""
    if path.exists():
        text = path.read_text(encoding="utf-8").strip()
        if text:
            return json.loads(text)  # type: ignore[no-any-return]
    return {}


def _read_toml(path: Path) -> dict:
    """Read existing TOML config or return empty dict."""
    if path.exists():
        import tomllib

        text = path.read_bytes()
        if text.strip():
            return tomllib.loads(text.decode("utf-8"))
    return {}


def _backup(path: Path) -> Path | None:
    """Create a .bak copy of the file if it exists. Returns backup path or None."""
    if path.exists():
        backup_path = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup_path)
        return backup_path
    return None


def _atomic_write(path: Path, content: str) -> None:
    """Write content atomically via temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        fd = -1
        os.replace(tmp, path)
    except BaseException:
        if fd >= 0:
            os.close(fd)
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _write_json(path: Path, data: dict) -> None:
    """Write JSON config with pretty formatting (atomic + backup)."""
    _backup(path)
    _atomic_write(path, json.dumps(data, indent=2) + "\n")


def _write_toml_full(path: Path, original_lines: list[str], server_key: str, merged_servers: dict) -> None:
    """Write TOML config preserving all content outside our server table.

    Strategy: read original file, find/replace the mcp_servers table block,
    preserve everything else verbatim.
    """
    _backup(path)
    new_block = _format_toml_config({server_key: merged_servers})

    # Find existing table boundaries
    table_start = None
    table_end = None
    for i, line in enumerate(original_lines):
        stripped = line.strip()
        if stripped.startswith(f"[{server_key}") and not stripped.startswith(f"[[{server_key}"):
            table_start = i
        elif table_start is not None and stripped.startswith("[") and not stripped.startswith(f"[{server_key}"):
            table_end = i
            break

    if table_start is not None:
        # Replace existing block
        if table_end is None:
            table_end = len(original_lines)
        result_lines = [*original_lines[:table_start], new_block + "\n", *original_lines[table_end:]]
    else:
        # Append new block at end
        result_lines = original_lines[:]
        if result_lines and result_lines[-1].strip():
            result_lines.append("\n")
        result_lines.append(new_block + "\n")

    _atomic_write(path, "".join(result_lines))


def configure_host(host: str, *, dry_run: bool = False, remove: bool = False) -> int:
    """Add or remove our MCP entry in a host's config file. Returns exit code."""
    if host not in _HOSTS:
        print(f"Error: unknown host '{host}'", file=sys.stderr)
        print(f"Supported hosts: {', '.join(sorted(_HOSTS.keys()))}", file=sys.stderr)
        return 2

    config_path = _resolve_config_path(host)
    fmt = str(_HOSTS[host].get("format", "json"))
    server_key = _SERVER_KEYS[host]
    entry_name = _ENTRY_NAMES[host]

    if remove:
        return _remove_entry(config_path, fmt, server_key, entry_name, dry_run=dry_run)
    return _add_entry(host, config_path, fmt, server_key, entry_name, dry_run=dry_run)


def _add_entry(host: str, config_path: Path, fmt: str, server_key: str, entry_name: str, *, dry_run: bool) -> int:
    """Merge our server entry into the config file."""
    # Build our entry
    our_config = _build_config(host, absolute=True)
    servers_block = our_config.get(server_key, {})
    our_entry = servers_block.get(entry_name, {})

    try:
        if fmt == "json":
            existing = _read_json(config_path)
            if server_key not in existing:
                existing[server_key] = {}
            existing[server_key][entry_name] = our_entry

            if dry_run:
                print(f"Would write to: {config_path}")
                print(json.dumps(existing, indent=2))
                return 0

            _write_json(config_path, existing)
        else:
            # TOML — preserve all existing content, only merge our server entry
            existing = _read_toml(config_path)
            if server_key not in existing:
                existing[server_key] = {}
            existing[server_key][entry_name] = our_entry

            # Read original lines to preserve non-mcp_servers content
            original_lines: list[str] = []
            if config_path.exists():
                original_lines = config_path.read_text(encoding="utf-8").splitlines(keepends=True)

            if dry_run:
                print(f"Would write to: {config_path}")
                print(_format_toml_config(existing))
                return 0

            _write_toml_full(config_path, original_lines, server_key, existing[server_key])
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: cannot parse {config_path}", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        print("  Manual repair needed. Then re-run this command.", file=sys.stderr)
        return 1

    print(f"✓ Configured {host}")
    print(f"  Written to: {config_path}")
    print(f"  Restart {host} to pick up the change.")
    return 0


def _remove_entry(config_path: Path, fmt: str, server_key: str, entry_name: str, *, dry_run: bool) -> int:
    """Remove our server entry from the config file."""
    if not config_path.exists():
        print(f"Config file does not exist: {config_path}")
        print("Nothing to remove.")
        return 0

    try:
        existing = _read_json(config_path) if fmt == "json" else _read_toml(config_path)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: cannot parse {config_path}", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        print("  Manual repair needed. Then re-run this command.", file=sys.stderr)
        return 1

    servers = existing.get(server_key, {})
    if entry_name not in servers:
        print(f"Entry '{entry_name}' not found in {config_path}")
        print("Nothing to remove.")
        return 0

    del servers[entry_name]
    if not servers:
        del existing[server_key]

    if dry_run:
        print(f"Would remove '{entry_name}' from: {config_path}")
        if fmt == "json":
            print(json.dumps(existing, indent=2))
        else:
            print(_format_toml_config(existing))
        return 0

    if fmt == "json":
        _write_json(config_path, existing)
    else:
        # For remove, rewrite full file preserving other content
        original_lines = config_path.read_text(encoding="utf-8").splitlines(keepends=True)
        if servers:
            _write_toml_full(config_path, original_lines, server_key, servers)
        else:
            # Remove entire server_key table block
            _write_toml_full(config_path, original_lines, server_key, {})

    print(f"✓ Removed sp-local-bridge entry from {config_path}")
    return 0


def check_host_configured(host: str) -> bool:
    """Check if a host config file contains our entry."""
    if host not in _HOSTS:
        return False

    config_path = _resolve_config_path(host)
    if not config_path.exists():
        return False

    fmt = _HOSTS[host].get("format", "json")
    server_key = _SERVER_KEYS[host]
    entry_name = _ENTRY_NAMES[host]

    existing = _read_json(config_path) if fmt == "json" else _read_toml(config_path)

    return entry_name in existing.get(server_key, {})


def _usage() -> None:
    print("Usage: sp-local-bridge-configure [OPTIONS] <host>")
    print()
    print("Write MCP configuration directly to a host's config file.")
    print()
    print("Options:")
    print("  --dry-run     Show what would be written without making changes")
    print("  --remove      Remove our entry from the host config")
    print()
    print("Supported hosts:")
    for host in sorted(_HOSTS.keys()):
        path = _resolve_config_path(host)
        print(f"  {host:20s} → {path}")


def main() -> None:
    """CLI entry point for sp-local-bridge-configure."""
    args = sys.argv[1:]
    dry_run = False
    remove = False

    if not args or (len(args) == 1 and args[0] in ("--help", "-h")):
        _usage()
        sys.exit(0 if args and args[0] in ("--help", "-h") else 2)

    remaining: list[str] = []
    for arg in args:
        if arg == "--dry-run":
            dry_run = True
        elif arg == "--remove":
            remove = True
        elif arg in ("--help", "-h"):
            _usage()
            sys.exit(0)
        else:
            remaining.append(arg)

    if not remaining:
        _usage()
        sys.exit(2)

    sys.exit(configure_host(remaining[0], dry_run=dry_run, remove=remove))


if __name__ == "__main__":
    main()
