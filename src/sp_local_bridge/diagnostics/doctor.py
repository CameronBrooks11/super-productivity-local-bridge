"""Bridge health diagnostics — checks connectivity and configuration."""

from __future__ import annotations

import asyncio
import os
import shutil
import sys

from sp_local_bridge import __version__
from sp_local_bridge.core.models import BridgeRequest
from sp_local_bridge.core.operations import Operation
from sp_local_bridge.core.service import BridgeService
from sp_local_bridge.sp_rest.client import DEFAULT_BASE_URL, SPRestClient


class _Check:
    """A single diagnostic check result."""

    def __init__(self, name: str, passed: bool, message: str, detail: str = "") -> None:
        self.name = name
        self.passed = passed
        self.message = message
        self.detail = detail


async def _run_checks() -> list[_Check]:
    """Run all diagnostic checks and return results."""
    checks: list[_Check] = []

    # 1. Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append(
        _Check(
            "python_version",
            sys.version_info >= (3, 11),
            f"Python {py_ver}",
            "Requires 3.11+" if sys.version_info < (3, 11) else "",
        )
    )

    # 2. Package version
    checks.append(_Check("bridge_version", True, f"sp-local-bridge {__version__}"))

    # 3. MCP SDK available
    try:
        import mcp  # noqa: F401

        checks.append(_Check("mcp_sdk", True, "MCP SDK available"))
    except ImportError:
        checks.append(_Check("mcp_sdk", False, "MCP SDK not installed", "pip install mcp"))

    # 4. SP connectivity
    base_url = os.environ.get("SP_BASE_URL", DEFAULT_BASE_URL)
    client = SPRestClient(base_url=base_url, timeout=5.0)
    service = BridgeService(client)

    health_result = await service.execute(BridgeRequest(operation=Operation.BRIDGE_HEALTH))
    if health_result.ok:
        checks.append(_Check("sp_connectivity", True, f"SP reachable at {base_url}"))
    else:
        assert health_result.error is not None
        checks.append(
            _Check(
                "sp_connectivity",
                False,
                f"Cannot reach SP at {base_url}",
                health_result.error.message,
            )
        )

    # 5. SP task list (verifies REST API is functional)
    if health_result.ok:
        task_result = await service.execute(BridgeRequest(operation=Operation.TASK_LIST))
        if task_result.ok:
            count = len(task_result.data) if isinstance(task_result.data, list) else "?"
            checks.append(_Check("sp_tasks", True, f"Task API functional ({count} tasks)"))
        else:
            assert task_result.error is not None
            checks.append(
                _Check(
                    "sp_tasks",
                    False,
                    "Task API not responding",
                    task_result.error.message,
                )
            )

    # 6. MCP entry point accessible
    mcp_cmd = shutil.which("sp-local-bridge-mcp")
    if mcp_cmd:
        checks.append(_Check("mcp_entrypoint", True, f"MCP server: {mcp_cmd}"))
    else:
        checks.append(
            _Check(
                "mcp_entrypoint",
                False,
                "sp-local-bridge-mcp not found on PATH",
                "Install with: uv tool install sp-local-bridge",
            )
        )

    # 7. Host configuration status
    from sp_local_bridge.diagnostics.configure import _HOSTS, check_host_configured

    configured_hosts: list[str] = []
    unconfigured_hosts: list[str] = []
    for host in sorted(_HOSTS.keys()):
        if check_host_configured(host):
            configured_hosts.append(host)
        else:
            unconfigured_hosts.append(host)

    if configured_hosts:
        hosts_str = ", ".join(configured_hosts)
        checks.append(_Check("host_config", True, f"Host config: {hosts_str}"))
    else:
        checks.append(
            _Check(
                "host_config",
                True,
                "No MCP hosts configured (optional)",
                "Run: sp-local-bridge-configure <host>",
            )
        )

    if unconfigured_hosts:
        uncfg_str = ", ".join(unconfigured_hosts)
        checks.append(
            _Check(
                "host_config_available",
                True,
                f"Available to configure: {uncfg_str}",
            )
        )

    return checks


def _print_report(checks: list[_Check]) -> bool:
    """Print the diagnostic report. Returns True if all checks passed."""
    print("sp-local-bridge doctor")
    print("=" * 40)
    all_passed = True
    for check in checks:
        icon = "\u2713" if check.passed else "\u2717"
        print(f"  {icon} {check.message}")
        if check.detail:
            print(f"    {check.detail}")
        if not check.passed:
            all_passed = False
    print("=" * 40)
    if all_passed:
        print("All checks passed.")
    else:
        failed = sum(1 for c in checks if not c.passed)
        print(f"{failed} check(s) failed.")
    return all_passed


def main() -> None:
    """Run the bridge doctor checks."""
    checks = asyncio.run(_run_checks())
    all_passed = _print_report(checks)
    sys.exit(0 if all_passed else 1)
