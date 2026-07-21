"""Opt-in provider model discovery utilities."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping

from .registry import PROVIDER_REGISTRY


class ProviderModelDiscoveryError(RuntimeError):
    """Raised when an opt-in provider model catalog request cannot be used safely."""


@dataclass(frozen=True)
class DiscoveredModel:
    provider: str
    model: str
    display_name: str
    supported_actions: tuple[str, ...]
    input_token_limit: int | None
    output_token_limit: int | None


def discover_provider_models(
    provider_name: str,
    *,
    api_key: str = "",
    base_url: str = "",
    http_client: Any = None,
    include_actions: tuple[str, ...] = ("generateContent",),
) -> list[DiscoveredModel]:
    """Discover a provider model catalog only when explicitly called.

    Gemini uses its native catalog endpoint. Other registered providers use their
    OpenAI-compatible ``GET /models`` endpoint. Returned metadata intentionally
    excludes API keys, authorization headers, and raw response payloads.
    """

    profile = PROVIDER_REGISTRY.get(provider_name)
    if profile is None:
        raise ValueError(f"Unsupported provider discovery: {provider_name}")
    if profile.is_cloud and not api_key:
        return []
    if provider_name == "gemini":
        return _discover_gemini_models(api_key=api_key, http_client=http_client, include_actions=include_actions)
    return _discover_openai_compatible_models(
        provider_name=provider_name,
        base_url=base_url or profile.base_url,
        api_key=api_key,
        http_client=http_client,
    )


def _discover_gemini_models(
    *,
    api_key: str,
    http_client: Any = None,
    include_actions: tuple[str, ...],
) -> list[DiscoveredModel]:
    models: list[DiscoveredModel] = []
    page_token = ""
    headers = {"X-Goog-Api-Key": api_key}
    while True:
        params: dict[str, str] = {}
        if page_token:
            params["pageToken"] = page_token
        url = "https://generativelanguage.googleapis.com/v1beta/models"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        payload = _get_json(url, headers=headers, http_client=http_client)
        for item in payload.get("models", []):
            if not isinstance(item, Mapping):
                continue
            raw_actions = item.get("supportedActions", item.get("supportedGenerationMethods", ()))
            actions = tuple(str(action) for action in raw_actions if action)
            if include_actions and not any(action in actions for action in include_actions):
                continue
            raw_name = str(item.get("name", "") or "")
            model = raw_name.removeprefix("models/")
            if not model:
                continue
            models.append(
                DiscoveredModel(
                    provider="gemini",
                    model=model,
                    display_name=str(item.get("displayName", "") or model),
                    supported_actions=actions,
                    input_token_limit=_optional_int(item.get("inputTokenLimit")),
                    output_token_limit=_optional_int(item.get("outputTokenLimit")),
                )
            )
        page_token = str(payload.get("nextPageToken", "") or "")
        if not page_token:
            break
    return models


def _discover_openai_compatible_models(
    *,
    provider_name: str,
    base_url: str,
    api_key: str,
    http_client: Any = None,
) -> list[DiscoveredModel]:
    headers = {"User-Agent": "nakazasen-ai-router/0.1"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = _get_json(_openai_models_url(base_url), headers=headers, http_client=http_client)
    items = payload.get("data", ())
    if not isinstance(items, list):
        raise ProviderModelDiscoveryError("model catalog response did not include a data list")

    models: list[DiscoveredModel] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        model = str(item.get("id", "") or "").strip()
        if not model or not _is_chat_model_id(model):
            continue
        models.append(
            DiscoveredModel(
                provider=provider_name,
                model=model,
                display_name=str(item.get("name") or item.get("display_name") or model),
                supported_actions=("chat.completions",),
                input_token_limit=_optional_int(item.get("context_length") or item.get("input_token_limit")),
                output_token_limit=_optional_int(item.get("max_output_tokens") or item.get("output_token_limit")),
            )
        )
    return models


def _openai_models_url(base_url: str) -> str:
    normalized = str(base_url or "").rstrip("/")
    if not normalized:
        raise ProviderModelDiscoveryError("provider does not define a model catalog URL")
    if normalized.endswith("/chat/completions"):
        return normalized.removesuffix("/chat/completions") + "/models"
    if normalized.endswith("/v1"):
        return normalized + "/models"
    return normalized + "/v1/models"


def _is_chat_model_id(model: str) -> bool:
    lowered = model.lower()
    excluded_fragments = ("embed", "moderation", "whisper", "transcri", "tts", "audio", "image", "dall-e", "sora", "video")
    return not any(fragment in lowered for fragment in excluded_fragments)


def _get_json(url: str, *, headers: Mapping[str, str] | None = None, http_client: Any = None) -> Mapping[str, Any]:
    safe_headers = dict(headers or {})
    if http_client is not None:
        get = getattr(http_client, "get", None)
        if not callable(get):
            raise ProviderModelDiscoveryError("configured HTTP client does not support GET model discovery")
        response = get(url, headers=safe_headers, timeout=30.0)
        status_code = getattr(response, "status_code", None)
        if isinstance(status_code, int) and status_code >= 400:
            raise ProviderModelDiscoveryError(f"model catalog request returned HTTP {status_code}")
        json_method = getattr(response, "json", None)
        payload = json_method() if callable(json_method) else json.loads(str(getattr(response, "text", "{}")))
    else:
        request_headers = {"User-Agent": "nakazasen-ai-router/0.1", **safe_headers}
        request = urllib.request.Request(url, headers=request_headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=30.0) as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as exc:
            raise ProviderModelDiscoveryError(f"model catalog request returned HTTP {exc.code}") from exc
    if not isinstance(payload, Mapping):
        raise ProviderModelDiscoveryError("model catalog response JSON must be an object")
    return payload


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
