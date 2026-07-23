"""Core routing primitives for Nakazasen AI Router.

This module intentionally contains no real AI provider calls.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from typing import Any, Mapping, Sequence
from datetime import datetime, timezone

from .capabilities import ModelCapability, capability_for, estimate_cost, normalize_token_usage, score_candidate_for_task
from .free_tier_catalog import DEFAULT_FREE_TIER_CATALOG
from .free_tiers import FreeTierBudget, FreeTierCatalog, LocalFreeTierUsageTracker
from .quota import InMemoryQuotaTracker, QuotaDecision
from .routing import RoutingScore, ScoreWeights, score_routing_candidate
from .state import MemoryStateStore, RouterStateStore

LOGGER = logging.getLogger(__name__)
SENSITIVE_KEYS = {"api_key", "apikey", "token", "secret", "authorization", "password", "raw_key"}

AUTH_HINTS = ("401", "403", "unauthorized", "authentication", "auth failure", "invalid api key", "incorrect api key", "permission denied", "forbidden", "api key", "invalid key")
DAILY_QUOTA_HINTS = ("daily limit", "daily quota", "requests per day", "request per day", "per day", "rpd", "quota exhausted", "quota exceeded for the day")
BILLING_LIMIT_HINTS = ("billing", "payment required", "credit balance", "credits exhausted", "billing hard limit")
INSUFFICIENT_QUOTA_HINTS = ("insufficient_quota", "insufficient quota", "not enough quota")
QUOTA_HINTS = ("429", "quota", "rate limit", "rate_limit", "resource exhausted", "too many requests", "requests per minute", "request per minute", "rpm", "tokens per minute", "token per minute", "tpm", "free tier", "rate_limit_exceeded")
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


@dataclass(frozen=True)
class AIStreamChunk:
    """A safe text chunk yielded by sync or async streaming APIs."""

    text: str
    provider_name: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
    done: bool = False


@dataclass(frozen=True)
class AttemptRecord:
    """Safe structured attempt metadata for callers and dashboards."""

    provider: str
    status: str
    is_cloud: bool
    model: str = ""
    key_index: int = -1
    key_id: str = ""
    reason: str = ""
    latency_ms: int = 0


@dataclass(frozen=True)
class AIRouteOutcome:
    """Non-throwing route result for durable queue integrations."""

    status: str
    result: AIResult | None = None
    error_type: str = ""
    retry_after_seconds: float | None = None
    attempts: Sequence[AttemptRecord] = field(default_factory=tuple)
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
    task_type: str = "general"
    quality_preference: str = "balanced"
    capability_overrides: Mapping[tuple[str, str], ModelCapability] = field(default_factory=dict)
    max_estimated_input_tokens: int | None = None
    max_estimated_output_tokens: int | None = None
    reject_over_budget: bool = True
    backoff_base_seconds: float = 15.0
    backoff_max_seconds: float = 3600.0
    backoff_jitter_ratio: float = 0.0
    routing_mode: str = "balanced"
    score_weights: ScoreWeights | None = None


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

    def __init__(
        self,
        providers: Sequence[ProviderBase | ProviderCandidate],
        policy: RouterPolicy | None = None,
        state_store: RouterStateStore | None = None,
        quota_tracker: InMemoryQuotaTracker | None = None,
        free_tier_catalog: FreeTierCatalog | None = None,
        free_tier_usage_tracker: LocalFreeTierUsageTracker | None = None,
    ) -> None:
        self.policy = policy or RouterPolicy()
        self.state_store = state_store or MemoryStateStore()
        self.quota_tracker = quota_tracker or InMemoryQuotaTracker()
        self.free_tier_catalog = free_tier_catalog or DEFAULT_FREE_TIER_CATALOG
        self.free_tier_usage_tracker = free_tier_usage_tracker or LocalFreeTierUsageTracker()
        self.providers = self._normalize(providers)

    def free_tier_budget(self) -> FreeTierBudget:
        """Return an audited headline using explicitly estimated local usage."""

        return self.free_tier_catalog.budget(
            usage_by_pool=self.free_tier_usage_tracker.snapshot(),
            usage_scope="estimated_local",
        )

    def route_outcome(self, request: AIRequest) -> AIRouteOutcome:
        """Route a request without raising for ordinary retry-later outcomes."""

        try:
            result = self.route(request)
        except RouterError as exc:
            attempts = tuple(self._attempt_record(attempt) for attempt in exc.attempts)
            if exc.attempts and all(attempt.get("reason") == "budget_exceeded" for attempt in exc.attempts):
                return AIRouteOutcome(
                    status="failed",
                    error_type="budget_exceeded",
                    attempts=attempts,
                )
            retry_after = self._next_retry_after_seconds()
            retryable_reasons = self._retryable_reasons()
            reasons = {attempt.reason for attempt in attempts if attempt.reason}
            status = "retry_later" if retry_after is not None or (reasons and reasons.issubset(retryable_reasons)) else "failed"
            return AIRouteOutcome(
                status=status,
                error_type="all_providers_exhausted" if status == "retry_later" else "route_failed",
                retry_after_seconds=retry_after,
                attempts=attempts,
            )
        return AIRouteOutcome(status="success", result=result, attempts=tuple(self._attempt_record(attempt) for attempt in result.metadata.get("attempts", [])))

    async def aroute_outcome(self, request: AIRequest) -> AIRouteOutcome:
        """Async route outcome API.

        Providers may implement a native `agenerate` coroutine. Providers without
        native async support are executed in a worker thread to avoid blocking the
        caller's event loop.
        """

        try:
            result = await self.aroute(request)
        except RouterError as exc:
            attempts = tuple(self._attempt_record(attempt) for attempt in exc.attempts)
            if exc.attempts and all(attempt.get("reason") == "budget_exceeded" for attempt in exc.attempts):
                return AIRouteOutcome(
                    status="failed",
                    error_type="budget_exceeded",
                    attempts=attempts,
                )
            retry_after = self._next_retry_after_seconds()
            retryable_reasons = self._retryable_reasons()
            reasons = {attempt.reason for attempt in attempts if attempt.reason}
            status = "retry_later" if retry_after is not None or (reasons and reasons.issubset(retryable_reasons)) else "failed"
            return AIRouteOutcome(
                status=status,
                error_type="all_providers_exhausted" if status == "retry_later" else "route_failed",
                retry_after_seconds=retry_after,
                attempts=attempts,
            )
        return AIRouteOutcome(status="success", result=result, attempts=tuple(self._attempt_record(attempt) for attempt in result.metadata.get("attempts", [])))

    def stream(self, request: AIRequest):
        """Yield text chunks, falling back to a single full-result chunk."""

        stream_generate = self._first_stream_provider_method("stream_generate")
        if callable(stream_generate):
            yield from stream_generate(request)
            return
        result = self.route(request)
        yield AIStreamChunk(text=result.text, provider_name=result.provider_name, metadata=sanitize_mapping(result.metadata), done=True)

    async def astream(self, request: AIRequest):
        """Async stream text chunks, falling back to the async route result."""

        astream_generate = self._first_stream_provider_method("astream_generate")
        if callable(astream_generate):
            async for chunk in astream_generate(request):
                yield chunk
            return
        result = await self.aroute(request)
        yield AIStreamChunk(text=result.text, provider_name=result.provider_name, metadata=sanitize_mapping(result.metadata), done=True)

    def _first_stream_provider_method(self, method_name: str) -> Any:
        for candidate in self._ordered_candidates():
            method = getattr(candidate.provider, method_name, None)
            if callable(method):
                return method
        return None

    async def aroute(self, request: AIRequest) -> AIResult:
        """Async variant of `route()` with native async provider support."""

        safe_metadata = sanitize_mapping(request.metadata)
        LOGGER.info("Async routing AI request metadata=%s", safe_metadata)

        budget_error = self._budget_error(request)
        if budget_error:
            raise RouterError("Request exceeded configured router budget", attempts=[self._budget_attempt(budget_error)])

        attempts: list[dict[str, Any]] = []
        estimated_tokens = self._estimated_tokens(request)
        task_type = self._effective_task_type(request)
        for base_candidate in self._ordered_candidates(request):
            provider = base_candidate.provider
            skip_reason = self._skip_reason(provider)
            if skip_reason:
                attempts.append(self._attempt(provider, base_candidate, "skipped", reason=skip_reason))
                continue
            for candidate in self._candidate_list(provider, base_candidate)[: max(1, self.policy.max_attempts)]:
                if not provider.health.is_available():
                    attempts.append(self._attempt(provider, candidate, "skipped", reason="cooldown"))
                    continue
                candidate_state = self.state_store.get_key_model_state(provider.name, candidate.model, candidate.key_id)
                if not candidate_state.is_available():
                    attempts.append(self._attempt(provider, candidate, "skipped", reason="key_cooldown"))
                    continue
                quota_check = self.quota_tracker.reserve(provider.name, candidate.model, candidate.key_id, estimated_tokens=estimated_tokens)
                if quota_check.decision != QuotaDecision.ALLOW:
                    attempts.append(self._attempt(provider, candidate, "skipped", reason=f"quota_{quota_check.decision.value}"))
                    continue
                started = time.time()
                try:
                    agenerate = getattr(provider, "agenerate", None)
                    result = await agenerate(request, candidate) if callable(agenerate) else await asyncio.to_thread(provider.generate, request, candidate)
                    latency_ms = round((time.time() - started) * 1000)
                    self._mark_success(provider, latency_ms)
                    self.state_store.record_success(provider.name, candidate.model, candidate.key_id, latency_ms=latency_ms)
                    self.quota_tracker.record_success(provider.name, candidate.model, candidate.key_id)
                    self._reconcile_usage(candidate, result, estimated_tokens)
                    self._record_free_tier_usage(candidate, result, estimated_tokens)
                    success_attempt = self._attempt(provider, candidate, "success", latency_ms=latency_ms)
                    attempts.append(success_attempt)
                    merged_metadata = self._result_metadata(result, candidate, task_type)
                    merged_metadata.setdefault("attempts", attempts)
                    return AIResult(text=result.text, provider_name=result.provider_name or provider.name, metadata=merged_metadata)
                except ProviderError as exc:
                    latency_ms = round((time.time() - started) * 1000)
                    error_type = classify_error(exc, status_code=getattr(exc, "status_code", None), response_body=getattr(exc, "response_body", None))
                    retry_after = extract_retry_after_seconds(exc) or extract_retry_after_seconds({"retry_after": getattr(exc, "retry_after", None)})
                    failure_streak = candidate_state.failure_streak + 1
                    cooldown_seconds = self._cooldown_seconds_for_error(error_type, retry_after, failure_streak=failure_streak)
                    cooldown_until = time.time() + cooldown_seconds if cooldown_seconds > 0 else 0.0
                    provider_has_key_pool = len(getattr(provider, "api_keys", []) or []) > 1
                    self._mark_failure(provider, error_type, str(exc), latency_ms, retry_after, provider_scope=not provider_has_key_pool)
                    self.state_store.record_failure(provider.name, candidate.model, candidate.key_id, error_type=error_type, error_message=str(exc), latency_ms=latency_ms, cooldown_until=cooldown_until, disable=error_type == "auth_failure")
                    self.quota_tracker.record_failure(provider.name, candidate.model, candidate.key_id, error_type=error_type)
                    attempts.append(self._attempt(provider, candidate, "failed", reason=error_type, latency_ms=latency_ms))
                finally:
                    self.quota_tracker.release(provider.name, candidate.model, candidate.key_id)
        detail = ", ".join(f"{a['provider']}:{a.get('reason', a['status'])}" for a in attempts) or "no eligible providers"
        raise RouterError(f"No provider returned a result: {detail}", attempts=attempts)

    def export_state(self) -> dict[str, Any]:
        """Export safe dashboard state for providers, models, and key IDs."""

        now = time.time()
        candidates: list[dict[str, Any]] = []
        summary = {"healthy": 0, "cooldown": 0, "dead": 0, "unknown": 0, "total": 0, "next_retry_after_seconds": None}
        next_retries: list[float] = []
        for state in self.state_store.list_states():
            retry_after = max(0.0, state.cooldown_until - now) if state.cooldown_until > now else None
            status = state.status or "unknown"
            if not state.enabled:
                status = "dead"
            elif retry_after is not None:
                status = "cooldown"
            elif status not in {"healthy", "cooldown", "dead"}:
                status = "unknown"
            if retry_after is not None:
                next_retries.append(retry_after)
            summary[status] = int(summary.get(status, 0)) + 1
            summary["total"] = int(summary["total"] or 0) + 1
            candidates.append(
                sanitize_mapping(
                    {
                        "provider": state.provider,
                        "model": state.model,
                        "key_id": state.key_id,
                        "status": status,
                        "enabled": state.enabled,
                        "cooldown_until": state.cooldown_until,
                        "retry_after_seconds": retry_after,
                        "last_error_type": state.last_error_type,
                        "success_count": state.success_count,
                        "failure_count": state.failure_count,
                        "failure_streak": state.failure_streak,
                        "last_latency_ms": state.last_latency_ms,
                        "last_success_at": state.last_success_at,
                        "last_failure_at": state.last_failure_at,
                    }
                )
            )
        if next_retries:
            summary["next_retry_after_seconds"] = min(next_retries)
        return {"summary": summary, "candidates": candidates}

    def route(self, request: AIRequest) -> AIResult:
        safe_metadata = sanitize_mapping(request.metadata)
        LOGGER.info("Routing AI request metadata=%s", safe_metadata)

        budget_error = self._budget_error(request)
        if budget_error:
            raise RouterError("Request exceeded configured router budget", attempts=[self._budget_attempt(budget_error)])

        attempts: list[dict[str, Any]] = []
        estimated_tokens = self._estimated_tokens(request)
        task_type = self._effective_task_type(request)
        for base_candidate in self._ordered_candidates(request):
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
                candidate_state = self.state_store.get_key_model_state(provider.name, candidate.model, candidate.key_id)
                if not candidate_state.is_available():
                    attempts.append(self._attempt(provider, candidate, "skipped", reason="key_cooldown"))
                    continue
                quota_check = self.quota_tracker.reserve(provider.name, candidate.model, candidate.key_id, estimated_tokens=estimated_tokens)
                if quota_check.decision != QuotaDecision.ALLOW:
                    attempts.append(self._attempt(provider, candidate, "skipped", reason=f"quota_{quota_check.decision.value}"))
                    continue
                started = time.time()
                try:
                    result = provider.generate(request, candidate)
                    latency_ms = round((time.time() - started) * 1000)
                    self._mark_success(provider, latency_ms)
                    self.state_store.record_success(provider.name, candidate.model, candidate.key_id, latency_ms=latency_ms)
                    self.quota_tracker.record_success(provider.name, candidate.model, candidate.key_id)
                    self._reconcile_usage(candidate, result, estimated_tokens)
                    self._record_free_tier_usage(candidate, result, estimated_tokens)
                    success_attempt = self._attempt(provider, candidate, "success", latency_ms=latency_ms)
                    attempts.append(success_attempt)
                    merged_metadata = self._result_metadata(result, candidate, task_type)
                    merged_metadata.setdefault("attempts", attempts)
                    return AIResult(text=result.text, provider_name=result.provider_name or provider.name, metadata=merged_metadata)
                except ProviderError as exc:
                    latency_ms = round((time.time() - started) * 1000)
                    error_type = classify_error(exc, status_code=getattr(exc, "status_code", None), response_body=getattr(exc, "response_body", None))
                    retry_after = extract_retry_after_seconds(exc) or extract_retry_after_seconds({"retry_after": getattr(exc, "retry_after", None)})
                    failure_streak = candidate_state.failure_streak + 1
                    cooldown_seconds = self._cooldown_seconds_for_error(error_type, retry_after, failure_streak=failure_streak)
                    cooldown_until = time.time() + cooldown_seconds if cooldown_seconds > 0 else 0.0
                    provider_has_key_pool = len(getattr(provider, "api_keys", []) or []) > 1
                    self._mark_failure(provider, error_type, str(exc), latency_ms, retry_after, provider_scope=not provider_has_key_pool)
                    self.state_store.record_failure(
                        provider.name,
                        candidate.model,
                        candidate.key_id,
                        error_type=error_type,
                        error_message=str(exc),
                        latency_ms=latency_ms,
                        cooldown_until=cooldown_until,
                        disable=error_type == "auth_failure",
                    )
                    self.quota_tracker.record_failure(provider.name, candidate.model, candidate.key_id, error_type=error_type)
                    attempts.append(self._attempt(provider, candidate, "failed", reason=error_type, latency_ms=latency_ms))
                    LOGGER.warning("Provider %s failed with %s; trying next candidate", provider.name, error_type)
                finally:
                    self.quota_tracker.release(provider.name, candidate.model, candidate.key_id)

        detail = ", ".join(f"{a['provider']}:{a.get('reason', a['status'])}" for a in attempts) or "no eligible providers"
        raise RouterError(f"No provider returned a result: {detail}", attempts=attempts)

    @staticmethod
    def _retryable_reasons() -> set[str]:
        return {
            "cooldown",
            "key_cooldown",
            "quota_throttle",
            "quota_rate_limit",
            "quota_exhausted_daily",
            "insufficient_quota",
            "billing_limit",
            "timeout",
            "transport_error",
            "unknown_transport_error",
            "provider_5xx",
        }


    def _ordered_candidates(self, request: AIRequest | None = None) -> list[ProviderCandidate]:
        allowed = set(self.policy.allowed_providers or [item.provider.name for item in self.providers])
        avoid = set(self.policy.avoid_providers)
        last_resort = set(self.policy.last_resort_providers)
        candidates = [item for item in self.providers if item.provider.name in allowed and item.provider.name not in avoid]
        task_type = self._effective_task_type(request) if request is not None else self.policy.task_type
        return sorted(candidates, key=lambda item: (item.provider.name in last_resort, -self._routing_score(item, task_type).total, item.priority))

    def _effective_task_type(self, request: AIRequest | None) -> str:
        if request is not None and isinstance(request.metadata, Mapping):
            task = str(request.metadata.get("task_type", "") or "").strip()
            if task:
                return task
        return self.policy.task_type or "general"

    def _candidate_task_score(self, candidate: ProviderCandidate, task_type: str) -> int:
        capability = self._candidate_capability(candidate)
        return score_candidate_for_task(capability, task_type, self.policy.quality_preference)

    def _candidate_capability(self, candidate: ProviderCandidate) -> ModelCapability:
        model = candidate.model
        if not model:
            provider_candidates = candidate.provider.iter_candidates()
            model = provider_candidates[0].model if provider_candidates else ""
        return capability_for(candidate.provider.name, model, self.policy.capability_overrides)

    def _routing_score(self, candidate: ProviderCandidate, task_type: str) -> RoutingScore:
        capability = self._candidate_capability(candidate)
        provider = candidate.provider
        quota_headroom = self.quota_tracker.headroom(provider.name, capability.model, candidate.key_id)
        plan = self.free_tier_catalog.plan_for(provider.name, capability.model)
        free_tier_headroom = 0.0
        if plan is not None and plan.is_routing_eligible():
            free_tier_headroom = self.free_tier_catalog.routing_headroom(
                provider.name,
                capability.model,
                usage_by_pool=self.free_tier_usage_tracker.snapshot(),
            )
        return score_routing_candidate(
            task_score=score_candidate_for_task(capability, task_type, self.policy.quality_preference),
            cost_tier=capability.cost_tier,
            success_count=provider.health.success_count,
            failure_count=provider.health.failure_count,
            latency_ms=provider.health.last_latency_ms,
            quota_headroom=quota_headroom,
            free_tier_headroom=free_tier_headroom,
            priority=candidate.priority,
            mode=self.policy.routing_mode,
            weights=self.policy.score_weights,
        )

    def _budget_error(self, request: AIRequest) -> str:
        if not self.policy.reject_over_budget or not isinstance(request.metadata, Mapping):
            return ""
        input_limit = self.policy.max_estimated_input_tokens
        output_limit = self.policy.max_estimated_output_tokens
        input_tokens = _optional_int(request.metadata.get("estimated_input_tokens"))
        output_tokens = _optional_int(request.metadata.get("estimated_output_tokens"))
        if input_limit is not None and input_tokens is not None and input_tokens > input_limit:
            return "estimated_input_tokens"
        if output_limit is not None and output_tokens is not None and output_tokens > output_limit:
            return "estimated_output_tokens"
        return ""

    @staticmethod
    def _estimated_tokens(request: AIRequest) -> int:
        if not isinstance(request.metadata, Mapping):
            return 0
        input_tokens = _optional_int(request.metadata.get("estimated_input_tokens")) or 0
        output_tokens = _optional_int(request.metadata.get("estimated_output_tokens")) or 0
        explicit_total = _optional_int(request.metadata.get("estimated_total_tokens"))
        return max(0, explicit_total if explicit_total is not None else input_tokens + output_tokens)

    def _reconcile_usage(self, candidate: ProviderCandidate, result: AIResult, estimated_tokens: int) -> None:
        usage = normalize_token_usage(result.metadata.get("token_usage") if isinstance(result.metadata, Mapping) else None)
        if usage.total_tokens > 0:
            self.quota_tracker.reconcile_tokens(
                candidate.provider.name,
                candidate.model,
                candidate.key_id,
                estimated_tokens=estimated_tokens,
                actual_tokens=usage.total_tokens,
            )

    def _record_free_tier_usage(self, candidate: ProviderCandidate, result: AIResult, estimated_tokens: int) -> None:
        plan = self.free_tier_catalog.plan_for(candidate.provider.name, candidate.model)
        if plan is None or not plan.pool_id:
            return
        usage = normalize_token_usage(result.metadata.get("token_usage") if isinstance(result.metadata, Mapping) else None)
        tokens = usage.total_tokens if usage.total_tokens > 0 else max(0, int(estimated_tokens or 0))
        self.free_tier_usage_tracker.record(plan.pool_id, tokens)

    def _result_metadata(self, result: AIResult, candidate: ProviderCandidate, task_type: str) -> dict[str, Any]:
        metadata = dict(result.metadata)
        capability = capability_for(candidate.provider.name, candidate.model, self.policy.capability_overrides)
        usage = normalize_token_usage(metadata.get("token_usage"))
        metadata["routing"] = self._routing_score(candidate, task_type).to_dict()
        metadata["catalog_provenance"] = {
            "provider": capability.provider,
            "model": capability.model,
            "source_url": capability.source_url,
            "verified_at": capability.verified_at,
            "confidence": capability.confidence,
            "terms_note": capability.terms_note,
        }
        plan = self.free_tier_catalog.plan_for(candidate.provider.name, candidate.model)
        if plan is not None:
            metadata["free_tier"] = {
                "pool_id": plan.pool_id,
                "status": plan.status,
                "routing_eligible": plan.is_routing_eligible(),
                "monthly_tokens": plan.monthly_tokens() if plan.is_auditable() else None,
                "usage_scope": "estimated_local",
                "source_url": plan.source_url,
                "verified_at": plan.verified_at,
            }
        metadata["cost_estimate"] = estimate_cost(usage, capability).to_dict()
        return sanitize_mapping(metadata)

    @staticmethod
    def _budget_attempt(field: str) -> dict[str, Any]:
        return {
            "provider": "router",
            "status": "failed",
            "reason": "budget_exceeded",
            "error_type": "budget_exceeded",
            "budget_field": field,
        }

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
    def _attempt_record(attempt: Mapping[str, Any]) -> AttemptRecord:
        return AttemptRecord(
            provider=str(attempt.get("provider", "")),
            status=str(attempt.get("status", "")),
            is_cloud=bool(attempt.get("is_cloud", True)),
            model=str(attempt.get("model", "")),
            key_index=int(attempt.get("key_index", -1)),
            key_id=str(attempt.get("key_id", "")),
            reason=str(attempt.get("reason", "")),
            latency_ms=int(attempt.get("latency_ms", 0)),
        )

    def _next_retry_after_seconds(self) -> float | None:
        now = time.time()
        candidates: list[float] = []
        for state in self.state_store.list_states():
            if state.enabled and state.cooldown_until > now:
                candidates.append(state.cooldown_until - now)
        for candidate in self.providers:
            provider_cooldown = candidate.provider.health.cooldown_until
            if candidate.provider.health.enabled and provider_cooldown > now:
                candidates.append(provider_cooldown - now)
        if not candidates:
            return None
        return max(0.0, min(candidates))

    @staticmethod
    def _mark_success(provider: ProviderBase, latency_ms: int) -> None:
        provider.health.enabled = True
        provider.health.cooldown_until = 0.0
        provider.health.last_error = None
        provider.health.last_error_type = ""
        provider.health.consecutive_failures = 0
        provider.health.success_count += 1
        provider.health.last_latency_ms = latency_ms

    def _mark_failure(
        self,
        provider: ProviderBase,
        error_type: str,
        message: str,
        latency_ms: int,
        retry_after_seconds: float | None,
        *,
        provider_scope: bool = True,
    ) -> None:
        provider.health.last_error = message
        provider.health.last_error_type = error_type
        provider.health.consecutive_failures += 1
        provider.health.failure_count += 1
        provider.health.last_latency_ms = latency_ms
        if not provider_scope:
            return
        if error_type == "auth_failure":
            provider.health.enabled = False
        cooldown = self._cooldown_seconds_for_error(error_type, retry_after_seconds, failure_streak=provider.health.consecutive_failures)
        if cooldown > 0:
            provider.health.cooldown_until = time.time() + cooldown

    def _cooldown_seconds_for_error(self, error_type: str, retry_after_seconds: float | None, *, failure_streak: int = 1) -> float:
        if error_type in {"quota_rate_limit", "quota_exhausted_daily", "insufficient_quota", "billing_limit"}:
            base = float(retry_after_seconds or self.policy.quota_cooldown_seconds)
        elif error_type in {"timeout", "transport_error", "unknown_transport_error", "provider_5xx"}:
            base = float(self.policy.backoff_base_seconds or self.policy.transient_cooldown_seconds)
        else:
            return 0.0
        streak = max(1, int(failure_streak or 1))
        exponential = base * (2 ** (streak - 1))
        capped = min(float(self.policy.backoff_max_seconds), exponential)
        if retry_after_seconds is not None:
            capped = max(capped, float(retry_after_seconds))
        jitter_ratio = max(0.0, float(self.policy.backoff_jitter_ratio or 0.0))
        jitter = capped * min(jitter_ratio, 1.0) * 0.5
        return max(1.0, capped + jitter)

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
    if any(token in detail for token in BILLING_LIMIT_HINTS):
        return "billing_limit"
    if any(token in detail for token in INSUFFICIENT_QUOTA_HINTS):
        return "insufficient_quota"
    if any(token in detail for token in DAILY_QUOTA_HINTS):
        return "quota_exhausted_daily"
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


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
