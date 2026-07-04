# Nakazasen AI Router

Nakazasen AI Router là nền móng Python để điều phối nhiều nhà cung cấp AI trong tương lai.

Ở phiên bản hiện tại, dự án **chưa gọi AI thật** và **không chứa API key thật**. Mục tiêu là chuẩn bị cấu trúc sạch để sau này port Provider Router từ `translation_app` sang.

## Trạng thái hiện tại

- API tối thiểu: `AIRouter`, `AIRequest`, `AIResult`, `ProviderBase`, `ProviderCandidate`, `ProviderHealth`, `RouterPolicy`.
- Provider giả lập để kiểm thử fallback, quota, auth, timeout.
- Không gọi mạng, không gọi provider thật.
- Không lưu API key thật.

## Cài đặt phát triển

```bash
python -m pip install -e .[dev]
```

## Chạy kiểm thử

```bash
python -m pytest -q
python -m compileall src
```

## Ví dụ nhanh

```python
from nakazasen_ai_router import AIRouter, AIRequest, RouterPolicy
from nakazasen_ai_router.fake_providers import provider_success

router = AIRouter(
    providers=[provider_success("local-demo", is_cloud=False)],
    policy=RouterPolicy(local_only=True),
)

result = router.route(AIRequest(prompt="Xin chào"))
print(result.text)
```

## Cam kết bảo mật

- Không commit API key thật.
- Log được làm sạch để tránh lộ chuỗi nhạy cảm trong metadata.
- Provider thật sẽ được thêm sau, kèm test riêng.
