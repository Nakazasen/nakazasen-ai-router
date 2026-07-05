"""Domain-neutral workload segmentation primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class ChunkingPolicy:
    """Controls heuristic text segmentation.

    Token counts are estimates only. Applications that need model-specific
    accounting should pre-tokenize or override budgets at the app layer.
    """

    max_estimated_tokens: int = 8_000
    overlap_tokens: int = 0
    preserve_paragraphs: bool = True
    paragraph_separator: str = "\n\n"
    chunk_metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.max_estimated_tokens <= 0:
            raise ValueError("max_estimated_tokens must be positive")
        if self.overlap_tokens < 0:
            raise ValueError("overlap_tokens must be non-negative")
        if self.overlap_tokens >= self.max_estimated_tokens:
            raise ValueError("overlap_tokens must be smaller than max_estimated_tokens")
        if self.preserve_paragraphs and not self.paragraph_separator:
            raise ValueError("paragraph_separator must be non-empty when preserve_paragraphs is enabled")


@dataclass(frozen=True)
class WorkChunk:
    """One ordered chunk of application-owned workload text."""

    index: int
    text: str
    estimated_tokens: int
    metadata: Mapping[str, Any] = field(default_factory=dict)


def estimate_tokens(text: str) -> int:
    """Return a lightweight heuristic token estimate.

    Empty input returns 0. Non-empty input returns at least 1. This heuristic is
    intentionally dependency-free and approximates one token per four chars.
    """

    if not text or not text.strip():
        return 0
    return max(1, ceil(len(text) / 4))


def segment_text(text: str, policy: ChunkingPolicy | None = None) -> list[WorkChunk]:
    """Split text into ordered chunks using a domain-neutral policy."""

    policy = policy or ChunkingPolicy()
    policy.validate()
    normalized = text.strip() if text else ""
    if not normalized:
        return []

    units = _paragraph_units(normalized, policy) if policy.preserve_paragraphs else []
    if not units:
        units = normalized.split()
        joiner = " "
    else:
        joiner = policy.paragraph_separator

    chunk_texts: list[str] = []
    current: list[str] = []
    for unit in units:
        if estimate_tokens(unit) > policy.max_estimated_tokens:
            if current:
                chunk_texts.append(joiner.join(current).strip())
                current = []
            chunk_texts.extend(_split_words(unit, policy))
            continue
        candidate = joiner.join([*current, unit]).strip() if current else unit.strip()
        if current and estimate_tokens(candidate) > policy.max_estimated_tokens:
            chunk_texts.append(joiner.join(current).strip())
            current = _overlap_units(current, policy.overlap_tokens)
            current.append(unit)
        else:
            current.append(unit)
    if current:
        chunk_texts.append(joiner.join(current).strip())

    total = len(chunk_texts)
    return [
        WorkChunk(
            index=index,
            text=chunk,
            estimated_tokens=estimate_tokens(chunk),
            metadata={**dict(policy.chunk_metadata), "chunk_index": index, "chunk_count": total},
        )
        for index, chunk in enumerate(chunk_texts)
        if chunk
    ]


def merge_chunk_texts(chunks: Sequence[str], separator: str = "\n") -> str:
    """Merge chunk outputs in the order provided by the caller."""

    return separator.join(chunks)


def _paragraph_units(text: str, policy: ChunkingPolicy) -> list[str]:
    return [part.strip() for part in text.split(policy.paragraph_separator) if part.strip()]


def _split_words(text: str, policy: ChunkingPolicy) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word]).strip() if current else word
        if current and estimate_tokens(candidate) > policy.max_estimated_tokens:
            chunks.append(" ".join(current).strip())
            current = _overlap_units(current, policy.overlap_tokens)
            current.append(word)
        else:
            current.append(word)
    if current:
        chunks.append(" ".join(current).strip())
    return chunks


def _overlap_units(units: list[str], overlap_tokens: int) -> list[str]:
    if overlap_tokens <= 0 or not units:
        return []
    selected: list[str] = []
    total = 0
    for unit in reversed(units):
        unit_tokens = estimate_tokens(unit)
        if selected and total + unit_tokens > overlap_tokens:
            break
        selected.append(unit)
        total += unit_tokens
        if total >= overlap_tokens:
            break
    return list(reversed(selected))
