# Công thức tích hợp: worker dịch chương dài

Tài liệu này mô tả cách nhúng `nakazasen-ai-router` vào một ứng dụng riêng để dịch nhiều chương trong thời gian dài.

## Kiến trúc khuyến nghị

Nên tách rõ hai lớp:

1. **Kho job của ứng dụng**
   - Lưu chapter ID, văn bản nguồn, bản dịch, trạng thái, số lần thử lại và metadata của project/user.
   - Có thể là SQLite, Postgres, Redis, queue system hoặc file.

2. **State store của Nakazasen AI Router**
   - Lưu trạng thái vận hành của provider/model/key.
   - Theo dõi cooldown, lỗi, latency và metadata trạng thái an toàn.
   - Không lưu prompt, API key thô, Authorization header hoặc response thô từ provider.

```text
Chapter queue -> Worker -> AIRouter.route_outcome()
                        -> Provider/model/key pool
                        -> Router SQLite state
                        -> App lưu bản dịch
```

## Cài đặt

```powershell
pip install nakazasen-ai-router
```

Nếu muốn dùng native async network transport:

```powershell
pip install nakazasen-ai-router[async]
```

## Biến môi trường

Nên dùng biến plural cho token pool:

```text
GEMINI_API_KEYS=<key_1>,<key_2>,<key_3>
OPENROUTER_API_KEYS=<key_1>,<key_2>
```

Luôn để key thật và file cấu hình môi trường ở ngoài repository.

## Skeleton worker sync

```python
from nakazasen_ai_router import AIRequest, RouterPolicy, create_router_from_env

router = create_router_from_env(
    enable_network=True,
    state_backend="sqlite",
    state_path="router_state.sqlite3",
    policy=RouterPolicy(
        task_type="translation_longform",
        max_attempts=3,
        max_estimated_input_tokens=120_000,
        max_estimated_output_tokens=12_000,
        backoff_base_seconds=15,
        backoff_max_seconds=3600,
    ),
)


def estimate_tokens(text: str) -> int:
    # Nên thay bằng tokenizer thật nếu có.
    return max(1, len(text.split()))


def process_chapter(job):
    source_text = job.source_text
    input_tokens = estimate_tokens(source_text)

    outcome = router.route_outcome(
        AIRequest(
            prompt=source_text,
            metadata={
                "task_type": "translation_longform",
                "chapter_id": job.chapter_id,
                "estimated_input_tokens": input_tokens,
                "estimated_output_tokens": input_tokens * 2,
            },
        )
    )

    if outcome.status == "success" and outcome.result is not None:
        job.mark_done(outcome.result.text)
        return

    if outcome.status == "retry_later":
        job.reschedule_after(outcome.retry_after_seconds or 60)
        return

    if outcome.error_type == "budget_exceeded":
        job.mark_needs_split("chapter quá lớn so với budget hiện tại")
        return

    job.mark_failed(outcome.error_type or "route_failed")
```

## Skeleton worker async

```python
router = create_router_from_env(
    enable_network=True,
    enable_async_network=True,
    state_backend="sqlite",
    state_path="router_state.sqlite3",
    policy=RouterPolicy(task_type="translation_longform", max_attempts=3),
)


async def process_chapter_async(job):
    outcome = await router.aroute_outcome(
        AIRequest(
            prompt=job.source_text,
            metadata={
                "task_type": "translation_longform",
                "chapter_id": job.chapter_id,
                "estimated_input_tokens": len(job.source_text.split()),
            },
        )
    )
    return outcome
```

## Streaming UI skeleton

`stream()` và `astream()` dùng được ngay cả khi provider chưa có streaming thật. Khi đó router fallback thành một chunk chứa full result.

```python
for chunk in router.stream(AIRequest(prompt=source_text, metadata={"task_type": "translation_longform"})):
    ui.append_text(chunk.text)
```

## Snapshot cho admin dashboard

```python
snapshot = router.export_state()
print(snapshot["summary"])
```

Dùng snapshot này cho dashboard vận hành: số candidate healthy/cooldown/dead, thời gian retry, loại lỗi gần nhất và latency. Không xem nó là audit log đầy đủ.

## Chính sách chia chương

Trong production translation, nên chia chương trước khi route nếu:

- estimated input tokens vượt budget router,
- estimated output tokens quá cao,
- model trả lỗi token/context,
- chương chứa bảng lớn hoặc metadata nhúng.

Flow thực tế:

1. Ước lượng token.
2. Nếu vượt budget, chia theo cảnh/đoạn.
3. Dịch từng chunk riêng.
4. Ghép output theo thứ tự gốc.
5. Lưu bản dịch chương hoàn chỉnh trong store của ứng dụng.

## Xử lý lỗi

| Outcome | Ý nghĩa | Hành động khuyến nghị |
| --- | --- | --- |
| `success` | Dịch xong | Lưu output và mark done |
| `retry_later` | Provider đang cooldown hoặc tạm lỗi | Reschedule job |
| `failed` + `budget_exceeded` | Job quá lớn so với budget | Chia chương hoặc nâng budget |
| `failed` + `route_failed` | Lỗi routing không retry được | Xem attempts và mark failed |

## Demo offline

Chạy demo offline có sẵn:

```powershell
py examples/translation_worker_demo.py --offline-demo
```

Demo sẽ tạo chapter mẫu, xử lý bằng fake provider, ghi output và export summary an toàn.

## Checklist an toàn

- Không commit API key.
- Không lưu prompt trong router state.
- Lưu input/output chương trong database của ứng dụng, không lưu trong router state.
- Dùng `route_outcome()` cho worker bền vững.
- Dùng SQLite state khi có nhiều worker local.
- Theo dõi `export_state()` để biết candidate cooldown/dead.
