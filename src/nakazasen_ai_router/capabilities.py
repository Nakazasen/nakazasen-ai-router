"""Model capability catalog and task-aware candidate scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ModelCapability:
    provider: str
    model: str
    context_window_tokens: int = 0
    max_output_tokens: int = 0
    cost_tier: str = "unknown"
    speed_tier: str = "unknown"
    quality_tier: str = "unknown"
    supports_streaming: bool = False
    supports_json_mode: bool = False
    recommended_tasks: tuple[str, ...] = ()


CAPABILITY_CATALOG: dict[tuple[str, str], ModelCapability] = {
    ("gemini", "gemini-3.5-flash"): ModelCapability("gemini", "gemini-3.5-flash", 1_000_000, 65_536, "standard", "fast", "strong", True, True, ("long_context", "translation_longform", "analysis", "summarization", "premium_reasoning")),
    ("gemini", "gemini-flash-latest"): ModelCapability("gemini", "gemini-flash-latest", 1_000_000, 65_536, "standard", "fast", "strong", True, True, ("long_context", "translation_longform", "analysis", "summarization", "premium_reasoning")),
    ("gemini", "gemini-flash-lite-latest"): ModelCapability("gemini", "gemini-flash-lite-latest", 1_000_000, 65_536, "cheap", "fast", "good", True, True, ("long_context", "translation_longform", "cheap_batch", "cheap_generation", "summarization")),
    ("gemini", "gemini-2.5-flash"): ModelCapability("gemini", "gemini-2.5-flash", 1_000_000, 65_536, "standard", "fast", "strong", True, True, ("long_context", "translation_longform", "analysis", "summarization", "premium_reasoning")),
    ("gemini", "gemini-2.5-flash-lite"): ModelCapability("gemini", "gemini-2.5-flash-lite", 1_000_000, 65_536, "cheap", "fast", "good", True, True, ("long_context", "translation_longform", "cheap_batch", "cheap_generation")),
    ("openrouter", "meta-llama/llama-3.3-70b-instruct:free"): ModelCapability("openrouter", "meta-llama/llama-3.3-70b-instruct:free", 131_072, 8_192, "free", "medium", "strong", True, False, ("cheap_batch", "cheap_generation", "analysis", "summarization")),
    ("groq", "llama-3.1-8b-instant"): ModelCapability("groq", "llama-3.1-8b-instant", 131_072, 8_192, "cheap", "fast", "good", True, False, ("cheap_batch", "cheap_generation", "summarization")),
    ("deepseek", "deepseek-chat"): ModelCapability("deepseek", "deepseek-chat", 64_000, 8_000, "cheap", "medium", "good", True, True, ("analysis", "cheap_batch", "cheap_generation", "summarization")),
    ("nvidia_nim", "meta/llama-3.1-8b-instruct"): ModelCapability("nvidia_nim", "meta/llama-3.1-8b-instruct", 131_072, 8_192, "standard", "fast", "good", True, False, ("summarization", "cheap_batch", "cheap_generation")),
    ("chatanywhere", "gpt-4o-mini"): ModelCapability("chatanywhere", "gpt-4o-mini", 128_000, 16_384, "standard", "fast", "good", True, True, ("long_context", "translation_longform", "summarization", "structured_json", "json_structured")),
    ("mistral", "mistral-small-latest"): ModelCapability("mistral", "mistral-small-latest", 128_000, 8_192, "standard", "fast", "good", True, True, ("summarization", "analysis", "structured_json", "json_structured")),
    ("local_openai_compatible", "local-model"): ModelCapability("local_openai_compatible", "local-model", 32_768, 4_096, "free", "medium", "unknown", False, False, ("private_local", "local_only", "cheap_batch", "cheap_generation")),
}

_COST_SCORE = {"free": 40, "cheap": 30, "standard": 15, "premium": 0, "unknown": 5}
_QUALITY_SCORE = {"strong": 35, "good": 25, "basic": 10, "unknown": 0}
_SPEED_SCORE = {"fast": 20, "medium": 10, "slow": 0, "unknown": 0}


def capability_for(provider: str, model: str, overrides: Mapping[tuple[str, str], ModelCapability] | None = None) -> ModelCapability:
    if overrides and (provider, model) in overrides:
        return overrides[(provider, model)]
    return CAPABILITY_CATALOG.get((provider, model), ModelCapability(provider=provider, model=model))


def _normalize_task_type(task_type: str) -> str:
    aliases = {
        "json_structured": "structured_json",
        "cheap_generation": "cheap_batch",
        "premium_quality": "premium_reasoning",
        "local_only": "private_local",
    }
    return aliases.get(task_type, task_type)


def score_candidate_for_task(capability: ModelCapability, task_type: str, quality_preference: str = "balanced") -> int:
    task = _normalize_task_type(task_type or "general")
    score = 0
    if task in capability.recommended_tasks:
        score += 100
    if task in {"long_context", "translation_longform"}:
        score += min(capability.context_window_tokens // 10_000, 80)
        score += min(capability.max_output_tokens // 2_000, 25)
        score += _QUALITY_SCORE.get(capability.quality_tier, 0)
    elif task in {"cheap_batch", "cheap_generation"}:
        score += _COST_SCORE.get(capability.cost_tier, 0) * 2
        score += _SPEED_SCORE.get(capability.speed_tier, 0)
    elif task in {"premium_reasoning", "premium_quality"}:
        score += _QUALITY_SCORE.get(capability.quality_tier, 0) * 2
        score += min(capability.context_window_tokens // 20_000, 40)
    elif task in {"structured_json", "json_structured"}:
        score += 60 if capability.supports_json_mode else 0
        score += _QUALITY_SCORE.get(capability.quality_tier, 0)
    elif task in {"private_local", "local_only"}:
        score += 80 if capability.cost_tier == "free" else 0
    else:
        score += _QUALITY_SCORE.get(capability.quality_tier, 0)
        score += _SPEED_SCORE.get(capability.speed_tier, 0)

    if quality_preference == "cheap":
        score += _COST_SCORE.get(capability.cost_tier, 0)
    elif quality_preference == "quality":
        score += _QUALITY_SCORE.get(capability.quality_tier, 0)
    else:
        score += _COST_SCORE.get(capability.cost_tier, 0) // 2
        score += _QUALITY_SCORE.get(capability.quality_tier, 0) // 2
    return score
