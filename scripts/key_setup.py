"""Create a provider key file safely outside the repository."""

from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS = [
    ("GEMINI_API_KEY", "Gemini API key"),
    ("GROQ_API_KEY", "Groq API key"),
    ("OPENROUTER_API_KEY", "OpenRouter API key"),
]


def is_inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def write_key_file(out: Path, values: dict[str, str], allow_inside_repo: bool = False) -> None:
    out = out.expanduser().resolve()
    if is_inside_repo(out) and not allow_inside_repo:
        raise SystemExit("Refusing to write keys inside this repository. Choose an external path or pass --allow-inside-repo.")
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Provider keys for nakazasen-ai-router. Keep this file private."]
    for name, value in values.items():
        if value:
            lines.append(f"{name}={value}")
    if len(lines) == 1:
        raise SystemExit("No keys entered; nothing to write.")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(out, 0o600)
    except OSError:
        pass


def prompt_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for env_name, label in PROVIDERS:
        values[env_name] = getpass.getpass(f"{label} (blank to skip): ").strip()
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely create a provider key file outside the repository.")
    parser.add_argument("--out", required=True, help="Output key file path outside this repository")
    parser.add_argument("--allow-inside-repo", action="store_true", help="Allow writing inside repo; not recommended")
    args = parser.parse_args()
    out = Path(args.out)
    if is_inside_repo(out) and not args.allow_inside_repo:
        raise SystemExit("Refusing to write keys inside this repository. Choose an external path or pass --allow-inside-repo.")
    write_key_file(out, prompt_values(), allow_inside_repo=args.allow_inside_repo)
    print(f"Wrote provider key file: {out.expanduser().resolve()}")
    print(f"Test with: py scripts/live_smoke.py --provider gemini --key-file \"{out.expanduser().resolve()}\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
