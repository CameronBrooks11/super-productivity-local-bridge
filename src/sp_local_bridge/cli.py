"""CLI entry point for sp-local-bridge."""

from __future__ import annotations

import asyncio
import json
import sys

from sp_local_bridge import __version__
from sp_local_bridge.core.models import BridgeRequest, BridgeResult
from sp_local_bridge.core.operations import Operation
from sp_local_bridge.core.service import BridgeService
from sp_local_bridge.sp_rest.client import SPRestClient

COMMANDS = ["health", "tasks", "projects", "tags"]


def _print_result(result: BridgeResult) -> int:
    """Print a bridge result as JSON and return exit code."""
    if result.ok:
        print(json.dumps(result.data, indent=2, default=str))
        return 0
    else:
        assert result.error is not None
        print(f"Error [{result.error.code}]: {result.error.message}", file=sys.stderr)
        return 1


def _usage() -> None:
    print(f"sp-local-bridge {__version__}")
    print("Usage: sp-local-bridge <command> [args]")
    print()
    print("Commands:")
    print("  health              Check SP connectivity")
    print("  tasks list          List all tasks")
    print("  tasks get <id>      Get a task by ID")
    print("  tasks add <title>   Create a new task")
    print("  projects list       List all projects")
    print("  tags list           List all tags")


async def _run(args: list[str]) -> int:
    """Parse args and execute the appropriate operation."""
    service = BridgeService(SPRestClient())

    if not args:
        _usage()
        return 0

    command = args[0]

    if command == "health":
        result = await service.execute(BridgeRequest(operation=Operation.BRIDGE_HEALTH))
        return _print_result(result)

    if command == "tasks":
        subcommand = args[1] if len(args) > 1 else "list"
        if subcommand == "list":
            result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST))
        elif subcommand == "get":
            if len(args) < 3:
                print("Error: tasks get requires a task ID", file=sys.stderr)
                return 2
            result = await service.execute(BridgeRequest(operation=Operation.TASK_GET, payload={"id": args[2]}))
        elif subcommand == "add":
            if len(args) < 3:
                print("Error: tasks add requires a title", file=sys.stderr)
                return 2
            result = await service.execute(
                BridgeRequest(operation=Operation.TASK_CREATE, payload={"title": " ".join(args[2:])})
            )
        else:
            print(f"Error: unknown tasks subcommand '{subcommand}'", file=sys.stderr)
            return 2
        return _print_result(result)

    if command == "projects":
        subcommand = args[1] if len(args) > 1 else "list"
        if subcommand == "list":
            result = await service.execute(BridgeRequest(operation=Operation.PROJECT_LIST))
        else:
            print(f"Error: unknown projects subcommand '{subcommand}'", file=sys.stderr)
            return 2
        return _print_result(result)

    if command == "tags":
        subcommand = args[1] if len(args) > 1 else "list"
        if subcommand == "list":
            result = await service.execute(BridgeRequest(operation=Operation.TAG_LIST))
        else:
            print(f"Error: unknown tags subcommand '{subcommand}'", file=sys.stderr)
            return 2
        return _print_result(result)

    print(f"Error: unknown command '{command}'", file=sys.stderr)
    print(f"Available commands: {', '.join(COMMANDS)}", file=sys.stderr)
    return 2


def main() -> None:
    """Run the sp-local-bridge CLI."""
    args = sys.argv[1:]

    if args and args[0] in ("--help", "-h"):
        _usage()
        sys.exit(0)

    if args and args[0] == "--version":
        print(__version__)
        sys.exit(0)

    exit_code = asyncio.run(_run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
