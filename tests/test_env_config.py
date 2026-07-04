import logging

import pytest

from nakazasen_ai_router import AIRequest, RouterError, create_router_from_env
from nakazasen_ai_router.registry import PROVIDER_REGISTRY


class MockResponse:
    def __init__(self, payload):
        self.status_code = 200
        self.payload = payload
        self.headers = {}

    def json(self):
        return self.payload


class MockHTTPClient:
    def __init__(self):
        self.calls = []

    def post(self, url, *, headers, json, timeout):
        self.calls.append({"url": url, "headers": dict(headers), "json": json, "timeout": timeout})
        return MockResponse({"choices": [{"message": {"content": "ok"}}]})


def test_env_openrouter_key_creates_provider():
    client = MockHTTPClient()
    router = create_router_from_env(
        env={"OPENROUTER_API_KEY": "sk-openrouter-secret"},
        provider_names=("openrouter",),
        http_client_factory=client,
    )

    assert [candidate.provider.name for candidate in router.providers] == ["openrouter"]


def test_env_groq_key_creates_provider():
    client = MockHTTPClient()
    router = create_router_from_env(
        env={"GROQ_API_KEY": "sk-groq-secret"},
        provider_names=("groq",),
        http_client_factory=client,
    )

    assert [candidate.provider.name for candidate in router.providers] == ["groq"]


def test_cloud_provider_without_key_is_skipped():
    router = create_router_from_env(env={}, provider_names=("openrouter", "groq"), http_client_factory=MockHTTPClient())

    assert router.providers == []


def test_local_openai_compatible_can_be_created_without_key_for_local_base_url():
    router = create_router_from_env(
        env={"LOCAL_OPENAI_COMPATIBLE_BASE_URL": "http://127.0.0.1:11434/v1"},
        provider_names=("local_openai_compatible",),
        http_client_factory=MockHTTPClient(),
    )

    assert [candidate.provider.name for candidate in router.providers] == ["local_openai_compatible"]
    assert router.providers[0].provider.is_cloud is False


def test_raw_api_key_not_in_router_repr_logs_or_attempts(caplog):
    raw_key = "sk-openrouter-raw-secret"
    client = MockHTTPClient()
    router = create_router_from_env(
        env={"OPENROUTER_API_KEY": raw_key},
        provider_names=("openrouter",),
        http_client_factory=client,
    )

    with caplog.at_level(logging.INFO):
        result = router.route(AIRequest(prompt="hello"))

    combined = f"{router.providers} {result.metadata} {caplog.text}"
    assert raw_key not in combined
    assert "****cret" in combined


def test_create_router_from_env_injects_mock_http_client_and_does_not_call_internet():
    clients = []

    def factory(profile):
        assert profile.name == "openrouter"
        client = MockHTTPClient()
        clients.append(client)
        return client

    router = create_router_from_env(
        env={"OPENROUTER_API_KEY": "sk-test-only"},
        provider_names=("openrouter",),
        http_client_factory=factory,
    )
    result = router.route(AIRequest(prompt="hello"))

    assert result.text == "ok"
    assert len(clients) == 1
    assert clients[0].calls[0]["url"] == "https://openrouter.ai/api/v1/chat/completions"


def test_registry_contains_expected_provider_profiles():
    expected = {
        "openrouter",
        "groq",
        "deepseek",
        "nvidia_nim",
        "chatanywhere",
        "mistral",
        "local_openai_compatible",
    }

    assert expected.issubset(PROVIDER_REGISTRY)
    for name in expected:
        profile = PROVIDER_REGISTRY[name]
        assert profile.name == name
        assert profile.base_url
        assert profile.default_models
        assert profile.note


def test_no_default_http_client_never_calls_internet():
    router = create_router_from_env(
        env={"OPENROUTER_API_KEY": "sk-test-only"},
        provider_names=("openrouter",),
    )

    with pytest.raises(RouterError) as exc_info:
        router.route(AIRequest(prompt="hello"))

    assert exc_info.value.attempts[0]["reason"] == "unknown_transport_error"
