"""HTTP transports for optional live provider calls.

No network transport is used by default. Applications must opt in explicitly.
"""

from __future__ import annotations

import json as json_module
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class HTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    text: str

    def json(self) -> Any:
        return json_module.loads(self.text)


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

    def __repr__(self) -> str:
        return "UrllibHTTPClient()"
