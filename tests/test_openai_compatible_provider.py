import logging

import pytest

from nakazasen_ai_router import AIRouter, AIRequest, ProviderError, RouterError, RouterPolicy
from nakazasen_ai_router.providers import OpenAICompatibleProvider


class MockResponse:
    def __init__(self, status_code=200, payload=None, headers=None, text=None):
        self.status_code = status_code
        self.payload = payload
        self.headers = headers or {}
        self.text = text

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload

    def __str__(self):
        return f"MockResponse(status_code={self.status_code})"


class MockHTTPClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, *, headers, json, timeout):
        self.calls.append({"url": url, "headers": dict(headers), "json": json, "timeout": timeout})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class MockAsyncHTTPClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def post(self, url, *, headers, json, timeout):
        self.calls.append({"url": url, "headers": dict(headers), "json": json, "timeout": timeout})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def make_provider(http_client, *, async_http_client=None, api_keys=None, models=None):
    return OpenAICompatibleProvider(
        name="openai_like",
        base_url="https://example.test/v1",
        api_keys=api_keys or ["fake-test-secret-1234"],
        models=models or ["model-a"],
        is_cloud=True,
        http_client=http_client,
        async_http_client=async_http_client,
        timeout=5,
    )


def success_response(content="hello", usage=None):
    payload = {"choices": [{"message": {"content": content}}]}
    if usage is not None:
        payload["usage"] = usage
    return MockResponse(payload=payload)


def test_mock_success_returns_content_and_builds_chat_completion_request():
    client = MockHTTPClient([success_response("xin chao")])
    provider = make_provider(client)

    result = provider.generate(AIRequest(prompt="hello"))

    assert result.text == "xin chao"
    assert client.calls[0]["url"] == "https://example.test/v1/chat/completions"
    assert client.calls[0]["json"] == {"model": "model-a", "messages": [{"role": "user", "content": "hello"}]}


def test_success_normalizes_usage_without_copying_raw_provider_fields():
    usage = {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8, "raw_secret": "must-not-leak"}
    provider = make_provider(MockHTTPClient([success_response("ok", usage)]))

    result = provider.generate(AIRequest(prompt="hello"))

    assert result.metadata["token_usage"] == {
        "input_tokens": 5,
        "output_tokens": 3,
        "total_tokens": 8,
        "source": "provider_reported",
    }
    assert "must-not-leak" not in str(result.metadata)


def test_messages_metadata_is_used_when_present():
    client = MockHTTPClient([success_response("ok")])
    provider = make_provider(client)
    messages = [{"role": "system", "content": "be short"}, {"role": "user", "content": "hi"}]

    provider.generate(AIRequest(prompt="ignored", metadata={"messages": messages}))

    assert client.calls[0]["json"]["messages"] == messages


def test_authorization_header_used_but_key_not_in_result_attempts_or_logs(caplog):
    raw_key = "fake-real-secret-value"
    client = MockHTTPClient([success_response("ok")])
    provider = make_provider(client, api_keys=[raw_key])
    router = AIRouter([provider])

    with caplog.at_level(logging.INFO):
        result = router.route(AIRequest(prompt="secret prompt"))

    assert client.calls[0]["headers"]["Authorization"] == f"Bearer {raw_key}"
    combined = f"{result.metadata} {caplog.text}"
    assert raw_key not in combined
    assert "****alue" in combined


def test_401_and_403_classify_auth_and_disable_provider_runtime():
    for status in (401, 403):
        client = MockHTTPClient([MockResponse(status_code=status, payload={"error": {"message": "bad key"}}), success_response("backup")])
        provider = make_provider(client)
        backup = make_provider(client, api_keys=["backup-key"], models=["backup-model"])
        backup.name = "backup"

        result = AIRouter([provider, backup]).route(AIRequest(prompt="hello"))

        assert result.provider_name == "backup"
        assert provider.health.enabled is False
        assert provider.health.last_error_type == "auth_failure"


