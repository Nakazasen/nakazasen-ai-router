# Nakazasen AI Router

## Provider keys and updates

See [docs/provider_keys.md](docs/provider_keys.md) for API key setup, [examples/key_setup_static/index.html](examples/key_setup_static/index.html) for a local-only key file helper, and [docs/install_update.md](docs/install_update.md) for update/uninstall commands.

## Path hygiene

See [docs/path_hygiene.md](docs/path_hygiene.md) for the local path/key-file guard used to keep the repository portable.

## Stable install

```powershell
pip install git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.2.2
```

Release notes: [0.2.2.md](docs/releases/0.2.2.md)


Vietnamese documentation: [README.vi.md](README.vi.md)

Nakazasen AI Router is a general-purpose AI capacity layer for Python applications. It routes AI requests across local and cloud providers, manages provider/model/key health, and gives other repositories durable access to AI capacity without tying the core to any single domain.

The default development and test path is mock-first, offline, and safe: unit tests do not call the internet and do not require real API keys.

## What it does

- Routes requests across OpenAI-compatible providers.
- Falls back across providers, models, and API keys when a candidate fails.
- Tracks provider/model/key health and cooldowns.
- Supports durable `route_outcome()` results for job queues.
- Supports JSON or SQLite state storage.
- Provides sync and async routing APIs.
- Supports workload/capability based candidate scoring.
- Provides budget guard and exponential retry backoff.
- Provides a streaming API foundation with safe fallback.
- Includes offline examples for summarization, JSON extraction, content generation, and translation as one long-context use case.

## Supported providers

The provider registry currently includes:

- Gemini
- OpenRouter
- Groq
- DeepSeek
- NVIDIA NIM
- ChatAnyWhere
- Mistral
- Local OpenAI-compatible server

## Install for local development

```powershell
py -m pip install -e .
py -m pytest -q
```

Optional native async network transport:

```powershell
py -m pip install -e .[async]
```

Developer tools, including package build support:

```powershell
py -m pip install -e .[dev]
```

## Quickstart

```python
from nakazasen_ai_router import AIRequest, create_router_from_env

router = create_router_from_env(provider_names=("gemini",), enable_network=True)
result = router.route(AIRequest(prompt="Reply with OK."))
print(result.text)
```

Network access is explicit opt-in. Tests and examples are offline by default unless stated otherwise.

## Multi-key token pool

Router factories support singular and plural environment variables. Plural variables are loaded first; singular variables are merged if not duplicated.

```text
GEMINI_API_KEYS=<gemini_key_1>,<gemini_key_2>,<gemini_key_3>
OPENROUTER_API_KEYS=<openrouter_key_1>,<openrouter_key_2>
GROQ_API_KEYS=<groq_key_1>,<groq_key_2>

# Backward-compatible single-key variable also exists:
# GEMINI_API_KEY
```

When one `provider + model + key_id` hits quota/rate limit, the router cools down that candidate so another key for the same provider can still be tried.

## Durable job queue API

`route()` returns `AIResult` or raises `RouterError`.

For long-running workers, prefer `route_outcome()` because it returns a non-throwing operational status:

```python
from nakazasen_ai_router import AIRequest, RouterPolicy, create_router_from_env

router = create_router_from_env(
    enable_network=True,
    state_path="router_state.json",
    policy=RouterPolicy(max_attempts=3),
)

outcome = router.route_outcome(AIRequest(prompt="Translate this chapter..."))

if outcome.status == "success":
    save_result(outcome.result.text)
elif outcome.status == "retry_later":
    reschedule_job(outcome.retry_after_seconds)
else:
    mark_failed(outcome.error_type)
```

## Dashboard/admin state export

Use `export_state()` for a JSON-safe dashboard snapshot:

```python
snapshot = router.export_state()
print(snapshot["summary"])
```

The snapshot contains only operational metadata such as provider, model, masked key ID, status, error type, counts, latency, and cooldowns. It must not contain prompts, raw keys, Authorization headers, or raw provider responses.

## Async API

Async APIs are additive and keep sync APIs stable:

```python
outcome = await router.aroute_outcome(AIRequest(prompt="Translate this chapter..."))
result = await router.aroute(AIRequest(prompt="Summarize this text..."))
```

Providers can implement native `agenerate()`. Providers without native async support fall back through a worker thread. Native async HTTP transport is optional via `nakazasen-ai-router[async]`.

```python
router = create_router_from_env(
    enable_network=True,
    enable_async_network=True,
)
```

## SQLite state store

Use SQLite for multiple local workers/processes sharing the same filesystem:

```python
router = create_router_from_env(
    enable_network=True,
    state_path="router_state.sqlite3",
    state_backend="sqlite",
    policy=RouterPolicy(max_attempts=3),
)
```

SQLite stores the current state for each `provider + model + key_id`; it does not store prompt text or raw provider responses.

## Task/capability routing

The router includes a model capability catalog. `RouterPolicy.task_type` and request metadata `task_type` let callers express workload intent.

