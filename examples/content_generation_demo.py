from __future__ import annotations

import argparse
import json
from pathlib import Path

from nakazasen_ai_router import AIRequest, AIResult, AIRouter, ProviderBase, RouterPolicy, SQLiteStateStore

class OfflineContentGenerator(ProviderBase):
    def __init__(self) -> None:
        super().__init__("offline_content_generator", is_cloud=False)

    def generate(self, request: AIRequest, candidate=None) -> AIResult:
        topic = request.metadata.get("topic", "generic topic")
        return AIResult(text=f"Draft content for {topic}: reliable AI capacity for every repository.", provider_name=self.name)


def run_demo(base_dir: Path) -> dict:
    base_dir.mkdir(parents=True, exist_ok=True)
    router = AIRouter([OfflineContentGenerator()], policy=RouterPolicy(task_type="cheap_batch"), state_store=SQLiteStateStore(base_dir / "router_state.sqlite3"))
    topics = ["release notes", "support reply", "product blurb"]
    results = []
    for topic in topics:
        outcome = router.route_outcome(AIRequest(prompt=f"Write {topic}", metadata={"task_type": "cheap_batch", "topic": topic}))
        results.append({"topic": topic, "status": outcome.status, "text": outcome.result.text if outcome.result else ""})
    summary = {"results": results, "router_state": router.export_state()}
    (base_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=".demo_content_generation")
    args = parser.parse_args()
    print(json.dumps(run_demo(Path(args.base_dir)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
