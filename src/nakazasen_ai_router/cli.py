"""Command-line interface for release awareness and free-tier reporting."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from typing import Any, Callable

from .free_tier_catalog import DEFAULT_FREE_TIER_CATALOG
from .updates import check_for_updates, installed_version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nakazasen-ai-router")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("version", help="print the installed version")

    update = subparsers.add_parser("update", help="check for or explicitly apply an update")
    action = update.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="check GitHub tags without changing the environment")
    action.add_argument("--apply", action="store_true", help="upgrade with the current Python interpreter after confirmation")
    update.add_argument("--yes", action="store_true", help="allow explicit non-interactive apply")
    update.add_argument("--timeout", type=float, default=3.0)

    free_tiers = subparsers.add_parser("free-tiers", help="show audited free-tier capacity")
    free_tiers.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    input_func: Callable[[str], str] = input,
    subprocess_run: Callable[..., Any] = subprocess.run,
    update_checker: Callable[..., Any] = check_for_updates,
) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "version":
        print(installed_version())
        return 0
    if args.command == "free-tiers":
        budget = DEFAULT_FREE_TIER_CATALOG.budget()
        payload = budget.to_dict()
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"Audited recurring tokens/month: {budget.audited_recurring_tokens_month}")
            print(f"One-time signup tokens: {budget.one_time_signup_tokens}")
            print(f"Usage scope: {budget.usage_scope}")
            print(f"Uncountable pools: {len(budget.unlimited_or_uncountable_pools)}")
            print(f"Excluded/stale pools: {len(budget.excluded_or_stale_pools)}")
        return 0

    info = update_checker(enable_network=True, timeout=args.timeout)
    print(f"Current version: {info.current_version}")
    print(f"Latest version: {info.latest_version or 'unknown'}")
    print(f"Status: {info.status}")
    if args.check or not info.update_available:
        return 0 if info.status in {"up_to_date", "update_available"} else 2

    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        f"nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v{info.latest_version}",
    ]
    print("Command preview:")
    print(" ".join(command))
    if not args.yes:
        answer = input_func("Apply this update? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Update cancelled.")
            return 1
    completed = subprocess_run(command, check=False)
    return int(getattr(completed, "returncode", 0))


if __name__ == "__main__":
    raise SystemExit(main())
