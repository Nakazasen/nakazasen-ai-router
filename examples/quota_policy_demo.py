from __future__ import annotations

import argparse
import json
from pathlib import Path

from nakazasen_ai_router import CapacityPolicy, InMemoryQuotaTracker, ProviderQuotaProfile, QuotaDecision, sort_profiles_for_fallback


def run_demo(base_dir: Path) -> dict:
    base_dir.mkdir(parents=True, exist_ok=True)
    profiles = [
        ProviderQuotaProfile("local", policy=CapacityPolicy(requests_per_minute=2, max_concurrency=1, cost_tier="free", fallback_priority=1)),
        ProviderQuotaProfile("cloud_cheap", policy=CapacityPolicy(requests_per_minute=3, tokens_per_minute=100, cost_tier="cheap", fallback_priority=2)),
        ProviderQuotaProfile("premium", policy=CapacityPolicy(requests_per_day=1, cost_tier="premium", fallback_priority=10)),
        ProviderQuotaProfile("disabled", policy=CapacityPolicy(enabled=False, fallback_priority=0)),
    ]
    tracker = InMemoryQuotaTracker(profiles)
    ordered = sort_profiles_for_fallback(profiles)
    counts = {QuotaDecision.ALLOW.value: 0, QuotaDecision.THROTTLE.value: 0, QuotaDecision.BLOCK.value: 0}
    decisions = []
    for index in range(6):
        selected = ordered[index % len(ordered)]
        check = tracker.reserve(selected.provider, estimated_tokens=40, now=float(index))
        counts[check.decision.value] += 1
        decisions.append({"provider": selected.provider, "decision": check.decision.value, "reason": check.reason})
        if check.decision == QuotaDecision.ALLOW:
            tracker.release(selected.provider)
    summary = {"counts": counts, "decisions": decisions, "snapshot": tracker.snapshot()}
    (base_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=".demo_quota_policy")
    args = parser.parse_args()
    print(json.dumps(run_demo(Path(args.base_dir)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
