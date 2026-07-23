import logging
from email.utils import format_datetime
from datetime import datetime, timedelta, timezone
import asyncio
import time

import pytest

from nakazasen_ai_router import (
    AIRequest,
    AIResult,
    AIStreamChunk,
    AIRouter,
    CapacityPolicy,
    InMemoryQuotaTracker,
    MemoryStateStore,
    ModelCapability,
    ProviderBase,
    ProviderCandidate,
    ProviderError,
    ProviderQuotaProfile,
    RouterError,
    RouterPolicy,
)
from nakazasen_ai_router.core import classify_error, extract_retry_after_seconds, mask_key_id
from nakazasen_ai_router.fake_providers import (
    provider_fail_auth,
    provider_fail_quota,
    provider_success,
    provider_timeout,
)


class CandidateProvider(ProviderBase):
    def __init__(self, name, responses, *, is_cloud=False, candidates=None):
        super().__init__(name, is_cloud=is_cloud)
        self.responses = list(responses)
        self.calls = 0
        self.seen_candidates = []
        self._candidates = candidates or []

    def iter_candidates(self):
        return self._candidates or super().iter_candidates()

    def generate(self, request, candidate=None):
        self.calls += 1
        self.seen_candidates.append(candidate)
        response = self.responses[min(self.calls - 1, len(self.responses) - 1)]
        if isinstance(response, Exception):
            raise response
        return response


def test_provider_a_error_fallback_to_provider_b():
    provider_a = provider_timeout("provider_a")
    provider_b = provider_success("provider_b")

    result = AIRouter([provider_a, provider_b]).route(AIRequest(prompt="hello"))

    assert result.provider_name == "provider_b"
    assert provider_a.calls == 1
    assert provider_b.calls == 1


def test_quota_error_puts_provider_on_cooldown():
    provider_a = provider_fail_quota("quota_provider")
    provider_b = provider_success("backup_provider")
    router = AIRouter([provider_a, provider_b], policy=RouterPolicy(quota_cooldown_seconds=120))

    result = router.route(AIRequest(prompt="hello"))

    assert result.provider_name == "backup_provider"
    assert provider_a.health.cooldown_until > 0
    assert not provider_a.health.is_available()


def test_auth_error_disables_provider():
    provider_a = provider_fail_auth("auth_provider")
    provider_b = provider_success("backup_provider")

    result = AIRouter([provider_a, provider_b]).route(AIRequest(prompt="hello"))

    assert result.provider_name == "backup_provider"
    assert provider_a.health.enabled is False
    assert not provider_a.health.is_available()


def test_local_only_does_not_call_cloud_provider():
    cloud_provider = provider_success("cloud_provider", is_cloud=True)
    local_provider = provider_success("local_provider", is_cloud=False)
    router = AIRouter([cloud_provider, local_provider], policy=RouterPolicy(local_only=True))

    result = router.route(AIRequest(prompt="hello"))

    assert result.provider_name == "local_provider"
    assert cloud_provider.calls == 0
    assert local_provider.calls == 1


def test_local_only_errors_when_only_cloud_provider_exists():
    cloud_provider = provider_success("cloud_provider", is_cloud=True)
    router = AIRouter([cloud_provider], policy=RouterPolicy(local_only=True))

    with pytest.raises(RouterError) as exc_info:
        router.route(AIRequest(prompt="hello"))

    assert cloud_provider.calls == 0
    assert exc_info.value.attempts[0]["reason"] == "local_only"


def test_api_key_is_not_logged(caplog):
    provider = provider_success("safe_provider")
    router = AIRouter([provider])

    with caplog.at_level(logging.INFO):
        router.route(
            AIRequest(
                prompt="hello",
                metadata={
                    "api_key": "fake-real-key-must-not-appear",
                    "nested": {"token": "secret-token-must-not-appear"},
                    "purpose": "test",
                },
            )
        )

    logs = caplog.text
    assert "fake-real-key-must-not-appear" not in logs
    assert "secret-token-must-not-appear" not in logs
    assert "[REDACTED]" in logs


def test_classify_auth_by_status_code():
    assert classify_error("", status_code=401) == "auth_failure"
    assert classify_error("", status_code=403) == "auth_failure"


def test_classify_quota_by_status_code():
    assert classify_error("", status_code=429) == "quota_rate_limit"


def test_classify_quota_by_body_hint():
    assert classify_error("", response_body={"error": "quota exceeded rate limit"}) == "quota_rate_limit"
    assert classify_error("", response_body={"error": "daily quota exceeded"}) == "quota_exhausted_daily"
    assert classify_error("", response_body={"error": "insufficient_quota"}) == "insufficient_quota"
    assert classify_error("", response_body={"error": "billing hard limit reached"}) == "billing_limit"


