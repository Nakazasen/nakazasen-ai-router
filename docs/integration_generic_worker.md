# Generic worker integration recipe

Use this recipe when another repository needs a durable AI capacity pool without tying the integration to a specific domain.

## Responsibilities

Your application owns:

- job IDs and domain state,
- payload storage,
- result storage,
- user/project ownership,
- domain validation,
- job scheduling.

`nakazasen-ai-router` owns:

- provider/model/key selection,
- cooldowns and failure streaks,
- retry/backoff recommendations,
- budget guard decisions,
- safe operational state,
- sanitized dashboard snapshots.

## Minimal sync worker

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

## Async worker

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

For persistent workers, see [job_queue.md](job_queue.md) for `SQLiteJobStore` enqueue/claim/retry patterns.

Collect safe operational snapshots with `collect_metrics(router, job_store).to_dict()`; see [metrics.md](metrics.md).

Use quota checks before expensive calls; see [quota_policy.md](quota_policy.md).

```python
check = quota.reserve(provider, model, estimated_tokens=chunk.estimated_tokens)
if check.decision != QuotaDecision.ALLOW:
    jobs.mark_retry_later(job.job_id, retry_after_seconds=check.retry_after_seconds, error_type=check.reason)
```

## Operational snapshot

```python
snapshot = router.export_state()
```

Use the snapshot for health dashboards and capacity decisions. Do not treat it as domain data storage.

## Profile examples

- `long_context`: large documents and context-heavy work.
- `cheap_batch`: high-volume low-cost jobs.
- `structured_json`: extraction tasks that prefer JSON-capable models.
- `low_latency`: user-facing workflows.
- `premium_reasoning`: quality-sensitive analysis/agent work.
- `private_local`: local/private routing.

## Integration checklist

- Keep API keys out of source control.
- Keep app payloads out of router state.
- Use `route_outcome()` for durable jobs.
- Use `aroute_outcome()` for async workers.
- Use SQLite state for multiple local workers.
- Use metadata for job IDs and workload profiles.
