"""Emit sanitized router/job metrics as JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from nakazasen_ai_router import SQLiteJobStore, collect_job_metrics, collect_metrics, collect_router_metrics


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit sanitized Nakazasen AI Router metrics JSON.")
    parser.add_argument("--jobs", default="", help="Path to SQLiteJobStore database")
    parser.add_argument("--router-state-json", default="", help="Path to JSON saved from router.export_state()")
    parser.add_argument("--json-out", default="", help="Optional output JSON path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    warnings: list[str] = []
    router_state = None
    job_store = None
    if args.router_state_json:
        path = Path(args.router_state_json)
        if path.exists():
            router_state = json.loads(path.read_text(encoding="utf-8-sig"))
        else:
            warnings.append(f"router_state_json_missing:{path}")
    if args.jobs:
        path = Path(args.jobs)
        if path.exists():
            job_store = SQLiteJobStore(path)
        else:
            warnings.append(f"jobs_missing:{path}")
    snapshot = collect_metrics(router_state, job_store).to_dict()
    snapshot["warnings"] = warnings
    text = json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True)
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
