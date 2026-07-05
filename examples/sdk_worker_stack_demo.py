from __future__ import annotations

import argparse
import json
from pathlib import Path

from nakazasen_ai_router import (
    AIRequest,
    AIResult,
    AIRouter,
    CapacityPolicy,
    ChunkingPolicy,
    InMemoryQuotaTracker,
    ProviderBase,
    ProviderQuotaProfile,
    QuotaDecision,
    RouterPolicy,
    SQLiteJobStore,
    SQLiteStateStore,
    collect_metrics,
    segment_text,
)


class SdkDemoProvider(ProviderBase):
    def __init__(self) -> None:
        super().__init__("sdk_demo_provider", is_cloud=False)

    def generate(self, request: AIRequest, candidate=None) -> AIResult:
        return AIResult(text="SDK processed: " + " ".join(request.prompt.split()[:12]), provider_name=self.name)


def run_demo(base_dir: Path) -> dict:
    base_dir.mkdir(parents=True, exist_ok=True)
    payload_dir = base_dir / "payloads"
    result_dir = base_dir / "results"
    payload_dir.mkdir(exist_ok=True)
    result_dir.mkdir(exist_ok=True)

    payload = "\n\n".join(f"Document section {i}: " + "SDK integration workload " * 12 for i in range(1, 5))
    chunks = segment_text(payload, ChunkingPolicy(max_estimated_tokens=70, chunk_metadata={"app": "external_sdk_demo"}))
    jobs = SQLiteJobStore(base_dir / "jobs.sqlite3")
    router = AIRouter([SdkDemoProvider()], policy=RouterPolicy(task_type="cheap_batch"), state_store=SQLiteStateStore(base_dir / "router_state.sqlite3"))
    quota = InMemoryQuotaTracker([
        ProviderQuotaProfile("sdk_demo_provider", policy=CapacityPolicy(requests_per_minute=100, tokens_per_minute=10_000, max_concurrency=1, cost_tier="free"))
    ])

    for chunk in chunks:
        payload_ref = payload_dir / f"chunk-{chunk.index}.txt"
        payload_ref.write_text(chunk.text, encoding="utf-8")
        jobs.enqueue(str(payload_ref), workload_type="sdk_worker_stack", metadata={"chunk_index": chunk.index, "app": "external_sdk_demo"}, next_run_at=0)

    decisions = []
    while True:
        job = jobs.claim_next("sdk-demo-worker", lease_seconds=60)
        if job is None:
            break
        text = Path(job.payload_ref).read_text(encoding="utf-8")
        check = quota.reserve("sdk_demo_provider", estimated_tokens=len(text) // 4)
        decisions.append(check.decision.value)
        if check.decision != QuotaDecision.ALLOW:
            jobs.mark_retry_later(job.job_id, retry_after_seconds=check.retry_after_seconds, error_type=check.reason)
            continue
        try:
            outcome = router.route_outcome(AIRequest(prompt=text, metadata={"task_type": "cheap_batch", "job_id": job.job_id}))
            if outcome.status == "success" and outcome.result:
                result_ref = result_dir / f"{job.job_id}.txt"
                result_ref.write_text(outcome.result.text, encoding="utf-8")
                jobs.mark_success(job.job_id, result_ref=str(result_ref))
            else:
                jobs.mark_retry_later(job.job_id, retry_after_seconds=outcome.retry_after_seconds or 60, error_type=outcome.error_type or "route_failed")
        finally:
            quota.release("sdk_demo_provider")

    metrics = collect_metrics(router, jobs).to_dict()
    summary = {
        "chunk_count": len(chunks),
        "jobs_total": metrics["jobs"]["total_jobs"],
        "jobs_succeeded": metrics["jobs"]["by_status"]["succeeded"],
        "quota_decisions": {name: decisions.count(name) for name in sorted(set(decisions))},
        "metrics": metrics,
        "router_state": router.export_state(),
    }
    (base_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=".demo_sdk_worker_stack")
    args = parser.parse_args()
    print(json.dumps(run_demo(Path(args.base_dir)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
