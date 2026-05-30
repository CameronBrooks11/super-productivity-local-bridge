"""Host configuration generator — prints host-specific config snippets."""

from __future__ import annotations

import json
import os
import shutil
import sys

_HOSTS: dict[str, dict[str, object]] = {
    "claude-desktop": {
        "config_template": {
            "mcpServers": {
                "super-productivity": {
                    "command": "sp-local-bridge-mcp",
                    "args": [],
                }
            }
        },
        "paths": {
            "linux": "~/.config/Claude/claude_desktop_config.json",
            "macos": "~/Library/Application Support/Claude/claude_desktop_config.json",
            "windows": "%APPDATA%\\Claude\\claude_desktop_config.json",
        },
    },
}


def _resolve_mcp_command() -> str:
    """Resolve the absolute path to sp-local-bridge-mcp if possible.

    GUI-launched MCP hosts often do not inherit shell PATH, so we prefer
    absolute paths. Falls back to bare command name if not found.
    """
    # Check if on PATH
    found = shutil.which("sp-local-bridge-mcp")
    if found:
        return os.path.realpath(found)

    # Check uv tool bin default locations
    uv_bin = os.environ.get("UV_TOOL_BIN_DIR", os.path.expanduser("~/.local/bin"))
    candidate = os.path.join(uv_bin, "sp-local-bridge-mcp")
    if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
        return os.path.realpath(candidate)

    # Fallback: bare command (user will need PATH configured)
    return "sp-local-bridge-mcp"


def _build_config(host: str, *, absolute: bool = True) -> dict:
    """Build the config dict for a host, optionally resolving absolute paths."""
    entry = _HOSTS[host]
    config = json.loads(json.dumps(entry["config_template"]))  # deep copy

    if absolute:
        mcp_cmd = _resolve_mcp_command()
        # Replace the command in all server entries
        for _name, server in config.get("mcpServers", {}).items():
            if server.get("command") == "sp-local-bridge-mcp":
                server["command"] = mcp_cmd

    return config


def _print_config(host: str, *, absolute: bool = True) -> int:
    """Print configuration snippet for the given host. Returns exit code."""
    entry = _HOSTS.get(host)
    if entry is None:
        print(f"Error: unknown host '{host}'", file=sys.stderr)
        print(f"Supported hosts: {', '.join(sorted(_HOSTS.keys()))}", file=sys.stderr)
        return 2

    config = _build_config(host, absolute=absolute)
    paths = entry["paths"]
    assert isinstance(paths, dict)

    mcp_cmd = config.get("mcpServers", {}).get("super-productivity", {}).get("command", "sp-local-bridge-mcp")
    if mcp_cmd == "sp-local-bridge-mcp" and absolute:
        print("Warning: could not resolve absolute path for sp-local-bridge-mcp.", file=sys.stderr)
        print("The host may fail to launch if ~/.local/bin is not on its PATH.", file=sys.stderr)
        print("", file=sys.stderr)

    print(json.dumps(config, indent=2))
    print()
    print("Add the above to your config file:")
    print(f"  Linux:   {paths['linux']}")
    print(f"  macOS:   {paths['macos']}")
    print(f"  Windows: {paths['windows']}")
    print()
    print("Then restart the host application.")
    return 0


def _usage() -> None:
    print("Usage: sp-local-bridge-print-config [OPTIONS] <host>")
    print()
    print("Options:")
    print("  --absolute    Use absolute path for commands (default)")
    print("  --bare        Use bare command names (requires PATH)")
    print()
    print("Supported hosts:")
    for host in sorted(_HOSTS.keys()):
        print(f"  {host}")


def main() -> None:
    """Print host-specific configuration snippet."""
    args = sys.argv[1:]
    absolute = True

    if not args or (len(args) == 1 and args[0] in ("--help", "-h")):
        _usage()
        sys.exit(0 if args and args[0] in ("--help", "-h") else 2)

    # Parse flags
    remaining: list[str] = []
    for arg in args:
        if arg in ("--absolute",):
            absolute = True
        elif arg in ("--bare",):
            absolute = False
        elif arg in ("--help", "-h"):
            _usage()
            sys.exit(0)
        else:
            remaining.append(arg)

    if not remaining:
        _usage()
        sys.exit(2)

    sys.exit(_print_config(remaining[0], absolute=absolute))


if __name__ == "__main__":
    main()
