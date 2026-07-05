# Integration recipe: long-running chapter translation worker

This guide shows how to embed `nakazasen-ai-router` into a separate application that translates many chapters over a long period of time.

## Recommended architecture

Keep two layers separate:

1. **Your application job store**
   - Owns chapter IDs, source text, output text, status, retries, and user/project metadata.
   - Can be SQLite, Postgres, Redis, a queue system, or files.

2. **Nakazasen AI Router state store**
   - Owns provider/model/key operational health.
   - Tracks cooldowns, failures, latency, and safe status metadata.
   - Must not store prompts, raw API keys, Authorization headers, or raw provider responses.

```text
Chapter queue -> Worker -> AIRouter.route_outcome()
                        -> Provider/model/key pool
                        -> Router SQLite state
                        -> App saves translated chapter
```

## Install

```powershell
pip install nakazasen-ai-router
```

For native async network transport:

```powershell
pip install nakazasen-ai-router[async]
```

## Environment variables

Use plural variables for key pools:

```text
GEMINI_API_KEYS=<key_1>,<key_2>,<key_3>
OPENROUTER_API_KEYS=<key_1>,<key_2>
```

Keep real key files and environment configuration outside the repository.

## Sync worker skeleton

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
    # Replace with your tokenizer if available.
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
        job.mark_needs_split("chapter is too large for configured budget")
        return

    job.mark_failed(outcome.error_type or "route_failed")
```

## Async worker skeleton

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

`stream()` and `astream()` work even before a provider supports native streaming. The fallback yields one full-result chunk.

```python
for chunk in router.stream(AIRequest(prompt=source_text, metadata={"task_type": "translation_longform"})):
    ui.append_text(chunk.text)
```

## Admin dashboard snapshot

```python
snapshot = router.export_state()
print(snapshot["summary"])
```

Use this for operational dashboards: healthy/cooldown/dead counts, retry time, last error type, and latency. Do not treat it as an audit log.

## Chapter splitting policy

For production translation, split chapters before routing when:

- estimated input tokens exceed the router budget,
- estimated output tokens are too high,
- the model returns token/context errors,
- the chapter contains large tables or embedded metadata.

A practical flow:

1. Estimate tokens.
2. If over budget, split by scene/paragraph.
3. Translate chunks independently.
4. Merge outputs in original order.
5. Save the full chapter result in your application store.

## Failure handling

| Outcome | Meaning | Recommended action |
| --- | --- | --- |
| `success` | Translation completed | Save output and mark done |
| `retry_later` | Providers are cooling down or temporarily unavailable | Reschedule job |
| `failed` + `budget_exceeded` | Job is too large for configured budget | Split chapter or raise budget |
| `failed` + `route_failed` | Non-retryable routing failure | Inspect attempts and mark failed |

## Offline demo

Run the built-in offline demo:

```powershell
py examples/translation_worker_demo.py --offline-demo
```

It creates sample chapters, processes them with a fake provider, writes outputs, and exports a safe summary.

## Safety checklist

- Keep API keys outside source control.
- Do not store prompts in router state.
- Store chapter input/output in your application database, not in router state.
- Use `route_outcome()` for durable workers.
- Use SQLite state for multiple local workers.
- Monitor `export_state()` for cooldown and dead candidates.
