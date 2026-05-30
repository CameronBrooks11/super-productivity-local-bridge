"""Host configuration generator — prints host-specific config snippets."""

from __future__ import annotations

import json
import os
import shutil
import sys

_HOSTS: dict[str, dict[str, object]] = {
    "claude-desktop": {
        "format": "json",
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
    "vscode-copilot": {
        "format": "json",
        "config_template": {
            "servers": {
                "superProductivity": {
                    "type": "stdio",
                    "command": "sp-local-bridge-mcp",
                    "args": [],
                }
            }
        },
        "paths": {
            "linux": ".vscode/mcp.json (workspace) or User settings.json",
            "macos": ".vscode/mcp.json (workspace) or User settings.json",
            "windows": ".vscode/mcp.json (workspace) or User settings.json",
        },
    },
    "codex": {
        "format": "toml",
        "config_template": {
            "mcp_servers": {
                "superProductivity": {
                    "command": "sp-local-bridge-mcp",
                    "args": [],
                }
            }
        },
        "paths": {
            "linux": "~/.codex/config.toml or .codex/config.toml (project)",
            "macos": "~/.codex/config.toml or .codex/config.toml (project)",
            "windows": "~/.codex/config.toml or .codex/config.toml (project)",
        },
    },
}


def _resolve_mcp_command() -> str:
    """Resolve the absolute path to sp-local-bridge-mcp if possible.

    GUI-launched MCP hosts often do not inherit shell PATH, so we prefer
    absolute paths. Resolution order:
    1. Sibling of the current executable (same bin directory)
    2. shutil.which (PATH lookup)
    3. UV_TOOL_BIN_DIR or ~/.local/bin
    4. Bare command name (fallback)
    """
    # 1. Sibling discovery: if this script was invoked by absolute path,
    #    sp-local-bridge-mcp is likely in the same directory.
    argv0 = sys.argv[0] if sys.argv else ""
    if argv0 and os.path.isabs(argv0):
        sibling = os.path.join(os.path.dirname(argv0), "sp-local-bridge-mcp")
        if os.path.isfile(sibling) and os.access(sibling, os.X_OK):
            return os.path.realpath(sibling)

    # Also check __file__-based resolution (works in installed entry_points)
    this_dir = os.path.dirname(os.path.abspath(__file__))
    # Walk up to find the bin dir: __file__ is in .../sp_local_bridge/diagnostics/
    # Entry points are in the same bin dir as python or the scripts dir
    bin_from_file = os.path.join(this_dir, "..", "..", "..", "bin", "sp-local-bridge-mcp")
    bin_from_file = os.path.normpath(bin_from_file)
    if os.path.isfile(bin_from_file) and os.access(bin_from_file, os.X_OK):
        return os.path.realpath(bin_from_file)

    # 2. PATH lookup
    found = shutil.which("sp-local-bridge-mcp")
    if found:
        return os.path.realpath(found)

    # 3. Check uv tool bin default locations
    uv_bin = os.environ.get("UV_TOOL_BIN_DIR", os.path.expanduser("~/.local/bin"))
    candidate = os.path.join(uv_bin, "sp-local-bridge-mcp")
    if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
        return os.path.realpath(candidate)

    # 4. Fallback: bare command (user will need PATH configured)
    return "sp-local-bridge-mcp"


def _build_config(host: str, *, absolute: bool = True) -> dict:
    """Build the config dict for a host, optionally resolving absolute paths."""
    entry = _HOSTS[host]
    config = json.loads(json.dumps(entry["config_template"]))  # deep copy

    if absolute:
        mcp_cmd = _resolve_mcp_command()
        # Replace the command in all server entries (mcpServers, servers, or mcp_servers)
        servers = config.get("mcpServers", config.get("servers", config.get("mcp_servers", {})))
        for _name, server in servers.items():
            if server.get("command") == "sp-local-bridge-mcp":
                server["command"] = mcp_cmd

    return config


def _format_toml_config(config: dict) -> str:
    """Format a config dict as TOML for Codex-style hosts.

    Uses TOML literal strings (single quotes) for values to avoid
    backslash escape issues with Windows paths like C:\\Users\\...
    """
    lines: list[str] = []
    mcp_servers = config.get("mcp_servers", {})
    for name, server in mcp_servers.items():
        lines.append(f"[mcp_servers.{name}]")
        for key, value in server.items():
            if isinstance(value, str):
                lines.append(f"{key} = '{value}'")
            elif isinstance(value, list):
                items = ", ".join(f"'{v}'" for v in value)
                lines.append(f"args = [{items}]")
            elif isinstance(value, bool):
                lines.append(f"{key} = {'true' if value else 'false'}")
        lines.append("")
    return "\n".join(lines)


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
    fmt = entry.get("format", "json")

    # Find the command from whichever server structure this host uses
    servers = config.get("mcpServers", config.get("servers", config.get("mcp_servers", {})))
    mcp_cmd = next(iter(servers.values()), {}).get("command", "sp-local-bridge-mcp")
    if mcp_cmd == "sp-local-bridge-mcp" and absolute:
        print("Warning: could not resolve absolute path for sp-local-bridge-mcp.", file=sys.stderr)
        print("The host may fail to launch if ~/.local/bin is not on its PATH.", file=sys.stderr)
        print("", file=sys.stderr)

    if fmt == "toml":
        print(_format_toml_config(config))
    else:
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
