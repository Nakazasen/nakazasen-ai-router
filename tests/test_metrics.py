import json
import time
import subprocess
import sys

from nakazasen_ai_router import JobStatus, SQLiteJobStore, collect_job_metrics, collect_metrics, collect_router_metrics


def test_empty_collect_returns_zero_metrics():
    snapshot = collect_metrics().to_dict()
    assert snapshot["router"]["total_candidates"] == 0
    assert snapshot["jobs"]["total_jobs"] == 0


def test_router_summary_collects_status_counts():
    state = {"summary": {"total": 2, "healthy": 1, "cooldown": 1, "dead": 0, "unknown": 0, "next_retry_after_seconds": 5}}
    metrics = collect_router_metrics(state)
    assert metrics["total_candidates"] == 2
    assert metrics["cooldown"] == 1
    assert metrics["next_retry_after_seconds"] == 5


def test_router_candidate_list_collects_by_provider_and_error_counts():
    state = {
        "summary": {"total": 2, "healthy": 1, "cooldown": 1},
        "candidates": [
            {"provider": "gemini", "status": "healthy", "success_count": 3, "failure_count": 1, "failure_streak": 0, "last_latency_ms": 100},
            {"provider": "groq", "status": "cooldown", "success_count": 0, "failure_count": 2, "failure_streak": 2, "last_error_type": "quota", "last_latency_ms": 300},
        ],
    }
    metrics = collect_router_metrics(state)
    assert metrics["by_provider"]["gemini"]["healthy"] == 1
    assert metrics["by_provider"]["groq"]["cooldown"] == 1
    assert metrics["success_count"] == 3
    assert metrics["failure_count"] == 3
    assert metrics["failure_streak_max"] == 2
    assert metrics["error_type_counts"] == {"quota": 1}
    assert metrics["latency_ms_avg"] == 200


def test_job_metrics_count_statuses_due_expired_and_workloads(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    pending = store.enqueue("payload-1", workload_type="summarization", next_run_at=10)
    running = store.enqueue("payload-2", workload_type="json", next_run_at=0)
    retry = store.enqueue("payload-3", workload_type="json", next_run_at=5)
    store.claim_next("worker", now=1, lease_seconds=2)
    store.mark_retry_later(retry.job_id, retry_after_seconds=0, error_type="quota")
    metrics = collect_job_metrics(store, now=time.time() + 1)
    assert metrics["total_jobs"] == 3
    assert metrics["by_status"][JobStatus.PENDING.value] == 1
    assert metrics["by_status"][JobStatus.RUNNING.value] == 1
    assert metrics["by_status"][JobStatus.RETRY_LATER.value] == 1
    assert metrics["due_now"] == 2
    assert metrics["expired_running"] == 1
    assert metrics["by_workload_type"] == {"summarization": 1, "json": 2}
    assert metrics["error_type_counts"] == {"quota": 1}


def test_metrics_json_does_not_include_sensitive_markers(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    store.enqueue("payload-ref", metadata={"prompt": "secret", "safe": "ok"}, next_run_at=0)
    text = json.dumps(collect_metrics({"summary": {}, "candidates": []}, store).to_dict()).lower()
    assert "secret" not in text
    assert "authorization" not in text
    assert "api_key" not in text


def test_cli_emits_parseable_json_for_jobs(tmp_path):
    db = tmp_path / "jobs.sqlite3"
    store = SQLiteJobStore(db)
    store.enqueue("payload", next_run_at=0)
    result = subprocess.run([sys.executable, "scripts/router_metrics.py", "--jobs", str(db)], check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    assert data["jobs"]["total_jobs"] == 1


def test_cli_emits_parseable_json_for_router_state(tmp_path):
    state = tmp_path / "router_state.json"
    state.write_text(json.dumps({"summary": {"total": 1, "healthy": 1}, "candidates": []}), encoding="utf-8")
    result = subprocess.run([sys.executable, "scripts/router_metrics.py", "--router-state-json", str(state)], check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    assert data["router"]["healthy"] == 1
