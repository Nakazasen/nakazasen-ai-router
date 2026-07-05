"""Durable-safe router state primitives.

The state layer stores only operational metadata. It must never store prompts,
raw API keys, request headers, or raw provider responses.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class KeyModelState:
    """Health and cooldown state for one provider/model/key candidate."""

    provider: str
    model: str
    key_id: str
    status: str = "unknown"
    enabled: bool = True
    cooldown_until: float = 0.0
    last_error_type: str = ""
    last_error_message: str = ""
    success_count: int = 0
    failure_count: int = 0
    failure_streak: int = 0
    last_latency_ms: int = 0
    last_success_at: float = 0.0
    last_failure_at: float = 0.0

    def is_available(self, now: float | None = None) -> bool:
        current = time.time() if now is None else now
        return self.enabled and current >= self.cooldown_until


class RouterStateStore(Protocol):
    """Persistence contract for safe router state."""

    def get_key_model_state(self, provider: str, model: str, key_id: str) -> KeyModelState:
        """Return existing state or create a default state entry."""

    def record_success(self, provider: str, model: str, key_id: str, *, latency_ms: int = 0) -> None:
        """Record a successful attempt."""

    def record_failure(
        self,
        provider: str,
        model: str,
        key_id: str,
        *,
        error_type: str,
        error_message: str = "",
        latency_ms: int = 0,
        cooldown_until: float = 0.0,
        disable: bool = False,
    ) -> None:
        """Record a failed attempt without storing sensitive payload data."""

    def list_states(self) -> list[KeyModelState]:
        """Return all known states."""

    def save(self) -> None:
        """Persist changes if this store is durable."""


class MemoryStateStore:
    """In-memory state store used by default and by tests."""

    def __init__(self, states: dict[tuple[str, str, str], KeyModelState] | None = None) -> None:
        self._states = states or {}

    def get_key_model_state(self, provider: str, model: str, key_id: str) -> KeyModelState:
        key = (provider, model, key_id)
        if key not in self._states:
            self._states[key] = KeyModelState(provider=provider, model=model, key_id=key_id)
        return self._states[key]

    def record_success(self, provider: str, model: str, key_id: str, *, latency_ms: int = 0) -> None:
        entry = self.get_key_model_state(provider, model, key_id)
        entry.status = "healthy"
        entry.enabled = True
        entry.cooldown_until = 0.0
        entry.last_error_type = ""
        entry.last_error_message = ""
        entry.success_count += 1
        entry.failure_streak = 0
        entry.last_latency_ms = latency_ms
        entry.last_success_at = time.time()
        self.save()

    def record_failure(
        self,
        provider: str,
        model: str,
        key_id: str,
        *,
        error_type: str,
        error_message: str = "",
        latency_ms: int = 0,
        cooldown_until: float = 0.0,
        disable: bool = False,
    ) -> None:
        entry = self.get_key_model_state(provider, model, key_id)
        entry.failure_count += 1
        entry.failure_streak += 1
        entry.last_error_type = str(error_type or "unknown_error")
        entry.last_error_message = _safe_message(error_message)
        entry.last_latency_ms = latency_ms
        entry.last_failure_at = time.time()
        if cooldown_until > 0:
            entry.cooldown_until = cooldown_until
            entry.status = "cooldown"
        else:
            entry.status = "failed"
        if disable:
            entry.enabled = False
            entry.status = "dead"
        self.save()

    def list_states(self) -> list[KeyModelState]:
        return sorted(self._states.values(), key=lambda entry: (entry.provider, entry.model, entry.key_id))

    def save(self) -> None:
        return None


class JsonStateStore(MemoryStateStore):
    """JSON-backed state store for single-process durable cooldowns."""

    schema_version = 1

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        super().__init__(self._load_states())

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.schema_version,
            "states": [asdict(entry) for entry in self.list_states()],
        }
        temp_path = self.path.with_name(f"{self.path.name}.tmp")
        temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(temp_path, self.path)

    def _load_states(self) -> dict[tuple[str, str, str], KeyModelState]:
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        states: dict[tuple[str, str, str], KeyModelState] = {}
        for raw in data.get("states", []):
            entry = KeyModelState(**raw)
            states[(entry.provider, entry.model, entry.key_id)] = entry
        return states


def _safe_message(message: str) -> str:
    compact = " ".join(str(message or "").replace("\r", " ").replace("\n", " ").split())
    return compact[:200]
