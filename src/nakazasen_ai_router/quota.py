"""Provider quota and capacity policy primitives."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Any, Iterable, Mapping, Sequence


class QuotaDecision(str, Enum):
    ALLOW = "allow"
    THROTTLE = "throttle"
    BLOCK = "block"


@dataclass(frozen=True)
class QuotaWindow:
    """Additional fixed capacity window for requests and/or tokens."""

    name: str
    seconds: float
    request_limit: int | None = None
    token_limit: int | None = None


@dataclass(frozen=True)
class CapacityPolicy:
    requests_per_minute: int | None = None
    tokens_per_minute: int | None = None
    requests_per_day: int | None = None
    max_concurrency: int | None = None
    cost_tier: str = "unknown"
    fallback_priority: int = 100
    enabled: bool = True
    flexible_windows: tuple[QuotaWindow, ...] = ()


@dataclass(frozen=True)
class ProviderQuotaProfile:
    provider: str
    model: str = ""
    key_id: str = ""
    policy: CapacityPolicy = field(default_factory=CapacityPolicy)
    pool_id: str = ""


@dataclass(frozen=True)
class QuotaCheck:
    decision: QuotaDecision
    retry_after_seconds: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class UsageSnapshot:
    requests_last_minute: int = 0
    tokens_last_minute: int = 0
    requests_today: int = 0
    in_flight: int = 0
    last_error_type: str = ""
    windows: Mapping[str, Mapping[str, int | float]] = field(default_factory=dict)


@dataclass
class _WindowUsage:
    start: float
    requests: int = 0
    tokens: int = 0


@dataclass
class _UsageBucket:
    minute_start: float = 0.0
    day_start: float = 0.0
    requests_last_minute: int = 0
    tokens_last_minute: int = 0
    requests_today: int = 0
    in_flight: int = 0
    last_error_type: str = ""
    windows: dict[tuple[str, float], _WindowUsage] = field(default_factory=dict)


class InMemoryQuotaTracker:
    """Thread-safe, process-local quota tracker with optional shared pools."""

    def __init__(self, profiles: Iterable[ProviderQuotaProfile] = ()) -> None:
        self._profiles = list(profiles)
        self._usage: dict[tuple[str, str, str], _UsageBucket] = {}
        self._lock = RLock()

    def check(self, provider: str, model: str = "", key_id: str = "", *, estimated_tokens: int = 0, now: float | None = None) -> QuotaCheck:
        current = time.time() if now is None else now
        with self._lock:
            profile = self._match_profile(provider, model, key_id)
            return self._check_locked(profile, estimated_tokens=max(0, estimated_tokens), now=current)

    def reserve(self, provider: str, model: str = "", key_id: str = "", *, estimated_tokens: int = 0, now: float | None = None) -> QuotaCheck:
        current = time.time() if now is None else now
        estimated = max(0, int(estimated_tokens or 0))
        with self._lock:
            profile = self._match_profile(provider, model, key_id)
            check = self._check_locked(profile, estimated_tokens=estimated, now=current)
            if check.decision != QuotaDecision.ALLOW or profile is None:
                return check
            usage = self._bucket(self._usage_key(profile), current)
            self._roll_windows(usage, current)
            usage.requests_last_minute += 1
            usage.tokens_last_minute += estimated
            usage.requests_today += 1
            usage.in_flight += 1
            for window in profile.policy.flexible_windows:
                window_usage = self._window_usage(usage, window, current)
                window_usage.requests += 1
                window_usage.tokens += estimated
            return check

    def release(self, provider: str, model: str = "", key_id: str = "") -> None:
        with self._lock:
            profile = self._match_profile(provider, model, key_id)
            if profile is None:
                return
            usage = self._bucket(self._usage_key(profile), time.time())
            usage.in_flight = max(0, usage.in_flight - 1)

    def reconcile_tokens(self, provider: str, model: str = "", key_id: str = "", *, estimated_tokens: int = 0, actual_tokens: int = 0, now: float | None = None) -> None:
        """Replace reserved token estimates with provider-reported totals."""

        current = time.time() if now is None else now
        delta = max(0, int(actual_tokens or 0)) - max(0, int(estimated_tokens or 0))
        with self._lock:
            profile = self._match_profile(provider, model, key_id)
            if profile is None:
                return
            usage = self._bucket(self._usage_key(profile), current)
            self._roll_windows(usage, current)
            usage.tokens_last_minute = max(0, usage.tokens_last_minute + delta)
            for window in profile.policy.flexible_windows:
                window_usage = self._window_usage(usage, window, current)
                window_usage.tokens = max(0, window_usage.tokens + delta)

    def headroom(self, provider: str, model: str = "", key_id: str = "", *, now: float | None = None) -> float:
        """Return bounded remaining capacity (0..1) for weighted routing."""

        current = time.time() if now is None else now
        with self._lock:
            profile = self._match_profile(provider, model, key_id)
            if profile is None:
                return 1.0
            if not profile.policy.enabled:
                return 0.0
            usage = self._bucket(self._usage_key(profile), current)
            self._roll_windows(usage, current)
            ratios: list[float] = []
            self._append_ratio(ratios, profile.policy.max_concurrency, usage.in_flight)
            self._append_ratio(ratios, profile.policy.requests_per_day, usage.requests_today)
            self._append_ratio(ratios, profile.policy.requests_per_minute, usage.requests_last_minute)
            self._append_ratio(ratios, profile.policy.tokens_per_minute, usage.tokens_last_minute)
            for window in profile.policy.flexible_windows:
                window_usage = self._window_usage(usage, window, current)
                self._append_ratio(ratios, window.request_limit, window_usage.requests)
                self._append_ratio(ratios, window.token_limit, window_usage.tokens)
            return min(ratios, default=1.0)

    def record_success(self, provider: str, model: str = "", key_id: str = "") -> None:
        with self._lock:
            profile = self._match_profile(provider, model, key_id)
            if profile is not None:
                self._bucket(self._usage_key(profile), time.time()).last_error_type = ""

    def record_failure(self, provider: str, model: str = "", key_id: str = "", *, error_type: str = "") -> None:
        with self._lock:
            profile = self._match_profile(provider, model, key_id)
            if profile is not None:
                self._bucket(self._usage_key(profile), time.time()).last_error_type = _clean_error_type(error_type)

    def snapshot(self, *, now: float | None = None) -> dict[str, Any]:
        current = time.time() if now is None else now
        with self._lock:
            profiles = []
            for profile in self._profiles:
                usage = self._bucket(self._usage_key(profile), current)
                self._roll_windows(usage, current)
                windows: dict[str, Mapping[str, int | float]] = {}
                for window in profile.policy.flexible_windows:
                    window_usage = self._window_usage(usage, window, current)
                    label = f"{window.name}:{float(window.seconds):g}s"
                    windows[label] = {
                        "seconds": float(window.seconds),
                        "requests": window_usage.requests,
                        "tokens": window_usage.tokens,
                    }
                profiles.append({
                    "provider": profile.provider,
                    "model": profile.model,
                    "pool_id": profile.pool_id,
                    "has_key_scope": bool(profile.key_id),
                    "policy": {
                        "requests_per_minute": profile.policy.requests_per_minute,
                        "tokens_per_minute": profile.policy.tokens_per_minute,
                        "requests_per_day": profile.policy.requests_per_day,
                        "max_concurrency": profile.policy.max_concurrency,
                        "cost_tier": profile.policy.cost_tier,
                        "fallback_priority": profile.policy.fallback_priority,
                        "enabled": profile.policy.enabled,
                        "flexible_windows": [window.__dict__ for window in profile.policy.flexible_windows],
                    },
                    "usage": UsageSnapshot(
                        requests_last_minute=usage.requests_last_minute,
                        tokens_last_minute=usage.tokens_last_minute,
                        requests_today=usage.requests_today,
                        in_flight=usage.in_flight,
                        last_error_type=usage.last_error_type,
                        windows=windows,
                    ).__dict__,
                })
            return {"scope": "process_local", "profiles": profiles}

    def _check_locked(self, profile: ProviderQuotaProfile | None, *, estimated_tokens: int, now: float) -> QuotaCheck:
        if profile is None:
            return QuotaCheck(QuotaDecision.ALLOW)
        policy = profile.policy
        if not policy.enabled:
            return QuotaCheck(QuotaDecision.BLOCK, reason="disabled")
        usage = self._bucket(self._usage_key(profile), now)
        self._roll_windows(usage, now)
        if policy.max_concurrency is not None and usage.in_flight >= policy.max_concurrency:
            return QuotaCheck(QuotaDecision.THROTTLE, retry_after_seconds=1.0, reason="concurrency_limit")
        if policy.requests_per_day is not None and usage.requests_today >= policy.requests_per_day:
            return QuotaCheck(QuotaDecision.BLOCK, retry_after_seconds=max(1.0, _day_start(now) + 86400.0 - now), reason="daily_limit")
        if policy.requests_per_minute is not None and usage.requests_last_minute >= policy.requests_per_minute:
            return QuotaCheck(QuotaDecision.THROTTLE, retry_after_seconds=max(1.0, 60.0 - (now - usage.minute_start)), reason="rpm_limit")
        if policy.tokens_per_minute is not None and usage.tokens_last_minute + estimated_tokens > policy.tokens_per_minute:
            return QuotaCheck(QuotaDecision.THROTTLE, retry_after_seconds=max(1.0, 60.0 - (now - usage.minute_start)), reason="tpm_limit")
        for window in policy.flexible_windows:
            window_usage = self._window_usage(usage, window, now)
            retry_after = max(1.0, float(window.seconds) - (now - window_usage.start))
            if window.request_limit is not None and window_usage.requests >= window.request_limit:
                return QuotaCheck(QuotaDecision.THROTTLE, retry_after_seconds=retry_after, reason=f"window_{window.name}_requests")
            if window.token_limit is not None and window_usage.tokens + estimated_tokens > window.token_limit:
                return QuotaCheck(QuotaDecision.THROTTLE, retry_after_seconds=retry_after, reason=f"window_{window.name}_tokens")
        return QuotaCheck(QuotaDecision.ALLOW)

    def _match_profile(self, provider: str, model: str, key_id: str) -> ProviderQuotaProfile | None:
        candidates = [
            (provider, model, key_id),
            (provider, model, ""),
            (provider, "", ""),
        ]
        for candidate in candidates:
            for profile in self._profiles:
                if (profile.provider, profile.model, profile.key_id) == candidate:
                    return profile
        return None

    def _bucket(self, key: tuple[str, str, str], now: float) -> _UsageBucket:
        if key not in self._usage:
            self._usage[key] = _UsageBucket(minute_start=now, day_start=_day_start(now))
        return self._usage[key]

    @staticmethod
    def _usage_key(profile: ProviderQuotaProfile) -> tuple[str, str, str]:
        if profile.pool_id:
            return ("@pool", profile.pool_id, "")
        return (profile.provider, profile.model, profile.key_id)

    @staticmethod
    def _roll_windows(usage: _UsageBucket, now: float) -> None:
        if now - usage.minute_start >= 60:
            usage.minute_start = now
            usage.requests_last_minute = 0
            usage.tokens_last_minute = 0
        current_day = _day_start(now)
        if current_day > usage.day_start:
            usage.day_start = current_day
            usage.requests_today = 0

    @staticmethod
    def _window_usage(usage: _UsageBucket, window: QuotaWindow, now: float) -> _WindowUsage:
        seconds = float(window.seconds)
        if seconds <= 0:
            raise ValueError("QuotaWindow.seconds must be greater than zero")
        key = (str(window.name), seconds)
        item = usage.windows.get(key)
        if item is None or now - item.start >= seconds:
            item = _WindowUsage(start=now)
            usage.windows[key] = item
        return item

    @staticmethod
    def _append_ratio(ratios: list[float], limit: int | None, used: int) -> None:
        if limit is None:
            return
        if limit <= 0:
            ratios.append(0.0)
            return
        ratios.append(min(1.0, max(0.0, (limit - max(0, used)) / limit)))


def sort_profiles_for_fallback(profiles: Sequence[ProviderQuotaProfile]) -> list[ProviderQuotaProfile]:
    cost_order = {"free": 0, "cheap": 1, "standard": 2, "premium": 3, "unknown": 4}
    return sorted(
        profiles,
        key=lambda item: (
            not item.policy.enabled,
            item.policy.fallback_priority,
            cost_order.get(item.policy.cost_tier, cost_order["unknown"]),
            item.provider,
            item.model,
            bool(item.key_id),
        ),
    )


def _day_start(now: float) -> float:
    return now - (now % 86400)


def _clean_error_type(error_type: str) -> str:
    blocked = ("api_key", "authorization", "bearer", "prompt", "payload", "secret", "token")
    text = " ".join(str(error_type or "").split())[:120]
    low = text.lower()
    if any(marker in low for marker in blocked):
        return "redacted"
    return text
