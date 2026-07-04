"""Environment-based configuration helpers for Nakazasen AI Router."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from .core import AIRouter, RouterPolicy
from .providers import OpenAICompatibleProvider
from .registry import PROVIDER_REGISTRY, ProviderProfile


def create_router_from_env(
    *,
    env: Mapping[str, str] | None = None,
    provider_names: list[str] | tuple[str, ...] | None = None,
    http_client_factory: Any | None = None,
    policy: RouterPolicy | None = None,
) -> AIRouter:
    """Create an AIRouter from environment variables only.

    Cloud providers are skipped when their API key environment variable is
    missing. The local OpenAI-compatible provider is allowed without a key when
    its base URL points to localhost/127.0.0.1.
    """

    source_env = env or os.environ
    selected_names = provider_names or tuple(PROVIDER_REGISTRY.keys())
    providers = []
    for name in selected_names:
        profile = PROVIDER_REGISTRY.get(name)
        if profile is None:
            continue
        provider = build_provider_from_profile(profile, source_env, http_client_factory=http_client_factory)
        if provider is not None:
            providers.append(provider)
    return AIRouter(providers, policy=policy)


def build_provider_from_profile(
    profile: ProviderProfile,
    env: Mapping[str, str],
    *,
    http_client_factory: Any | None = None,
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
        http_client = _NoNetworkHTTPClient()

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
