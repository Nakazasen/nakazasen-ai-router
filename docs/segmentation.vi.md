# Primitive segmentation generic

`nakazasen-ai-router` có helper segmentation nhẹ, trung lập domain, dành cho app cần xử lý payload dài trước khi route AI request.

Segmentation không gọi provider và không persist dữ liệu. Ứng dụng vẫn sở hữu semantics payload và nơi lưu kết quả.

## Cách dùng cơ bản

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

- `max_estimated_tokens`: budget heuristic cho mỗi chunk.
- `overlap_tokens`: overlap ước lượng nhỏ giữa các chunk gần nhau.
- `preserve_paragraphs`: giữ ranh giới paragraph khi có thể.
- `chunk_metadata`: metadata copy vào từng `WorkChunk`.

## Ước lượng token

`estimate_tokens()` không cần dependency và chỉ là xấp xỉ. App cần đếm token theo provider nên dùng tokenizer riêng và đặt budget thận trọng.

## An toàn

- Không lưu full payload trong router state.
- Dùng chunk metadata cho ID và thứ tự, không dùng để lưu dữ liệu nhạy cảm.
- Validate merged output ở app layer.