def test_classify_timeout_transport_model_token_and_5xx():
    assert classify_error("request timeout") == "timeout"
    assert classify_error("connection refused") == "transport_error"
    assert classify_error("invalid model") == "model_error"
    assert classify_error("context length too many tokens") == "token_limit"
    assert classify_error("", status_code=503) == "provider_5xx"
    assert classify_error("model unavailable", status_code=404) == "model_unavailable"


def test_retry_after_number_string_http_date_and_invalid():
    assert extract_retry_after_seconds({"Retry-After": 3}) == 3
    assert extract_retry_after_seconds({"Retry-After": "4"}) == 4
    future = datetime.now(timezone.utc) + timedelta(seconds=30)
    parsed = extract_retry_after_seconds({"Retry-After": format_datetime(future, usegmt=True)})
    assert parsed is not None
    assert 0 < parsed <= 31
    assert extract_retry_after_seconds({"Retry-After": "not-a-date"}) is None
    assert extract_retry_after_seconds({}) is None


def test_quota_uses_retry_after_for_cooldown():
    provider_a = CandidateProvider("quota", [ProviderError("quota", status_code=429, retry_after=7)])
    provider_b = provider_success("backup")

    result = AIRouter([provider_a, provider_b]).route(AIRequest(prompt="hello"))

    assert result.provider_name == "backup"
    remaining = provider_a.health.cooldown_until - datetime.now().timestamp()
    assert 0 < remaining <= 8


def test_auth_disable_is_runtime_only_without_persisting_config():
    provider = CandidateProvider("auth", [ProviderError("bad key", status_code=401)])
    backup = provider_success("backup")
    config = {"enabled": True}

    result = AIRouter([provider, backup]).route(AIRequest(prompt="hello"))

    assert result.provider_name == "backup"
    assert provider.health.enabled is False
    assert config == {"enabled": True}


def test_key_id_is_masked_and_raw_key_not_visible():
    raw = "fake-secret-1234567890"
    provider = CandidateProvider(
        "masked",
        [provider_success("unused").generate(AIRequest(prompt="x"))],
        candidates=[ProviderCandidate(provider=None, key_index=0, key_id=raw, model="m1")],
    )
    candidate = provider.iter_candidates()[0]

    assert candidate.key_id == "****7890"
    assert raw not in str(candidate)
    assert mask_key_id("abcd") == "***"


def test_attempts_do_not_contain_raw_api_key_or_prompt_by_default():
    raw = "fake-secret-raw-key"
    provider_a = CandidateProvider(
        "quota",
        [ProviderError("429 quota")],
        candidates=[ProviderCandidate(provider=None, key_index=0, key_id=raw, model="m1")],
    )
    provider_b = provider_success("backup")
    request = AIRequest(prompt="sensitive prompt must not appear")

    result = AIRouter([provider_a, provider_b]).route(request)
    attempts_text = str(result.metadata["attempts"])

    assert raw not in attempts_text
    assert "sensitive prompt must not appear" not in attempts_text
    assert "****-key" in attempts_text


def test_avoid_providers_works():
    avoided = provider_success("avoid_me")
    chosen = provider_success("choose_me")
    router = AIRouter([avoided, chosen], policy=RouterPolicy(avoid_providers=("avoid_me",)))

    result = router.route(AIRequest(prompt="hello"))

    assert result.provider_name == "choose_me"
    assert avoided.calls == 0
    assert chosen.calls == 1


def test_health_success_failure_counts_update_correctly():
    provider_a = provider_fail_quota("quota")
    provider_b = provider_success("backup")

    result = AIRouter([provider_a, provider_b]).route(AIRequest(prompt="hello"))

    assert result.provider_name == "backup"
    assert provider_a.health.failure_count == 1
    assert provider_a.health.consecutive_failures == 1
    assert provider_a.health.last_error_type == "quota_rate_limit"
    assert provider_b.health.success_count == 1
    assert provider_b.health.consecutive_failures == 0


def test_export_state_returns_safe_dashboard_summary_without_raw_prompt_or_key():
    raw_key = "fake-secret-dashboard-key"
    store = MemoryStateStore()
    store.record_failure(
        "gemini",
        "gemini-2.5-flash",
        mask_key_id(raw_key),
        error_type="quota_rate_limit",
        error_message="sensitive prompt must not appear",
        cooldown_until=time.time() + 30,
    )
    store.record_success("openrouter", "free-model", "openrouter_1", latency_ms=123)
    router = AIRouter([], state_store=store)

    exported = router.export_state()
    exported_text = str(exported)

    assert exported["summary"]["total"] == 2
    assert exported["summary"]["healthy"] == 1
    assert exported["summary"]["cooldown"] == 1
    assert exported["summary"]["next_retry_after_seconds"] is not None
    assert raw_key not in exported_text
    assert "sensitive prompt must not appear" not in exported_text
    assert "****-key" in exported_text


