import json
from pathlib import Path

from scripts.live_conformance import TEST_PROMPT, leak_check, load_provider_keys, parse_args, run_provider
from nakazasen_ai_router import AIResult, AIRequest, ProviderBase


class FakeProvider(ProviderBase):
    def __init__(self):
        super().__init__("fake", is_cloud=False)

    def generate(self, request: AIRequest, candidate=None) -> AIResult:
        return AIResult(text="OK", provider_name=self.name)


def test_parse_args_requires_provider_or_all_configured():
    args = parse_args(["--provider", "gemini", "--key-file", "D:/outside/key.txt"])
    assert args.provider == "gemini"


def test_key_file_loader_rejects_repo_relative_file(tmp_path):
    repo_file = Path("tmp_key_file.txt")
    try:
        repo_file.write_text("GEMINI_API_KEY=secret", encoding="utf-8")
        assert load_provider_keys(repo_file, ["gemini"]) == {}
    finally:
        repo_file.unlink(missing_ok=True)


def test_leak_check_detects_raw_key_and_prompt():
    report = {"message": f"secret-key {TEST_PROMPT}"}
    result = leak_check(report, ["secret-key"])
    assert result["raw_key_detected"] is True
    assert result["prompt_detected"] is True


def test_run_provider_with_fake_router_does_not_leak(monkeypatch):
    def fake_builder(provider, key, model=""):
        from nakazasen_ai_router import AIRouter, MemoryStateStore, RouterPolicy
        return AIRouter([FakeProvider()], policy=RouterPolicy(), state_store=MemoryStateStore())

    monkeypatch.setattr("scripts.live_conformance._build_router", fake_builder)
    report = run_provider("gemini", "secret-key", raw_keys=["secret-key"])
    blob = json.dumps(report, ensure_ascii=False)
    assert report["status"] == "pass"
    assert "secret-key" not in blob
    assert TEST_PROMPT not in blob
