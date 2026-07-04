import logging

import pytest

from nakazasen_ai_router import AIRouter, AIRequest, RouterError, RouterPolicy
from nakazasen_ai_router.fake_providers import (
    provider_fail_auth,
    provider_fail_quota,
    provider_success,
    provider_timeout,
)


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

    with pytest.raises(RouterError):
        router.route(AIRequest(prompt="hello"))

    assert cloud_provider.calls == 0


def test_api_key_is_not_logged(caplog):
    provider = provider_success("safe_provider")
    router = AIRouter([provider])

    with caplog.at_level(logging.INFO):
        router.route(
            AIRequest(
                prompt="hello",
                metadata={
                    "api_key": "sk-real-key-must-not-appear",
                    "nested": {"token": "secret-token-must-not-appear"},
                    "purpose": "test",
                },
            )
        )

    logs = caplog.text
    assert "sk-real-key-must-not-appear" not in logs
    assert "secret-token-must-not-appear" not in logs
    assert "[REDACTED]" in logs
