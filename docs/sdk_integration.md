# SDK-first integration

Use `nakazasen-ai-router` as an embedded Python SDK when you do not want a central Router Server.

## Install

From a local wheel:

```powershell
py -m pip install dist\nakazasen_ai_router-0.2.0-py3-none-any.whl
```

From GitHub:

```powershell
py -m pip install git+https://github.com/Nakazasen/nakazasen-ai-router.git
```

## Minimal route

```python
from nakazasen_ai_router import AIRequest, create_router_from_env

router = create_router_from_env(provider_names=("gemini", "groq"), enable_network=True)
outcome = router.route_outcome(AIRequest(prompt="Summarize this", metadata={"task_type": "summarization"}))
```

## Full worker stack

Use these pieces together for durable AI workloads:

- `segment_text()` for long payloads.
- `SQLiteJobStore` for durable jobs.
- `InMemoryQuotaTracker` for process-local capacity checks.
- `AIRouter.route_outcome()` for safe routing.
- `collect_metrics()` for observability.

See `examples/sdk_worker_stack_demo.py`.

## Hygiene

Do not commit API keys, live reports, production SQLite state, or raw prompts in job metadata.
