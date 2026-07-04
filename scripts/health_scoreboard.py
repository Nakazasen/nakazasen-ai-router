"""Print a safe provider/model health scoreboard."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nakazasen_ai_router.registry import PROVIDER_REGISTRY
from nakazasen_ai_router.scoreboard import HealthScoreboard


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print Nakazasen AI Router health scoreboard.")
    parser.add_argument("--health-cache", required=True)
    parser.add_argument("--provider", default="")
    parser.add_argument("--rank-configured", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scoreboard = HealthScoreboard.load_json(args.health_cache)
    entries = scoreboard.entries()
    if args.provider:
        entries = [entry for entry in entries if entry.provider == args.provider]
    for entry in entries:
        print(
            f"provider={entry.provider} | model={entry.model} | success={entry.success_count} | "
            f"failure={entry.failure_count} | streak={entry.failure_streak} | last_status={entry.last_status} | "
            f"last_error_type={entry.last_error_type} | last_latency_ms={entry.last_latency_ms or ''}"
        )
    if args.rank_configured:
        providers = [args.provider] if args.provider else sorted(PROVIDER_REGISTRY)
        for provider in providers:
            profile = PROVIDER_REGISTRY.get(provider)
            if not profile:
                continue
            ranked = scoreboard.rank_models(provider, profile.default_models)
            print(f"provider={provider} | ranked_models={','.join(ranked)}")
            last_good = scoreboard.last_known_good(provider) or ""
            print(f"provider={provider} | last_known_good={last_good}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
