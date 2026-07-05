# Public API Contract

`nakazasen-ai-router` is still pre-1.0, but applications should import stable integration surfaces from the package root:

```python
from nakazasen_ai_router import AIRouter, AIRequest, RouterPolicy, create_router_from_env
```

## Public root exports

### Request/result types

- `AIRequest`
- `AIResult`
- `AIStreamChunk`
- `AIRouteOutcome`
- `AttemptRecord`

### Router and policy

- `AIRouter`
- `RouterPolicy`

### Errors

- `RouterError`
- `ProviderError`
- `ProviderAuthError`
- `ProviderQuotaError`
- `ProviderTimeoutError`

### Provider extension points

- `ProviderBase`
- `ProviderCandidate`
- `ProviderHealth`

### State stores

- `MemoryStateStore`
- `JsonStateStore`
- `SQLiteStateStore`
- `KeyModelState`

### Factories

- `create_router_from_env`
- `create_live_free_first_router_from_env`

### Capability helpers

- `ModelCapability`
- `capability_for`
- `score_candidate_for_task`

## Compatibility promise

Until 1.0, public root exports may still evolve, but changes should be documented in the changelog. Internal modules may change without compatibility guarantees.

Prefer root imports for application code. Importing deep internal helpers is allowed for advanced users, but those helpers are less stable.

## Safety contract

Public attempts, route outcomes, state stores, and dashboard exports must not include:

- raw API keys
- Authorization headers
- raw provider responses
- prompts stored in state

`export_state()` and state stores are for operational metadata only.

## Minimal examples

### Sync route

```python
router = create_router_from_env(enable_network=True)
result = router.route(AIRequest(prompt="Say hello"))
```

### Durable route outcome

```python
outcome = router.route_outcome(AIRequest(prompt="Translate chapter..."))
if outcome.status == "retry_later":
    save_job_for_later(outcome.retry_after_seconds)
```

### SQLite state

```python
router = create_router_from_env(
    state_path="router_state.sqlite3",
    state_backend="sqlite",
)
```

### Async route

```python
outcome = await router.aroute_outcome(AIRequest(prompt="Translate chapter..."))
```

### Streaming fallback

```python
for chunk in router.stream(AIRequest(prompt="Translate chapter...")):
    handle_text(chunk.text)
```
