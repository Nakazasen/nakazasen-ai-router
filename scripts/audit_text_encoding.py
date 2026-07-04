"""Audit text files for common mojibake patterns."""

from __future__ import annotations

from pathlib import Path

MOJIBAKE_PATTERNS = tuple(chr(code) for code in (
    0x862F,
    0xFF86,
    0x76FB,
    0x51A2,
    0x7E5D,
    0x7E3A,
    0x00C3,
    0x00C2,
    0xFFFD,
    0x9B1F,
    0x8737,
    0x8B41,
    0x90B1,
    0x90E2,
    0x9B2F,
    0x9A5B,
    0x9A3E,
    0x9AEF,
    0x9642,
    0x9036,
))

TEXT_EXTENSIONS = {".md", ".py", ".toml", ".txt", ".yml", ".yaml"}
SKIP_PARTS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", "local_cases", ".ai", "build", "dist"}


def should_scan(path: Path) -> bool:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return False
    return not any(part in SKIP_PARTS or part.endswith(".egg-info") for part in path.parts)


def audit(root: Path) -> list[tuple[Path, int, str]]:
    findings: list[tuple[Path, int, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or not should_scan(path):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), 1):
            if any(pattern in line for pattern in MOJIBAKE_PATTERNS):
                safe_context = line.strip()[:120].encode("ascii", "backslashreplace").decode("ascii")
                findings.append((path, line_number, safe_context))
    return findings


def main() -> int:
    findings = audit(Path("."))
    for path, line_number, context in findings:
        print(f"{path}:{line_number}: {context}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
