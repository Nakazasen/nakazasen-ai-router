# Provider quota và capacity policy

Quota primitives giúp ứng dụng tránh gọi provider một cách mù quáng. Chúng là optional, không cần dependency, thread-safe và trung lập domain.

## API pool dùng chung và cửa sổ linh hoạt

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

Cả hai model dùng chung một bucket `gemini-free`. Router reserve token ước tính ngay trước khi gọi provider, release in-flight capacity trong `finally`, rồi reconcile ước tính bằng usage đã chuẩn hóa do provider trả về sau khi thành công.

## Limit được hỗ trợ

- request và token mỗi phút;
- request mỗi ngày theo Unix epoch;
- số request in-flight tối đa;
- bật/tắt profile;
- cửa sổ cố định có tên với limit request/token;
- bucket dùng chung qua `pool_id`;
- fallback priority và cost tier sorting;
- headroom scoring cho weighted routing;
- reconcile token ước tính thành token thực tế.

Thứ tự match profile là `provider + model + key_id`, sau đó `provider + model`, rồi chỉ provider.

## An toàn

Snapshot báo `scope: process_local` và không chứa raw key ID, prompt, payload, Authorization header hoặc provider response. Attempt của router chỉ dùng reason thô `quota_block` hoặc `quota_throttle`, không làm lộ tên window nội bộ tùy ý.

## Giới hạn

`InMemoryQuotaTracker` chỉ điều phối caller dùng chung tracker object trong một Python process. Đây không phải quota backend distributed hay multi-process. Hãy dùng external atomic store khi topology triển khai cần enforcement phân tán.

Flexible window là fixed window, không phải rolling/sliding window. Các profile dùng chung một `pool_id` phải có policy tương thích vì chúng đánh giá limit của policy đã match trên usage dùng chung.
