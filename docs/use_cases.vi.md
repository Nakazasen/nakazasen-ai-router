# Các use case đa nhiệm

`nakazasen-ai-router` là một lớp cung cấp năng lực AI đa nhiệm cho ứng dụng Python. Nó không bị buộc vào dịch thuật, chatbot, agent hay một domain riêng nào. Router chịu trách nhiệm chọn provider/model/key, cooldown, budget check, retry, outcome và state vận hành an toàn. Ứng dụng của bạn chịu trách nhiệm ngữ nghĩa payload và nơi lưu kết quả.

## Bản đồ use case

| Use case | Workload profile gợi ý | API gợi ý | Ghi chú |
| --- | --- | --- | --- |
| Dịch batch | `long_context` hoặc `translation_longform` | `route_outcome()` | Dịch chỉ là một workload context dài, không phải mục tiêu duy nhất. |
| Tóm tắt tài liệu | `summarization` hoặc `long_context` | `route_outcome()` / `aroute_outcome()` | App tự chia tài liệu lớn. |
| Trích xuất JSON | `structured_json` | `route_outcome()` | App tự validate JSON. |
| Sinh nội dung | `cheap_batch` hoặc `cheap_generation` | `route_outcome()` | Phù hợp workload số lượng lớn, chi phí thấp. |
| Phân tích/phân loại văn bản | `analysis` | `route()` / `route_outcome()` | Dùng metadata để lưu job ID của app. |
| Tiền xử lý RAG | `cheap_batch` hoặc `summarization` | async route outcomes | Document store nằm ngoài router state. |
| Tự động hóa hỗ trợ khách hàng | `low_latency` | `aroute()` / `astream()` | Ưu tiên provider nhanh và UX streaming. |
| AI local/private | `private_local` hoặc `local_only` | `route()` | Tắt network hoặc chọn provider local. |
| Agent/tool orchestration | `premium_reasoning` | `route_outcome()` | Route theo chất lượng reasoning và retry semantics. |

## Ranh giới domain

Router không nên biết payload là chương truyện, ticket, log file, hợp đồng, tin nhắn hỗ trợ, source file hay ghi chú nghiên cứu. Router chỉ nhận `AIRequest` và metadata tùy chọn:

```python
AIRequest(
    prompt=payload_text,
    metadata={
        "workload_type": "json_extraction",
        "job_id": "job-123",
        "estimated_input_tokens": 10_000,
    },
)
```

## Pattern tích hợp khuyến nghị

1. Lưu job và payload trong database/queue riêng của app.
2. Dùng `create_router_from_env()` với JSON hoặc SQLite router state.
3. Dùng `route_outcome()` cho worker bền vững.
4. Reschedule outcome `retry_later` trong queue của app.
5. Lưu kết quả cuối trong database của app.
6. Dùng `export_state()` chỉ cho dashboard vận hành an toàn.

## Nguyên tắc an toàn

- Router state không chứa prompt, raw key, Authorization header hoặc raw provider response.
- App data store sở hữu payload/output theo domain.
- Live provider tests phải opt-in rõ ràng.
- Examples offline nên giữ mock-first.
