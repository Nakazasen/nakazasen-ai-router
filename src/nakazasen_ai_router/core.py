"""Core routing primitives for Nakazasen AI Router.

This module intentionally contains no real AI provider calls.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

LOGGER = logging.getLogger(__name__)
SENSITIVE_KEYS = {"api_key", "apikey", "token", "secret", "authorization", "password"}


class ProviderError(Exception):
    """Base class for provider failures."""


class ProviderQuotaError(ProviderError):
    """Provider cannot serve because quota or rate limit is exhausted."""


class ProviderAuthError(ProviderError):
    """Provider credentials are invalid or rejected."""


class ProviderTimeoutError(ProviderError):
    """Provider did not respond within the expected time."""


class RouterError(Exception):
    """Raised when the router cannot return a successful result."""


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

    def is_available(self, now: float | None = None) -> bool:
        current = time.time() if now is None else now
        return self.enabled and current >= self.cooldown_until


@dataclass
class ProviderCandidate:
    """Provider plus metadata used by routing decisions."""

    provider: "ProviderBase"
    priority: int = 100


@dataclass(frozen=True)
class RouterPolicy:
    """Routing policy for safe provider selection."""

    local_only: bool = False
    quota_cooldown_seconds: float = 60.0


class ProviderBase:
    """Base class for all providers.

    Real providers will subclass this later. For now tests use fake providers only.
    """

    def __init__(self, name: str, *, is_cloud: bool) -> None:
        self.name = name
        self.is_cloud = is_cloud
        self.health = ProviderHealth()

    def generate(self, request: AIRequest) -> AIResult:
        raise NotImplementedError


class AIRouter:
    """Minimal provider router with fallback and health handling."""

    def __init__(self, providers: Sequence[ProviderBase | ProviderCandidate], policy: RouterPolicy | None = None) -> None:
        self.policy = policy or RouterPolicy()
        self.providers = self._normalize(providers)

    def route(self, request: AIRequest) -> AIResult:
        safe_metadata = sanitize_mapping(request.metadata)
        LOGGER.info("Routing AI request metadata=%s", safe_metadata)

        failures: list[str] = []
        for candidate in sorted(self.providers, key=lambda item: item.priority):
            provider = candidate.provider
            if self.policy.local_only and provider.is_cloud:
                LOGGER.info("Skipping cloud provider %s because local_only=True", provider.name)
                continue
            if not provider.health.is_available():
                LOGGER.info("Skipping unavailable provider %s", provider.name)
                continue

            try:
                return provider.generate(request)
            except ProviderQuotaError as exc:
                provider.health.last_error = str(exc)
                provider.health.cooldown_until = time.time() + self.policy.quota_cooldown_seconds
                failures.append(f"{provider.name}: quota")
                LOGGER.warning("Provider %s quota failure; provider is cooling down", provider.name)
            except ProviderAuthError as exc:
                provider.health.last_error = str(exc)
                provider.health.enabled = False
                failures.append(f"{provider.name}: auth")
                LOGGER.warning("Provider %s auth failure; provider is disabled", provider.name)
            except ProviderTimeoutError as exc:
                provider.health.last_error = str(exc)
                failures.append(f"{provider.name}: timeout")
                LOGGER.warning("Provider %s timeout; trying next provider", provider.name)
            except ProviderError as exc:
                provider.health.last_error = str(exc)
                failures.append(f"{provider.name}: error")
                LOGGER.warning("Provider %s failed; trying next provider", provider.name)

        detail = ", ".join(failures) if failures else "no eligible providers"
        raise RouterError(f"No provider returned a result: {detail}")

    @staticmethod
    def _normalize(providers: Sequence[ProviderBase | ProviderCandidate]) -> list[ProviderCandidate]:
        normalized: list[ProviderCandidate] = []
        for index, item in enumerate(providers):
            if isinstance(item, ProviderCandidate):
                normalized.append(item)
            else:
                normalized.append(ProviderCandidate(provider=item, priority=index))
        return normalized


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
