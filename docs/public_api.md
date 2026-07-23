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

### Capability, usage, and accounting helpers

- `ModelCapability`
- `TokenUsage`
- `CostEstimate`
- `capability_for`
- `score_candidate_for_task`
- `normalize_token_usage`
- `estimate_cost`

### Weighted routing

- `RoutingMode`
- `ScoreWeights`
- `RoutingScore`
- `MODE_WEIGHTS`
- `weights_for_mode`
- `score_routing_candidate`

### Quota and capacity

- `QuotaDecision`
- `QuotaWindow`
- `CapacityPolicy`
- `ProviderQuotaProfile`
- `QuotaCheck`
- `UsageSnapshot`
- `InMemoryQuotaTracker`
- `sort_profiles_for_fallback`

### Audited free-tier capacity

- `FreeTierPlan`
- `FreeTierBudget`
- `FreeTierCatalog`
- `DEFAULT_FREE_TIER_CATALOG`
- `calculate_free_tier_budget`

### Safe release awareness

- `UpdateInfo`
- `installed_version`
- `check_for_updates`
- `clear_update_cache`

## Host-application keys and startup catalog refresh

A host application supplies provider keys through its own secret manager, environment, or private `env` mapping. The key is never supplied by this package:

```python
router = create_router_from_env(
    env={"GEMINI_API_KEY": host_secret_manager.read("gemini")},
    provider_names=("gemini",),
    enable_network=True,
)
```

To query the provider model catalog when the router starts, opt into both networking and refresh:

```python
router = create_router_from_env(
    provider_names=("gemini", "deepseek"),
    enable_network=True,
    refresh_models_on_startup=True,
)
```

Discovery is process-local and non-blocking: discovered chat models are placed before static defaults only for this router instance; a discovery failure preserves static defaults.

## Routing, quota, and accounting semantics

`RouterPolicy.routing_mode` accepts `balanced`, `fast`, `cheap`, `quality`, or `quota`; callers can override built-in weights with `ScoreWeights`. Successful results include a sanitized score breakdown in `metadata["routing"]`.

`InMemoryQuotaTracker` supports shared `pool_id` buckets and named fixed windows. It is thread-safe but process-local, not a distributed quota backend. Profiles sharing a pool should use compatible policies.

Provider-reported usage is normalized to `TokenUsage`. Cost is marked `estimated` only when verified input/output prices and usage splits are available; otherwise its status is `unknown`. Cost estimates are operational guidance, not billing truth.

`FreeTierCatalog.budget()` counts fresh fixed recurring allowances once per shared pool and separates one-time or uncountable plans. `AIRouter.free_tier_budget()` adds only process-local observed usage and labels it `estimated_local`. Provider dashboards remain authoritative.

`check_for_updates()` is network-disabled by default and returns status data instead of raising on check failure. The explicit CLI apply path is intentionally outside request routing and uses a confirmed current-interpreter pip command.

## Compatibility promise

Until 1.0, public root exports may still evolve, but changes should be documented in the changelog. Internal modules may change without compatibility guarantees.

Prefer root imports for application code. Importing deep internal helpers is allowed for advanced users, but those helpers are less stable.

## Safety contract

Public attempts, route outcomes, state stores, quota snapshots, accounting metadata, and dashboard exports must not include:

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
