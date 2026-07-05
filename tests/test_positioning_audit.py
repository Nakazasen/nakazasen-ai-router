from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_general_purpose_positioning_docs_exist():
    assert (ROOT / "docs" / "use_cases.md").exists()
    assert (ROOT / "docs" / "use_cases.vi.md").exists()
    assert (ROOT / "docs" / "integration_generic_worker.md").exists()
    assert (ROOT / "docs" / "integration_generic_worker.vi.md").exists()


def test_readmes_position_router_as_general_purpose():
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    readme_vi = (ROOT / "README.vi.md").read_text(encoding="utf-8").lower()
    assert "general-purpose ai capacity layer" in readme
    assert "lớp cung cấp năng lực ai đa nhiệm" in readme_vi
    assert "translation is intentionally only one example" in readme
    assert "dịch chương chỉ là một ví dụ" in readme_vi


def test_translation_is_not_the_only_example():
    examples = [path.name for path in (ROOT / "examples").glob("*_demo.py")]
    non_translation = [name for name in examples if "translation" not in name]
    assert "translation_worker_demo.py" in examples
    assert len(non_translation) >= 3
