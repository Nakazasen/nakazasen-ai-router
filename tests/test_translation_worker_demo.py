from pathlib import Path

from examples.translation_worker_demo import run_demo


def test_translation_worker_demo_runs_offline(tmp_path):
    summary = run_demo(tmp_path)

    assert summary["completed"] == ["chapter-001.txt", "chapter-002.txt", "chapter-003.txt"]
    assert summary["pending"] == []
    assert (tmp_path / "chapters_out" / "chapter-001.txt").exists()
    assert (tmp_path / "summary.json").exists()
    assert summary["router_state"]["summary"]["total"] >= 1
