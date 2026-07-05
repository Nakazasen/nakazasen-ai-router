"""Persistent generic job queue primitives."""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Protocol

SENSITIVE_JOB_KEYS = {"api_key", "apikey", "token", "secret", "authorization", "password", "raw_key", "prompt", "payload"}


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    RETRY_LATER = "retry_later"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    status: JobStatus
    workload_type: str
    payload_ref: str
    result_ref: str = ""
    attempt_count: int = 0
    max_attempts: int = 3
    next_run_at: float = 0.0
    lease_owner: str = ""
    lease_expires_at: float = 0.0
    error_type: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)


class JobStore(Protocol):
    def enqueue(self, payload_ref: str, *, workload_type: str = "general", job_id: str | None = None, metadata: Mapping[str, Any] | None = None, max_attempts: int = 3, next_run_at: float | None = None) -> JobRecord: ...
    def claim_next(self, worker_id: str, *, lease_seconds: float = 300, now: float | None = None) -> JobRecord | None: ...
    def mark_success(self, job_id: str, *, result_ref: str = "") -> JobRecord: ...
    def mark_retry_later(self, job_id: str, *, retry_after_seconds: float, error_type: str = "") -> JobRecord: ...
    def mark_failed(self, job_id: str, *, error_type: str = "") -> JobRecord: ...
    def release_expired_leases(self, *, now: float | None = None) -> int: ...
    def get(self, job_id: str) -> JobRecord | None: ...
    def list_jobs(self, *, status: JobStatus | str | None = None) -> list[JobRecord]: ...


def sanitize_job_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in dict(metadata or {}).items():
        key_text = str(key)
        if key_text.lower() in SENSITIVE_JOB_KEYS:
            continue
        try:
            json.dumps(value)
            safe[key_text] = value
        except (TypeError, ValueError):
            safe[key_text] = str(value)
    return safe


def _clean_error_type(error_type: str) -> str:
    return " ".join(str(error_type or "").split())[:120]


