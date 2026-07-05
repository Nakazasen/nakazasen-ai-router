# General-purpose use cases

`nakazasen-ai-router` is a general-purpose AI capacity layer for Python applications. It is not tied to translation, chatbots, agents, or any single domain. The router owns provider/model/key selection, cooldowns, budget checks, retries, outcomes, and safe operational state. Your application owns payload semantics and result storage.

## Use-case map

| Use case | Suggested workload profile | Suggested API | Notes |
| --- | --- | --- | --- |
| Batch translation | `long_context` or `translation_longform` | `route_outcome()` | Translation is one long-context workload, not the only purpose. |
| Document summarization | `summarization` or `long_context` | `route_outcome()` / `aroute_outcome()` | Split large documents in the app layer. |
| JSON extraction | `structured_json` | `route_outcome()` | Validate JSON in the app layer. |
| Content generation | `cheap_batch` or `cheap_generation` | `route_outcome()` | Good for high-volume low-cost generation. |
| Text analysis/classification | `analysis` | `route()` / `route_outcome()` | Use metadata to track app-level job IDs. |
| RAG preprocessing | `cheap_batch` or `summarization` | async route outcomes | Keep document stores outside router state. |
| Support automation | `low_latency` | `aroute()` / `astream()` | Prefer fast providers and streaming UX. |
| Local/private AI | `private_local` or `local_only` | `route()` | Keep network disabled or select local providers only. |
| Agent/tool orchestration | `premium_reasoning` | `route_outcome()` | Route by reasoning quality and retry semantics. |

## Domain boundary

The router should not know whether a payload is a chapter, ticket, log file, contract, support message, source file, or research note. It only sees an `AIRequest` and optional metadata such as:

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

## Recommended integration pattern

1. Store app jobs and payloads in your own database or queue.
2. Use `create_router_from_env()` with JSON or SQLite router state.
3. Call `route_outcome()` for durable workers.
4. Reschedule `retry_later` outcomes in your app queue.
5. Store final results in your app database.
6. Use `export_state()` only for safe operational dashboards.

## Safety principles

- Router state must not contain prompts, raw keys, Authorization headers, or raw provider responses.
- App data stores own domain payloads and outputs.
- Live provider tests are explicit opt-in.
- Offline examples should remain mock-first.
