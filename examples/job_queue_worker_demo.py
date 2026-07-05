from __future__ import annotations

import argparse
import json
from pathlib import Path

from nakazasen_ai_router import (
    AIRequest,
    AIResult,
    AIRouter,
    JobStatus,
    ProviderBase,
    RouterPolicy,
    SQLiteJobStore,
    SQLiteStateStore,
    segment_text,
)


class OfflineJobProvider(ProviderBase):
    def __init__(self) -> None:
        super().__init__("offline_job_provider", is_cloud=False)

    def generate(self, request: AIRequest, candidate=None) -> AIResult:
        return AIResult(text="processed: " + " ".join(request.prompt.split()[:8]), provider_name=self.name)


def run_demo(base_dir: Path) -> dict:
    base_dir.mkdir(parents=True, exist_ok=True)
    payload_dir = base_dir / "payloads"
    result_dir = base_dir / "results"
    payload_dir.mkdir(exist_ok=True)
    result_dir.mkdir(exist_ok=True)

    source_text = "\n\n".join("generic persistent job queue payload " * 10 for _ in range(4))
    chunks = segment_text(source_text)
    job_store = SQLiteJobStore(base_dir / "jobs.sqlite3")
    router = AIRouter([OfflineJobProvider()], policy=RouterPolicy(task_type="cheap_batch"), state_store=SQLiteStateStore(base_dir / "router_state.sqlite3"))

    for chunk in chunks:
        payload_path = payload_dir / f"chunk-{chunk.index}.txt"
        payload_path.write_text(chunk.text, encoding="utf-8")
        job_store.enqueue(str(payload_path), workload_type="segmented_batch", metadata={"chunk_index": chunk.index})

    while True:
        job = job_store.claim_next("demo-worker", lease_seconds=60)
        if job is None:
            break
        text = Path(job.payload_ref).read_text(encoding="utf-8")
        outcome = router.route_outcome(AIRequest(prompt=text, metadata={"task_type": "cheap_batch", "job_id": job.job_id}))
        if outcome.status == "success" and outcome.result:
            result_path = result_dir / f"{job.job_id}.txt"
            result_path.write_text(outcome.result.text, encoding="utf-8")
            job_store.mark_success(job.job_id, result_ref=str(result_path))
        elif outcome.status == "retry_later":
            job_store.mark_retry_later(job.job_id, retry_after_seconds=outcome.retry_after_seconds or 60, error_type=outcome.error_type or "retry_later")
        else:
            job_store.mark_failed(job.job_id, error_type=outcome.error_type or "route_failed")

    jobs = job_store.list_jobs()
    summary = {
        "total_jobs": len(jobs),
        "succeeded": sum(1 for job in jobs if job.status == JobStatus.SUCCEEDED),
        "failed": sum(1 for job in jobs if job.status == JobStatus.FAILED),
        "router_state": router.export_state(),
    }
    (base_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=".demo_job_queue")
    args = parser.parse_args()
    print(json.dumps(run_demo(Path(args.base_dir)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