def test_async_route_and_route_outcome_succeed_with_sync_provider_fallback():
    router = AIRouter([provider_success("async_backup")])

    result = asyncio.run(router.aroute(AIRequest(prompt="hello")))
    outcome = asyncio.run(router.aroute_outcome(AIRequest(prompt="hello")))

    assert result.provider_name == "async_backup"
    assert outcome.status == "success"
    assert outcome.result is not None
    assert outcome.result.provider_name == "async_backup"


def test_task_aware_policy_prefers_longform_translation_capability():
    openrouter = CandidateProvider(
        "openrouter",
        [AIResult("cheap", "openrouter")],
        candidates=[ProviderCandidate(provider=None, model="meta-llama/llama-3.3-70b-instruct:free")],
    )
    gemini = CandidateProvider(
        "gemini",
        [AIResult("long", "gemini")],
        candidates=[ProviderCandidate(provider=None, model="gemini-2.5-flash")],
    )
    router = AIRouter([openrouter, gemini], policy=RouterPolicy(task_type="translation_longform"))

    result = router.route(AIRequest(prompt="chapter"))

    assert result.provider_name == "gemini"
    assert gemini.calls == 1
    assert openrouter.calls == 0


def test_request_task_type_overrides_policy_task_type():
    openrouter = CandidateProvider(
        "openrouter",
        [AIResult("cheap", "openrouter")],
        candidates=[ProviderCandidate(provider=None, model="meta-llama/llama-3.3-70b-instruct:free")],
    )
    gemini = CandidateProvider(
        "gemini",
        [AIResult("long", "gemini")],
        candidates=[ProviderCandidate(provider=None, model="gemini-2.5-flash")],
    )
    router = AIRouter([gemini, openrouter], policy=RouterPolicy(task_type="translation_longform"))

    result = router.route(AIRequest(prompt="short", metadata={"task_type": "cheap_generation"}))

    assert result.provider_name == "openrouter"
    assert openrouter.calls == 1
    assert gemini.calls == 0



def test_budget_guard_blocks_provider_call_and_route_outcome_reports_budget_exceeded():
    provider = provider_success("primary")
    router = AIRouter([provider], policy=RouterPolicy(max_estimated_input_tokens=100))

    outcome = router.route_outcome(AIRequest(prompt="large", metadata={"estimated_input_tokens": 101}))

    assert outcome.status == "failed"
    assert outcome.error_type == "budget_exceeded"
    assert provider.calls == 0
    assert outcome.attempts[0].reason == "budget_exceeded"


def test_budget_guard_allows_under_budget_request():
    provider = provider_success("primary")
    router = AIRouter([provider], policy=RouterPolicy(max_estimated_output_tokens=100))

    result = router.route(AIRequest(prompt="small", metadata={"estimated_output_tokens": 99}))

    assert result.provider_name == "primary"
    assert provider.calls == 1


def test_backoff_grows_with_failure_streak_and_respects_retry_after():
    router = AIRouter([], policy=RouterPolicy(backoff_base_seconds=10, backoff_max_seconds=60, backoff_jitter_ratio=0.2))

    first = router._cooldown_seconds_for_error("transport_error", None, failure_streak=1)
    third = router._cooldown_seconds_for_error("transport_error", None, failure_streak=3)
    retry_after = router._cooldown_seconds_for_error("transport_error", 50, failure_streak=1)

    assert first == 11
    assert third == 44
    assert retry_after >= 50


def test_quota_backoff_uses_retry_after_as_minimum():
    router = AIRouter([], policy=RouterPolicy(quota_cooldown_seconds=20, backoff_max_seconds=120))

    cooldown = router._cooldown_seconds_for_error("quota_rate_limit", 90, failure_streak=1)

    assert cooldown >= 90


class StreamingProvider(CandidateProvider):
    def stream_generate(self, request):
        yield AIStreamChunk(text="part-1", provider_name=self.name, done=False)
        yield AIStreamChunk(text="part-2", provider_name=self.name, done=True)

    async def astream_generate(self, request):
        yield AIStreamChunk(text="apart-1", provider_name=self.name, done=False)
        yield AIStreamChunk(text="apart-2", provider_name=self.name, done=True)


