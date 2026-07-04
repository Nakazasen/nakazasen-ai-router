"""Offline performance benchmark for Nakazasen AI Router."""

from __future__ import annotations

import logging
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nakazasen_ai_router import AIRequest, AIRouter, ProviderBase, ProviderCandidate, RouterPolicy, create_router_from_env
from nakazasen_ai_router.discovery import _discover_gemini_models
from nakazasen_ai_router.scoreboard import HealthScoreboard

THRESHOLDS_MS = {
    "import_package": 500.0,
    "create_router_from_env": 100.0,
    "create_router_live_free_first": 100.0,
    "single_mock_route": 50.0,
    "ten_model_mock_route": 100.0,
    "fallback_many_provider_route": 100.0,
    "scoreboard_rank_1000": 300.0,
    "scoreboard_save_load_1000": 500.0,
    "discovery_parse_1000": 500.0,
}


class MockHTTPResponse:
    def __init__(self, payload: Mapping[str, Any]) -> None:
        self._payload = payload
        self.status_code = 200
        self.text = json.dumps(payload)

    def json(self) -> Mapping[str, Any]:
        return self._payload


class MockHTTPClient:
    def post(self, url: str, *, headers: Mapping[str, str], json: Mapping[str, Any], timeout: float) -> MockHTTPResponse:
        return MockHTTPResponse({"choices": [{"message": {"content": "OK"}}]})


class MockDiscoveryClient:
    def __init__(self, pages: list[Mapping[str, Any]]) -> None:
        self.pages = pages
        self.index = 0

    def get(self, url: str, timeout: float) -> MockHTTPResponse:
        payload = self.pages[min(self.index, len(self.pages) - 1)]
        self.index += 1
        return MockHTTPResponse(payload)


class FastProvider(ProviderBase):
    def __init__(self, name: str = "fast", *, models: int = 1, fail: bool = False) -> None:
        super().__init__(name, is_cloud=False)
        self.models = [f"model-{i}" for i in range(models)]
        self.fail = fail

    def iter_candidates(self) -> list[ProviderCandidate]:
        return [ProviderCandidate(provider=self, priority=i, model=model) for i, model in enumerate(self.models)]

    def generate(self, request: AIRequest, candidate: ProviderCandidate | None = None):
        if self.fail:
            from nakazasen_ai_router import ProviderError
            raise ProviderError("mock failure")
        from nakazasen_ai_router import AIResult
        return AIResult(text="OK", provider_name=self.name, metadata={"model": candidate.model if candidate else ""})


def measure(name: str, func, *, repeat: int = 1) -> tuple[str, float, float | None, str]:
    started = time.perf_counter()
    for _ in range(repeat):
        func()
    elapsed_ms = (time.perf_counter() - started) * 1000 / repeat
    threshold = THRESHOLDS_MS.get(name)
    status = "PASS" if threshold is None or elapsed_ms <= threshold else "FAIL"
    return name, elapsed_ms, threshold, status


def benchmark_import() -> tuple[str, float, float | None, str]:
    code = "import time; s=time.perf_counter(); import nakazasen_ai_router; print((time.perf_counter()-s)*1000)"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    elapsed = float(result.stdout.strip())
    threshold = THRESHOLDS_MS["import_package"]
    return "import_package", elapsed, threshold, "PASS" if elapsed <= threshold else "FAIL"


def fake_env() -> dict[str, str]:
    return {"GEMINI_API_KEY": "fake-key"}


def discovery_pages(count: int, page_size: int = 100) -> list[Mapping[str, Any]]:
    pages = []
    for start in range(0, count, page_size):
        end = min(count, start + page_size)
        models = [
            {
                "name": f"models/gemini-mock-{i}",
                "displayName": f"Gemini Mock {i}",
                "supportedGenerationMethods": ["generateContent"],
                "inputTokenLimit": 1000,
                "outputTokenLimit": 100,
            }
            for i in range(start, end)
        ]
        payload: dict[str, Any] = {"models": models}
        if end < count:
            payload["nextPageToken"] = f"page-{end}"
        pages.append(payload)
    return pages


def main() -> int:
    logging.getLogger("nakazasen_ai_router").setLevel(logging.CRITICAL)
    results: list[tuple[str, float, float | None, str]] = []
    results.append(benchmark_import())
    results.append(measure("create_router_from_env", lambda: create_router_from_env(env=fake_env(), provider_names=("gemini",), http_client_factory=MockHTTPClient(), enable_network=False), repeat=200))
    results.append(measure("create_router_live_free_first", lambda: create_router_from_env(env=fake_env(), strategy="live_free_first", http_client_factory=MockHTTPClient(), enable_network=False), repeat=200))
    results.append(measure("single_mock_route", lambda: AIRouter([FastProvider(models=1)]).route(AIRequest(prompt="x")), repeat=1000))
    results.append(measure("ten_model_mock_route", lambda: AIRouter([FastProvider(models=10)]).route(AIRequest(prompt="x")), repeat=1000))
    results.append(measure("fallback_many_provider_route", lambda: AIRouter([FastProvider("fail", fail=True), FastProvider("ok")], RouterPolicy(max_attempts=1, transient_cooldown_seconds=0)).route(AIRequest(prompt="x")), repeat=1000))

    def scoreboard_ops() -> None:
        board = HealthScoreboard()
        for i in range(1000):
            if i % 2:
                board.record_success("gemini", f"model-{i}")
            else:
                board.record_failure("gemini", f"model-{i}", "quota_rate_limit")

    results.append(measure("scoreboard_record_1000", scoreboard_ops, repeat=50))

    board = HealthScoreboard()
    for i in range(1000):
        board.record_success("gemini", f"model-{i}")
    results.append(measure("scoreboard_rank_10", lambda: board.rank_models("gemini", [f"model-{i}" for i in range(10)]), repeat=500))
    results.append(measure("scoreboard_rank_100", lambda: board.rank_models("gemini", [f"model-{i}" for i in range(100)]), repeat=200))
    results.append(measure("scoreboard_rank_1000", lambda: board.rank_models("gemini", [f"model-{i}" for i in range(1000)]), repeat=50))

    def save_load() -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "health.json"
            board.save_json(path)
            HealthScoreboard.load_json(path)

    results.append(measure("scoreboard_save_load_1000", save_load, repeat=20))
    results.append(measure("discovery_parse_100", lambda: _discover_gemini_models(api_key="fake", http_client=MockDiscoveryClient(discovery_pages(100)), include_actions=("generateContent",)), repeat=50))
    results.append(measure("discovery_parse_1000", lambda: _discover_gemini_models(api_key="fake", http_client=MockDiscoveryClient(discovery_pages(1000)), include_actions=("generateContent",)), repeat=10))
    results.append(measure("audit_text_encoding", lambda: subprocess.run([sys.executable, "scripts/audit_text_encoding.py"], cwd=ROOT, capture_output=True, text=True, check=True)))
    results.append(measure("audit_docs_quality", lambda: subprocess.run([sys.executable, "scripts/audit_docs_quality.py"], cwd=ROOT, capture_output=True, text=True, check=True)))

    print("case | measured_ms | threshold_ms | status")
    print("--- | ---: | ---: | ---")
    failed = False
    for name, measured, threshold, status in results:
        if status == "FAIL":
            failed = True
        threshold_text = "" if threshold is None else f"{threshold:.2f}"
        print(f"{name} | {measured:.3f} | {threshold_text} | {status}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
