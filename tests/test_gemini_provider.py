from nakazasen_ai_router import AIRequest, create_router_from_env
from nakazasen_ai_router.registry import PROVIDER_REGISTRY
from nakazasen_ai_router.providers.openai_compatible import OpenAICompatibleProvider
from scripts.live_smoke import DEFAULT_LOCAL_KEY_FILE, parse_args, read_key_from_file


class MockHTTPClient:
    def __init__(self):
        self.calls = []
        self.get_calls = []

    def get(self, url, *, headers=None, timeout):
        self.get_calls.append({"url": url, "headers": dict(headers or {}), "timeout": timeout})
        return type("Response", (), {"status_code": 200, "headers": {}, "json": lambda self: {"models": []}})()

    def post(self, url, *, headers, json, timeout):
        self.calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return type("Response", (), {"status_code": 200, "headers": {}, "json": lambda self: {"choices": [{"message": {"content": "OK"}}]}})()


def test_registry_has_gemini_profile():
    profile = PROVIDER_REGISTRY["gemini"]

    assert profile.api_key_env_var == "GEMINI_API_KEY"
    assert profile.base_url == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    assert profile.default_models[0] == "gemini-3.6-flash"
    assert profile.is_cloud is True


def test_env_gemini_key_creates_provider():
    router = create_router_from_env(
        env={"GEMINI_API_KEY": "fake-gemini-key"},
        provider_names=("gemini",),
        http_client_factory=MockHTTPClient(),
    )

    assert [candidate.provider.name for candidate in router.providers] == ["gemini"]


def test_env_without_gemini_key_skips_provider():
    router = create_router_from_env(env={}, provider_names=("gemini",), http_client_factory=MockHTTPClient())

    assert router.providers == []


def test_gemini_full_chat_completions_url_is_not_modified():
    provider = OpenAICompatibleProvider(
        name="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        api_keys=("fake-gemini-key",),
        models=("gemini-3.5-flash",),
        is_cloud=True,
        http_client=MockHTTPClient(),
    )

    assert provider._chat_completions_url() == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"


def test_live_free_first_places_gemini_first_when_key_exists():
    router = create_router_from_env(
        env={
            "GEMINI_API_KEY": "fake-gemini-key",
            "DEEPSEEK_API_KEY": "fake-deepseek-key",
        },
        strategy="live_free_first",
        http_client_factory=MockHTTPClient(),
    )

    assert [candidate.provider.name for candidate in router.providers[:2]] == ["gemini", "deepseek"]


def test_fake_gemini_key_not_in_result_logs_or_attempts(caplog):
    client = MockHTTPClient()
    raw_key = "fake-gemini-private-value"
    router = create_router_from_env(
        env={"GEMINI_API_KEY": raw_key},
        provider_names=("gemini",),
        http_client_factory=client,
    )

    result = router.route(AIRequest(prompt="hello"))
    combined = f"{result.metadata} {caplog.text}"

    assert raw_key not in combined
    assert "****alue" in combined


def test_live_smoke_key_parser_accepts_gemini_formats(tmp_path):
    key_file = tmp_path / "keys.txt"
    key_file.write_text("Gemini\nfake-gemini-key\nGoogle AI Studio: fake-google-ai-key\n", encoding="utf-8")

    assert read_key_from_file(key_file, "GEMINI_API_KEY", "gemini") == "fake-gemini-key"


def test_live_smoke_argparse_uses_ignored_local_key_file_by_default(monkeypatch):
    monkeypatch.setattr("sys.argv", ["live_smoke.py", "--provider", "gemini"])

    args = parse_args()

    assert args.key_file == str(DEFAULT_LOCAL_KEY_FILE)
    assert DEFAULT_LOCAL_KEY_FILE.name == "API Key.txt"


def test_live_smoke_argparse_accepts_gemini(monkeypatch):
    monkeypatch.setattr("sys.argv", ["live_smoke.py", "--provider", "gemini", "--key-file", "keys.txt"])

    args = parse_args()

    assert args.provider == "gemini"


GEMINI_MODELS = (
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
)


def test_gemini_model_catalog_contains_all_configured_models():
    assert PROVIDER_REGISTRY["gemini"].default_models == GEMINI_MODELS


def test_startup_model_refresh_uses_gemini_discovery_endpoint():
    client = MockHTTPClient()
    raw_key = "fake-gemini-key"

    router = create_router_from_env(
        env={"GEMINI_API_KEY": raw_key},
        provider_names=("gemini",),
        http_client_factory=client,
        enable_network=True,
        refresh_models_on_startup=True,
    )

    assert client.get_calls[0]["url"] == "https://generativelanguage.googleapis.com/v1beta/models"
    assert client.get_calls[0]["headers"]["X-Goog-Api-Key"] == raw_key
    assert raw_key not in client.get_calls[0]["url"]
    assert router.providers[0].provider.models == list(GEMINI_MODELS)


def test_live_smoke_model_override_uses_requested_model(tmp_path):
    from scripts.live_smoke import run_provider

    key_file = tmp_path / "keys.txt"
    key_file.write_text("Gemini\nfake-gemini-key\n", encoding="utf-8")
    row = run_provider("gemini", key_file, model="gemma-3-1b-it", http_client_factory=MockHTTPClient())

    assert row["status"] == "PASS"
    assert row["model"] == "gemma-3-1b-it"


def test_live_smoke_test_all_models_with_mock(tmp_path):
    from scripts.live_smoke import run_models

    key_file = tmp_path / "keys.txt"
    key_file.write_text("Gemini\nfake-gemini-key\n", encoding="utf-8")
    rows = run_models("gemini", key_file, test_all_models=True, http_client_factory=MockHTTPClient())

    assert [row["model"] for row in rows] == list(GEMINI_MODELS)
    assert {row["status"] for row in rows} == {"PASS"}


def test_configured_gemini_models_use_current_stable_general_models():
    models = PROVIDER_REGISTRY["gemini"].default_models

    assert "gemini-3.5-flash-lite" in models
    assert "gemini-2.5-pro" in models
    assert "gemini-flash-latest" not in models
    assert "gemini-flash-lite-latest" not in models
    assert "gemini-3.1-flash-lite-preview" not in models


def test_live_smoke_writes_safe_health_cache(tmp_path):
    from scripts.live_smoke import run_provider, update_health_cache

    key_file = tmp_path / "keys.txt"
    cache_file = tmp_path / "health.json"
    key_file.write_text("Gemini\nfake-gemini-key\n", encoding="utf-8")
    row = run_provider("gemini", key_file, model="gemini-3.5-flash", http_client_factory=MockHTTPClient())
    update_health_cache(cache_file, row)
    content = cache_file.read_text(encoding="utf-8")

    assert "gemini-3.5-flash" in content
    assert "fake-gemini-key" not in content
    assert "Reply with OK" not in content
    assert "Authorization" not in content
    assert "choices" not in content
