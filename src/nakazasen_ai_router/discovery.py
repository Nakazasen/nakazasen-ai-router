"""Opt-in provider model discovery utilities."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


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
    api_key: str,
    http_client: Any = None,
    include_actions: tuple[str, ...] = ("generateContent",),
) -> list[DiscoveredModel]:
    """Discover provider models. This function performs network I/O only when called."""

    if provider_name != "gemini":
        raise ValueError(f"Unsupported provider discovery: {provider_name}")
    if not api_key:
        return []
    return _discover_gemini_models(api_key=api_key, http_client=http_client, include_actions=include_actions)


def _discover_gemini_models(
    *,
    api_key: str,
    http_client: Any = None,
    include_actions: tuple[str, ...],
) -> list[DiscoveredModel]:
    models: list[DiscoveredModel] = []
    page_token = ""
    while True:
        params = {"key": api_key}
        if page_token:
            params["pageToken"] = page_token
        url = "https://generativelanguage.googleapis.com/v1beta/models?" + urllib.parse.urlencode(params)
        payload = _get_json(url, http_client=http_client)
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


def _get_json(url: str, *, http_client: Any = None) -> Mapping[str, Any]:
    if http_client is not None:
        get = getattr(http_client, "get", None)
        if not callable(get):
            raise TypeError("http_client must provide get(url, timeout=...)")
        response = get(url, timeout=30.0)
        json_method = getattr(response, "json", None)
        payload = json_method() if callable(json_method) else json.loads(str(getattr(response, "text", "{}")))
    else:
        request = urllib.request.Request(url, headers={"User-Agent": "nakazasen-ai-router/0.1"}, method="GET")
        with urllib.request.urlopen(request, timeout=30.0) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    if not isinstance(payload, Mapping):
        raise ValueError("discovery response JSON must be an object")
    return payload


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
