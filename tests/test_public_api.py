import nakazasen_ai_router as nar


EXPECTED_PUBLIC_NAMES = {
    "AIRequest",
    "AIResult",
    "AIStreamChunk",
    "AIRouteOutcome",
    "AttemptRecord",
    "AIRouter",
    "RouterPolicy",
    "RouterError",
    "ProviderError",
    "ProviderAuthError",
    "ProviderQuotaError",
    "ProviderTimeoutError",
    "ProviderBase",
    "ProviderCandidate",
    "ProviderHealth",
    "MemoryStateStore",
    "JsonStateStore",
    "SQLiteStateStore",
    "KeyModelState",
    "create_router_from_env",
    "create_live_free_first_router_from_env",
    "ModelCapability",
    "capability_for",
    "score_candidate_for_task",
}


def test_public_api_exports_expected_names():
    assert EXPECTED_PUBLIC_NAMES.issubset(set(nar.__all__))
    for name in EXPECTED_PUBLIC_NAMES:
        assert hasattr(nar, name), name


def test_public_api_basic_construction_smoke():
    request = nar.AIRequest(prompt="hello")
    policy = nar.RouterPolicy(task_type="general")
    router = nar.AIRouter([], policy=policy, state_store=nar.MemoryStateStore())
    chunk = nar.AIStreamChunk(text="hello", provider_name="test", done=True)

    assert request.prompt == "hello"
    assert router.policy is policy
    assert chunk.done is True


def test_public_api_capability_helper_smoke():
    capability = nar.capability_for("gemini", "gemini-2.5-flash")
    score = nar.score_candidate_for_task(capability, "translation_longform")

    assert isinstance(capability, nar.ModelCapability)
    assert score > 0
