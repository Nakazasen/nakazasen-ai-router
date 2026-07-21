"""HTTP transports for optional live provider calls.

No network transport is used by default. Applications must opt in explicitly.
"""

from __future__ import annotations

import json as json_module
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass
class HTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    text: str

    def json(self) -> Any:
        return json_module.loads(self.text)


class AsyncHTTPClient(Protocol):
    async def post(self, url: str, *, headers: Mapping[str, str], json: Mapping[str, Any], timeout: float) -> Any:
        """Send an async POST request and return a response-like object."""


class HTTPClient(Protocol):
    def get(self, url: str, *, headers: Mapping[str, str] | None = None, timeout: float) -> Any:
        """Send a GET request and return a response-like object."""


class HttpxAsyncHTTPClient:
    """Optional httpx-based async HTTP client.

    Install with `nakazasen-ai-router[async]` to use this transport.
    """

    def __init__(self) -> None:
        try:
            import httpx  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install nakazasen-ai-router[async] to use native async HTTP transport") from exc
        self._httpx = httpx

    async def post(self, url: str, *, headers: Mapping[str, str], json: Mapping[str, Any], timeout: float) -> Any:
        try:
            async with self._httpx.AsyncClient(timeout=timeout) as client:
                return await client.post(url, headers=dict(headers), json=dict(json))
        except self._httpx.TimeoutException as exc:
            raise TimeoutError("HTTP request timed out") from exc

    def __repr__(self) -> str:
        return "HttpxAsyncHTTPClient()"


class UrllibHTTPClient:
    """Small urllib-based HTTP client with explicit timeout support."""

    def post(self, url: str, *, headers: Mapping[str, str], json: Mapping[str, Any], timeout: float) -> HTTPResponse:
        body = json_module.dumps(json).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                text = response.read().decode("utf-8", errors="replace")
                return HTTPResponse(status_code=int(response.status), headers=dict(response.headers), text=text)
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
            return HTTPResponse(status_code=int(exc.code), headers=dict(exc.headers), text=text)
        except (TimeoutError, socket.timeout) as exc:
            raise TimeoutError("HTTP request timed out") from exc

    def get(self, url: str, *, headers: Mapping[str, str] | None = None, timeout: float) -> HTTPResponse:
        request = urllib.request.Request(url, headers=dict(headers or {}), method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                text = response.read().decode("utf-8", errors="replace")
                return HTTPResponse(status_code=int(response.status), headers=dict(response.headers), text=text)
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
            return HTTPResponse(status_code=int(exc.code), headers=dict(exc.headers), text=text)
        except (TimeoutError, socket.timeout) as exc:
            raise TimeoutError("HTTP request timed out") from exc

    def __repr__(self) -> str:
        return "UrllibHTTPClient()"
