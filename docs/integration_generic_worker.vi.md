# Công thức tích hợp worker generic

Dùng recipe này khi một repository khác cần một AI capacity pool bền vững mà không gắn với domain cụ thể.

## Trách nhiệm

Ứng dụng của bạn sở hữu:

- job ID và domain state,
- nơi lưu payload,
- nơi lưu kết quả,
- ownership theo user/project,
- validate theo domain,
- job scheduling.

`nakazasen-ai-router` sở hữu:

- chọn provider/model/key,
- cooldown và failure streak,
- gợi ý retry/backoff,
- quyết định budget guard,
- state vận hành an toàn,
- dashboard snapshot đã sanitize.

## Worker sync tối thiểu

```python
from nakazasen_ai_router import AIRequest, RouterPolicy, create_router_from_env

router = create_router_from_env(
    enable_network=True,
    state_backend="sqlite",
    state_path="router_state.sqlite3",
    policy=RouterPolicy(
        task_type="cheap_batch",
        max_attempts=3,
        max_estimated_input_tokens=120_000,
        max_estimated_output_tokens=16_000,
    ),
)


def process_job(job):
    outcome = router.route_outcome(
        AIRequest(
            prompt=job.payload_text,
            metadata={
                "job_id": job.id,
                "workload_type": job.workload_type,
                "task_type": job.workload_profile,
                "estimated_input_tokens": job.estimated_input_tokens,
                "estimated_output_tokens": job.estimated_output_tokens,
            },
        )
    )

    if outcome.status == "success" and outcome.result:
        job.mark_success(outcome.result.text)
    elif outcome.status == "retry_later":
        job.reschedule(outcome.retry_after_seconds or 60)
    else:
        job.mark_failed(outcome.error_type or "route_failed")
```

## Worker async

```python
router = create_router_from_env(
    enable_network=True,
    enable_async_network=True,
    state_backend="sqlite",
    state_path="router_state.sqlite3",
    policy=RouterPolicy(task_type="low_latency", max_attempts=3),
)


async def process_job_async(job):
    return await router.aroute_outcome(
        AIRequest(
            prompt=job.payload_text,
            metadata={"job_id": job.id, "task_type": job.workload_profile},
        )
    )
```

Với worker bền vững, xem [job_queue.vi.md](job_queue.vi.md) để dùng pattern `SQLiteJobStore` enqueue/claim/retry.

## Snapshot vận hành

```python
snapshot = router.export_state()
```

Dùng snapshot cho dashboard health và quyết định capacity. Không dùng nó làm nơi lưu domain data.

## Ví dụ profile

- `long_context`: tài liệu lớn và tác vụ cần context dài.
- `cheap_batch`: job số lượng lớn, chi phí thấp.
- `structured_json`: extraction cần model hỗ trợ JSON.
- `low_latency`: workflow có user chờ trực tiếp.
- `premium_reasoning`: analysis/agent cần chất lượng cao.
- `private_local`: routing local/private.

## Checklist tích hợp

- Không đưa API key vào source control.
- Không đưa payload của app vào router state.
- Dùng `route_outcome()` cho job bền vững.
- Dùng `aroute_outcome()` cho async worker.
- Dùng SQLite state khi có nhiều worker local.
- Dùng metadata cho job ID và workload profile.
