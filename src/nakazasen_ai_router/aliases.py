"""Provider/model reference aliases."""

from __future__ import annotations

from dataclasses import dataclass


GEMINI_ALIASES = {
    "default": "gemini-3.5-flash",
    "fast": "gemini-3.6-flash",
    "latest": "gemini-3.6-flash",
    "lite": "gemini-3.5-flash-lite",
    "cheap": "gemini-3.5-flash-lite",
}

MODEL_ALIASES = {"gemini": GEMINI_ALIASES}


@dataclass(frozen=True)
class ModelRef:
    provider: str
    model: str
    alias: str = ""


def parse_model_ref(ref: str) -> ModelRef:
    if ":" not in ref:
        raise ValueError("Model reference must use provider:model syntax")
    provider, model_or_alias = (part.strip() for part in ref.split(":", 1))
    if not provider or not model_or_alias:
        raise ValueError("Model reference must include both provider and model")
    aliases = MODEL_ALIASES.get(provider, {})
    if model_or_alias in aliases:
        return ModelRef(provider=provider, model=aliases[model_or_alias], alias=model_or_alias)
    if model_or_alias in aliases.values() or "-" in model_or_alias or "/" in model_or_alias:
        return ModelRef(provider=provider, model=model_or_alias)
    raise ValueError(f"Unknown model alias for provider {provider}: {model_or_alias}")
