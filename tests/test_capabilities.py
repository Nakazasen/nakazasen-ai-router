from nakazasen_ai_router import ModelCapability, TokenUsage, capability_for, estimate_cost, normalize_token_usage, score_candidate_for_task


def test_capability_for_known_and_unknown_model():
    known = capability_for("gemini", "gemini-2.5-flash")
    unknown = capability_for("unknown", "model")

    assert known.context_window_tokens >= 1_000_000
    assert "translation_longform" in known.recommended_tasks
    assert unknown.provider == "unknown"
    assert unknown.model == "model"
    assert unknown.cost_tier == "unknown"


def test_capability_override_takes_precedence():
    override = ModelCapability("p", "m", cost_tier="free", recommended_tasks=("cheap_generation",))

    assert capability_for("p", "m", {("p", "m"): override}) is override


def test_task_scoring_prefers_long_context_for_translation_and_free_for_cheap():
    long_context = ModelCapability("a", "long", context_window_tokens=1_000_000, max_output_tokens=32_000, quality_tier="strong", cost_tier="standard", recommended_tasks=("translation_longform",))
    free_small = ModelCapability("b", "free", context_window_tokens=8_000, max_output_tokens=2_000, quality_tier="basic", cost_tier="free", speed_tier="fast", recommended_tasks=("cheap_generation",))

    assert score_candidate_for_task(long_context, "translation_longform") > score_candidate_for_task(free_small, "translation_longform")
    assert score_candidate_for_task(free_small, "cheap_generation") > score_candidate_for_task(long_context, "cheap_generation")


def test_normalize_token_usage_supports_openai_and_gemini_shapes():
    openai = normalize_token_usage({"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20})
    gemini = normalize_token_usage({"promptTokenCount": 7, "candidatesTokenCount": 3, "totalTokenCount": 10})

    assert openai == TokenUsage(12, 8, 20, "provider_reported")
    assert gemini == TokenUsage(7, 3, 10, "provider_reported")


def test_cost_estimate_requires_verified_prices_and_usage_split():
    priced = ModelCapability("p", "m", input_cost_per_million=1.0, output_cost_per_million=2.0, currency="USD")

    known = estimate_cost(TokenUsage(1_000_000, 500_000, 1_500_000), priced)
    total_only = estimate_cost(TokenUsage(total_tokens=100), priced)
    unpriced = estimate_cost(TokenUsage(10, 20, 30), ModelCapability("p", "unknown"))

    assert known.status == "estimated"
    assert known.total_cost == 2.0
    assert total_only.status == "unknown"
    assert unpriced.status == "unknown"
