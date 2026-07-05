"""Safe opt-in live provider conformance checks."""
from __future__ import annotations

import argparse, asyncio, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nakazasen_ai_router import AIRequest, RouterPolicy, create_router_from_env
from nakazasen_ai_router.config import LIVE_FREE_FIRST_ORDER
from scripts.live_smoke import PROVIDER_ENV, read_key_from_file

TEST_PROMPT = "Reply with exactly: OK"
SENSITIVE_WORDS = ("authorization", "bearer", "api_key", "apikey")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run opt-in sanitized live provider conformance checks.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--provider", choices=sorted(PROVIDER_ENV))
    group.add_argument("--all-configured", action="store_true")
    parser.add_argument("--model", default="")
    parser.add_argument("--key-file", required=True, help="External key file outside this repository")
    parser.add_argument("--json-out", default="")
    parser.add_argument("--include-async", action="store_true")
    parser.add_argument("--include-stream", action="store_true")
    return parser.parse_args(argv)


def _repo_relative(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def load_provider_keys(key_file: Path, providers: list[str]) -> dict[str, str]:
    if not key_file.exists() or _repo_relative(key_file):
        return {}
    keys = {}
    for provider in providers:
        env_name = PROVIDER_ENV[provider]
        key = read_key_from_file(key_file, env_name, provider)
        if key:
            keys[provider] = key
    return keys


def _safe_preview(text: str, limit: int = 80) -> str:
    return " ".join((text or "").split())[:limit]


def _contains_any(blob: str, needles: list[str] | tuple[str, ...]) -> bool:
    low = blob.lower()
    return any(needle and needle.lower() in low for needle in needles)


def leak_check(report: dict[str, Any], raw_keys: list[str], prompt: str = TEST_PROMPT) -> dict[str, bool]:
    blob = json.dumps(report, ensure_ascii=False, sort_keys=True)
    return {
        "raw_key_detected": _contains_any(blob, raw_keys),
        "authorization_detected": _contains_any(blob, SENSITIVE_WORDS),
        "prompt_detected": prompt in blob,
    }


def _check_attempts(attempts: Any, raw_keys: list[str]) -> bool:
    blob = json.dumps(attempts, ensure_ascii=False, default=str)
    return not _contains_any(blob, raw_keys) and TEST_PROMPT not in blob and not _contains_any(blob, SENSITIVE_WORDS)


def _check_state(state: dict[str, Any], raw_keys: list[str]) -> bool:
    blob = json.dumps(state, ensure_ascii=False, default=str)
    return not _contains_any(blob, raw_keys) and TEST_PROMPT not in blob and not _contains_any(blob, SENSITIVE_WORDS)


def _build_router(provider: str, key: str, model: str = ""):
    env = {PROVIDER_ENV[provider]: key}
    router = create_router_from_env(provider_names=(provider,), env=env, enable_network=True, policy=RouterPolicy(max_attempts=2))
    if model and router.providers:
        router.providers[0].provider.models = [model]
    return router


def run_sync_check(provider: str, key: str, model: str, raw_keys: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    checks = []
    router = _build_router(provider, key, model)
    started = time.time()
    outcome = router.route_outcome(AIRequest(prompt=TEST_PROMPT, metadata={"task_type": "low_latency", "conformance": True}))
    latency_ms = int((time.time() - started) * 1000)
    checks.append({
        "name": "sync_route_outcome",
        "status": "pass" if outcome.status == "success" else "fail",
        "outcome_status": outcome.status,
        "error_type": outcome.error_type or "",
        "latency_ms": latency_ms,
        "response_preview": _safe_preview(outcome.result.text if outcome.result else ""),
    })
    state = router.export_state()
    checks.append({"name": "attempt_safety", "status": "pass" if _check_attempts(outcome.attempts, raw_keys) else "fail"})
    checks.append({"name": "export_state_safety", "status": "pass" if _check_state(state, raw_keys) else "fail"})
    return checks, state


async def run_async_check(provider: str, key: str, model: str) -> dict[str, Any]:
    router = _build_router(provider, key, model)
    outcome = await router.aroute_outcome(AIRequest(prompt=TEST_PROMPT, metadata={"task_type": "low_latency", "conformance": True}))
    return {"name": "async_route_outcome", "status": "pass" if outcome.status == "success" else "fail", "outcome_status": outcome.status, "error_type": outcome.error_type or ""}


def run_stream_check(provider: str, key: str, model: str) -> dict[str, Any]:
    router = _build_router(provider, key, model)
    chunks = list(router.stream(AIRequest(prompt=TEST_PROMPT, metadata={"task_type": "low_latency", "conformance": True})))
    return {"name": "stream_contract", "status": "pass" if chunks else "fail", "chunks": len(chunks), "done": bool(chunks and chunks[-1].done)}


def run_provider(provider: str, key: str, *, model: str = "", include_async: bool = False, include_stream: bool = False, raw_keys: list[str] | None = None) -> dict[str, Any]:
    raw_keys = raw_keys or [key]
    checks, state = run_sync_check(provider, key, model, raw_keys)
    if include_async:
        checks.append(asyncio.run(run_async_check(provider, key, model)))
    if include_stream:
        checks.append(run_stream_check(provider, key, model))
    report = {"provider": provider, "model": model, "checks": checks, "router_state_summary": state.get("summary", {})}
    report["leak_check"] = leak_check(report, raw_keys)
    if any(report["leak_check"].values()):
        report["status"] = "fail"
    else:
        report["status"] = "pass" if all(c.get("status") == "pass" for c in checks) else "fail"
    return report


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    providers = list(LIVE_FREE_FIRST_ORDER) if args.all_configured else [args.provider]
    key_file = Path(args.key_file)
    keys = load_provider_keys(key_file, providers)
    reports = []
    for provider in providers:
        key = keys.get(provider)
        if not key:
            reports.append({"provider": provider, "status": "skip", "reason": "missing key"})
            continue
        reports.append(run_provider(provider, key, model=args.model, include_async=args.include_async, include_stream=args.include_stream, raw_keys=list(keys.values())))
    final = {"generated_at": datetime.now(timezone.utc).isoformat(), "reports": reports}
    text = json.dumps(final, ensure_ascii=False, indent=2)
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if any(r.get("status") == "pass" for r in reports) else 2


if __name__ == "__main__":
    raise SystemExit(main())
