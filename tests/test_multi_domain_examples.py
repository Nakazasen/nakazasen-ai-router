import importlib.util
from pathlib import Path


def load_example(name: str):
    path = Path("examples") / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_multi_domain_examples_run_offline(tmp_path):
    examples = [
        "summarization_batch_demo.py",
        "json_extraction_demo.py",
        "content_generation_demo.py",
        "segmented_batch_demo.py",
        "job_queue_worker_demo.py",
        "quota_policy_demo.py",
    ]
    for example in examples:
        module = load_example(example)
        base_dir = tmp_path / example.replace(".py", "")
        summary = module.run_demo(base_dir)
        assert (base_dir / "summary.json").exists()
        if "router_state" in summary:
            assert summary["router_state"]["summary"]["healthy"] >= 1
        else:
            assert summary["counts"]["allow"] >= 1
