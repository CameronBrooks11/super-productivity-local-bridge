"""CLI entry point for sp-local-bridge."""

import sys


def main() -> None:
    """Run the sp-local-bridge CLI."""
    print("sp-local-bridge v0.1.0")
    print("Usage: sp-local-bridge <command>")
    print("Commands: health, tasks, projects, tags")
    sys.exit(0)


if __name__ == "__main__":
    main()
