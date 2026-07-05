"""Offline long-running translation worker demo for Nakazasen AI Router."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nakazasen_ai_router import AIRequest, AIResult, AIRouter, ProviderBase, RouterPolicy, SQLiteStateStore


class OfflineTranslationProvider(ProviderBase):
    def __init__(self) -> None:
        super().__init__("offline_translator", is_cloud=False)
        self.calls = 0

    def generate(self, request: AIRequest, candidate=None) -> AIResult:
        self.calls += 1
        title = request.metadata.get("chapter_id", "chapter")
        return AIResult(
            text=f"[DEMO VI] {title}: " + request.prompt.replace("Translate: ", ""),
            provider_name=self.name,
            metadata={"chapter_id": title, "offline_demo": True},
        )


DEFAULT_CHAPTERS = {
    "chapter-001.txt": "Translate: The rain fell softly over the old city.",
    "chapter-002.txt": "Translate: She opened the letter and smiled.",
    "chapter-003.txt": "Translate: At dawn, the journey began again.",
}


def ensure_demo_inputs(input_dir: Path) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    for name, text in DEFAULT_CHAPTERS.items():
        path = input_dir / name
        if not path.exists():
            path.write_text(text, encoding="utf-8")


def run_demo(base_dir: Path) -> dict:
    input_dir = base_dir / "chapters_in"
    output_dir = base_dir / "chapters_out"
    output_dir.mkdir(parents=True, exist_ok=True)
    ensure_demo_inputs(input_dir)

    router = AIRouter(
        [OfflineTranslationProvider()],
        policy=RouterPolicy(task_type="translation_longform", max_estimated_input_tokens=10_000),
        state_store=SQLiteStateStore(base_dir / "router_state.sqlite3"),
    )

    completed = []
    pending = []
    for chapter_path in sorted(input_dir.glob("*.txt")):
        prompt = chapter_path.read_text(encoding="utf-8")
        outcome = router.route_outcome(
            AIRequest(
                prompt=prompt,
                metadata={
                    "task_type": "translation_longform",
                    "chapter_id": chapter_path.stem,
                    "estimated_input_tokens": max(1, len(prompt.split())),
                    "estimated_output_tokens": max(1, len(prompt.split()) * 2),
                },
            )
        )
        if outcome.status == "success" and outcome.result is not None:
            (output_dir / chapter_path.name).write_text(outcome.result.text, encoding="utf-8")
            completed.append(chapter_path.name)
        else:
            pending.append({"chapter": chapter_path.name, "status": outcome.status, "error_type": outcome.error_type})

    summary = {"completed": completed, "pending": pending, "router_state": router.export_state()}
    (base_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an offline translation worker demo.")
    parser.add_argument("--base-dir", default=".demo_translation_worker", help="Demo working directory")
    parser.add_argument("--offline-demo", action="store_true", help="Run without network using fake provider")
    args = parser.parse_args()
    if not args.offline_demo:
        raise SystemExit("Only --offline-demo is supported by this safe demo.")
    summary = run_demo(Path(args.base_dir))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
