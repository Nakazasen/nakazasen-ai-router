"""Model capability catalog, provenance, token usage, and cost helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class TokenUsage:
    """Normalized, non-sensitive token usage for one provider response."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    source: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "source": self.source,
        }


@dataclass(frozen=True)
class CostEstimate:
    """Calculated cost. Unknown pricing is represented explicitly, never guessed."""

    input_cost: float | None = None
    output_cost: float | None = None
    total_cost: float | None = None
    currency: str = "USD"
    status: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "total_cost": self.total_cost,
            "currency": self.currency,
            "status": self.status,
        }


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
    input_cost_per_million: float | None = None
    output_cost_per_million: float | None = None
    currency: str = "USD"
    quota_pool_id: str = ""
    source_url: str = ""
    verified_at: str = ""
    confidence: str = "unknown"
    terms_note: str = ""


CAPABILITY_CATALOG: dict[tuple[str, str], ModelCapability] = {
    ("gemini", "gemini-3.6-flash"): ModelCapability("gemini", "gemini-3.6-flash", 1_000_000, 65_536, "standard", "fast", "strong", True, True, ("long_context", "translation_longform", "analysis", "summarization", "premium_reasoning")),
    ("gemini", "gemini-3.5-flash"): ModelCapability("gemini", "gemini-3.5-flash", 1_000_000, 65_536, "standard", "fast", "strong", True, True, ("long_context", "translation_longform", "analysis", "summarization", "premium_reasoning")),
    ("gemini", "gemini-3.5-flash-lite"): ModelCapability("gemini", "gemini-3.5-flash-lite", 1_000_000, 65_536, "cheap", "fast", "good", True, True, ("long_context", "translation_longform", "cheap_batch", "cheap_generation", "summarization")),
    ("gemini", "gemini-3.1-flash-lite"): ModelCapability("gemini", "gemini-3.1-flash-lite", 1_000_000, 65_536, "cheap", "fast", "good", True, True, ("long_context", "translation_longform", "cheap_batch", "cheap_generation", "summarization")),
    ("gemini", "gemini-2.5-flash"): ModelCapability("gemini", "gemini-2.5-flash", 1_000_000, 65_536, "standard", "fast", "strong", True, True, ("long_context", "translation_longform", "analysis", "summarization", "premium_reasoning")),
    ("gemini", "gemini-2.5-flash-lite"): ModelCapability("gemini", "gemini-2.5-flash-lite", 1_000_000, 65_536, "cheap", "fast", "good", True, True, ("long_context", "translation_longform", "cheap_batch", "cheap_generation")),
    ("gemini", "gemini-2.5-pro"): ModelCapability("gemini", "gemini-2.5-pro", 1_000_000, 65_536, "premium", "medium", "strong", True, True, ("long_context", "translation_longform", "analysis", "summarization", "premium_reasoning")),
    ("openrouter", "meta-llama/llama-3.3-70b-instruct:free"): ModelCapability("openrouter", "meta-llama/llama-3.3-70b-instruct:free", 131_072, 8_192, "free", "medium", "strong", True, False, ("cheap_batch", "cheap_generation", "analysis", "summarization")),
    ("groq", "llama-3.1-8b-instant"): ModelCapability("groq", "llama-3.1-8b-instant", 131_072, 8_192, "cheap", "fast", "good", True, False, ("cheap_batch", "cheap_generation", "summarization")),
    ("deepseek", "deepseek-v4-flash"): ModelCapability("deepseek", "deepseek-v4-flash", cost_tier="cheap", speed_tier="fast", quality_tier="good", supports_streaming=True, supports_json_mode=True, recommended_tasks=("analysis", "cheap_batch", "cheap_generation", "summarization")),
    ("deepseek", "deepseek-v4-pro"): ModelCapability("deepseek", "deepseek-v4-pro", cost_tier="standard", speed_tier="medium", quality_tier="strong", supports_streaming=True, supports_json_mode=True, recommended_tasks=("analysis", "premium_reasoning", "summarization")),
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


def normalize_token_usage(value: Any, *, source: str = "provider_reported") -> TokenUsage:
    """Normalize common OpenAI/Gemini-style usage mappings without retaining raw data."""

    if isinstance(value, TokenUsage):
        return value
    if not isinstance(value, Mapping):
        return TokenUsage()
    input_tokens = _non_negative_int(value.get("input_tokens", value.get("prompt_tokens", value.get("promptTokenCount", 0))))
    output_tokens = _non_negative_int(value.get("output_tokens", value.get("completion_tokens", value.get("candidatesTokenCount", 0))))
    total_tokens = _non_negative_int(value.get("total_tokens", value.get("totalTokenCount", 0)))
    if total_tokens == 0:
        total_tokens = input_tokens + output_tokens
    if input_tokens == 0 and output_tokens == 0 and total_tokens == 0:
        return TokenUsage()
    declared_source = str(value.get("source", source) or source)
    return TokenUsage(input_tokens, output_tokens, total_tokens, declared_source)


def estimate_cost(usage: TokenUsage | Mapping[str, Any], capability: ModelCapability) -> CostEstimate:
    """Calculate token cost only when prices and the input/output split are known."""

    normalized = normalize_token_usage(usage) if not isinstance(usage, TokenUsage) else usage
    pricing_known = capability.input_cost_per_million is not None and capability.output_cost_per_million is not None
    split_known = normalized.total_tokens == 0 or normalized.input_tokens > 0 or normalized.output_tokens > 0
    if not pricing_known or not split_known or normalized.total_tokens <= 0:
        return CostEstimate(currency=capability.currency)
    input_cost = normalized.input_tokens * capability.input_cost_per_million / 1_000_000
    output_cost = normalized.output_tokens * capability.output_cost_per_million / 1_000_000
    return CostEstimate(input_cost, output_cost, input_cost + output_cost, capability.currency, "estimated")


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


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0
