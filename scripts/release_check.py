"""Validate release metadata and required release documentation.

This check is offline and never reads credential files.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r'version\s*=\s*"([^"]+)"')


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check release version and documentation consistency.")
    parser.add_argument("version", help="Expected SemVer without the v prefix, for example 0.3.0")
    args = parser.parse_args()
    version = args.version.strip().removeprefix("v")

    errors: list[str] = []
    pyproject = _read("pyproject.toml")
    match = VERSION_RE.search(pyproject)
    actual = match.group(1) if match else None
    if actual != version:
        errors.append(f"pyproject.toml version is {actual!r}, expected {version!r}")

    required_files = (
        "CHANGELOG.md",
        "README.md",
        "README.vi.md",
        "ARCHITECTURE.md",
        "docs/releasing.md",
        "docs/releasing.vi.md",
        f"docs/releases/{version}.md",
    )
    for relative in required_files:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    if not errors:
        changelog = _read("CHANGELOG.md")
        readme = _read("README.md")
        readme_vi = _read("README.vi.md")
        release_note = _read(f"docs/releases/{version}.md")
        checks = (
            (f"## {version} -", changelog, "CHANGELOG.md version heading"),
            (f"@v{version}", readme, "README.md stable install tag"),
            (f"{version}.md", readme, "README.md release-note link"),
            (f"@v{version}", readme_vi, "README.vi.md stable install tag"),
            (f"{version}.md", readme_vi, "README.vi.md release-note link"),
            (f"# Nakazasen AI Router {version}", release_note, "release-note heading"),
        )
        for needle, haystack, label in checks:
            if needle not in haystack:
                errors.append(f"missing {label}: {needle}")

    if errors:
        print("release-check: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"release-check: OK ({version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())