class SQLiteJobStore:
    """SQLite-backed generic job queue store."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def enqueue(self, payload_ref: str, *, workload_type: str = "general", job_id: str | None = None, metadata: Mapping[str, Any] | None = None, max_attempts: int = 3, next_run_at: float | None = None) -> JobRecord:
        if not payload_ref:
            raise ValueError("payload_ref must be non-empty")
        if max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        now = time.time()
        job_id = job_id or str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ai_router_jobs (
                    job_id, status, workload_type, payload_ref, result_ref,
                    attempt_count, max_attempts, next_run_at, lease_owner,
                    lease_expires_at, error_type, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, '', 0, ?, ?, '', 0, '', ?, ?, ?)
                """,
                (job_id, JobStatus.PENDING.value, workload_type or "general", payload_ref, max_attempts, now if next_run_at is None else next_run_at, json.dumps(sanitize_job_metadata(metadata)), now, now),
            )
        record = self.get(job_id)
        assert record is not None
        return record

    def claim_next(self, worker_id: str, *, lease_seconds: float = 300, now: float | None = None) -> JobRecord | None:
        if not worker_id:
            raise ValueError("worker_id must be non-empty")
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        now = time.time() if now is None else now
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT job_id FROM ai_router_jobs
                WHERE status IN (?, ?) AND next_run_at <= ?
                ORDER BY next_run_at ASC, created_at ASC
                LIMIT 1
                """,
                (JobStatus.PENDING.value, JobStatus.RETRY_LATER.value, now),
            ).fetchone()
            if row is None:
                row = conn.execute(
                    """
                    SELECT job_id FROM ai_router_jobs
                    WHERE status = ? AND lease_expires_at <= ?
                    ORDER BY lease_expires_at ASC, created_at ASC
                    LIMIT 1
                    """,
                    (JobStatus.RUNNING.value, now),
                ).fetchone()
            if row is None:
                conn.commit()
                return None
            job_id = row[0]
            conn.execute(
                """
                UPDATE ai_router_jobs
                SET status = ?, lease_owner = ?, lease_expires_at = ?,
                    attempt_count = attempt_count + 1, updated_at = ?
                WHERE job_id = ?
                """,
                (JobStatus.RUNNING.value, worker_id, now + lease_seconds, now, job_id),
            )
            conn.commit()
        return self.get(job_id)

    def mark_success(self, job_id: str, *, result_ref: str = "") -> JobRecord:
        return self._update_status(job_id, JobStatus.SUCCEEDED, result_ref=result_ref)

    def mark_retry_later(self, job_id: str, *, retry_after_seconds: float, error_type: str = "") -> JobRecord:
        if retry_after_seconds < 0:
            raise ValueError("retry_after_seconds must be non-negative")
        record = self._require(job_id)
        if record.attempt_count >= record.max_attempts:
            return self.mark_failed(job_id, error_type=error_type or "max_attempts_exceeded")
        now = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE ai_router_jobs
                SET status = ?, next_run_at = ?, lease_owner = '', lease_expires_at = 0,
                    error_type = ?, updated_at = ?
                WHERE job_id = ?
                """,
                (JobStatus.RETRY_LATER.value, now + retry_after_seconds, _clean_error_type(error_type), now, job_id),
            )
        return self._require(job_id)

    def mark_failed(self, job_id: str, *, error_type: str = "") -> JobRecord:
        return self._update_status(job_id, JobStatus.FAILED, error_type=_clean_error_type(error_type))

    def release_expired_leases(self, *, now: float | None = None) -> int:
        now = time.time() if now is None else now
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE ai_router_jobs
                SET status = ?, next_run_at = ?, lease_owner = '', lease_expires_at = 0,
                    error_type = 'lease_expired', updated_at = ?
                WHERE status = ? AND lease_expires_at <= ?
                """,
                (JobStatus.RETRY_LATER.value, now, now, JobStatus.RUNNING.value, now),
            )
            return cur.rowcount

    def get(self, job_id: str) -> JobRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM ai_router_jobs WHERE job_id = ?", (job_id,)).fetchone()
        return self._row_to_record(row) if row else None

    def list_jobs(self, *, status: JobStatus | str | None = None) -> list[JobRecord]:
        with self._connect() as conn:
            if status is None:
                rows = conn.execute("SELECT * FROM ai_router_jobs ORDER BY created_at ASC").fetchall()
            else:
                status_value = status.value if isinstance(status, JobStatus) else str(status)
                rows = conn.execute("SELECT * FROM ai_router_jobs WHERE status = ? ORDER BY created_at ASC", (status_value,)).fetchall()
        return [self._row_to_record(row) for row in rows]

    def _update_status(self, job_id: str, status: JobStatus, *, result_ref: str = "", error_type: str = "") -> JobRecord:
        now = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE ai_router_jobs
                SET status = ?, result_ref = CASE WHEN ? != '' THEN ? ELSE result_ref END,
                    lease_owner = '', lease_expires_at = 0, error_type = ?, updated_at = ?
                WHERE job_id = ?
                """,
                (status.value, result_ref, result_ref, error_type, now, job_id),
            )
        return self._require(job_id)

    def _require(self, job_id: str) -> JobRecord:
        record = self.get(job_id)
        if record is None:
            raise KeyError(job_id)
        return record

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_router_jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    workload_type TEXT NOT NULL,
                    payload_ref TEXT NOT NULL,
                    result_ref TEXT NOT NULL DEFAULT '',
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    next_run_at REAL NOT NULL DEFAULT 0,
                    lease_owner TEXT NOT NULL DEFAULT '',
                    lease_expires_at REAL NOT NULL DEFAULT 0,
                    error_type TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_router_jobs_claim ON ai_router_jobs(status, next_run_at, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_router_jobs_lease ON ai_router_jobs(status, lease_expires_at)")

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> JobRecord:
        return JobRecord(
            job_id=row["job_id"],
            status=JobStatus(row["status"]),
            workload_type=row["workload_type"],
            payload_ref=row["payload_ref"],
            result_ref=row["result_ref"],
            attempt_count=int(row["attempt_count"]),
            max_attempts=int(row["max_attempts"]),
            next_run_at=float(row["next_run_at"]),
            lease_owner=row["lease_owner"],
            lease_expires_at=float(row["lease_expires_at"]),
            error_type=row["error_type"],
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
            metadata=json.loads(row["metadata_json"] or "{}"),
        )
