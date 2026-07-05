from __future__ import annotations

import argparse
import json
from pathlib import Path

from nakazasen_ai_router import AIRequest, AIResult, AIRouter, ProviderBase, RouterPolicy, SQLiteStateStore

class OfflineSummarizer(ProviderBase):
    def __init__(self) -> None:
        super().__init__("offline_summarizer", is_cloud=False)

    def generate(self, request: AIRequest, candidate=None) -> AIResult:
        words = request.prompt.split()
        summary = " ".join(words[:12])
        if len(words) > 12:
            summary += " ..."
        return AIResult(text=summary, provider_name=self.name)


def run_demo(base_dir: Path) -> dict:
    base_dir.mkdir(parents=True, exist_ok=True)
    store = SQLiteStateStore(base_dir / "router_state.sqlite3")
    router = AIRouter([OfflineSummarizer()], policy=RouterPolicy(task_type="summarization"), state_store=store)
    docs = [
        "Router capacity layers help applications survive transient provider failures.",
        "Batch summarization can process many documents without storing payloads in router state.",
    ]
    results = []
    for index, text in enumerate(docs, 1):
        outcome = router.route_outcome(AIRequest(prompt=text, metadata={"task_type": "summarization", "job_id": f"doc-{index}"}))
        results.append({"job_id": f"doc-{index}", "status": outcome.status, "text": outcome.result.text if outcome.result else ""})
    summary = {"results": results, "router_state": router.export_state()}
    (base_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=".demo_summarization")
    args = parser.parse_args()
    print(json.dumps(run_demo(Path(args.base_dir)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
