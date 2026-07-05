# Provider quota and capacity policies

Quota primitives help applications avoid calling providers blindly. They are optional, dependency-free, and domain-neutral.

## Python API

```python
from nakazasen_ai_router import CapacityPolicy, InMemoryQuotaTracker, ProviderQuotaProfile, QuotaDecision

quota = InMemoryQuotaTracker([
    ProviderQuotaProfile("gemini", policy=CapacityPolicy(requests_per_minute=10, max_concurrency=2, cost_tier="free"))
])
check = quota.reserve("gemini", estimated_tokens=500)
if check.decision != QuotaDecision.ALLOW:
    retry_later(check.retry_after_seconds, check.reason)
try:
    run_ai_request()
finally:
    quota.release("gemini")
```

## Supported limits

- requests per minute
- tokens per minute
- requests per day
- max concurrency
- enabled/disabled profiles
- fallback priority and cost tier sorting

## Safety

Snapshots do not include raw key IDs, prompts, payloads, authorization headers, or provider responses.

## Limitations

`InMemoryQuotaTracker` is process-local. For multi-process distributed workers, store shared quota state in your application infrastructure or add a future persistent tracker.
