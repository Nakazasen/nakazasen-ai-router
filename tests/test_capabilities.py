from nakazasen_ai_router import ModelCapability, capability_for, score_candidate_for_task


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
