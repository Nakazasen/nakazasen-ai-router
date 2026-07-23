# Provider quota and capacity policies

Quota primitives help applications avoid calling providers blindly. They are optional, dependency-free, thread-safe, and domain-neutral.

## Shared pool and flexible-window API

```python
from nakazasen_ai_router import (
    CapacityPolicy,
    InMemoryQuotaTracker,
    ProviderQuotaProfile,
    QuotaWindow,
    create_router_from_env,
)

policy = CapacityPolicy(
    requests_per_minute=10,
    tokens_per_minute=20_000,
    max_concurrency=2,
    flexible_windows=(QuotaWindow("daily-allocation", 86_400, request_limit=1_000),),
)
quota = InMemoryQuotaTracker([
    ProviderQuotaProfile("gemini", "model-a", policy=policy, pool_id="gemini-free"),
    ProviderQuotaProfile("gemini", "model-b", policy=policy, pool_id="gemini-free"),
])
router = create_router_from_env(
    provider_names=("gemini",),
    enable_network=True,
    quota_tracker=quota,
)
```

Both models consume one `gemini-free` usage bucket. The router reserves estimated tokens immediately before provider invocation, releases in-flight capacity in `finally`, and reconciles the estimate with normalized provider-reported usage after success.

## Supported limits

- requests and tokens per minute;
- requests per Unix epoch day;
- maximum in-flight requests;
- enabled/disabled profiles;
- named fixed windows with request/token limits;
- shared `pool_id` buckets;
- fallback priority and cost tier sorting;
- headroom scoring for weighted routing;
- estimated-to-actual token reconciliation.

Profile matching precedence is `provider + model + key_id`, then `provider + model`, then provider only.

## Safety

Snapshots report `scope: process_local` and do not include raw key IDs, prompts, payloads, Authorization headers, or provider responses. Router attempts use coarse `quota_block` or `quota_throttle` reasons rather than exposing arbitrary internal window names.

## Limitations

`InMemoryQuotaTracker` coordinates only callers sharing the same tracker object in one Python process. It is not a distributed or multi-process quota backend. Use an external atomic store when deployment topology requires distributed enforcement.

Flexible windows are fixed windows, not rolling/sliding windows. Profiles sharing one `pool_id` must use compatible policies because they evaluate matched policy limits against shared usage.
