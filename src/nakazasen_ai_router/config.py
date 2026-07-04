"""Environment-based configuration helpers for Nakazasen AI Router."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any

from .core import AIRouter, RouterPolicy
from .http import UrllibHTTPClient
from .providers import OpenAICompatibleProvider
from .registry import PROVIDER_REGISTRY, ProviderProfile

LIVE_FREE_FIRST_ORDER = ("deepseek", "nvidia_nim", "chatanywhere", "mistral", "openrouter", "groq")


def create_router_from_env(
    *,
    env: Mapping[str, str] | None = None,
    provider_names: Sequence[str] | None = None,
    http_client_factory: Any | None = None,
    policy: RouterPolicy | None = None,
    enable_network: bool = False,
    strategy: str | None = None,
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
        )
        if provider is not None:
            providers.append(provider)
    return AIRouter(providers, policy=policy)


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
) -> OpenAICompatibleProvider | None:
    api_key = str(env.get(profile.api_key_env_var, "") or "").strip() if profile.api_key_env_var else ""
    base_url = str(env.get(profile.base_url_env_var, "") or "").strip() if profile.base_url_env_var else ""
    base_url = base_url or profile.base_url

    if profile.is_cloud and not api_key:
        return None
    if not profile.is_cloud and not api_key and not _is_local_base_url(base_url):
        return None

    http_client = http_client_factory(profile) if callable(http_client_factory) else http_client_factory
    if http_client is None:
        http_client = UrllibHTTPClient() if enable_network else _NoNetworkHTTPClient()

    return OpenAICompatibleProvider(
        name=profile.name,
        base_url=base_url,
        api_keys=[api_key] if api_key else [],
        models=list(profile.default_models),
        is_cloud=profile.is_cloud,
        http_client=http_client,
    )


def _is_local_base_url(base_url: str) -> bool:
    lowered = base_url.lower()
    return "localhost" in lowered or "127.0.0.1" in lowered or "::1" in lowered


class _NoNetworkHTTPClient:
    """Safety placeholder so construction never performs network I/O."""

    def post(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("No http_client configured for OpenAI-compatible provider")

    def __repr__(self) -> str:
        return "NoNetworkHTTPClient()"
