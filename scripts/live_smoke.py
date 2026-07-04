"""Safe live smoke test for Nakazasen AI Router."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nakazasen_ai_router import AIRequest, RouterError, create_router_from_env
from nakazasen_ai_router.config import LIVE_FREE_FIRST_ORDER

PROVIDER_ENV = {
    "gemini": "GEMINI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "groq": "GROQ_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "nvidia_nim": "NVIDIA_NIM_API_KEY",
    "chatanywhere": "CHATANYWHERE_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}

PROVIDER_LABEL_ALIASES = {
    "gemini": ("gemini", "google gemini", "gemini api key", "google ai", "google ai studio"),
    "openrouter": ("open router",),
    "groq": ("groq api key",),
    "nvidia_nim": ("nvidia nim",),
    "chatanywhere": ("chatanywhere", "chat anywhere"),
    "mistral": ("mistral ai",),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe live provider smoke tests.")
    parser.add_argument("--provider", required=True, choices=sorted(PROVIDER_ENV | {"all": ""}))
    parser.add_argument("--key-file", required=True, help="Path to key file outside this repository")
    parser.add_argument("--stop-on-first-pass", action="store_true")
    return parser.parse_args()


def read_key_from_file(path: Path, env_name: str, provider: str) -> str:
    if not path.exists():
        return ""
    try:
        content = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""
    aliases = {
        env_name.lower(),
        provider.lower(),
        provider.lower().replace("_", "-"),
        provider.lower().replace("_", " "),
        provider.lower().replace("router", " router"),
    }
    aliases.update(PROVIDER_LABEL_ALIASES.get(provider, ()))
    lines = content.splitlines()
    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower() in aliases and index + 1 < len(lines):
            return lines[index + 1].strip().strip('"').strip("'")
        separator = "=" if "=" in line else (":" if ":" in line else "")
        if not separator:
            continue
        name, value = line.split(separator, 1)
        if name.strip().lower() in aliases:
            cleaned = value.strip().strip('"').strip("'")
            if cleaned:
                return cleaned
            if index + 1 < len(lines):
                return lines[index + 1].strip().strip('"').strip("'")
    return ""


def run_provider(provider: str, key_file: Path) -> dict[str, str]:
    env_name = PROVIDER_ENV[provider]
    key = read_key_from_file(key_file, env_name, provider)
    if not key:
        return {"provider": provider, "status": "SKIP", "reason": "missing key for provider", "model": ""}

    old_value = os.environ.get(env_name)
    old_log_level = logging.getLogger("nakazasen_ai_router").level
    logging.getLogger("nakazasen_ai_router").setLevel(logging.CRITICAL)
    os.environ[env_name] = key
    try:
        router = create_router_from_env(provider_names=(provider,), enable_network=True)
        if not router.providers:
            return {"provider": provider, "status": "SKIP", "reason": "provider not created", "model": ""}
        result = router.route(AIRequest(prompt="Reply with OK."))
        attempts = list(result.metadata.get("attempts", []))
        model = str(result.metadata.get("model") or (attempts[-1].get("model") if attempts else ""))
        text = result.text.strip().replace("\r", " ").replace("\n", " ")
        return {
            "provider": provider,
            "status": "PASS",
            "reason": "",
            "model": model,
            "text_length": str(len(result.text)),
            "text_preview": text[:80],
        }
    except RouterError as exc:
        attempt = exc.attempts[-1] if exc.attempts else {}
        provider_obj = router.providers[0].provider if 'router' in locals() and router.providers else None
        status_code = ""
        safe_message = ""
        if provider_obj is not None:
            safe_message = str(provider_obj.health.last_error or "")[:120]
            status_code = _status_code_from_message(safe_message)
        return {
            "provider": provider,
            "status": "FAIL",
            "reason": str(attempt.get("reason", "router_error")),
            "error_type": str(attempt.get("reason", "router_error")),
            "status_code": status_code,
            "model": str(attempt.get("model", "")),
            "message": safe_message,
        }
    finally:
        logging.getLogger("nakazasen_ai_router").setLevel(old_log_level)
        if old_value is None:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = old_value


def _status_code_from_message(message: str) -> str:
    for code in ("400", "401", "403", "404", "429", "500", "502", "503", "504"):
        if code in message:
            return code
    return ""


def print_result(row: dict[str, str]) -> None:
    keys = ["provider", "status", "reason", "error_type", "status_code", "model", "text_length", "text_preview", "message"]
    print(" | ".join(f"{key}={row[key]}" for key in keys if row.get(key)))


def main() -> int:
    args = parse_args()
    providers = list(LIVE_FREE_FIRST_ORDER) if args.provider == "all" else [args.provider]
    any_fail = False
    any_pass = False
    for provider in providers:
        row = run_provider(provider, Path(args.key_file))
        print_result(row)
        any_pass = any_pass or row["status"] == "PASS"
        any_fail = any_fail or row["status"] == "FAIL"
        if args.stop_on_first_pass and row["status"] == "PASS":
            break
    return 0 if any_pass or not any_fail else 2


if __name__ == "__main__":
    raise SystemExit(main())
