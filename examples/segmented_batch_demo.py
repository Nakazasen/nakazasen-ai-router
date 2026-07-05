from __future__ import annotations

import argparse
import json
from pathlib import Path

from nakazasen_ai_router import (
    AIRequest,
    AIResult,
    AIRouter,
    ChunkingPolicy,
    ProviderBase,
    RouterPolicy,
    SQLiteStateStore,
    merge_chunk_texts,
    segment_text,
)


class OfflineChunkProcessor(ProviderBase):
    def __init__(self) -> None:
        super().__init__("offline_chunk_processor", is_cloud=False)

    def generate(self, request: AIRequest, candidate=None) -> AIResult:
        chunk_index = request.metadata.get("chunk_index", 0)
        words = request.prompt.split()
        return AIResult(text=f"chunk {chunk_index}: {' '.join(words[:10])}", provider_name=self.name)


def run_demo(base_dir: Path) -> dict:
    base_dir.mkdir(parents=True, exist_ok=True)
    payload = "\n\n".join(
        f"Section {i}: " + "generic workload payload " * 20
        for i in range(1, 8)
    )
    chunks = segment_text(payload, ChunkingPolicy(max_estimated_tokens=80, chunk_metadata={"workload_type": "segmented_batch"}))
    router = AIRouter(
        [OfflineChunkProcessor()],
        policy=RouterPolicy(task_type="long_context"),
        state_store=SQLiteStateStore(base_dir / "router_state.sqlite3"),
    )
    outputs = []
    for chunk in chunks:
        outcome = router.route_outcome(
            AIRequest(
                prompt=chunk.text,
                metadata={
                    **chunk.metadata,
                    "task_type": "long_context",
                    "estimated_input_tokens": chunk.estimated_tokens,
                },
            )
        )
        if outcome.result:
            outputs.append(outcome.result.text)
    merged = merge_chunk_texts(outputs, separator="\n")
    summary = {
        "chunk_count": len(chunks),
        "merged_length": len(merged),
        "router_state": router.export_state(),
    }
    (base_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (base_dir / "merged.txt").write_text(merged, encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=".demo_segmented_batch")
    args = parser.parse_args()
    print(json.dumps(run_demo(Path(args.base_dir)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
