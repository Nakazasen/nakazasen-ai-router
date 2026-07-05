"""Safe metrics and observability snapshots."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Mapping

from .jobs import JobStatus


@dataclass(frozen=True)
class MetricsSnapshot:
    generated_at: float
    router: Mapping[str, Any] = field(default_factory=dict)
    jobs: Mapping[str, Any] = field(default_factory=dict)
    providers: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "router": dict(self.router),
            "jobs": dict(self.jobs),
            "providers": dict(self.providers),
        }


def collect_router_metrics(router_or_state: Any | None = None) -> dict[str, Any]:
    if router_or_state is None:
        return _empty_router_metrics()
    state = router_or_state.export_state() if hasattr(router_or_state, "export_state") else router_or_state
    if not isinstance(state, Mapping):
        return _empty_router_metrics()
    summary = dict(state.get("summary", {}) or {})
    candidates = list(state.get("candidates", []) or [])
    metrics = _empty_router_metrics()
    metrics.update({
        "total_candidates": int(summary.get("total", len(candidates)) or 0),
        "healthy": int(summary.get("healthy", 0) or 0),
        "cooldown": int(summary.get("cooldown", 0) or 0),
        "dead": int(summary.get("dead", 0) or 0),
        "unknown": int(summary.get("unknown", 0) or 0),
        "next_retry_after_seconds": summary.get("next_retry_after_seconds"),
    })
    by_provider: dict[str, dict[str, Any]] = {}
    error_type_counts: dict[str, int] = {}
    success_count = 0
    failure_count = 0
    failure_streak_max = 0
    latency_values: list[float] = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        provider = str(candidate.get("provider", "unknown") or "unknown")
        status = str(candidate.get("status", "unknown") or "unknown")
        bucket = by_provider.setdefault(provider, {"total": 0, "healthy": 0, "cooldown": 0, "dead": 0, "unknown": 0})
        bucket["total"] += 1
        bucket[status if status in {"healthy", "cooldown", "dead"} else "unknown"] += 1
        success_count += int(candidate.get("success_count", 0) or 0)
        failure_count += int(candidate.get("failure_count", 0) or 0)
        failure_streak_max = max(failure_streak_max, int(candidate.get("failure_streak", 0) or 0))
        error_type = str(candidate.get("last_error_type", "") or "")
        if error_type:
            error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        latency = candidate.get("last_latency_ms")
        if isinstance(latency, (int, float)) and latency > 0:
            latency_values.append(float(latency))
    metrics.update({
        "by_provider": by_provider,
        "success_count": success_count,
        "failure_count": failure_count,
        "failure_streak_max": failure_streak_max,
        "error_type_counts": error_type_counts,
        "latency_ms_avg": round(sum(latency_values) / len(latency_values), 2) if latency_values else None,
    })
    return metrics


def collect_job_metrics(job_store: Any | None = None, *, now: float | None = None) -> dict[str, Any]:
    metrics = _empty_job_metrics()
    if job_store is None:
        return metrics
    now = time.time() if now is None else now
    jobs = list(job_store.list_jobs())
    metrics["total_jobs"] = len(jobs)
    for job in jobs:
        status = job.status.value if isinstance(job.status, JobStatus) else str(job.status)
        metrics["by_status"][status] = metrics["by_status"].get(status, 0) + 1
        if status in {JobStatus.PENDING.value, JobStatus.RETRY_LATER.value} and job.next_run_at <= now:
            metrics["due_now"] += 1
        if status == JobStatus.RUNNING.value and job.lease_expires_at <= now:
            metrics["expired_running"] += 1
        if job.attempt_count >= job.max_attempts:
            metrics["max_attempts_reached"] += 1
        metrics["by_workload_type"][job.workload_type] = metrics["by_workload_type"].get(job.workload_type, 0) + 1
        if job.error_type:
            metrics["error_type_counts"][job.error_type] = metrics["error_type_counts"].get(job.error_type, 0) + 1
    return metrics


def collect_metrics(router_or_state: Any | None = None, job_store: Any | None = None) -> MetricsSnapshot:
    router = collect_router_metrics(router_or_state)
    return MetricsSnapshot(
        generated_at=time.time(),
        router=router,
        jobs=collect_job_metrics(job_store),
        providers=router.get("by_provider", {}),
    )


def _empty_router_metrics() -> dict[str, Any]:
    return {
        "total_candidates": 0,
        "healthy": 0,
        "cooldown": 0,
        "dead": 0,
        "unknown": 0,
        "next_retry_after_seconds": None,
        "by_provider": {},
        "success_count": 0,
        "failure_count": 0,
        "failure_streak_max": 0,
        "error_type_counts": {},
        "latency_ms_avg": None,
    }


def _empty_job_metrics() -> dict[str, Any]:
    return {
        "total_jobs": 0,
        "by_status": {status.value: 0 for status in JobStatus},
        "due_now": 0,
        "expired_running": 0,
        "max_attempts_reached": 0,
        "by_workload_type": {},
        "error_type_counts": {},
    }
