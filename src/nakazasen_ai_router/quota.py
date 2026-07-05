"""Provider quota and capacity policy primitives."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence


class QuotaDecision(str, Enum):
    ALLOW = "allow"
    THROTTLE = "throttle"
    BLOCK = "block"


@dataclass(frozen=True)
class CapacityPolicy:
    requests_per_minute: int | None = None
    tokens_per_minute: int | None = None
    requests_per_day: int | None = None
    max_concurrency: int | None = None
    cost_tier: str = "unknown"
    fallback_priority: int = 100
    enabled: bool = True


@dataclass(frozen=True)
class ProviderQuotaProfile:
    provider: str
    model: str = ""
    key_id: str = ""
    policy: CapacityPolicy = field(default_factory=CapacityPolicy)


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


@dataclass
class _UsageBucket:
    minute_start: float = 0.0
    day_start: float = 0.0
    requests_last_minute: int = 0
    tokens_last_minute: int = 0
    requests_today: int = 0
    in_flight: int = 0
    last_error_type: str = ""


class InMemoryQuotaTracker:
    """Dependency-free quota tracker for process-local capacity decisions."""

    def __init__(self, profiles: Iterable[ProviderQuotaProfile] = ()) -> None:
        self._profiles = list(profiles)
        self._usage: dict[tuple[str, str, str], _UsageBucket] = {}

    def check(self, provider: str, model: str = "", key_id: str = "", *, estimated_tokens: int = 0, now: float | None = None) -> QuotaCheck:
        now = time.time() if now is None else now
        profile = self._match_profile(provider, model, key_id)
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
            return QuotaCheck(QuotaDecision.BLOCK, retry_after_seconds=86400.0, reason="daily_limit")
        if policy.requests_per_minute is not None and usage.requests_last_minute >= policy.requests_per_minute:
            return QuotaCheck(QuotaDecision.THROTTLE, retry_after_seconds=max(1.0, 60.0 - (now - usage.minute_start)), reason="rpm_limit")
        if policy.tokens_per_minute is not None and usage.tokens_last_minute + max(0, estimated_tokens) > policy.tokens_per_minute:
            return QuotaCheck(QuotaDecision.THROTTLE, retry_after_seconds=max(1.0, 60.0 - (now - usage.minute_start)), reason="tpm_limit")
        return QuotaCheck(QuotaDecision.ALLOW)

    def reserve(self, provider: str, model: str = "", key_id: str = "", *, estimated_tokens: int = 0, now: float | None = None) -> QuotaCheck:
        now = time.time() if now is None else now
        check = self.check(provider, model, key_id, estimated_tokens=estimated_tokens, now=now)
        if check.decision != QuotaDecision.ALLOW:
            return check
        profile = self._match_profile(provider, model, key_id)
        if profile is None:
            return check
        usage = self._bucket(self._usage_key(profile), now)
        self._roll_windows(usage, now)
        usage.requests_last_minute += 1
        usage.tokens_last_minute += max(0, estimated_tokens)
        usage.requests_today += 1
        usage.in_flight += 1
        return check

    def release(self, provider: str, model: str = "", key_id: str = "") -> None:
        profile = self._match_profile(provider, model, key_id)
        if profile is None:
            return
        usage = self._bucket(self._usage_key(profile), time.time())
        usage.in_flight = max(0, usage.in_flight - 1)

    def record_success(self, provider: str, model: str = "", key_id: str = "") -> None:
        profile = self._match_profile(provider, model, key_id)
        if profile is not None:
            self._bucket(self._usage_key(profile), time.time()).last_error_type = ""

    def record_failure(self, provider: str, model: str = "", key_id: str = "", *, error_type: str = "") -> None:
        profile = self._match_profile(provider, model, key_id)
        if profile is not None:
            self._bucket(self._usage_key(profile), time.time()).last_error_type = _clean_error_type(error_type)

    def snapshot(self, *, now: float | None = None) -> dict[str, Any]:
        now = time.time() if now is None else now
        profiles = []
        for profile in self._profiles:
            usage = self._bucket(self._usage_key(profile), now)
            self._roll_windows(usage, now)
            profiles.append({
                "provider": profile.provider,
                "model": profile.model,
                "has_key_scope": bool(profile.key_id),
                "policy": {
                    "requests_per_minute": profile.policy.requests_per_minute,
                    "tokens_per_minute": profile.policy.tokens_per_minute,
                    "requests_per_day": profile.policy.requests_per_day,
                    "max_concurrency": profile.policy.max_concurrency,
                    "cost_tier": profile.policy.cost_tier,
                    "fallback_priority": profile.policy.fallback_priority,
                    "enabled": profile.policy.enabled,
                },
                "usage": UsageSnapshot(
                    requests_last_minute=usage.requests_last_minute,
                    tokens_last_minute=usage.tokens_last_minute,
                    requests_today=usage.requests_today,
                    in_flight=usage.in_flight,
                    last_error_type=usage.last_error_type,
                ).__dict__,
            })
        return {"profiles": profiles}

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
