import logging
from email.utils import format_datetime
from datetime import datetime, timedelta, timezone

import pytest

from nakazasen_ai_router import AIRouter, AIRequest, ProviderBase, ProviderCandidate, ProviderError, RouterError, RouterPolicy
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
