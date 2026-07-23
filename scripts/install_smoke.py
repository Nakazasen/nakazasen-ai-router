"""Install-from-wheel smoke test for SDK-first integrations."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import nakazasen_ai_router as nar


class SmokeProvider(nar.ProviderBase):
    def __init__(self) -> None:
        super().__init__("install_smoke_provider", is_cloud=False)

    def generate(self, request: nar.AIRequest, candidate=None) -> nar.AIResult:
        return nar.AIResult(text="OK " + request.prompt[:20], provider_name=self.name)


def main() -> int:
    required = {
        "AIRouter",
        "AIRequest",
        "create_router_from_env",
        "segment_text",
        "SQLiteJobStore",
        "InMemoryQuotaTracker",
        "collect_metrics",
        "QuotaDecision",
        "FreeTierCatalog",
        "DEFAULT_FREE_TIER_CATALOG",
        "UpdateInfo",
        "check_for_updates",
    }
    missing = required - set(nar.__all__)
    if missing:
        raise AssertionError(f"missing public names: {sorted(missing)}")

    tmp = tempfile.mkdtemp(prefix="nar_install_smoke_")
    try:
        base = Path(tmp)
        router = nar.AIRouter([SmokeProvider()], policy=nar.RouterPolicy(task_type="general"), state_store=nar.MemoryStateStore())
        outcome = router.route_outcome(nar.AIRequest(prompt="install smoke", metadata={"task_type": "general"}))
        assert outcome.status == "success"

        chunks = nar.segment_text("payload " * 40, nar.ChunkingPolicy(max_estimated_tokens=20))
        assert chunks

        jobs = nar.SQLiteJobStore(base / "jobs.sqlite3")
        job = jobs.enqueue("payload-ref", workload_type="install_smoke", next_run_at=0)
        claimed = jobs.claim_next("install-smoke-worker")
        assert claimed and claimed.job_id == job.job_id
        jobs.mark_success(job.job_id, result_ref="result-ref")

        quota = nar.InMemoryQuotaTracker([
            nar.ProviderQuotaProfile("install_smoke_provider", policy=nar.CapacityPolicy(requests_per_minute=2, max_concurrency=1))
        ])
        check = quota.reserve("install_smoke_provider", estimated_tokens=1)
        assert check.decision == nar.QuotaDecision.ALLOW
        quota.release("install_smoke_provider")

        metrics = nar.collect_metrics(router, jobs).to_dict()
        assert metrics["router"]["healthy"] >= 1
        assert metrics["jobs"]["total_jobs"] == 1
        print(json.dumps({"status": "pass", "public_names": len(nar.__all__), "chunks": len(chunks)}, sort_keys=True))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
