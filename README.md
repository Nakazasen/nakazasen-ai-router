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

## Dùng trong repo khác

Bạn có thể tạo router nhanh từ biến môi trường, không cần lưu API key trong code.

Ví dụ PowerShell:

```powershell
$env:OPENROUTER_API_KEY = "sk-..."
```

Ví dụ Python:

```python
from nakazasen_ai_router import AIRequest, create_router_from_env

router = create_router_from_env()
result = router.route(AIRequest(prompt="Xin chào"))
print(result.text)
```

Các biến môi trường đang hỗ trợ:

| Provider | Biến API key | Ghi chú |
|---|---|---|
| OpenRouter | `OPENROUTER_API_KEY` | Cloud OpenAI-compatible |
| Groq | `GROQ_API_KEY` | Cloud OpenAI-compatible |
| DeepSeek | `DEEPSEEK_API_KEY` | Cloud OpenAI-compatible |
| NVIDIA NIM | `NVIDIA_NIM_API_KEY` | Cloud OpenAI-compatible |
| ChatAnyWhere | `CHATANYWHERE_API_KEY` | Cloud OpenAI-compatible |
| Mistral | `MISTRAL_API_KEY` | Cloud OpenAI-compatible |
| Local server | `LOCAL_OPENAI_COMPATIBLE_BASE_URL` | Localhost có thể không cần key |

Trong test mặc định, dự án vẫn không gọi internet. App bên ngoài nên truyền `http_client` thật khi muốn gọi provider thật.
