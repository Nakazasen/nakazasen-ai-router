"""Audit public documentation quality."""

from __future__ import annotations

import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_text_encoding import audit as audit_text_encoding
PUBLIC_DOCS = [ROOT / "README.md", ROOT / "README.vi.md", ROOT / "CHANGELOG.md", ROOT / "ARCHITECTURE.md", ROOT / "ROADMAP.md"]
REQUIRED_VI_DOCS = [
    ROOT / "docs" / "vi" / "QUICKSTART.vi.md",
    ROOT / "docs" / "vi" / "SECURITY_AND_PRIVACY.vi.md",
    ROOT / "docs" / "vi" / "ROADMAP.vi.md",
    ROOT / "docs" / "vi" / "OPERATION_RULES.vi.md",
]
SECRET_RE = re.compile(r"sk-|AIza|GEMINI_API_KEY=.*[A-Za-z0-9]|OPENROUTER_API_KEY=.*[A-Za-z0-9]", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\b(TODO|FIXME)\b", re.IGNORECASE)


def public_doc_paths() -> list[Path]:
    docs = list(PUBLIC_DOCS)
    docs.extend(REQUIRED_VI_DOCS)
    docs.extend(sorted((ROOT / "docs").rglob("*.md")))
    return sorted(set(path for path in docs if path.exists()))


def audit_docs_quality() -> list[str]:
    findings: list[str] = []
    readme = ROOT / "README.md"
    readme_vi = ROOT / "README.vi.md"
    if not readme_vi.exists():
        findings.append("README.vi.md is missing")
    for path in REQUIRED_VI_DOCS:
        if not path.exists():
            findings.append(f"{path.relative_to(ROOT)} is missing")
    if readme.exists() and "README.vi.md" not in readme.read_text(encoding="utf-8", errors="replace"):
        findings.append("README.md must link to README.vi.md")
    for path, line_number, context in audit_text_encoding(ROOT):
        findings.append(f"mojibake: {path.relative_to(ROOT)}:{line_number}: {context}")
    for path in public_doc_paths():
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        if "\ufffd" in text:
            findings.append(f"replacement-character: {rel}")
        if PLACEHOLDER_RE.search(text):
            findings.append(f"placeholder: {rel}")
        if SECRET_RE.search(text):
            findings.append(f"secret-pattern: {rel}")
        if "API Key.txt" in text:
            key_file_docs = {
                "README.md",
                "README.vi.md",
                "ARCHITECTURE.md",
                "CHANGELOG.md",
                "docs/provider_keys.md",
                "docs/provider_keys.vi.md",
                "docs/releases/0.2.2.md",
                "docs/releases/0.2.3.md",
                "docs/install_update.md",
                "docs/install_update.vi.md",
                "docs/live_conformance.md",
                "docs/path_hygiene.vi.md",
                "docs/vi/ROADMAP.vi.md",
            }
            if rel.as_posix() not in key_file_docs:
                findings.append(f"hard-coded-key-file-name: {rel}")
    return findings


def main() -> int:
    findings = audit_docs_quality()
    for finding in findings:
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
