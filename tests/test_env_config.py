import logging

import pytest

from nakazasen_ai_router import AIRequest, ProviderError, RouterError, RouterPolicy, create_router_from_env
from nakazasen_ai_router.registry import PROVIDER_REGISTRY


class MockResponse:
    def __init__(self, payload, status_code=200):
        self.status_code = status_code
        self.payload = payload
        self.headers = {}

    def json(self):
        return self.payload


class MockHTTPClient:
    def __init__(self, responses=None, get_responses=None):
        self.calls = []
        self.get_calls = []
        self.responses = list(responses or [])
        self.get_responses = list(get_responses or [])

    def post(self, url, *, headers, json, timeout):
        self.calls.append({"url": url, "headers": dict(headers), "json": json, "timeout": timeout})
        if self.responses:
            response = self.responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response
        return MockResponse({"choices": [{"message": {"content": "ok"}}]})

    def get(self, url, *, headers, timeout):
        self.get_calls.append({"url": url, "headers": dict(headers), "timeout": timeout})
        if self.get_responses:
            response = self.get_responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response
        return MockResponse({"data": []})


def test_env_openrouter_key_creates_provider():
    client = MockHTTPClient()
    router = create_router_from_env(
        env={"OPENROUTER_API_KEY": "fake-openrouter-secret"},
        provider_names=("openrouter",),
        http_client_factory=client,
    )

    assert [candidate.provider.name for candidate in router.providers] == ["openrouter"]


