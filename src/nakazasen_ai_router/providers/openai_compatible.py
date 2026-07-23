"""Mock-first OpenAI-compatible provider adapter.

The adapter supports OpenAI-compatible `/chat/completions` endpoints, but it does
not own networking. Tests and applications must inject an `http_client`/transport
with a `post(...)` method, which keeps unit tests offline and deterministic.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Mapping, Protocol

from nakazasen_ai_router.capabilities import normalize_token_usage
from nakazasen_ai_router.core import (
    AIRequest,
    AIResult,
    ProviderAuthError,
    ProviderBase,
    ProviderCandidate,
    ProviderError,
    ProviderQuotaError,
    ProviderTimeoutError,
    extract_retry_after_seconds,
    mask_key_id,
    sanitize_mapping,
)


class HTTPClient(Protocol):
    def post(self, url: str, *, headers: Mapping[str, str], json: Mapping[str, Any], timeout: float) -> Any:
        """Send a POST request and return a response-like object."""


class AsyncHTTPClient(Protocol):
    async def post(self, url: str, *, headers: Mapping[str, str], json: Mapping[str, Any], timeout: float) -> Any:
        """Send an async POST request and return a response-like object."""


class OpenAICompatibleProvider(ProviderBase):
    """Generic OpenAI-compatible chat completions provider.

    Raw API keys are kept private inside the provider. Public candidates expose
    only a masked `key_id` so router attempts/results do not leak secrets.
    """

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        api_keys: list[str] | tuple[str, ...],
        models: list[str] | tuple[str, ...],
        is_cloud: bool,
        http_client: HTTPClient,
        async_http_client: AsyncHTTPClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        super().__init__(name, is_cloud=is_cloud)
        self.base_url = base_url.rstrip("/")
        self.api_keys = [key for key in api_keys if str(key or "").strip()]
        self.models = [model for model in models if str(model or "").strip()]
        self.http_client = http_client
        self.async_http_client = async_http_client
        self.timeout = max(0.1, float(timeout))
        self._next_key_index = 0
        self._next_model_index = 0

    def iter_candidates(self) -> list[ProviderCandidate]:
        if not self.models:
            return []
        models = _rotate(self.models, self._next_model_index)
        key_entries = list(enumerate(self.api_keys)) if self.api_keys else [(-1, "")]
        key_entries = _rotate(key_entries, self._next_key_index)

        candidates: list[ProviderCandidate] = []
        priority = 0
        for model in models:
            for key_index, key in key_entries:
                candidates.append(
                    ProviderCandidate(
                        provider=self,
                        priority=priority,
                        model=model,
                        key_index=key_index,
                        key_id=mask_key_id(key) if key_index >= 0 else "",
                    )
                )
                priority += 1
        return candidates

    def generate(self, request: AIRequest, candidate: ProviderCandidate | None = None) -> AIResult:
        candidate = candidate or self._default_candidate()
        started = time.time()
        payload, headers = self._build_payload_and_headers(request, candidate)

        try:
            response = self.http_client.post(
                self._chat_completions_url(),
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except TimeoutError as exc:
            self._advance_after_failure(candidate, "timeout")
            raise ProviderTimeoutError("OpenAI-compatible request timed out") from exc
        except ProviderTimeoutError:
            self._advance_after_failure(candidate, "timeout")
            raise
        except Exception as exc:
            self._raise_transport_error(exc, candidate)

        return self._result_from_response(response, candidate, started)

    async def agenerate(self, request: AIRequest, candidate: ProviderCandidate | None = None) -> AIResult:
        candidate = candidate or self._default_candidate()
        if self.async_http_client is None:
            return await asyncio.to_thread(self.generate, request, candidate)
        started = time.time()
        payload, headers = self._build_payload_and_headers(request, candidate)

        try:
            response = await self.async_http_client.post(
                self._chat_completions_url(),
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except TimeoutError as exc:
            self._advance_after_failure(candidate, "timeout")
            raise ProviderTimeoutError("OpenAI-compatible request timed out") from exc
        except ProviderTimeoutError:
            self._advance_after_failure(candidate, "timeout")
            raise
        except Exception as exc:
            self._raise_transport_error(exc, candidate)

        return self._result_from_response(response, candidate, started)

    def _build_payload_and_headers(self, request: AIRequest, candidate: ProviderCandidate) -> tuple[dict[str, Any], dict[str, str]]:
        payload = {
            "model": candidate.model or (self.models[0] if self.models else ""),
            "messages": _messages_from_request(request),
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "nakazasen-ai-router/0.1",
        }
        api_key = self._api_key_for(candidate.key_index)
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return payload, headers

    def _raise_transport_error(self, exc: Exception, candidate: ProviderCandidate) -> None:
        if _looks_like_timeout(exc):
            self._advance_after_failure(candidate, "timeout")
            raise ProviderTimeoutError("OpenAI-compatible request timed out") from exc
        status_code = _status_code(exc)
        if status_code:
            self._advance_after_failure(candidate, "http_error")
            raise _error_for_status(status_code, _safe_error_message(exc), exc) from exc
        self._advance_after_failure(candidate, "transport_error")
        raise ProviderError(_safe_error_message(exc)) from exc

    def _result_from_response(self, response: Any, candidate: ProviderCandidate, started: float) -> AIResult:
        status_code = _status_code(response) or 200
        if status_code >= 400:
            self._advance_after_failure(candidate, "http_error")
            raise _error_for_status(status_code, _response_error_message(response), response)

        try:
            data = _response_json(response)
        except Exception as exc:
            raise ProviderError("OpenAI-compatible response was not valid JSON") from exc

        content = _extract_content(data)
        if not content:
            raise ProviderError("OpenAI-compatible response did not include message content")

        self._advance_after_success(candidate)
        metadata: dict[str, Any] = {
            "model": candidate.model,
            "key_index": candidate.key_index,
            "key_id": candidate.key_id,
            "latency_ms": round((time.time() - started) * 1000),
        }
        usage = normalize_token_usage(data.get("usage"))
        if usage.total_tokens > 0:
            metadata["token_usage"] = usage.to_dict()
        return AIResult(
            text=content,
            provider_name=self.name,
            metadata=metadata,
        )

    def _default_candidate(self) -> ProviderCandidate:
        candidates = self.iter_candidates()
        if not candidates:
            return ProviderCandidate(provider=self)
        return candidates[0]

    def _chat_completions_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/chat/completions"
        return f"{self.base_url}/v1/chat/completions"

    def _api_key_for(self, key_index: int) -> str:
        if key_index < 0 or key_index >= len(self.api_keys):
            return ""
        return self.api_keys[key_index]

    def _advance_after_success(self, candidate: ProviderCandidate) -> None:
        if self.api_keys:
            self._next_key_index = (max(0, candidate.key_index) + 1) % len(self.api_keys)
        if candidate.model in self.models:
            self._next_model_index = self.models.index(candidate.model)

    def _advance_after_failure(self, candidate: ProviderCandidate, error_type: str) -> None:
        if self.api_keys and error_type in {"http_error", "timeout", "transport_error"}:
            self._next_key_index = (max(0, candidate.key_index) + 1) % len(self.api_keys)
        if candidate.model in self.models and error_type in {"model_error", "model_unavailable", "token_limit"}:
            self._next_model_index = (self.models.index(candidate.model) + 1) % len(self.models)


def _rotate(values: list[Any], start_index: int) -> list[Any]:
    if not values:
        return []
    index = max(0, int(start_index)) % len(values)
    return values[index:] + values[:index]


def _messages_from_request(request: AIRequest) -> list[dict[str, str]]:
    raw_messages = request.metadata.get("messages") if isinstance(request.metadata, Mapping) else None
    if isinstance(raw_messages, list) and raw_messages:
        messages: list[dict[str, str]] = []
        for item in raw_messages:
            if isinstance(item, Mapping):
                role = str(item.get("role", "user") or "user")
                content = str(item.get("content", "") or "")
                messages.append({"role": role, "content": content})
        if messages:
            return messages
    return [{"role": "user", "content": request.prompt}]


def _response_json(response: Any) -> Mapping[str, Any]:
    json_method = getattr(response, "json", None)
    if callable(json_method):
        payload = json_method()
    else:
        text = getattr(response, "text", None)
        if text is None:
            content = getattr(response, "content", b"")
            text = content.decode("utf-8", errors="replace") if isinstance(content, bytes) else str(content)
        payload = json.loads(str(text))
    if not isinstance(payload, Mapping):
        raise ValueError("response JSON must be an object")
    return payload


def _extract_content(payload: Mapping[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, Mapping):
        return ""
    message = first.get("message")
    if not isinstance(message, Mapping):
        return ""
    content = message.get("content", "")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, Mapping):
                parts.append(str(item.get("text", "") or ""))
        return "".join(parts).strip()
    return str(content or "").strip()


def _error_for_status(status_code: int, message: str, source: Any) -> ProviderError:
    retry_after = extract_retry_after_seconds(source)
    safe_message = message or f"HTTP {status_code}"
    if status_code in (401, 403):
        return ProviderAuthError(safe_message, status_code=status_code, response_body=safe_message, retry_after=retry_after)
    if status_code == 429:
        return ProviderQuotaError(safe_message, status_code=status_code, response_body=safe_message, retry_after=retry_after)
    return ProviderError(safe_message, status_code=status_code, response_body=safe_message, retry_after=retry_after)


def _status_code(value: Any) -> int | None:
    for attr in ("status_code", "status", "code"):
        status = getattr(value, attr, None)
        if isinstance(status, int):
            return status
    return None


def _response_error_message(response: Any) -> str:
    try:
        payload = _response_json(response)
        error = payload.get("error")
        if isinstance(error, Mapping):
            return str(error.get("message") or error.get("type") or error.get("code") or "HTTP error")
        if error:
            return str(error)
        if payload.get("message"):
            return str(payload.get("message"))
    except Exception:
        pass
    return _safe_error_message(response)


def _safe_error_message(value: Any) -> str:
    raw = str(value or "HTTP error")
    return str(sanitize_mapping({"message": raw})["message"])


def _looks_like_timeout(exc: Exception) -> bool:
    return "timeout" in type(exc).__name__.lower() or "timed out" in str(exc).lower() or "timeout" in str(exc).lower()
