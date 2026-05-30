"""Host configuration generator — prints host-specific config snippets."""

from __future__ import annotations

import json
import sys

_HOSTS: dict[str, dict[str, object]] = {
    "claude-desktop": {
        "config": {
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


def _print_config(host: str) -> int:
    """Print configuration snippet for the given host. Returns exit code."""
    entry = _HOSTS.get(host)
    if entry is None:
        print(f"Error: unknown host '{host}'", file=sys.stderr)
        print(f"Supported hosts: {', '.join(sorted(_HOSTS.keys()))}", file=sys.stderr)
        return 2

    config = entry["config"]
    paths = entry["paths"]
    assert isinstance(paths, dict)

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
    print("Usage: sp-local-bridge-print-config <host>")
    print()
    print("Supported hosts:")
    for host in sorted(_HOSTS.keys()):
        print(f"  {host}")


def main() -> None:
    """Print host-specific configuration snippet."""
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        _usage()
        sys.exit(0 if args and args[0] in ("--help", "-h") else 2)

    sys.exit(_print_config(args[0]))


if __name__ == "__main__":
    main()
