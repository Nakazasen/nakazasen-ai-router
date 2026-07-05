"""Environment-based configuration helpers for Nakazasen AI Router."""

from __future__ import annotations

import os
from pathlib import Path
from collections.abc import Mapping, Sequence
from typing import Any

from .core import AIRouter, RouterPolicy
from .http import HttpxAsyncHTTPClient, UrllibHTTPClient
from .providers import OpenAICompatibleProvider
from .registry import PROVIDER_REGISTRY, ProviderProfile
from .state import JsonStateStore
from .storage_sqlite import SQLiteStateStore

LIVE_FREE_FIRST_ORDER = ("gemini", "deepseek", "nvidia_nim", "chatanywhere", "mistral", "openrouter", "groq")


def create_router_from_env(
    *,
    env: Mapping[str, str] | None = None,
    provider_names: Sequence[str] | None = None,
    http_client_factory: Any | None = None,
    policy: RouterPolicy | None = None,
    enable_network: bool = False,
    strategy: str | None = None,
    state_store: Any | None = None,
    state_path: str | Path | None = None,
    state_backend: str = "json",
    async_http_client_factory: Any | None = None,
    enable_async_network: bool = False,
) -> AIRouter:
    """Create an AIRouter from environment variables only.

    `strategy="live_free_first"` reorders providers for live smoke usage but
    never enables network by itself.
    """

    source_env = env or os.environ
    selected_names = _resolve_provider_names(provider_names, strategy)
    providers = []
    for name in selected_names:
        profile = PROVIDER_REGISTRY.get(name)
        if profile is None:
            continue
        provider = build_provider_from_profile(
            profile,
            source_env,
            http_client_factory=http_client_factory,
            enable_network=enable_network,
            async_http_client_factory=async_http_client_factory,
            enable_async_network=enable_async_network,
        )
        if provider is not None:
            providers.append(provider)
    effective_state_store = state_store or _state_store_from_path(state_path, state_backend)
    return AIRouter(providers, policy=policy, state_store=effective_state_store)


def _state_store_from_path(state_path: str | Path | None, state_backend: str) -> Any | None:
    if state_path is None:
        return None
    if state_backend == "json":
        return JsonStateStore(state_path)
    if state_backend == "sqlite":
        return SQLiteStateStore(state_path)
    raise ValueError(f"Unknown state_backend: {state_backend}")


def _resolve_provider_names(provider_names: Sequence[str] | None, strategy: str | None) -> tuple[str, ...]:
    if strategy is None:
        return tuple(provider_names or PROVIDER_REGISTRY.keys())
    if strategy != "live_free_first":
        raise ValueError(f"Unknown router strategy: {strategy}")
    names = tuple(provider_names or PROVIDER_REGISTRY.keys())
    name_set = set(names)
    ordered = tuple(name for name in LIVE_FREE_FIRST_ORDER if name in name_set)
    remainder = tuple(name for name in names if name not in ordered)
    return ordered + remainder


def create_live_free_first_router_from_env(**kwargs: Any) -> AIRouter:
    """Convenience wrapper for the live_free_first strategy."""

    return create_router_from_env(strategy="live_free_first", **kwargs)


def build_provider_from_profile(
    profile: ProviderProfile,
    env: Mapping[str, str],
    *,
    http_client_factory: Any | None = None,
    enable_network: bool = False,
    async_http_client_factory: Any | None = None,
    enable_async_network: bool = False,
) -> OpenAICompatibleProvider | None:
    api_keys = parse_api_keys(env, profile)
    base_url = str(env.get(profile.base_url_env_var, "") or "").strip() if profile.base_url_env_var else ""
    base_url = base_url or profile.base_url

    if profile.is_cloud and not api_keys:
        return None
    if not profile.is_cloud and not api_keys and not _is_local_base_url(base_url):
        return None

    http_client = http_client_factory(profile) if callable(http_client_factory) else http_client_factory
    if http_client is None:
        http_client = UrllibHTTPClient() if enable_network else _NoNetworkHTTPClient()
    async_http_client = async_http_client_factory(profile) if callable(async_http_client_factory) else async_http_client_factory
    if async_http_client is None and enable_async_network:
        async_http_client = HttpxAsyncHTTPClient()

    return OpenAICompatibleProvider(
        name=profile.name,
        base_url=base_url,
        api_keys=api_keys,
        models=list(profile.default_models),
        is_cloud=profile.is_cloud,
        http_client=http_client,
        async_http_client=async_http_client,
    )


def parse_api_keys(env: Mapping[str, str], profile: ProviderProfile) -> list[str]:
    """Parse singular and plural API key environment variables safely.

    Plural env values are read first, followed by the legacy singular env value.
    Commas, semicolons, and newlines are accepted as separators. Empty entries
    and duplicates are ignored while preserving the first-seen order.
    """

    values: list[str] = []
    if profile.api_keys_env_var:
        values.extend(_split_api_key_value(str(env.get(profile.api_keys_env_var, "") or "")))
    if profile.api_key_env_var:
        values.extend(_split_api_key_value(str(env.get(profile.api_key_env_var, "") or "")))

    parsed: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            parsed.append(value)
            seen.add(value)
    return parsed


def _split_api_key_value(raw_value: str) -> list[str]:
    normalized = raw_value.replace("\r", "\n").replace(";", ",")
    parts: list[str] = []
    for line in normalized.split("\n"):
        parts.extend(line.split(","))
    return [part.strip().strip('"').strip("'") for part in parts if part.strip().strip('"').strip("'")]


def _is_local_base_url(base_url: str) -> bool:
    lowered = base_url.lower()
    return "localhost" in lowered or "127.0.0.1" in lowered or "::1" in lowered


class _NoNetworkHTTPClient:
    """Safety placeholder so construction never performs network I/O."""

    def post(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("No http_client configured for OpenAI-compatible provider")

    def __repr__(self) -> str:
        return "NoNetworkHTTPClient()"
