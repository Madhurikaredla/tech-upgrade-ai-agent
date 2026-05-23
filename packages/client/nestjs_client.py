import asyncio
from typing import Any

import httpx
import logfire

from packages.config.settings import get_settings
from packages.logging.context import get_active_role, get_bearer_token, get_request_id

from .retry import with_retry


class NestJSClient:
    """Singleton async HTTP client for the downstream NestJS service.

    All NestJS responses use the envelope:
        {"success": true, "data": {...}, "error": null}
    _unwrap() checks success and returns data, raising on failure.
    """

    _instance: "NestJSClient | None" = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self) -> None:
        self._settings = get_settings()
        self._http: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # Singleton factory
    # ------------------------------------------------------------------

    @classmethod
    async def get_instance(cls) -> "NestJSClient":
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    obj = cls()
                    await obj._init()
                    cls._instance = obj
        return cls._instance

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _init(self) -> None:
        self._http = httpx.AsyncClient(
            base_url=self._settings.nestjs_base_url,
            timeout=self._settings.nestjs_timeout,
            headers={"Content-Type": "application/json"},
        )

    async def close(self) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        # NestJS CombinedAuthGuard routes auth by token suffix:
        #   "Bearer <token> custom" → OTP/JWT path (validates the user's NestJS-issued token)
        #   "Bearer <token>"        → Firebase path (requires userid header — not applicable here)
        headers: dict[str, str] = {"X-Request-ID": get_request_id()}
        if caller_token := get_bearer_token():
            headers["Authorization"] = f"Bearer {caller_token} custom"
        if active_role := get_active_role():
            headers["active-role"] = active_role
        return headers

    # ------------------------------------------------------------------
    # Response envelope
    # ------------------------------------------------------------------

    @staticmethod
    def _unwrap(body: Any) -> Any:
        """Unwrap the standard NestJS envelope {"success": true, "data": {...}}.

        Raises RuntimeError if success is false.
        Returns body as-is when there is no envelope (e.g. plain arrays).
        """
        if not isinstance(body, dict):
            return body
        if "success" in body:
            if not body.get("success"):
                err = body.get("error") or body
                raise RuntimeError(f"NestJS error: {err}")
            return body.get("data")
        return body

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _raise_for_status(self, resp: httpx.Response, path: str) -> None:
        if resp.status_code < 400:
            return
        try:
            body = resp.text[:4000]
        except Exception:
            body = "<unreadable>"
        logfire.warning("nestjs.http_error", path=path, status=resp.status_code, body=body)
        # Include the NestJS response body in the exception message so it
        # appears directly in the terminal traceback — no logfire click needed.
        raise httpx.HTTPStatusError(
            f"NestJS {resp.status_code} on {path}: {body}",
            request=resp.request,
            response=resp,
        )

    @with_retry
    async def post(self, path: str, payload: dict[str, Any]) -> Any:
        assert self._http is not None
        with logfire.span("nestjs.post", path=path):
            resp = await self._http.post(path, json=payload, headers=self._auth_headers())
            self._raise_for_status(resp, path)
            return self._unwrap(resp.json())

    @with_retry
    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        assert self._http is not None
        with logfire.span("nestjs.get", path=path):
            resp = await self._http.get(path, params=params, headers=self._auth_headers())
            self._raise_for_status(resp, path)
            return self._unwrap(resp.json())

    @with_retry
    async def put(self, path: str, payload: dict[str, Any]) -> Any:
        assert self._http is not None
        with logfire.span("nestjs.put", path=path):
            resp = await self._http.put(path, json=payload, headers=self._auth_headers())
            self._raise_for_status(resp, path)
            return self._unwrap(resp.json())

    @with_retry
    async def patch(self, path: str, payload: dict[str, Any]) -> Any:
        assert self._http is not None
        with logfire.span("nestjs.patch", path=path):
            resp = await self._http.patch(path, json=payload, headers=self._auth_headers())
            self._raise_for_status(resp, path)
            return self._unwrap(resp.json())

    # send_payload kept as an alias so existing callers don't break
    async def send_payload(self, path: str, payload: dict[str, Any]) -> Any:
        return await self.post(path, payload)

    async def get_jwt(self) -> str:
        """Return the caller's bearer token from request context."""
        return get_bearer_token()
