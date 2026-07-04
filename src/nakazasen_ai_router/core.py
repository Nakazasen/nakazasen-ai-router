"""Core routing primitives for Nakazasen AI Router.

This module intentionally contains no real AI provider calls.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from typing import Any, Mapping, Sequence
from datetime import datetime, timezone

LOGGER = logging.getLogger(__name__)
SENSITIVE_KEYS = {"api_key", "apikey", "token", "secret", "authorization", "password", "raw_key"}

AUTH_HINTS = ("401", "403", "unauthorized", "authentication", "auth failure", "invalid api key", "incorrect api key", "permission denied", "forbidden", "api key", "invalid key")
QUOTA_HINTS = ("429", "quota", "rate limit", "rate_limit", "resource exhausted", "too many requests", "requests per day", "request per day", "rpd", "requests per minute", "request per minute", "rpm", "tokens per minute", "token per minute", "tpm", "daily limit", "daily quota", "free tier", "insufficient quota", "rate_limit_exceeded")
TIMEOUT_HINTS = ("timeout", "timed out")
TRANSPORT_HINTS = ("connection failed", "connection aborted", "connection refused", "connection reset", "connection error", "actively refused", "winerror 10061", "winerror 10054", "winerror 11001", "remote end closed connection", "temporary failure in name resolution", "name or service not known", "network is unreachable", "failed to establish a new connection", "max retries exceeded")
MODEL_ERROR_HINTS = ("invalid model", "model not found", "unknown model", "unsupported model")
MODEL_UNAVAILABLE_HINTS = ("404", "410", "not found", "model unavailable")
TOKEN_LIMIT_HINTS = ("token limit", "token_limit", "prompt token", "context length", "context window", "maximum context", "too many tokens", "input is too long", "reduce the input", "max tokens")
PROVIDER_5XX_HINTS = ("500", "502", "503", "504", "server error", "bad gateway", "service unavailable", "gateway timeout")


class ProviderError(Exception):
    """Base class for provider failures."""

    def __init__(self, message: str = "", *, status_code: int | None = None, response_body: Any = None, retry_after: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.retry_after = retry_after


class ProviderQuotaError(ProviderError):
    """Provider cannot serve because quota or rate limit is exhausted."""


class ProviderAuthError(ProviderError):
    """Provider credentials are invalid or rejected."""


class ProviderTimeoutError(ProviderError):
    """Provider did not respond within the expected time."""


class RouterError(Exception):
    """Raised when the router cannot return a successful result."""

    def __init__(self, message: str, *, attempts: Sequence[Mapping[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.attempts = list(attempts or [])


@dataclass(frozen=True)
class AIRequest:
    """A minimal request sent to a provider."""

    prompt: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIResult:
    """A minimal result returned by a provider."""

    text: str
    provider_name: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class ProviderHealth:
    """Mutable provider health state tracked by the router."""

    enabled: bool = True
    cooldown_until: float = 0.0
    last_error: str | None = None
    last_error_type: str = ""
    consecutive_failures: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_latency_ms: int = 0

    def is_available(self, now: float | None = None) -> bool:
        current = time.time() if now is None else now
        return self.enabled and current >= self.cooldown_until


@dataclass
class ProviderCandidate:
    """Provider plus metadata used by routing decisions.

    `key_id` must be a masked identifier only; never store a raw API key here.
    """

    provider: "ProviderBase"
    priority: int = 100
    model: str = ""
    key_index: int = -1
    key_id: str = ""

    def __post_init__(self) -> None:
        self.key_id = mask_key_id(self.key_id)


@dataclass(frozen=True)
class RouterPolicy:
    """Typed routing policy for safe provider selection."""

    mode: str = "waterfall"
    allowed_providers: Sequence[str] | None = None
    avoid_providers: Sequence[str] = field(default_factory=tuple)
    last_resort_providers: Sequence[str] = field(default_factory=tuple)
    local_only: bool = False
    max_attempts: int = 1
    quota_cooldown_seconds: float = 60.0
    transient_cooldown_seconds: float = 15.0


class ProviderBase:
    """Base class for all providers.

    Real providers will subclass this later. For now tests use fake providers only.
    """

    def __init__(self, name: str, *, is_cloud: bool) -> None:
        self.name = name
        self.is_cloud = is_cloud
        self.health = ProviderHealth()

    def iter_candidates(self) -> list[ProviderCandidate]:
        return [ProviderCandidate(provider=self, priority=0)]

    def generate(self, request: AIRequest, candidate: ProviderCandidate | None = None) -> AIResult:
        raise NotImplementedError


class AIRouter:
    """Provider router with fallback, typed policy, attempts trace, and health handling."""

    def __init__(self, providers: Sequence[ProviderBase | ProviderCandidate], policy: RouterPolicy | None = None) -> None:
        self.policy = policy or RouterPolicy()
        self.providers = self._normalize(providers)

    def route(self, request: AIRequest) -> AIResult:
        safe_metadata = sanitize_mapping(request.metadata)
        LOGGER.info("Routing AI request metadata=%s", safe_metadata)

        attempts: list[dict[str, Any]] = []
        for base_candidate in self._ordered_candidates():
            provider = base_candidate.provider
            skip_reason = self._skip_reason(provider)
            if skip_reason:
                attempts.append(self._attempt(provider, base_candidate, "skipped", reason=skip_reason))
                LOGGER.info("Skipping provider %s: %s", provider.name, skip_reason)
                continue

            for candidate in self._candidate_list(provider, base_candidate)[: max(1, self.policy.max_attempts)]:
                if not provider.health.is_available():
                    attempts.append(self._attempt(provider, candidate, "skipped", reason="cooldown"))
                    continue
                started = time.time()
                try:
                    result = provider.generate(request, candidate)
                    latency_ms = round((time.time() - started) * 1000)
                    self._mark_success(provider, latency_ms)
                    success_attempt = self._attempt(provider, candidate, "success", latency_ms=latency_ms)
                    attempts.append(success_attempt)
                    merged_metadata = dict(result.metadata)
                    merged_metadata.setdefault("attempts", attempts)
                    return AIResult(text=result.text, provider_name=result.provider_name or provider.name, metadata=merged_metadata)
                except ProviderError as exc:
                    latency_ms = round((time.time() - started) * 1000)
                    error_type = classify_error(exc, status_code=getattr(exc, "status_code", None), response_body=getattr(exc, "response_body", None))
                    retry_after = extract_retry_after_seconds(exc) or extract_retry_after_seconds({"retry_after": getattr(exc, "retry_after", None)})
                    self._mark_failure(provider, error_type, str(exc), latency_ms, retry_after)
                    attempts.append(self._attempt(provider, candidate, "failed", reason=error_type, latency_ms=latency_ms))
                    LOGGER.warning("Provider %s failed with %s; trying next candidate", provider.name, error_type)

        detail = ", ".join(f"{a['provider']}:{a.get('reason', a['status'])}" for a in attempts) or "no eligible providers"
        raise RouterError(f"No provider returned a result: {detail}", attempts=attempts)

    def _ordered_candidates(self) -> list[ProviderCandidate]:
        allowed = set(self.policy.allowed_providers or [item.provider.name for item in self.providers])
        avoid = set(self.policy.avoid_providers)
        last_resort = set(self.policy.last_resort_providers)
        candidates = [item for item in self.providers if item.provider.name in allowed and item.provider.name not in avoid]
        return sorted(candidates, key=lambda item: (item.provider.name in last_resort, item.priority))

    def _skip_reason(self, provider: ProviderBase) -> str:
        if self.policy.local_only and provider.is_cloud:
            return "local_only"
        if not provider.health.enabled:
            return "disabled"
        if not provider.health.is_available():
            return "cooldown"
        return ""

    @staticmethod
    def _candidate_list(provider: ProviderBase, fallback: ProviderCandidate) -> list[ProviderCandidate]:
        candidates = provider.iter_candidates() or [fallback]
        return [candidate if candidate.provider is provider else ProviderCandidate(provider=provider, priority=candidate.priority, model=candidate.model, key_index=candidate.key_index, key_id=candidate.key_id) for candidate in candidates]

    @staticmethod
    def _attempt(provider: ProviderBase, candidate: ProviderCandidate, status: str, *, reason: str = "", latency_ms: int = 0) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "provider": provider.name,
            "status": status,
            "is_cloud": provider.is_cloud,
        }
        if candidate.model:
            payload["model"] = candidate.model
        if candidate.key_index >= 0:
            payload["key_index"] = candidate.key_index
        if candidate.key_id:
            payload["key_id"] = mask_key_id(candidate.key_id)
        if reason:
            payload["reason"] = reason
        if latency_ms:
            payload["latency_ms"] = latency_ms
        return sanitize_mapping(payload)

    @staticmethod
    def _mark_success(provider: ProviderBase, latency_ms: int) -> None:
        provider.health.enabled = True
        provider.health.cooldown_until = 0.0
        provider.health.last_error = None
        provider.health.last_error_type = ""
        provider.health.consecutive_failures = 0
        provider.health.success_count += 1
        provider.health.last_latency_ms = latency_ms

    def _mark_failure(self, provider: ProviderBase, error_type: str, message: str, latency_ms: int, retry_after_seconds: float | None) -> None:
        provider.health.last_error = message
        provider.health.last_error_type = error_type
        provider.health.consecutive_failures += 1
        provider.health.failure_count += 1
        provider.health.last_latency_ms = latency_ms
        if error_type == "auth_failure":
            provider.health.enabled = False
        cooldown = self._cooldown_seconds_for_error(error_type, retry_after_seconds)
        if cooldown > 0:
            provider.health.cooldown_until = time.time() + cooldown

    def _cooldown_seconds_for_error(self, error_type: str, retry_after_seconds: float | None) -> float:
        if error_type == "quota_rate_limit":
            return max(1.0, float(retry_after_seconds or self.policy.quota_cooldown_seconds))
        if error_type in {"timeout", "transport_error", "unknown_transport_error", "provider_5xx"}:
            return max(1.0, float(self.policy.transient_cooldown_seconds))
        return 0.0

    @staticmethod
    def _normalize(providers: Sequence[ProviderBase | ProviderCandidate]) -> list[ProviderCandidate]:
        normalized: list[ProviderCandidate] = []
        for index, item in enumerate(providers):
            if isinstance(item, ProviderCandidate):
                normalized.append(item)
            else:
                normalized.append(ProviderCandidate(provider=item, priority=index))
        return normalized


def classify_error(error: Any, status_code: int | None = None, response_body: Any = None) -> str:
    if isinstance(error, ProviderAuthError):
        return "auth_failure"
    if isinstance(error, ProviderQuotaError):
        return "quota_rate_limit"
    if isinstance(error, ProviderTimeoutError):
        return "timeout"
    if status_code in (401, 403):
        return "auth_failure"
    if status_code == 429:
        return "quota_rate_limit"
    if status_code == 400 and any(token in _build_error_detail(error, response_body) for token in MODEL_ERROR_HINTS):
        return "model_error"
    if status_code in (404, 410) and any(token in _build_error_detail(error, response_body) for token in MODEL_ERROR_HINTS + MODEL_UNAVAILABLE_HINTS):
        return "model_unavailable"
    if status_code is not None and 500 <= status_code <= 599:
        return "provider_5xx"

    detail = _build_error_detail(error, response_body)
    if any(token in detail for token in AUTH_HINTS):
        return "auth_failure"
    if any(token in detail for token in QUOTA_HINTS):
        return "quota_rate_limit"
    if any(token in detail for token in TOKEN_LIMIT_HINTS):
        return "token_limit"
    if any(token in detail for token in TIMEOUT_HINTS):
        return "timeout"
    if any(token in detail for token in TRANSPORT_HINTS):
        return "transport_error"
    if any(token in detail for token in MODEL_ERROR_HINTS):
        return "model_error"
    if any(token in detail for token in MODEL_UNAVAILABLE_HINTS):
        return "model_unavailable"
    if any(token in detail for token in PROVIDER_5XX_HINTS):
        return "provider_5xx"
    return "unknown_transport_error"


def extract_retry_after_seconds(error: Any) -> float | None:
    if isinstance(error, Mapping):
        for key in ("retry_after_seconds", "retry_after", "retry-after", "Retry-After"):
            parsed = _parse_retry_after_value(error.get(key))
            if parsed is not None:
                return parsed
    for attr_name in ("retry_after_seconds", "retry_after"):
        parsed = _parse_retry_after_value(getattr(error, attr_name, None))
        if parsed is not None:
            return parsed
    headers = getattr(error, "headers", None) or getattr(error, "hdrs", None)
    if headers is not None:
        get_header = getattr(headers, "get", None)
        if callable(get_header):
            parsed = _parse_retry_after_value(get_header("Retry-After") or get_header("retry-after"))
            if parsed is not None:
                return parsed
    return None


def _parse_retry_after_value(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return max(0.0, float(value))
    text = str(value).strip()
    if not text:
        return None
    try:
        return max(0.0, float(text))
    except ValueError:
        pass
    try:
        retry_at = parsedate_to_datetime(text)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
    except Exception:
        return None


def _build_error_detail(error: Any, response_body: Any = None) -> str:
    parts: list[str] = []
    for item in (response_body, error):
        if isinstance(item, Mapping):
            parts.append(" ".join(str(value) for value in item.values()))
        elif item is not None:
            parts.append(str(item))
    return " ".join(part for part in parts if part).lower()


def mask_key_id(raw: Any) -> str:
    token = str(raw or "").strip()
    if not token:
        return ""
    if token.startswith("****") or token == "***":
        return token
    if len(token) <= 4:
        return "***"
    return f"****{token[-4:]}"


def sanitize_mapping(metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of metadata with sensitive values redacted."""

    sanitized: dict[str, Any] = {}
    for key, value in metadata.items():
        if key.lower() in SENSITIVE_KEYS:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, Mapping):
            sanitized[key] = sanitize_mapping(value)
        else:
            sanitized[key] = value
    return sanitized
