"""Audit repository text files for machine-local path leaks."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", "build", "dist"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".sqlite3", ".whl", ".gz", ".zip"}
ALLOWED_WINDOWS_PATHS = {
    r"D:\path\to\provider_keys.txt",
    r"D:\duong_dan_ngoai\provider_keys.txt",
}
ALLOWED_FRAGMENTS = {
    r"path\to\provider_keys.txt",
    "local_cases/",
    "local_cases\\",
    ".demo_summarization",
    ".demo_json_extraction",
    ".demo_content_generation",
    ".demo_segmented_batch",
    ".demo_job_queue",
    ".demo_quota_policy",
    ".demo_sdk_worker_stack",
    ".demo_translation_worker",
}
LEAK_PATTERNS = [
    ("sandbox-path", re.compile(r"D:\\Sandbox\\", re.IGNORECASE)),
    ("user-profile-path", re.compile(r"C:\\Users\\", re.IGNORECASE)),
    ("file-uri-local-path", re.compile(r"file:///[A-Z]:/", re.IGNORECASE)),
    ("hard-coded-key-file-name", re.compile(r"API Key\.txt", re.IGNORECASE)),
    ("tmp-install-smoke", re.compile(r"\.tmp_install_smoke", re.IGNORECASE)),
    ("windows-absolute-path", re.compile(r"\b[A-Z]:\\(?!path\\to\\provider_keys\.txt|duong_dan_ngoai\\provider_keys\.txt)", re.IGNORECASE)),
]


def _should_scan(path: Path) -> bool:
    rel_parts = set(path.relative_to(ROOT).parts)
    if rel_parts & SKIP_PARTS:
        return False
    if "src" in rel_parts and "nakazasen_ai_router.egg-info" in rel_parts:
        return False
    return path.is_file() and path.suffix.lower() not in SKIP_SUFFIXES


def _is_allowed(rel: Path, line: str) -> bool:
    if rel.as_posix() in {"scripts/audit_local_paths.py", "scripts/audit_docs_quality.py"}:
        return True
    if any(path in line for path in ALLOWED_WINDOWS_PATHS):
        return True
    return any(fragment in line for fragment in ALLOWED_FRAGMENTS)


def audit_local_paths(root: Path = ROOT) -> list[str]:
    findings: list[str] = []
    for path in sorted(root.rglob("*")):
        if not _should_scan(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root)
        for line_number, line in enumerate(text.splitlines(), 1):
            if _is_allowed(rel, line):
                continue
            for name, pattern in LEAK_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{name}: {rel}:{line_number}: {line.strip()}")
    return findings


def main() -> int:
    findings = audit_local_paths()
    for finding in findings:
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