```python
from nakazasen_ai_router import AIRequest, AIRouter, RouterPolicy

router = AIRouter(providers, policy=RouterPolicy(task_type="translation_longform"))
result = router.route(AIRequest(prompt="Translate chapter 12..."))
```

Per-request override:

```python
request = AIRequest(
    prompt="Write a short blurb",
    metadata={"task_type": "cheap_generation"},
)
```

Initial task types include `translation_longform`, `summarization`, `cheap_generation`, `analysis`, `premium_quality`, `local_only`, and `json_structured`.

## Budget guard and retry backoff

The router can reject over-budget jobs before any provider call when the application supplies token estimates:

```python
from nakazasen_ai_router import AIRequest, RouterPolicy, create_router_from_env

router = create_router_from_env(
    policy=RouterPolicy(
        max_estimated_input_tokens=120_000,
        max_estimated_output_tokens=8_000,
    ),
)

outcome = router.route_outcome(
    AIRequest(
        prompt="Translate long chapter...",
        metadata={
            "estimated_input_tokens": 130_000,
            "estimated_output_tokens": 4_000,
        },
    )
)

assert outcome.status == "failed"
assert outcome.error_type == "budget_exceeded"
```

Transient/quota cooldowns use exponential backoff based on failure streaks. Provider `Retry-After` values are treated as minimum cooldowns.

```python
RouterPolicy(
    backoff_base_seconds=15,
    backoff_max_seconds=3600,
    backoff_jitter_ratio=0.2,
)
```

## Streaming foundation

`stream()` and `astream()` provide streaming-compatible APIs. If the provider does not support native streaming yet, the router falls back to one chunk containing the full result.

```python
for chunk in router.stream(AIRequest(prompt="Translate chapter...")):
    print(chunk.text, chunk.done)
```

```python
async for chunk in router.astream(AIRequest(prompt="Translate chapter...")):
    print(chunk.text, chunk.done)
```

Providers may implement `stream_generate` or `astream_generate` to provide native streaming chunks.

## Offline examples

Examples are mock-first and run without network or API keys:

```powershell
py examples/summarization_batch_demo.py --base-dir .demo_summarization
py examples/json_extraction_demo.py --base-dir .demo_json_extraction
py examples/content_generation_demo.py --base-dir .demo_content_generation
py examples/translation_worker_demo.py --offline-demo
```

Translation is intentionally only one example of a long-context workload. See [docs/use_cases.md](docs/use_cases.md), [docs/integration_generic_worker.md](docs/integration_generic_worker.md), and [docs/integration_translation_worker.md](docs/integration_translation_worker.md).

## Gemini model discovery and live smoke tests

Live provider checks are opt-in. Keep key files outside the repository.

```powershell
py scripts/live_smoke.py --provider gemini --key-file "D:\path\to\provider_keys.txt" --model gemini-3.5-flash
py scripts/live_smoke.py --provider gemini --key-file "D:\path\to\provider_keys.txt" --test-all-models
```

Discovery lists provider models but does not enable them automatically:

```powershell
py scripts/discover_models.py --provider gemini --key-file "D:\path\to\provider_keys.txt"
py scripts/discover_models.py --provider gemini --key-file "D:\path\to\provider_keys.txt" --validate-live --only-new
```

A discovered model must pass live validation and be manually reviewed before being added to the runtime catalog.

## Static local dashboard

Open [examples/dashboard_static/index.html](examples/dashboard_static/index.html) or read [docs/dashboard_static.md](docs/dashboard_static.md) for a no-server dashboard that renders router/job/quota metrics JSON.

## SDK-first integration

Use [docs/sdk_integration.md](docs/sdk_integration.md) and [docs/integration_blueprints.md](docs/integration_blueprints.md) to embed this package directly into other Python repos without a Router Server.

## Quota and capacity policies

Use [docs/quota_policy.md](docs/quota_policy.md) for optional provider/model/key capacity limits, fallback sorting, and in-memory throttling.

## Metrics snapshots

Use [docs/metrics.md](docs/metrics.md) and `scripts/router_metrics.py` for sanitized router/job queue observability JSON.

## Persistent job queue

Use [docs/job_queue.md](docs/job_queue.md) for the optional SQLite queue adapter that supports enqueue, claim, lease, retry, success, and failure without storing raw payloads.

## Segmentation primitives

Use [docs/segmentation.md](docs/segmentation.md) for domain-neutral chunking/merge helpers before `route_outcome()`.

## Live provider conformance

See [docs/live_conformance.md](docs/live_conformance.md) for opt-in sanitized live provider checks.

## Public API contract

See [docs/public_api.md](docs/public_api.md) for root exports, compatibility notes, and safety guarantees.

## Security and privacy principles

- Never commit API keys.
- Never copy external key files into this repository.
- Never print API keys or Authorization headers.
- Do not store raw prompts, raw provider responses, raw evidence, or confidential documents in traces, state stores, or health caches.
- Network/live provider calls are explicit opt-in.
- Unit tests are offline by default.
