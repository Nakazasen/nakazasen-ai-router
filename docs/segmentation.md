# Generic segmentation primitives

`nakazasen-ai-router` includes lightweight domain-neutral segmentation helpers for apps that need to process long payloads before routing AI requests.

Segmentation does not call providers and does not persist data. Your application still owns payload semantics and result storage.

## Basic usage

```python
from nakazasen_ai_router import AIRequest, ChunkingPolicy, merge_chunk_texts, segment_text

chunks = segment_text(long_text, ChunkingPolicy(max_estimated_tokens=8_000))
outputs = []
for chunk in chunks:
    outcome = router.route_outcome(
        AIRequest(
            prompt=chunk.text,
            metadata={**chunk.metadata, "task_type": "long_context"},
        )
    )
    if outcome.result:
        outputs.append(outcome.result.text)

merged = merge_chunk_texts(outputs)
```

## Policy

- `max_estimated_tokens`: heuristic budget per chunk.
- `overlap_tokens`: small estimated overlap between neighboring chunks.
- `preserve_paragraphs`: keep paragraph boundaries when possible.
- `chunk_metadata`: metadata copied to each `WorkChunk`.

## Token estimate

`estimate_tokens()` is dependency-free and approximate. Apps that need provider-specific accounting should use their own tokenizer and set conservative budgets.

## Safety

- Do not store full payloads in router state.
- Use chunk metadata for IDs and ordering only.
- Validate merged outputs in the app layer.
