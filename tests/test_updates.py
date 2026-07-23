from datetime import date
from types import SimpleNamespace

import pytest

from nakazasen_ai_router.cli import main
from nakazasen_ai_router.updates import UpdateInfo, check_for_updates, clear_update_cache


class Response:
    status_code = 200

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class Client:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return Response(self.payload)


def test_update_check_is_network_disabled_by_default():
    client = Client([{"name": "v9.0.0"}])
    info = check_for_updates(current_version="0.4.0", http_client=client)
    assert info.status == "network_disabled"
    assert client.calls == 0


def test_update_check_finds_latest_stable_and_ignores_prerelease():
    client = Client([{"name": "v0.5.0-rc.1"}, {"name": "v0.4.1"}, {"name": "bad"}])
    info = check_for_updates(enable_network=True, current_version="0.4.0", http_client=client, cache_ttl_seconds=0)
    assert info.latest_version == "0.4.1"
    assert info.update_available is True


def test_update_check_preserves_opt_in_prerelease_and_orders_semver():
    prerelease = check_for_updates(
        enable_network=True,
        current_version="0.4.0",
        include_prerelease=True,
        http_client=Client([{"name": "v0.5.0-rc.2"}, {"name": "v0.5.0-rc.10"}]),
        cache_ttl_seconds=0,
    )
    assert prerelease.latest_version == "0.5.0-rc.10"
    assert prerelease.update_available is True

    stable = check_for_updates(
        enable_network=True,
        current_version="0.5.0-rc.10",
        include_prerelease=True,
        http_client=Client([{"name": "v0.5.0-rc.10"}, {"name": "v0.5.0"}]),
        cache_ttl_seconds=0,
    )
    assert stable.latest_version == "0.5.0"
    assert stable.update_available is True


def test_update_check_failure_is_safe_data():
    info = check_for_updates(enable_network=True, current_version="0.4.0", http_client=Client(error=TimeoutError()), cache_ttl_seconds=0)
    assert info.status == "check_failed"
    assert info.error_type == "timeout"


def test_update_check_uses_process_cache():
    clear_update_cache()
    client = Client([{"name": "v0.4.0"}])
    first = check_for_updates(enable_network=True, current_version="0.4.0", http_client=client, clock=lambda: 100)
    second = check_for_updates(enable_network=True, current_version="0.4.0", http_client=client, clock=lambda: 101)
    assert first == second
    assert client.calls == 1


def test_cli_check_never_calls_subprocess():
    def forbidden(*args, **kwargs):
        raise AssertionError("subprocess must not run")

    code = main(["update", "--check"], subprocess_run=forbidden, update_checker=lambda **kwargs: UpdateInfo("0.4.0", "0.4.1", "update_available"))
    assert code == 0


def test_cli_apply_uses_current_interpreter_and_exact_tag(monkeypatch):
    seen = []
    monkeypatch.setattr("nakazasen_ai_router.cli.sys.executable", "python-under-test")
    code = main(
        ["update", "--apply", "--yes"],
        update_checker=lambda **kwargs: UpdateInfo("0.4.0", "0.4.1", "update_available"),
        subprocess_run=lambda command, **kwargs: seen.append(command) or SimpleNamespace(returncode=0),
    )
    assert code == 0
    assert seen[0][:4] == ["python-under-test", "-m", "pip", "install"]
    assert seen[0][-1].endswith("@v0.4.1")
