"""Safely discover provider model catalogs."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from nakazasen_ai_router.discovery import DiscoveredModel, ProviderModelDiscoveryError, discover_provider_models
from nakazasen_ai_router.registry import PROVIDER_REGISTRY
from scripts.live_smoke import DEFAULT_LOCAL_KEY_FILE, PROVIDER_ENV, print_result, read_key_from_file, run_provider

logging.getLogger("nakazasen_ai_router").setLevel(logging.CRITICAL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover provider models safely.")
    parser.add_argument("--provider", required=True, choices=sorted(PROVIDER_ENV))
    parser.add_argument(
        "--key-file",
        default=str(DEFAULT_LOCAL_KEY_FILE),
        help="Local ignored API Key.txt path; override with another external key file when needed",
    )
    parser.add_argument("--validate-live", action="store_true")
    parser.add_argument("--only-new", action="store_true")
    parser.add_argument("--write-report", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env_name = PROVIDER_ENV[args.provider]
    key = read_key_from_file(Path(args.key_file), env_name, args.provider)
    if not key:
        print(f"provider={args.provider} | status=SKIP | reason=missing key for provider")
        return 0

    try:
        discovered = discover_provider_models(args.provider, api_key=key)
    except ProviderModelDiscoveryError as exc:
        print(f"provider={args.provider} | status=SKIP | reason={type(exc).__name__}")
        return 0
    existing = set(PROVIDER_REGISTRY[args.provider].default_models)
    rows = [model for model in discovered if not args.only_new or model.model not in existing]
    for model in rows:
        print_model(model)
        if args.validate_live:
            print_result(run_provider(args.provider, Path(args.key_file), model=model.model))
    if args.write_report:
        print("status=SKIP | reason=write_report disabled unless target is pre-gitignored")
    return 0


def print_model(model: DiscoveredModel) -> None:
    actions = ",".join(model.supported_actions)
    print(
        f"provider={model.provider} | model={model.model} | actions={actions} | "
        f"input_tokens={model.input_token_limit or ''} | output_tokens={model.output_token_limit or ''}"
    )


if __name__ == "__main__":
    raise SystemExit(main())