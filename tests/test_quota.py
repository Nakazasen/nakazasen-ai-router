import json

from nakazasen_ai_router import (
    CapacityPolicy,
    InMemoryQuotaTracker,
    ProviderQuotaProfile,
    QuotaDecision,
    sort_profiles_for_fallback,
)


def profile(provider="p", model="", key_id="", **policy_kwargs):
    return ProviderQuotaProfile(provider, model, key_id, CapacityPolicy(**policy_kwargs))


def test_no_profile_defaults_to_allow():
    assert InMemoryQuotaTracker().check("unknown").decision == QuotaDecision.ALLOW


def test_disabled_policy_blocks():
    tracker = InMemoryQuotaTracker([profile(enabled=False)])
    check = tracker.check("p")
    assert check.decision == QuotaDecision.BLOCK
    assert check.reason == "disabled"


def test_rpm_limit_throttles_after_reserves():
    tracker = InMemoryQuotaTracker([profile(requests_per_minute=2)])
    assert tracker.reserve("p", now=0).decision == QuotaDecision.ALLOW
    assert tracker.reserve("p", now=1).decision == QuotaDecision.ALLOW
    check = tracker.reserve("p", now=2)
    assert check.decision == QuotaDecision.THROTTLE
    assert check.reason == "rpm_limit"


def test_tpm_limit_throttles_based_on_estimated_tokens():
    tracker = InMemoryQuotaTracker([profile(tokens_per_minute=10)])
    assert tracker.reserve("p", estimated_tokens=6, now=0).decision == QuotaDecision.ALLOW
    check = tracker.reserve("p", estimated_tokens=5, now=1)
    assert check.decision == QuotaDecision.THROTTLE
    assert check.reason == "tpm_limit"


def test_daily_request_cap_blocks_after_reserve():
    tracker = InMemoryQuotaTracker([profile(requests_per_day=1)])
    assert tracker.reserve("p", now=0).decision == QuotaDecision.ALLOW
    check = tracker.reserve("p", now=1)
    assert check.decision == QuotaDecision.BLOCK
    assert check.reason == "daily_limit"


def test_concurrency_limit_throttles_until_release():
    tracker = InMemoryQuotaTracker([profile(max_concurrency=1)])
    assert tracker.reserve("p").decision == QuotaDecision.ALLOW
    assert tracker.reserve("p").decision == QuotaDecision.THROTTLE
    tracker.release("p")
    assert tracker.reserve("p").decision == QuotaDecision.ALLOW


def test_release_does_not_decrement_below_zero():
    tracker = InMemoryQuotaTracker([profile(max_concurrency=1)])
    tracker.release("p")
    assert tracker.snapshot()["profiles"][0]["usage"]["in_flight"] == 0


def test_exact_profile_overrides_provider_only():
    tracker = InMemoryQuotaTracker([
        profile("p", requests_per_minute=0),
        profile("p", "m", "k", requests_per_minute=2),
    ])
    assert tracker.reserve("p", "m", "k", now=0).decision == QuotaDecision.ALLOW


def test_provider_model_profile_overrides_provider_only():
    tracker = InMemoryQuotaTracker([
        profile("p", requests_per_minute=0),
        profile("p", "m", requests_per_minute=1),
    ])
    assert tracker.reserve("p", "m", now=0).decision == QuotaDecision.ALLOW
    assert tracker.reserve("p", "m", now=1).decision == QuotaDecision.THROTTLE


def test_snapshot_does_not_include_raw_key_or_secret_markers():
    tracker = InMemoryQuotaTracker([profile("p", "m", "secret-key", requests_per_minute=1)])
    tracker.reserve("p", "m", "secret-key", now=0)
    blob = json.dumps(tracker.snapshot()).lower()
    assert "secret-key" not in blob
    assert "authorization" not in blob
    assert "prompt" not in blob


def test_record_failure_sanitizes_error_type():
    tracker = InMemoryQuotaTracker([profile()])
    tracker.record_failure("p", error_type="authorization bearer secret")
    assert tracker.snapshot()["profiles"][0]["usage"]["last_error_type"] == "redacted"


def test_fallback_sorting_respects_enabled_priority_and_cost():
    profiles = [
        profile("premium", cost_tier="premium", fallback_priority=1),
        profile("cheap", cost_tier="cheap", fallback_priority=1),
        profile("disabled", enabled=False, fallback_priority=0),
        profile("free", cost_tier="free", fallback_priority=5),
    ]
    ordered = sort_profiles_for_fallback(profiles)
    assert [item.provider for item in ordered] == ["cheap", "premium", "free", "disabled"]
