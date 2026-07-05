from __future__ import annotations

import argparse
import json
from pathlib import Path

from nakazasen_ai_router import AIRequest, AIResult, AIRouter, ProviderBase, RouterPolicy, SQLiteStateStore

class OfflineJsonExtractor(ProviderBase):
    def __init__(self) -> None:
        super().__init__("offline_json_extractor", is_cloud=False)

    def generate(self, request: AIRequest, candidate=None) -> AIResult:
        payload = {"title": "Sample", "category": "demo", "word_count": len(request.prompt.split())}
        return AIResult(text=json.dumps(payload), provider_name=self.name, latency_ms=0)


def run_demo(base_dir: Path) -> dict:
    base_dir.mkdir(parents=True, exist_ok=True)
    router = AIRouter([OfflineJsonExtractor()], policy=RouterPolicy(task_type="structured_json"), state_store=SQLiteStateStore(base_dir / "router_state.sqlite3"))
    outcome = router.route_outcome(AIRequest(prompt="Extract fields from this generic payload", metadata={"task_type": "structured_json", "job_id": "extract-1"}))
    extracted = json.loads(outcome.result.text) if outcome.result else {}
    summary = {"status": outcome.status, "extracted": extracted, "router_state": router.export_state()}
    (base_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=".demo_json_extraction")
    args = parser.parse_args()
    print(json.dumps(run_demo(Path(args.base_dir)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