def test_429_classifies_quota_and_uses_retry_after_cooldown():
    client = MockHTTPClient([
        MockResponse(status_code=429, payload={"error": {"message": "rate limit"}}, headers={"Retry-After": "9"}),
        success_response("backup"),
    ])
    provider = make_provider(client)
    backup = make_provider(client, api_keys=["backup-key"], models=["backup-model"])
    backup.name = "backup"

    result = AIRouter([provider, backup]).route(AIRequest(prompt="hello"))

    assert result.provider_name == "backup"
    assert provider.health.last_error_type == "quota_rate_limit"
    remaining = provider.health.cooldown_until - __import__("time").time()
    assert 0 < remaining <= 10


def test_5xx_classifies_provider_5xx():
    client = MockHTTPClient([MockResponse(status_code=503, payload={"error": {"message": "service unavailable"}})])
    provider = make_provider(client)

    with pytest.raises(RouterError) as exc_info:
        AIRouter([provider]).route(AIRequest(prompt="hello"))

    assert provider.health.last_error_type == "provider_5xx"
    assert exc_info.value.attempts[0]["reason"] == "provider_5xx"


def test_timeout_classifies_timeout():
    client = MockHTTPClient([TimeoutError("timed out")])
    provider = make_provider(client)

    with pytest.raises(RouterError) as exc_info:
        AIRouter([provider]).route(AIRequest(prompt="hello"))

    assert provider.health.last_error_type == "timeout"
    assert exc_info.value.attempts[0]["reason"] == "timeout"


def test_model_key_candidate_rotation_creates_cartesian_product_and_masks_keys():
    client = MockHTTPClient([])
    provider = make_provider(client, api_keys=["fake-one-1111", "fake-two-2222"], models=["m1", "m2"])

    candidates = provider.iter_candidates()

    assert [(c.model, c.key_index, c.key_id) for c in candidates] == [
        ("m1", 0, "****1111"),
        ("m1", 1, "****2222"),
        ("m2", 0, "****1111"),
        ("m2", 1, "****2222"),
    ]
    assert "fake-one-1111" not in str(candidates)
    assert "fake-two-2222" not in str(candidates)


def test_prompt_not_in_attempts_by_default():
    client = MockHTTPClient([MockResponse(status_code=429, payload={"error": {"message": "quota"}})])
    provider = make_provider(client)

    with pytest.raises(RouterError) as exc_info:
        AIRouter([provider]).route(AIRequest(prompt="do not leak this prompt"))

    assert "do not leak this prompt" not in str(exc_info.value.attempts)


def test_missing_content_and_invalid_json_raise_safe_provider_error():
    missing = make_provider(MockHTTPClient([MockResponse(payload={"choices": [{"message": {}}]})]))
    with pytest.raises(ProviderError, match="message content"):
        missing.generate(AIRequest(prompt="hello"))

    invalid = make_provider(MockHTTPClient([MockResponse(payload=ValueError("bad json"))]))
    with pytest.raises(ProviderError, match="not valid JSON"):
        invalid.generate(AIRequest(prompt="hello"))


def test_local_only_does_not_call_cloud_openai_provider():
    client = MockHTTPClient([success_response("should not call")])
    provider = make_provider(client)

    with pytest.raises(RouterError):
        AIRouter([provider], policy=RouterPolicy(local_only=True)).route(AIRequest(prompt="hello"))

    assert client.calls == []


def test_native_async_provider_agenerate_uses_async_client():
    sync_client = MockHTTPClient([])
    async_client = MockAsyncHTTPClient([success_response("async ok")])
    provider = make_provider(sync_client, async_http_client=async_client)

    result = __import__("asyncio").run(provider.agenerate(AIRequest(prompt="hello async")))

    assert result.text == "async ok"
    assert sync_client.calls == []
    assert async_client.calls[0]["json"]["messages"] == [{"role": "user", "content": "hello async"}]


def test_native_async_provider_429_raises_quota_error():
    async_client = MockAsyncHTTPClient([MockResponse(status_code=429, payload={"error": {"message": "rate limit"}})])
    provider = make_provider(MockHTTPClient([]), async_http_client=async_client)

    with pytest.raises(Exception) as exc_info:
        __import__("asyncio").run(provider.agenerate(AIRequest(prompt="hello")))

    assert type(exc_info.value).__name__ == "ProviderQuotaError"
