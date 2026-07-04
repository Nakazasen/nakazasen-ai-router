from nakazasen_ai_router import create_live_free_first_router_from_env, create_router_from_env


class MockHTTPClient:
    def post(self, *args, **kwargs):
        raise AssertionError("unit test must not call network")


def env_for_all_cloud_providers():
    return {
        "DEEPSEEK_API_KEY": "fake-deepseek",
        "NVIDIA_NIM_API_KEY": "fake-nim",
        "CHATANYWHERE_API_KEY": "fake-chatanywhere",
        "MISTRAL_API_KEY": "fake-mistral",
        "OPENROUTER_API_KEY": "fake-openrouter",
        "GROQ_API_KEY": "fake-groq",
    }


def test_live_free_first_strategy_orders_providers():
    router = create_router_from_env(env=env_for_all_cloud_providers(), strategy="live_free_first")

    assert [candidate.provider.name for candidate in router.providers[:6]] == [
        "deepseek",
        "nvidia_nim",
        "chatanywhere",
        "mistral",
        "openrouter",
        "groq",
    ]


def test_live_free_first_without_key_skips_cloud_provider():
    router = create_router_from_env(env={}, provider_names=("deepseek", "groq"), strategy="live_free_first")

    assert router.providers == []


def test_live_free_first_does_not_enable_network_by_default():
    router = create_router_from_env(env=env_for_all_cloud_providers(), provider_names=("deepseek",), strategy="live_free_first")

    assert repr(router.providers[0].provider.http_client) == "NoNetworkHTTPClient()"


def test_live_free_first_convenience_wrapper():
    router = create_live_free_first_router_from_env(env=env_for_all_cloud_providers(), provider_names=("groq", "deepseek"))

    assert [candidate.provider.name for candidate in router.providers] == ["deepseek", "groq"]
