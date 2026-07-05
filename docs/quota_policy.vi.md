# Provider quota và capacity policy

Quota primitives giúp ứng dụng tránh gọi provider một cách mù quáng. Chúng là optional, không cần dependency và trung lập domain.

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

## Limit được hỗ trợ

- requests per minute
- tokens per minute
- requests per day
- max concurrency
- bật/tắt profile
- fallback priority và cost tier sorting

## An toàn

Snapshot không chứa raw key ID, prompt, payload, authorization header hoặc provider response.

## Giới hạn

`InMemoryQuotaTracker` chỉ nằm trong một process. Với distributed workers nhiều process, hãy lưu quota state chung trong hạ tầng app hoặc thêm persistent tracker ở phase sau.
