from nakazasen_ai_router import create_router_from_env
from nakazasen_ai_router.registry import PROVIDER_REGISTRY


class MockHTTPClient:
    def post(self, url, *, headers, json, timeout):
        return type(
            "Response",
            (),
            {"status_code": 200, "headers": {}, "json": lambda self: {"choices": [{"message": {"content": "OK"}}]}},
        )()


def test_deepseek_default_models_use_current_v4_identifiers():
    models = PROVIDER_REGISTRY["deepseek"].default_models

    assert models == ("deepseek-v4-flash", "deepseek-v4-pro")
    assert "deepseek-chat" not in models
    assert "deepseek-reasoner" not in models


def test_env_deepseek_key_creates_provider_with_current_v4_models():
    router = create_router_from_env(
        env={"DEEPSEEK_API_KEY": "fake-deepseek-key"},
        provider_names=("deepseek",),
        http_client_factory=MockHTTPClient(),
    )

    assert [candidate.provider.name for candidate in router.providers] == ["deepseek"]
    assert tuple(router.providers[0].provider.models) == ("deepseek-v4-flash", "deepseek-v4-pro")
