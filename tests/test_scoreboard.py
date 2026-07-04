import json
import time

from nakazasen_ai_router.scoreboard import HealthScoreboard


def test_scoreboard_record_success_failure_and_last_known_good():
    board = HealthScoreboard()
    board.record_failure("gemini", "a", "quota_rate_limit")
    board.record_success("gemini", "b", latency_ms=12.5)

    assert board.last_known_good("gemini") == "b"
    data = board.to_dict()
    assert "prompt" not in json.dumps(data).lower()
    assert "authorization" not in json.dumps(data).lower()


def test_rank_models_keeps_configured_order_without_data():
    board = HealthScoreboard()

    assert board.rank_models("gemini", ("a", "b")) == ["a", "b"]


def test_rank_models_prioritizes_success():
    board = HealthScoreboard()
    board.record_success("gemini", "b")

    assert board.rank_models("gemini", ("a", "b"))[0] == "b"


def test_rank_models_demotes_quota_and_cooldown():
    board = HealthScoreboard()
    board.record_success("gemini", "a")
    board.record_failure("gemini", "a", "quota_rate_limit", cooldown_until=time.time() + 60)
    board.record_success("gemini", "b")

    assert board.rank_models("gemini", ("a", "b")) == ["b", "a"]


def test_scoreboard_json_roundtrip(tmp_path):
    path = tmp_path / "health.json"
    board = HealthScoreboard()
    board.record_success("gemini", "gemini-3.5-flash")
    board.save_json(path)

    loaded = HealthScoreboard.load_json(path)

    assert loaded.last_known_good("gemini") == "gemini-3.5-flash"
