"""Safe provider/model health scoreboard."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class ModelHealth:
    provider: str
    model: str
    success_count: int = 0
    failure_count: int = 0
    failure_streak: int = 0
    last_status: str = "unknown"
    last_error_type: str = ""
    last_latency_ms: float | None = None
    last_success_at: float | None = None
    last_failure_at: float | None = None
    cooldown_until: float | None = None


class HealthScoreboard:
    """Stores safe routing metadata only: no prompts, keys, headers, or raw responses."""

    def __init__(self, models: dict[tuple[str, str], ModelHealth] | None = None) -> None:
        self._models = models or {}

    def record_success(self, provider: str, model: str, latency_ms: float | None = None) -> None:
        entry = self._entry(provider, model)
        entry.success_count += 1
        entry.failure_streak = 0
        entry.last_status = "success"
        entry.last_error_type = ""
        entry.last_latency_ms = latency_ms
        entry.last_success_at = time.time()
        entry.cooldown_until = None

    def record_failure(
        self,
        provider: str,
        model: str,
        error_type: str,
        latency_ms: float | None = None,
        cooldown_until: float | None = None,
    ) -> None:
        entry = self._entry(provider, model)
        entry.failure_count += 1
        entry.failure_streak += 1
        entry.last_status = "failure"
        entry.last_error_type = str(error_type or "unknown_error")
        entry.last_latency_ms = latency_ms
        entry.last_failure_at = time.time()
        entry.cooldown_until = cooldown_until

    def rank_models(self, provider: str, configured_models: list[str] | tuple[str, ...]) -> list[str]:
        indexed = list(enumerate(configured_models))
        now = time.time()

        def score(item: tuple[int, str]) -> tuple[int, int, float, int]:
            index, model = item
            entry = self._models.get((provider, model))
            if entry is None:
                return (1, 0, 0.0, index)
            in_cooldown = bool(entry.cooldown_until and entry.cooldown_until > now)
            quota_like = entry.last_error_type in {"quota_rate_limit", "rate_limit", "quota"}
            if in_cooldown or quota_like:
                bucket = 3
            elif entry.last_status == "success":
                bucket = 0
            elif entry.failure_streak > 0:
                bucket = 2
            else:
                bucket = 1
            last_success = -(entry.last_success_at or 0.0)
            return (bucket, entry.failure_streak, last_success, index)

        return [model for _, model in sorted(indexed, key=score)]

    def last_known_good(self, provider: str) -> str | None:
        successes = [entry for (entry_provider, _), entry in self._models.items() if entry_provider == provider and entry.last_success_at]
        if not successes:
            return None
        return max(successes, key=lambda entry: entry.last_success_at or 0.0).model

    def to_dict(self) -> dict[str, Any]:
        return {"models": [asdict(entry) for entry in sorted(self._models.values(), key=lambda item: (item.provider, item.model))]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HealthScoreboard":
        models: dict[tuple[str, str], ModelHealth] = {}
        for raw in data.get("models", []):
            entry = ModelHealth(**raw)
            models[(entry.provider, entry.model)] = entry
        return cls(models)

    @classmethod
    def load_json(cls, path: str | Path) -> "HealthScoreboard":
        target = Path(path)
        if not target.exists():
            return cls()
        return cls.from_dict(json.loads(target.read_text(encoding="utf-8")))

    def save_json(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    def entries(self) -> list[ModelHealth]:
        return sorted(self._models.values(), key=lambda entry: (entry.provider, entry.model))

    def _entry(self, provider: str, model: str) -> ModelHealth:
        key = (provider, model)
        if key not in self._models:
            self._models[key] = ModelHealth(provider=provider, model=model)
        return self._models[key]
