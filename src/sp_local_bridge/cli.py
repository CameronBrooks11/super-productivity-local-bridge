"""CLI entry point for sp-local-bridge."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

from sp_local_bridge import __version__
from sp_local_bridge.core.models import BridgeRequest, BridgeResult
from sp_local_bridge.core.operations import Operation
from sp_local_bridge.core.service import BridgeService
from sp_local_bridge.sp_rest.client import SPRestClient

COMMANDS = ["health", "status", "tasks", "projects", "tags"]


def _print_result(result: BridgeResult) -> int:
    """Print a bridge result as JSON and return exit code."""
    if result.ok:
        print(json.dumps(result.data, indent=2, default=str))
        return 0
    else:
        assert result.error is not None
        print(f"Error [{result.error.code}]: {result.error.message}", file=sys.stderr)
        return 1


def _parse_list_flags(args: list[str], allowed: set[str] | None = None) -> tuple[dict[str, Any], str | None]:
    """Parse --flag value pairs from args.

    Returns (flags_dict, error_message). If error_message is not None, parsing failed.
    ``allowed`` restricts which flags are valid; None means all known task-list flags.
    """
    task_list_flags = {"--query", "--project-id", "--tag-id", "--include-done", "--source"}
    valid_flags = allowed if allowed is not None else task_list_flags
    flags: dict[str, Any] = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if not arg.startswith("--"):
            return {}, f"Unexpected argument: {arg}"
        if arg not in valid_flags:
            return {}, f"Unknown flag: {arg}"
        if arg == "--query":
            if i + 1 >= len(args):
                return {}, "Flag --query requires a value"
            flags["query"] = args[i + 1]
            i += 2
        elif arg == "--project-id":
            if i + 1 >= len(args):
                return {}, "Flag --project-id requires a value"
            flags["projectId"] = args[i + 1]
            i += 2
        elif arg == "--tag-id":
            if i + 1 >= len(args):
                return {}, "Flag --tag-id requires a value"
            flags["tagId"] = args[i + 1]
            i += 2
        elif arg == "--include-done":
            flags["includeDone"] = True
            i += 1
        elif arg == "--source":
            if i + 1 >= len(args):
                return {}, "Flag --source requires a value"
            flags["source"] = args[i + 1]
            i += 2
        else:
            return {}, f"Unknown flag: {arg}"
    return flags, None


def _usage() -> None:
    print(f"sp-local-bridge {__version__}")
    print("Usage: sp-local-bridge <command> [args]")
    print()
    print("Commands:")
    print("  health                       Check SP connectivity")
    print("  status                       Get SP app status")
    print("  tasks list [filters]         List tasks (see filters below)")
    print("  tasks get <id>               Get a task by ID")
    print("  tasks add <title>            Create a new task")
    print("  tasks current                Get currently tracked task")
    print("  tasks set-current <id>       Set current task by ID")
    print("  tasks clear-current          Clear current task")
    print("  projects list [--query ...]  List projects")
    print("  tags list [--query ...]      List tags")
    print()
    print("Task list filters:")
    print("  --query <text>               Filter by title substring")
    print("  --project-id <id>            Filter by project")
    print("  --tag-id <id>                Filter by tag (use TODAY for today's tasks)")
    print("  --include-done               Include completed tasks")
    print("  --source <active|archived|all>  Task pool to query")


async def _run(args: list[str]) -> int:
    """Parse args and execute the appropriate operation."""
    base_url = os.environ.get("SP_BASE_URL")
    client = SPRestClient(base_url=base_url) if base_url else SPRestClient()
    service = BridgeService(client)

    if not args:
        _usage()
        return 0

    command = args[0]

    if command == "health":
        result = await service.execute(BridgeRequest(operation=Operation.BRIDGE_HEALTH))
        return _print_result(result)

    if command == "status":
        result = await service.execute(BridgeRequest(operation=Operation.STATUS_GET))
        return _print_result(result)

    if command == "tasks":
        subcommand = args[1] if len(args) > 1 else "list"
        if subcommand == "list":
            flags, err = _parse_list_flags(args[2:])
            if err:
                print(f"Error: {err}", file=sys.stderr)
                return 2
            result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST, payload=flags))
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
        elif subcommand == "current":
            result = await service.execute(BridgeRequest(operation=Operation.TASK_GET_CURRENT))
        elif subcommand == "set-current":
            if len(args) < 3:
                print("Error: tasks set-current requires a task ID", file=sys.stderr)
                return 2
            result = await service.execute(
                BridgeRequest(operation=Operation.TASK_SET_CURRENT, payload={"taskId": args[2]})
            )
        elif subcommand == "clear-current":
            result = await service.execute(
                BridgeRequest(operation=Operation.TASK_SET_CURRENT, payload={"taskId": None})
            )
        else:
            print(f"Error: unknown tasks subcommand '{subcommand}'", file=sys.stderr)
            return 2
        return _print_result(result)

    if command == "projects":
        subcommand = args[1] if len(args) > 1 else "list"
        if subcommand == "list":
            flags, err = _parse_list_flags(args[2:], allowed={"--query"})
            if err:
                print(f"Error: {err}", file=sys.stderr)
                return 2
            payload = {"query": flags["query"]} if "query" in flags else {}
            result = await service.execute(BridgeRequest(operation=Operation.PROJECT_LIST, payload=payload))
        else:
            print(f"Error: unknown projects subcommand '{subcommand}'", file=sys.stderr)
            return 2
        return _print_result(result)

    if command == "tags":
        subcommand = args[1] if len(args) > 1 else "list"
        if subcommand == "list":
            flags, err = _parse_list_flags(args[2:], allowed={"--query"})
            if err:
                print(f"Error: {err}", file=sys.stderr)
                return 2
            payload = {"query": flags["query"]} if "query" in flags else {}
            result = await service.execute(BridgeRequest(operation=Operation.TAG_LIST, payload=payload))
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
