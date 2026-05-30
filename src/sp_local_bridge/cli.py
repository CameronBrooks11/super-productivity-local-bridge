"""CLI entry point for sp-local-bridge."""

import sys

COMMANDS = ["health", "tasks", "projects", "tags"]


def main() -> None:
    """Run the sp-local-bridge CLI."""
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print("sp-local-bridge v0.1.0")
        print("Usage: sp-local-bridge <command>")
        print(f"Commands: {', '.join(COMMANDS)}")
        sys.exit(0)

    if args[0] == "--version":
        print("0.1.0")
        sys.exit(0)

    command = args[0]
    if command not in COMMANDS:
        print(f"Error: unknown command '{command}'", file=sys.stderr)
        print(f"Available commands: {', '.join(COMMANDS)}", file=sys.stderr)
        sys.exit(2)

    # All real commands are not yet implemented
    print(f"Error: '{command}' is not yet implemented", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