def test_env_groq_key_creates_provider():
    client = MockHTTPClient()
    router = create_router_from_env(
        env={"GROQ_API_KEY": "fake-groq-secret"},
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
    raw_key = "fake-openrouter-raw-secret"
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


def test_plural_api_keys_env_creates_key_pool_candidates():
    router = create_router_from_env(
        env={"GEMINI_API_KEYS": "fake-key-one,fake-key-two; fake-key-three"},
        provider_names=("gemini",),
        http_client_factory=MockHTTPClient(),
    )

    provider = router.providers[0].provider
    candidates = provider.iter_candidates()

    assert provider.api_keys == ["fake-key-one", "fake-key-two", "fake-key-three"]
    assert [candidate.key_index for candidate in candidates[:3]] == [0, 1, 2]
    assert "fake-key-one" not in str(candidates)


def test_plural_and_singular_api_keys_are_merged_and_deduplicated():
    router = create_router_from_env(
        env={
            "OPENROUTER_API_KEYS": " fake-a , fake-b\nfake-a ",
            "OPENROUTER_API_KEY": "fake-c",
        },
        provider_names=("openrouter",),
        http_client_factory=MockHTTPClient(),
    )

    provider = router.providers[0].provider

    assert provider.api_keys == ["fake-a", "fake-b", "fake-c"]


def test_empty_plural_api_key_entries_are_ignored():
    router = create_router_from_env(
        env={"GROQ_API_KEYS": " , ; \n 'fake-groq-one' \n \"fake-groq-two\" "},
        provider_names=("groq",),
        http_client_factory=MockHTTPClient(),
    )

    provider = router.providers[0].provider

    assert provider.api_keys == ["fake-groq-one", "fake-groq-two"]


def test_startup_model_refresh_requires_network_opt_in():
    with pytest.raises(ValueError, match="requires enable_network=True"):
        create_router_from_env(
            env={"DEEPSEEK_API_KEY": "fake-deepseek-key"},
            provider_names=("deepseek",),
            http_client_factory=MockHTTPClient(),
            refresh_models_on_startup=True,
        )


def test_startup_model_refresh_is_disabled_by_default():
    client = MockHTTPClient(get_responses=[MockResponse({"data": [{"id": "deepseek-v5-chat"}]})])

    router = create_router_from_env(
        env={"DEEPSEEK_API_KEY": "fake-deepseek-key"},
        provider_names=("deepseek",),
        http_client_factory=client,
        enable_network=True,
    )

    assert client.get_calls == []
    assert router.providers[0].provider.models == ["deepseek-v4-flash", "deepseek-v4-pro"]


def test_startup_model_refresh_merges_discovered_models_before_static_fallbacks():
    raw_key = "fake-deepseek-key"
    client = MockHTTPClient(
        get_responses=[MockResponse({"data": [{"id": "deepseek-v5-chat"}, {"id": "text-embedding-v4"}, {"id": "deepseek-v4-flash"}]})]
    )

    router = create_router_from_env(
        env={"DEEPSEEK_API_KEY": raw_key},
        provider_names=("deepseek",),
        http_client_factory=client,
        enable_network=True,
        refresh_models_on_startup=True,
    )

    provider = router.providers[0].provider
    assert provider.models == ["deepseek-v5-chat", "deepseek-v4-flash", "deepseek-v4-pro"]
    assert client.get_calls[0]["url"] == "https://api.deepseek.com/v1/models"
    assert client.get_calls[0]["headers"]["Authorization"] == f"Bearer {raw_key}"
    assert raw_key not in str(provider)


def test_startup_model_refresh_failure_keeps_static_models(caplog):
    client = MockHTTPClient(get_responses=[MockResponse({}, status_code=500)])

    with caplog.at_level(logging.WARNING):
        router = create_router_from_env(
            env={"DEEPSEEK_API_KEY": "fake-deepseek-key"},
            provider_names=("deepseek",),
            http_client_factory=client,
            enable_network=True,
            refresh_models_on_startup=True,
        )

    assert router.providers[0].provider.models == ["deepseek-v4-flash", "deepseek-v4-pro"]
    assert "deepseek" in caplog.text
    assert "fake-deepseek-key" not in caplog.text


def test_key_quota_cooldown_falls_back_to_next_key_same_provider():
    client = MockHTTPClient([
        ProviderError("quota", status_code=429, retry_after=30),
        MockResponse({"choices": [{"message": {"content": "key two ok"}}]}),
    ])
    router = create_router_from_env(
        env={"GEMINI_API_KEYS": "fake-key-one,fake-key-two"},
        provider_names=("gemini",),
        http_client_factory=client,
        policy=RouterPolicy(max_attempts=2),
    )

    result = router.route(AIRequest(prompt="hello"))
    states = router.state_store.list_states()

    assert result.text == "key two ok"
    assert len(client.calls) == 2
    assert client.calls[0]["headers"]["Authorization"] == "Bearer fake-key-one"
    assert client.calls[1]["headers"]["Authorization"] == "Bearer fake-key-two"
    assert states[0].key_id == "****-one"
    assert states[0].last_error_type == "quota_rate_limit"
    assert states[0].cooldown_until > 0
    assert states[1].key_id == "****-two"
    assert states[1].success_count == 1


def test_route_outcome_returns_retry_later_when_all_keys_are_cooling_down():
    client = MockHTTPClient([
        ProviderError("quota", status_code=429, retry_after=30),
        ProviderError("quota", status_code=429, retry_after=60),
    ])
    router = create_router_from_env(
        env={"GEMINI_API_KEYS": "fake-key-one,fake-key-two"},
        provider_names=("gemini",),
        http_client_factory=client,
        policy=RouterPolicy(max_attempts=2),
    )

    outcome = router.route_outcome(AIRequest(prompt="hello"))

    assert outcome.status == "retry_later"
    assert outcome.error_type == "all_providers_exhausted"
    assert outcome.retry_after_seconds is not None
    assert 0 < outcome.retry_after_seconds <= 31
    assert [attempt.reason for attempt in outcome.attempts] == ["quota_rate_limit", "quota_rate_limit"]


def test_json_state_path_preserves_key_cooldown_after_restart(tmp_path):
    state_path = tmp_path / "router_state.json"
    first_client = MockHTTPClient([ProviderError("quota", status_code=429, retry_after=60)])
    first_router = create_router_from_env(
        env={"GEMINI_API_KEYS": "fake-key-one"},
        provider_names=("gemini",),
        http_client_factory=first_client,
        policy=RouterPolicy(max_attempts=1),
        state_path=state_path,
    )

    first_outcome = first_router.route_outcome(AIRequest(prompt="hello"))

    assert first_outcome.status == "retry_later"
    assert state_path.exists()

    second_client = MockHTTPClient()
    second_router = create_router_from_env(
        env={"GEMINI_API_KEYS": "fake-key-one"},
        provider_names=("gemini",),
        http_client_factory=second_client,
        policy=RouterPolicy(max_attempts=1),
        state_path=state_path,
    )
    second_outcome = second_router.route_outcome(AIRequest(prompt="hello again"))

    assert second_outcome.status == "retry_later"
    assert second_outcome.attempts[0].reason == "key_cooldown"
    assert second_client.calls == []


def test_sqlite_state_backend_preserves_key_cooldown_after_restart(tmp_path):
    state_path = tmp_path / "router_state.sqlite3"
    first_client = MockHTTPClient([ProviderError("quota", status_code=429, retry_after=60)])
    first_router = create_router_from_env(
        env={"GEMINI_API_KEYS": "fake-key-one"},
        provider_names=("gemini",),
        http_client_factory=first_client,
        policy=RouterPolicy(max_attempts=1),
        state_path=state_path,
        state_backend="sqlite",
    )

    first_outcome = first_router.route_outcome(AIRequest(prompt="hello"))

    assert first_outcome.status == "retry_later"
    assert state_path.exists()

    second_client = MockHTTPClient()
    second_router = create_router_from_env(
        env={"GEMINI_API_KEYS": "fake-key-one"},
        provider_names=("gemini",),
        http_client_factory=second_client,
        policy=RouterPolicy(max_attempts=1),
        state_path=state_path,
        state_backend="sqlite",
    )
    second_outcome = second_router.route_outcome(AIRequest(prompt="hello again"))

    assert second_outcome.status == "retry_later"
    assert second_outcome.attempts[0].reason == "key_cooldown"
    assert second_client.calls == []


def test_async_http_client_factory_is_injected_into_provider():
    async_clients = []

    class AsyncClient:
        async def post(self, url, *, headers, json, timeout):
            return MockResponse(payload={"choices": [{"message": {"content": "async"}}]})

    def factory(profile):
        client = AsyncClient()
        async_clients.append((profile.name, client))
        return client

    router = create_router_from_env(
        env={"GEMINI_API_KEY": "fake-key"},
        provider_names=("gemini",),
        http_client_factory=MockHTTPClient(),
        async_http_client_factory=factory,
    )

    assert async_clients[0][0] == "gemini"
    assert getattr(router.providers[0].provider, "async_http_client") is async_clients[0][1]


def test_create_router_from_env_injects_mock_http_client_and_does_not_call_internet():
    clients = []

    def factory(profile):
        assert profile.name == "openrouter"
        client = MockHTTPClient()
        clients.append(client)
        return client

    router = create_router_from_env(
        env={"OPENROUTER_API_KEY": "fake-test-only"},
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
        env={"OPENROUTER_API_KEY": "fake-test-only"},
        provider_names=("openrouter",),
    )

    with pytest.raises(RouterError) as exc_info:
        router.route(AIRequest(prompt="hello"))

    assert exc_info.value.attempts[0]["reason"] == "unknown_transport_error"
