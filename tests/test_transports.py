import logging

from nakazasen_ai_router import AIRequest, create_router_from_env
from nakazasen_ai_router.http import UrllibHTTPClient


def test_create_router_from_env_enable_network_creates_real_transport_without_calling_it():
    router = create_router_from_env(
        env={"OPENROUTER_API_KEY": "fake-test-only"},
        provider_names=("openrouter",),
        enable_network=True,
    )

    provider = router.providers[0].provider
    assert isinstance(provider.http_client, UrllibHTTPClient)


def test_real_transport_repr_does_not_include_authorization(caplog):
    client = UrllibHTTPClient()

    with caplog.at_level(logging.INFO):
        logging.getLogger("test").info("client=%r", client)

    assert "Authorization" not in repr(client)
    assert "Bearer" not in caplog.text


def test_default_env_router_still_uses_no_network_placeholder():
    router = create_router_from_env(
        env={"OPENROUTER_API_KEY": "fake-test-only"},
        provider_names=("openrouter",),
    )

    assert repr(router.providers[0].provider.http_client) == "NoNetworkHTTPClient()"


def test_enable_network_with_local_provider_creates_transport_without_request():
    router = create_router_from_env(
        env={"LOCAL_OPENAI_COMPATIBLE_BASE_URL": "http://localhost:11434/v1"},
        provider_names=("local_openai_compatible",),
        enable_network=True,
    )

    provider = router.providers[0].provider
    assert isinstance(provider.http_client, UrllibHTTPClient)
    assert provider.is_cloud is False
