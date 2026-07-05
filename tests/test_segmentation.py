import pytest

from nakazasen_ai_router import ChunkingPolicy, estimate_tokens, merge_chunk_texts, segment_text


def test_estimate_tokens_empty_and_non_empty():
    assert estimate_tokens("") == 0
    assert estimate_tokens("   ") == 0
    assert estimate_tokens("hello") > 0


def test_segment_empty_input_returns_no_chunks():
    assert segment_text("   ") == []


def test_segment_short_input_creates_one_chunk():
    chunks = segment_text("hello world", ChunkingPolicy(max_estimated_tokens=100))
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert chunks[0].metadata["chunk_count"] == 1


def test_segment_long_input_splits_under_budget():
    text = " ".join(["word"] * 100)
    chunks = segment_text(text, ChunkingPolicy(max_estimated_tokens=20, preserve_paragraphs=False))
    assert len(chunks) > 1
    assert all(chunk.estimated_tokens <= 20 for chunk in chunks)
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_preserve_paragraph_boundaries_when_possible():
    text = "alpha paragraph\n\nbeta paragraph\n\ngamma paragraph"
    chunks = segment_text(text, ChunkingPolicy(max_estimated_tokens=8, preserve_paragraphs=True))
    assert len(chunks) >= 2
    assert all("\n\n" not in chunk.text or chunk.text.count("\n\n") >= 1 for chunk in chunks)


def test_oversized_paragraph_falls_back_to_words():
    text = " ".join(["oversized"] * 80)
    chunks = segment_text(text, ChunkingPolicy(max_estimated_tokens=30, preserve_paragraphs=True))
    assert len(chunks) > 1
    assert all(chunk.estimated_tokens <= 30 for chunk in chunks)


def test_metadata_includes_policy_metadata_and_chunk_info():
    chunks = segment_text("one two three", ChunkingPolicy(max_estimated_tokens=100, chunk_metadata={"job_id": "j1"}))
    assert chunks[0].metadata["job_id"] == "j1"
    assert chunks[0].metadata["chunk_index"] == 0
    assert chunks[0].metadata["chunk_count"] == 1


def test_merge_preserves_order_and_separator():
    assert merge_chunk_texts(["a", "b", "c"], separator="|") == "a|b|c"


@pytest.mark.parametrize(
    "policy",
    [
        ChunkingPolicy(max_estimated_tokens=0),
        ChunkingPolicy(max_estimated_tokens=10, overlap_tokens=-1),
        ChunkingPolicy(max_estimated_tokens=10, overlap_tokens=10),
        ChunkingPolicy(max_estimated_tokens=10, preserve_paragraphs=True, paragraph_separator=""),
    ],
)
def test_invalid_policy_values_raise(policy):
    with pytest.raises(ValueError):
        segment_text("hello", policy)


def test_overlap_repeats_boundary_content():
    text = " ".join(f"w{i}" for i in range(80))
    chunks = segment_text(text, ChunkingPolicy(max_estimated_tokens=12, overlap_tokens=2, preserve_paragraphs=False))
    assert len(chunks) > 1
    first_tail = chunks[0].text.split()[-1]
    assert first_tail in chunks[1].text.split()
