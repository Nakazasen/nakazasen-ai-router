import time

from nakazasen_ai_router import SQLiteStateStore


def test_sqlite_state_store_records_success_and_failure(tmp_path):
    store = SQLiteStateStore(tmp_path / "router_state.sqlite3")

    store.record_failure(
        "gemini",
        "gemini-2.5-flash",
        "gemini_1",
        error_type="quota_rate_limit",
        error_message="quota",
        latency_ms=321,
        cooldown_until=time.time() + 60,
    )
    failed = store.get_key_model_state("gemini", "gemini-2.5-flash", "gemini_1")

    assert failed.status == "cooldown"
    assert failed.failure_count == 1
    assert failed.failure_streak == 1
    assert failed.last_error_type == "quota_rate_limit"
    assert failed.cooldown_until > time.time()

    store.record_success("gemini", "gemini-2.5-flash", "gemini_1", latency_ms=111)
    healthy = store.get_key_model_state("gemini", "gemini-2.5-flash", "gemini_1")

    assert healthy.status == "healthy"
    assert healthy.success_count == 1
    assert healthy.failure_count == 1
    assert healthy.failure_streak == 0
    assert healthy.cooldown_until == 0.0
    assert healthy.last_latency_ms == 111


def test_sqlite_state_store_is_shared_between_instances(tmp_path):
    path = tmp_path / "shared.sqlite3"
    first = SQLiteStateStore(path)
    second = SQLiteStateStore(path)

    first.record_failure(
        "openrouter",
        "free-model",
        "openrouter_1",
        error_type="quota_exhausted_daily",
        cooldown_until=time.time() + 120,
    )

    state = second.get_key_model_state("openrouter", "free-model", "openrouter_1")

    assert state.status == "cooldown"
    assert state.last_error_type == "quota_exhausted_daily"
    assert state.failure_count == 1


def test_sqlite_state_store_list_states_sorted(tmp_path):
    store = SQLiteStateStore(tmp_path / "sorted.sqlite3")

    store.record_success("b", "m", "k")
    store.record_success("a", "m", "k")

    assert [state.provider for state in store.list_states()] == ["a", "b"]
