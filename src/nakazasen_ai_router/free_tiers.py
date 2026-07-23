"""Auditable free-tier catalog and pool-deduplicated budget calculations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from threading import RLock
import time
from typing import Any, Callable, Iterable, Mapping


@dataclass(frozen=True)
class FreeTierPlan:
    provider: str
    pool_id: str
    models: tuple[str, ...] = ()
    recurring_tokens: int | None = None
    period_days: int = 30
    signup_credit_tokens: int | None = None
    unlimited: bool = False
    requires_account: bool = True
    requires_card_or_topup: bool = False
    terms_warning: str = ""
    source_url: str = ""
    verified_at: str = ""
    confidence: str = "unknown"
    status: str = "uncertain"
    notes: str = ""

    def matches(self, provider: str, model: str = "") -> bool:
        return self.provider == provider and (not self.models or not model or model in self.models)

    def is_auditable(self, *, as_of: date | None = None, max_age_days: int = 45) -> bool:
        if self.status != "verified" or self.confidence not in {"high", "medium"} or not self.source_url or not self.pool_id:
            return False
        if self.recurring_tokens is None or self.recurring_tokens < 0 or self.period_days <= 0:
            return False
        try:
            verified = datetime.strptime(self.verified_at, "%Y-%m-%d").date()
        except ValueError:
            return False
        age = ((as_of or date.today()) - verified).days
        return 0 <= age <= max(0, max_age_days)

    def monthly_tokens(self) -> int | None:
        if self.recurring_tokens is None or self.period_days <= 0:
            return None
        return max(0, round(self.recurring_tokens * 30 / self.period_days))

    def is_routing_eligible(self, *, as_of: date | None = None, max_age_days: int = 45) -> bool:
        """Return whether this plan may receive a free-first routing preference.

        Dynamic rate-limited plans may qualify without contributing to the
        monthly token headline. Uncertain, stale, card-gated, or terms-flagged
        plans never receive this preference.
        """

        if self.status != "verified" or self.confidence not in {"high", "medium"}:
            return False
        if not self.source_url or not self.pool_id or self.requires_card_or_topup or self.terms_warning:
            return False
        try:
            verified = datetime.strptime(self.verified_at, "%Y-%m-%d").date()
        except ValueError:
            return False
        age = ((as_of or date.today()) - verified).days
        return 0 <= age <= max(0, max_age_days)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "pool_id": self.pool_id,
            "models": list(self.models),
            "recurring_tokens": self.recurring_tokens,
            "period_days": self.period_days,
            "signup_credit_tokens": self.signup_credit_tokens,
            "unlimited": self.unlimited,
            "requires_account": self.requires_account,
            "requires_card_or_topup": self.requires_card_or_topup,
            "has_terms_warning": bool(self.terms_warning),
            "source_url": self.source_url,
            "verified_at": self.verified_at,
            "confidence": self.confidence,
            "status": self.status,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class FreeTierBudget:
    audited_recurring_tokens_month: int = 0
    one_time_signup_tokens: int = 0
    used_tokens: int = 0
    remaining_tokens: int = 0
    audited_pools: tuple[str, ...] = ()
    unlimited_or_uncountable_pools: tuple[str, ...] = ()
    excluded_or_stale_pools: tuple[str, ...] = ()
    usage_scope: str = "estimated_local"
    pool_allowances: Mapping[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "audited_recurring_tokens_month": self.audited_recurring_tokens_month,
            "one_time_signup_tokens": self.one_time_signup_tokens,
            "used_tokens": self.used_tokens,
            "remaining_tokens": self.remaining_tokens,
            "audited_pools": list(self.audited_pools),
            "unlimited_or_uncountable_pools": list(self.unlimited_or_uncountable_pools),
            "excluded_or_stale_pools": list(self.excluded_or_stale_pools),
            "usage_scope": self.usage_scope,
            "pool_allowances": dict(self.pool_allowances),
        }


@dataclass
class _LocalUsageBucket:
    window_id: int
    tokens: int = 0


class LocalFreeTierUsageTracker:
    """Thread-safe, process-local token estimates in fixed 30-day windows.

    This deliberately does not claim to mirror provider billing-cycle balances.
    It exists only to make local free-tier reports and routing headroom coherent
    within a running process.
    """

    WINDOW_SECONDS = 30 * 24 * 60 * 60

    def __init__(self, *, clock: Callable[[], float] = time.time) -> None:
        self._clock = clock
        self._usage: dict[str, _LocalUsageBucket] = {}
        self._lock = RLock()

    def record(self, pool_id: str, tokens: int) -> None:
        pool = str(pool_id or "").strip()
        amount = max(0, int(tokens or 0))
        if not pool or amount <= 0:
            return
        window_id = int(self._clock() // self.WINDOW_SECONDS)
        with self._lock:
            bucket = self._usage.get(pool)
            if bucket is None or bucket.window_id != window_id:
                bucket = _LocalUsageBucket(window_id)
                self._usage[pool] = bucket
            bucket.tokens += amount

    def snapshot(self) -> dict[str, int]:
        window_id = int(self._clock() // self.WINDOW_SECONDS)
        with self._lock:
            return {
                pool_id: max(0, bucket.tokens)
                for pool_id, bucket in self._usage.items()
                if bucket.window_id == window_id
            }


class FreeTierCatalog:
    """Immutable view over free-tier plans with conservative reporting helpers."""

    def __init__(self, plans: Iterable[FreeTierPlan] = ()) -> None:
        self.plans = tuple(plans)

    def plan_for(self, provider: str, model: str = "") -> FreeTierPlan | None:
        return next((plan for plan in self.plans if plan.matches(provider, model)), None)

    def budget(
        self,
        *,
        usage_by_pool: Mapping[str, int] | None = None,
        usage_scope: str = "estimated_local",
        as_of: date | None = None,
        max_age_days: int = 45,
    ) -> FreeTierBudget:
        return calculate_free_tier_budget(
            self.plans,
            usage_by_pool=usage_by_pool,
            usage_scope=usage_scope,
            as_of=as_of,
            max_age_days=max_age_days,
        )

    def routing_headroom(self, provider: str, model: str = "", *, usage_by_pool: Mapping[str, int] | None = None, as_of: date | None = None) -> float:
        plan = self.plan_for(provider, model)
        if plan is None or not plan.is_routing_eligible(as_of=as_of) or plan.unlimited:
            return 1.0
        allowance = self._audited_pool_allowance(plan.pool_id, as_of=as_of)
        if allowance is None:
            return 1.0
        if allowance <= 0:
            return 0.0
        used = max(0, int((usage_by_pool or {}).get(plan.pool_id, 0)))
        return min(1.0, max(0.0, (allowance - used) / allowance))

    def _audited_pool_allowance(self, pool_id: str, *, as_of: date | None = None, max_age_days: int = 45) -> int | None:
        values = [
            plan.monthly_tokens()
            for plan in self.plans
            if plan.pool_id == pool_id and plan.is_auditable(as_of=as_of, max_age_days=max_age_days)
        ]
        numeric = [value for value in values if value is not None]
        return min(numeric) if numeric else None


def calculate_free_tier_budget(
    plans: Iterable[FreeTierPlan],
    *,
    usage_by_pool: Mapping[str, int] | None = None,
    usage_scope: str = "estimated_local",
    as_of: date | None = None,
    max_age_days: int = 45,
) -> FreeTierBudget:
    """Calculate an honest monthly headline, counting each shared pool once."""

    groups: dict[str, list[FreeTierPlan]] = {}
    for plan in plans:
        groups.setdefault(plan.pool_id or f"@missing:{plan.provider}", []).append(plan)

    allowances: dict[str, int] = {}
    signup: dict[str, int] = {}
    uncountable: list[str] = []
    excluded: list[str] = []
    for pool_id, group in groups.items():
        auditable = [plan for plan in group if plan.is_auditable(as_of=as_of, max_age_days=max_age_days)]
        monthly_values = [plan.monthly_tokens() for plan in auditable if plan.monthly_tokens() is not None]
        if monthly_values:
            allowances[pool_id] = min(monthly_values)
            credits = [max(0, int(plan.signup_credit_tokens or 0)) for plan in auditable]
            signup[pool_id] = min(credits) if credits else 0
        elif any(plan.unlimited or plan.recurring_tokens is None for plan in group if plan.status == "verified"):
            uncountable.append(pool_id)
        else:
            excluded.append(pool_id)

    usage = usage_by_pool or {}
    used_by_audited_pool = {pool_id: min(limit, max(0, int(usage.get(pool_id, 0)))) for pool_id, limit in allowances.items()}
    total = sum(allowances.values())
    used = sum(used_by_audited_pool.values())
    return FreeTierBudget(
        audited_recurring_tokens_month=total,
        one_time_signup_tokens=sum(signup.values()),
        used_tokens=used,
        remaining_tokens=max(0, total - used),
        audited_pools=tuple(sorted(allowances)),
        unlimited_or_uncountable_pools=tuple(sorted(uncountable)),
        excluded_or_stale_pools=tuple(sorted(excluded)),
        usage_scope=usage_scope,
        pool_allowances=allowances,
    )