def test_stream_falls_back_to_single_route_chunk_and_sanitizes_metadata():
    provider = CandidateProvider("primary", [AIResult("hello", "primary", metadata={"api_key": "secret", "safe": "ok"})])
    router = AIRouter([provider])

    chunks = list(router.stream(AIRequest(prompt="hello")))

    assert len(chunks) == 1
    assert chunks[0].text == "hello"
    assert chunks[0].done is True
    assert chunks[0].metadata["api_key"] == "[REDACTED]"
    assert chunks[0].metadata["safe"] == "ok"


def test_stream_uses_provider_stream_generate_when_available():
    provider = StreamingProvider("streamer", [])
    router = AIRouter([provider])

    chunks = list(router.stream(AIRequest(prompt="hello")))

    assert [chunk.text for chunk in chunks] == ["part-1", "part-2"]
    assert chunks[-1].done is True


def test_astream_falls_back_to_single_async_route_chunk():
    provider = CandidateProvider("primary", [AIResult("hello", "primary")])
    router = AIRouter([provider])

    async def collect():
        return [chunk async for chunk in router.astream(AIRequest(prompt="hello"))]

    chunks = asyncio.run(collect())

    assert len(chunks) == 1
    assert chunks[0].text == "hello"
    assert chunks[0].done is True


def test_astream_uses_provider_astream_generate_when_available():
    provider = StreamingProvider("streamer", [])
    router = AIRouter([provider])

    async def collect():
        return [chunk async for chunk in router.astream(AIRequest(prompt="hello"))]

    chunks = asyncio.run(collect())

    assert [chunk.text for chunk in chunks] == ["apart-1", "apart-2"]
    assert chunks[-1].done is True


def test_weighted_mode_pack_changes_candidate_selection():
    fast = CandidateProvider("fast", [AIResult("fast", "fast")], candidates=[ProviderCandidate(provider=None, model="m-fast")])
    cheap = CandidateProvider("cheap", [AIResult("cheap", "cheap")], candidates=[ProviderCandidate(provider=None, model="m-cheap")])
    fast.health.last_latency_ms = 20
    cheap.health.last_latency_ms = 2000
    overrides = {
        ("fast", "m-fast"): ModelCapability("fast", "m-fast", cost_tier="premium"),
        ("cheap", "m-cheap"): ModelCapability("cheap", "m-cheap", cost_tier="free"),
    }

    fast_result = AIRouter([cheap, fast], policy=RouterPolicy(routing_mode="fast", capability_overrides=overrides)).route(AIRequest("x"))
    cheap_result = AIRouter([fast, cheap], policy=RouterPolicy(routing_mode="cheap", capability_overrides=overrides)).route(AIRequest("x"))

    assert fast_result.provider_name == "fast"
    assert cheap_result.provider_name == "cheap"


def test_quota_block_skips_provider_without_calling_it():
    blocked = provider_success("blocked")
    quota = InMemoryQuotaTracker([ProviderQuotaProfile("blocked", policy=CapacityPolicy(enabled=False))])

    with pytest.raises(RouterError) as exc_info:
        AIRouter([blocked], quota_tracker=quota).route(AIRequest("x"))

    assert blocked.calls == 0
    assert exc_info.value.attempts[0]["reason"] == "quota_block"


def test_router_reconciles_usage_and_adds_safe_accounting_metadata():
    provider = CandidateProvider(
        "metered",
        [AIResult("ok", "metered", metadata={"token_usage": {"input_tokens": 4, "output_tokens": 2, "total_tokens": 6}})],
        candidates=[ProviderCandidate(provider=None, model="m")],
    )
    capability = ModelCapability(
        "metered",
        "m",
        input_cost_per_million=1.0,
        output_cost_per_million=2.0,
        source_url="https://example.test/catalog",
        verified_at="2026-07-23",
        confidence="verified",
    )
    quota = InMemoryQuotaTracker([ProviderQuotaProfile("metered", "m", policy=CapacityPolicy(tokens_per_minute=100))])
    router = AIRouter([provider], policy=RouterPolicy(capability_overrides={("metered", "m"): capability}), quota_tracker=quota)

    result = router.route(AIRequest("x", metadata={"estimated_total_tokens": 10}))
    usage = quota.snapshot()["profiles"][0]["usage"]

    assert usage["tokens_last_minute"] == 6
    assert result.metadata["cost_estimate"]["status"] == "estimated"
    assert result.metadata["catalog_provenance"]["confidence"] == "verified"
    assert result.metadata["routing"]["mode"] == "balanced"
    assert "components" in result.metadata["routing"]
