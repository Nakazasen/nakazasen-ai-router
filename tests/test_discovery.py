from nakazasen_ai_router.discovery import (
    DiscoveredModel,
    ProviderModelDiscoveryError,
    discover_provider_models,
)
from nakazasen_ai_router.registry import PROVIDER_REGISTRY


class MockResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.text = "{}"

    def json(self):
        return self.payload


class MockHTTPClient:
    def __init__(self, pages):
        self.pages = list(pages)
        self.urls = []
        self.headers = []

    def get(self, url, *, headers=None, timeout):
        self.urls.append(url)
        self.headers.append(dict(headers or {}))
        return self.pages.pop(0)


def test_gemini_discovery_parses_and_normalizes_models():
    client = MockHTTPClient([
        MockResponse(
            {
                "models": [
                    {
                        "name": "models/gemini-new",
                        "displayName": "Gemini New",
                        "supportedActions": ["generateContent"],
                        "inputTokenLimit": 123,
                        "outputTokenLimit": 456,
                    }
                ]
            }
        )
    ])

    models = discover_provider_models("gemini", api_key="fake-gemini-key", http_client=client)

    assert models == [
        DiscoveredModel(
            provider="gemini",
            model="gemini-new",
            display_name="Gemini New",
            supported_actions=("generateContent",),
            input_token_limit=123,
            output_token_limit=456,
        )
    ]


def test_gemini_discovery_filters_embedding_only_models():
    client = MockHTTPClient([
        MockResponse(
            {
                "models": [
                    {"name": "models/text-embedding", "supportedActions": ["embedContent"]},
                    {"name": "models/gemini-chat", "supportedActions": ["generateContent"]},
                ]
            }
        )
    ])

    models = discover_provider_models("gemini", api_key="fake-gemini-key", http_client=client)

    assert [model.model for model in models] == ["gemini-chat"]


def test_gemini_discovery_pagination():
    client = MockHTTPClient([
        MockResponse({"models": [{"name": "models/gemini-a", "supportedActions": ["generateContent"]}], "nextPageToken": "next"}),
        MockResponse({"models": [{"name": "models/gemini-b", "supportedActions": ["generateContent"]}]}),
    ])

    models = discover_provider_models("gemini", api_key="fake-gemini-key", http_client=client)

    assert [model.model for model in models] == ["gemini-a", "gemini-b"]
    assert "pageToken=next" in client.urls[1]


def test_openai_compatible_discovery_uses_models_endpoint_and_filters_non_chat_models():
    client = MockHTTPClient([
        MockResponse(
            {
                "data": [
                    {"id": "deepseek-v5-chat", "context_length": 256000},
                    {"id": "text-embedding-v4"},
                    {"id": "whisper-v3"},
                ]
            }
        )
    ])

    models = discover_provider_models(
        "deepseek",
        api_key="fake-deepseek-key",
        base_url="https://api.deepseek.com/v1",
        http_client=client,
    )

    assert [model.model for model in models] == ["deepseek-v5-chat"]
    assert client.urls == ["https://api.deepseek.com/v1/models"]
    assert client.headers[0]["Authorization"] == "Bearer fake-deepseek-key"
    assert "fake-deepseek-key" not in str(models)


def test_openai_compatible_discovery_rejects_invalid_catalog_payload():
    client = MockHTTPClient([MockResponse({"data": {}})])

    try:
        discover_provider_models("groq", api_key="fake-groq-key", http_client=client)
    except ProviderModelDiscoveryError as exc:
        assert "data list" in str(exc)
    else:
        raise AssertionError("invalid model catalog should fail safely")


def test_discovery_does_not_print_key(capsys):
    client = MockHTTPClient([MockResponse({"models": []})])

    discover_provider_models("gemini", api_key="fake-gemini-key", http_client=client)

    captured = capsys.readouterr()
    assert "fake-gemini-key" not in captured.out
    assert "fake-gemini-key" not in captured.err


def test_gemini_default_models_are_current_stable_general_models():
    assert PROVIDER_REGISTRY["gemini"].default_models == (
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro",
    )
