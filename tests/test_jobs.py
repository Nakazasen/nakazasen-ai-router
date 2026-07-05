import time

import pytest

from nakazasen_ai_router import JobStatus, SQLiteJobStore, sanitize_job_metadata


def test_enqueue_creates_pending_job(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    job = store.enqueue("payloads/1.txt", workload_type="summarization", metadata={"job_id": "1"})
    assert job.status == JobStatus.PENDING
    assert job.payload_ref == "payloads/1.txt"
    assert job.metadata == {"job_id": "1"}


def test_enqueue_validates_inputs(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    with pytest.raises(ValueError):
        store.enqueue("")
    with pytest.raises(ValueError):
        store.enqueue("payload", max_attempts=0)


def test_claim_next_claims_due_pending_job(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    store.enqueue("payload", next_run_at=0)
    claimed = store.claim_next("worker-1", now=100, lease_seconds=10)
    assert claimed is not None
    assert claimed.status == JobStatus.RUNNING
    assert claimed.lease_owner == "worker-1"
    assert claimed.attempt_count == 1
    assert claimed.lease_expires_at == 110


def test_claim_next_respects_next_run_at(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    store.enqueue("payload", next_run_at=200)
    assert store.claim_next("worker", now=100) is None
    assert store.claim_next("worker", now=201) is not None


def test_lease_prevents_double_claim(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    store.enqueue("payload", next_run_at=0)
    assert store.claim_next("worker-1", now=100, lease_seconds=50) is not None
    assert store.claim_next("worker-2", now=120, lease_seconds=50) is None


def test_expired_lease_is_released_and_reclaimed(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    store.enqueue("payload", next_run_at=0)
    first = store.claim_next("worker-1", now=100, lease_seconds=5)
    assert first is not None
    assert store.release_expired_leases(now=106) == 1
    second = store.claim_next("worker-2", now=106, lease_seconds=5)
    assert second is not None
    assert second.lease_owner == "worker-2"
    assert second.attempt_count == 2


def test_mark_success_stores_result_and_clears_lease(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    job = store.enqueue("payload", next_run_at=0)
    store.claim_next("worker", now=100)
    done = store.mark_success(job.job_id, result_ref="results/1.txt")
    assert done.status == JobStatus.SUCCEEDED
    assert done.result_ref == "results/1.txt"
    assert done.lease_owner == ""


def test_mark_retry_later_schedules_retry(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    job = store.enqueue("payload", max_attempts=3)
    store.claim_next("worker")
    retry = store.mark_retry_later(job.job_id, retry_after_seconds=30, error_type="quota")
    assert retry.status == JobStatus.RETRY_LATER
    assert retry.error_type == "quota"
    assert retry.lease_owner == ""
    assert retry.next_run_at > time.time()


def test_mark_retry_later_fails_after_max_attempts(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    job = store.enqueue("payload", max_attempts=1)
    store.claim_next("worker")
    failed = store.mark_retry_later(job.job_id, retry_after_seconds=30, error_type="quota")
    assert failed.status == JobStatus.FAILED


def test_mark_failed_stores_sanitized_error_type(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    job = store.enqueue("payload")
    failed = store.mark_failed(job.job_id, error_type="x" * 200)
    assert failed.status == JobStatus.FAILED
    assert len(failed.error_type) == 120


def test_persistence_across_store_instances(tmp_path):
    path = tmp_path / "jobs.sqlite3"
    first = SQLiteJobStore(path)
    job = first.enqueue("payload", metadata={"a": 1})
    second = SQLiteJobStore(path)
    loaded = second.get(job.job_id)
    assert loaded is not None
    assert loaded.metadata == {"a": 1}


def test_metadata_sanitizer_removes_sensitive_values():
    metadata = sanitize_job_metadata({"prompt": "secret", "payload": "raw", "token": "abc", "safe": object()})
    assert "prompt" not in metadata
    assert "payload" not in metadata
    assert "token" not in metadata
    assert "safe" in metadata


def test_list_jobs_filters_by_status(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    first = store.enqueue("payload-1")
    store.enqueue("payload-2")
    store.mark_failed(first.job_id, error_type="test")
    assert len(store.list_jobs(status=JobStatus.FAILED)) == 1
    assert len(store.list_jobs(status="pending")) == 1


def test_claiming_order_by_next_run_then_created(tmp_path):
    store = SQLiteJobStore(tmp_path / "jobs.sqlite3")
    later = store.enqueue("later", job_id="later", next_run_at=20)
    earlier = store.enqueue("earlier", job_id="earlier", next_run_at=10)
    claimed = store.claim_next("worker", now=30)
    assert claimed is not None
    assert claimed.job_id == earlier.job_id
