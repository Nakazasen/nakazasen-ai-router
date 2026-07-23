"""Explainable weighted routing scores and reusable mode packs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RoutingMode(str, Enum):
    """Built-in routing weight packs."""

    BALANCED = "balanced"
    FAST = "fast"
    CHEAP = "cheap"
    QUALITY = "quality"
    QUOTA = "quota"


@dataclass(frozen=True)
class ScoreWeights:
    """Weights for normalized candidate signals.

    Weights are normalized before use, so callers may provide percentages or
    fractions. Negative values are treated as zero.
    """

    capability: float = 0.35
    health: float = 0.20
    latency: float = 0.15
    cost: float = 0.10
    quota: float = 0.15
    priority: float = 0.05
    free_tier: float = 0.0

    def normalized(self) -> "ScoreWeights":
        values = [
            max(0.0, float(self.capability)),
            max(0.0, float(self.health)),
            max(0.0, float(self.latency)),
            max(0.0, float(self.cost)),
            max(0.0, float(self.quota)),
            max(0.0, float(self.priority)),
            max(0.0, float(self.free_tier)),
        ]
        total = sum(values)
        if total <= 0:
            return ScoreWeights()
        return ScoreWeights(*(value / total for value in values))


MODE_WEIGHTS: dict[RoutingMode, ScoreWeights] = {
    RoutingMode.BALANCED: ScoreWeights(),
    RoutingMode.FAST: ScoreWeights(capability=0.20, health=0.20, latency=0.40, cost=0.05, quota=0.10, priority=0.05),
    RoutingMode.CHEAP: ScoreWeights(capability=0.15, health=0.12, latency=0.08, cost=0.30, quota=0.10, priority=0.05, free_tier=0.20),
    RoutingMode.QUALITY: ScoreWeights(capability=0.55, health=0.15, latency=0.05, cost=0.05, quota=0.15, priority=0.05),
    RoutingMode.QUOTA: ScoreWeights(capability=0.16, health=0.12, latency=0.05, cost=0.05, quota=0.37, priority=0.05, free_tier=0.20),
}


@dataclass(frozen=True)
class RoutingScore:
    """Sanitized score breakdown for one candidate."""

    total: float
    capability: float
    health: float
    latency: float
    cost: float
    quota: float
    priority: float
    mode: str
    free_tier: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": round(self.total, 6),
            "components": {
                "capability": round(self.capability, 6),
                "health": round(self.health, 6),
                "latency": round(self.latency, 6),
                "cost": round(self.cost, 6),
                "quota": round(self.quota, 6),
                "free_tier": round(self.free_tier, 6),
                "priority": round(self.priority, 6),
            },
            "mode": self.mode,
        }


def weights_for_mode(mode: RoutingMode | str, custom: ScoreWeights | None = None) -> ScoreWeights:
    """Return normalized custom weights or the selected built-in pack."""

    if custom is not None:
        return custom.normalized()
    try:
        selected = mode if isinstance(mode, RoutingMode) else RoutingMode(str(mode or "balanced").lower())
    except ValueError as exc:
        valid = ", ".join(item.value for item in RoutingMode)
        raise ValueError(f"Unknown routing mode: {mode!r}; expected one of {valid}") from exc
    return MODE_WEIGHTS[selected].normalized()


def score_routing_candidate(
    *,
    task_score: float,
    cost_tier: str = "unknown",
    success_count: int = 0,
    failure_count: int = 0,
    latency_ms: int = 0,
    quota_headroom: float = 1.0,
    free_tier_headroom: float = 0.0,
    priority: int = 0,
    mode: RoutingMode | str = RoutingMode.BALANCED,
    weights: ScoreWeights | None = None,
) -> RoutingScore:
    """Score already-eligible candidates using bounded non-sensitive signals."""

    selected_mode = mode.value if isinstance(mode, RoutingMode) else str(mode or RoutingMode.BALANCED.value).lower()
    effective = weights_for_mode(mode, weights)
    capability = _clamp(float(task_score) / 250.0)
    attempts = max(0, int(success_count)) + max(0, int(failure_count))
    health = 0.5 if attempts == 0 else _clamp(max(0, int(success_count)) / attempts)
    latency = 0.5 if latency_ms <= 0 else _clamp(1.0 / (1.0 + max(0, int(latency_ms)) / 1000.0))
    cost = {"free": 1.0, "cheap": 0.8, "standard": 0.5, "premium": 0.2, "unknown": 0.4}.get(str(cost_tier).lower(), 0.4)
    quota = _clamp(float(quota_headroom))
    free_tier = _clamp(float(free_tier_headroom))
    priority_signal = 1.0 / (1.0 + max(0, int(priority)))
    total = (
        capability * effective.capability
        + health * effective.health
        + latency * effective.latency
        + cost * effective.cost
        + quota * effective.quota
        + free_tier * effective.free_tier
        + priority_signal * effective.priority
    )
    return RoutingScore(
        total=total,
        capability=capability,
        health=health,
        latency=latency,
        cost=cost,
        quota=quota,
        priority=priority_signal,
        mode=selected_mode,
        free_tier=free_tier,
    )


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))
