"""Safe live smoke test for Nakazasen AI Router.

Reads a key file in memory, maps provider names to environment variable names,
and performs one short opt-in network request. Never prints API keys.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nakazasen_ai_router import AIRequest, RouterError, create_router_from_env

PROVIDER_ENV = {
    "openrouter": "OPENROUTER_API_KEY",
    "groq": "GROQ_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "nvidia_nim": "NVIDIA_NIM_API_KEY",
    "chatanywhere": "CHATANYWHERE_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}

PROVIDER_LABEL_ALIASES = {
    "openrouter": ("open router",),
    "groq": ("groq api key",),
    "nvidia_nim": ("nvidia nim",),
    "chatanywhere": ("chatanywhere", "chat anywhere"),
    "mistral": ("mistral ai",),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one safe live provider smoke test.")
    parser.add_argument("--provider", required=True, choices=sorted(PROVIDER_ENV))
    parser.add_argument("--key-file", required=True, help="Path to key file outside this repository")
    return parser.parse_args()


def read_key_from_file(path: Path, env_name: str, provider: str) -> str:
    if not path.exists():
        print("key_file_status=missing")
        return ""
    try:
        content = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        print("key_file_status=unreadable")
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
    print("key_file_status=present_but_unmapped")
    return ""


def main() -> int:
    args = parse_args()
    provider = args.provider
    env_name = PROVIDER_ENV[provider]
    key = read_key_from_file(Path(args.key_file), env_name, provider)
    if not key:
        print(f"provider={provider}")
        print("status=SKIP")
        print("reason=missing key for provider")
        return 0

    old_value = os.environ.get(env_name)
    os.environ[env_name] = key
    try:
        router = create_router_from_env(provider_names=(provider,), enable_network=True)
        if not router.providers:
            print(f"provider={provider}")
            print("status=SKIP")
            print("reason=provider not created")
            return 0
        result = router.route(AIRequest(prompt="Reply with OK."))
        attempts = list(result.metadata.get("attempts", []))
        model = result.metadata.get("model") or (attempts[-1].get("model") if attempts else "")
        text = result.text.strip().replace("\r", " ").replace("\n", " ")
        print(f"provider={provider}")
        print("status=PASS")
        print(f"model={model}")
        print(f"text_length={len(result.text)}")
        print(f"text_preview={text[:80]}")
        return 0
    except RouterError as exc:
        reason = exc.attempts[-1].get("reason", "router_error") if exc.attempts else "router_error"
        print(f"provider={provider}")
        print("status=FAIL")
        print(f"reason={reason}")
        return 2
    finally:
        if old_value is None:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = old_value


if __name__ == "__main__":
    raise SystemExit(main())
