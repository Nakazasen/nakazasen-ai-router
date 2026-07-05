"""Audit project positioning for general-purpose AI capacity messaging."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSLATION_RE = re.compile(r"translation|translate|chapter|dịch|truyện|longform", re.IGNORECASE)
GENERAL_RE = re.compile(r"general-purpose|ai capacity layer|đa nhiệm|workload|summarization|analysis|json|content|provider|router", re.IGNORECASE)


def _text_files() -> list[Path]:
    files: list[Path] = []
    for root in [ROOT / "README.md", ROOT / "README.vi.md", ROOT / "docs", ROOT / "examples"]:
        if root.is_file():
            files.append(root)
        elif root.exists():
            files.extend(path for path in root.rglob("*") if path.suffix.lower() in {".md", ".py"})
    return sorted(files)


def audit_positioning() -> list[str]:
    findings: list[str] = []
    readme = (ROOT / "README.md").read_text(encoding="utf-8", errors="replace").lower()
    readme_vi = (ROOT / "README.vi.md").read_text(encoding="utf-8", errors="replace").lower()
    if "general-purpose ai capacity layer" not in readme:
        findings.append("README.md missing general-purpose positioning")
    if "lớp cung cấp năng lực ai đa nhiệm" not in readme_vi:
        findings.append("README.vi.md missing general-purpose positioning")
    for required in [
        ROOT / "docs" / "use_cases.md",
        ROOT / "docs" / "use_cases.vi.md",
        ROOT / "docs" / "integration_generic_worker.md",
        ROOT / "docs" / "integration_generic_worker.vi.md",
    ]:
        if not required.exists():
            findings.append(f"missing {required.relative_to(ROOT)}")
    examples = list((ROOT / "examples").glob("*_demo.py"))
    non_translation = [path for path in examples if "translation" not in path.name]
    if len(non_translation) < 3:
        findings.append("need at least three non-translation offline demos")
    return findings


def summarize_terms() -> dict[str, int]:
    translation = 0
    general = 0
    for path in _text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        translation += len(TRANSLATION_RE.findall(text))
        general += len(GENERAL_RE.findall(text))
    return {"translation_terms": translation, "general_terms": general}


def main() -> int:
    findings = audit_positioning()
    summary = summarize_terms()
    print(summary)
    for finding in findings:
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
