"""SP Local REST API client.

Wraps httpx.AsyncClient for communicating with the Super Productivity
desktop app's Local REST API at http://127.0.0.1:3876.
"""

from __future__ import annotations

from typing import Any

import httpx

from sp_local_bridge.core import errors
from sp_local_bridge.core.models import BridgeResult

DEFAULT_BASE_URL = "http://127.0.0.1:3876"
DEFAULT_TIMEOUT = 10.0


class SPRestClient:
    """Async client for the Super Productivity Local REST API."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    async def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> BridgeResult:
        """Execute a request and translate the SP response envelope."""
        try:
            async with self._client() as client:
                response = await client.request(method, path, json=json)
        except httpx.ConnectError:
            return BridgeResult.failure(errors.SP_UNAVAILABLE, "Cannot connect to Super Productivity Local REST API.")
        except httpx.TimeoutException:
            return BridgeResult.failure(errors.TIMEOUT, "Request to Super Productivity timed out.")
        except httpx.HTTPError as exc:
            return BridgeResult.failure(errors.SP_UNAVAILABLE, f"HTTP error: {exc}")

        return self._translate_response(response)

    def _translate_response(self, response: httpx.Response) -> BridgeResult:
        """Translate an HTTP response into a BridgeResult."""
        if response.status_code == 404:
            return BridgeResult.failure(
                errors.TASK_NOT_FOUND,
                "Resource not found.",
                {"status_code": 404},
            )

        try:
            body = response.json()
        except (ValueError, TypeError):
            if response.is_success:
                return BridgeResult.success(None)
            return BridgeResult.failure(
                errors.SP_ERROR,
                f"SP returned non-JSON response with status {response.status_code}.",
                {"status_code": response.status_code},
            )

        # SP REST envelope: { ok: bool, data?: ..., error?: { code, message, details? } }
        if isinstance(body, dict) and "ok" in body:
            if body.get("ok"):
                return BridgeResult.success(body.get("data", body))
            else:
                error_val = body.get("error")
                if isinstance(error_val, dict):
                    # Structured error: { code: string, message: string, details?: unknown }
                    code = error_val.get("code", errors.SP_ERROR)
                    message = error_val.get("message", "Unknown SP error.")
                    details: dict[str, Any] = {"status_code": response.status_code}
                    if error_val.get("details") is not None:
                        details["sp_details"] = error_val["details"]
                    return BridgeResult.failure(code, message, details)
                elif isinstance(error_val, str):
                    # Legacy/fallback: plain string error
                    return BridgeResult.failure(
                        errors.SP_ERROR,
                        error_val,
                        {"status_code": response.status_code},
                    )
                else:
                    return BridgeResult.failure(
                        errors.SP_ERROR,
                        "Unknown SP error.",
                        {"status_code": response.status_code, "body": body},
                    )

        # If response is successful but not envelope-shaped, return body as data
        if response.is_success:
            return BridgeResult.success(body)

        return BridgeResult.failure(
            errors.SP_ERROR,
            f"SP returned status {response.status_code}.",
            {"status_code": response.status_code, "body": body},
        )

    # --- Public API methods ---

    async def health(self) -> BridgeResult:
        """GET /health"""
        return await self._request("GET", "/health")

    async def status(self) -> BridgeResult:
        """GET /status"""
        return await self._request("GET", "/status")

    async def list_tasks(self) -> BridgeResult:
        """GET /tasks"""
        return await self._request("GET", "/tasks")

    async def get_task(self, task_id: str) -> BridgeResult:
        """GET /tasks/:id"""
        return await self._request("GET", f"/tasks/{task_id}")

    async def create_task(self, data: dict[str, Any]) -> BridgeResult:
        """POST /tasks"""
        return await self._request("POST", "/tasks", json=data)

    async def update_task(self, task_id: str, data: dict[str, Any]) -> BridgeResult:
        """PATCH /tasks/:id"""
        return await self._request("PATCH", f"/tasks/{task_id}", json=data)

    async def start_task(self, task_id: str) -> BridgeResult:
        """POST /tasks/:id/start"""
        return await self._request("POST", f"/tasks/{task_id}/start")

    async def stop_current_task(self) -> BridgeResult:
        """POST /task-control/stop"""
        return await self._request("POST", "/task-control/stop")

    async def archive_task(self, task_id: str) -> BridgeResult:
        """POST /tasks/:id/archive"""
        return await self._request("POST", f"/tasks/{task_id}/archive")

    async def restore_task(self, task_id: str) -> BridgeResult:
        """POST /tasks/:id/restore"""
        return await self._request("POST", f"/tasks/{task_id}/restore")

    async def list_projects(self) -> BridgeResult:
        """GET /projects"""
        return await self._request("GET", "/projects")

    async def list_tags(self) -> BridgeResult:
        """GET /tags"""
        return await self._request("GET", "/tags")
