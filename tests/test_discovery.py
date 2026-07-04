from nakazasen_ai_router.discovery import DiscoveredModel, discover_provider_models
from nakazasen_ai_router.registry import PROVIDER_REGISTRY


class MockResponse:
    def __init__(self, payload):
        self.payload = payload
        self.text = "{}"

    def json(self):
        return self.payload


class MockHTTPClient:
    def __init__(self, pages):
        self.pages = list(pages)
        self.urls = []

    def get(self, url, *, timeout):
        self.urls.append(url)
        return MockResponse(self.pages.pop(0))


def test_gemini_discovery_parses_and_normalizes_models():
    client = MockHTTPClient([
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
        {
            "models": [
                {"name": "models/text-embedding", "supportedActions": ["embedContent"]},
                {"name": "models/gemini-chat", "supportedActions": ["generateContent"]},
            ]
        }
    ])

    models = discover_provider_models("gemini", api_key="fake-gemini-key", http_client=client)

    assert [model.model for model in models] == ["gemini-chat"]


def test_gemini_discovery_pagination():
    client = MockHTTPClient([
        {"models": [{"name": "models/gemini-a", "supportedActions": ["generateContent"]}], "nextPageToken": "next"},
        {"models": [{"name": "models/gemini-b", "supportedActions": ["generateContent"]}]},
    ])

    models = discover_provider_models("gemini", api_key="fake-gemini-key", http_client=client)

    assert [model.model for model in models] == ["gemini-a", "gemini-b"]
    assert "pageToken=next" in client.urls[1]


def test_discovery_does_not_print_key(capsys):
    client = MockHTTPClient([{"models": []}])

    discover_provider_models("gemini", api_key="fake-gemini-key", http_client=client)

    captured = capsys.readouterr()
    assert "fake-gemini-key" not in captured.out
    assert "fake-gemini-key" not in captured.err


def test_gemini_default_models_are_live_pass_only():
    assert PROVIDER_REGISTRY["gemini"].default_models == (
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-3-flash-preview",
        "gemini-flash-latest",
        "gemini-robotics-er-1.6-preview",
    )
