# API key nhà cung cấp

Nakazasen AI Router không bao giờ ship API key. Chương trình tích hợp tự cung cấp key qua environment variables, secret manager hoặc cấu hình chỉ tồn tại trong process của chương trình đó.

## Cách tích hợp

```python
import os
from nakazasen_ai_router import AIRequest, create_router_from_env

os.environ["GEMINI_API_KEY"] = load_secret("gemini")
os.environ["DEEPSEEK_API_KEY"] = load_secret("deepseek")
router = create_router_from_env(
    provider_names=("gemini", "deepseek"),
    enable_network=True,
)
result = router.route(AIRequest(prompt="Reply with OK."))
```

Router đọc biến singular/plural từ mapping `env` truyền vào; nếu bỏ qua `env` thì đọc từ `os.environ`. Nhờ vậy chương trình khác có thể truyền mapping riêng mà không thay đổi global process state:

```python
router = create_router_from_env(
    env={"GEMINI_API_KEY": load_secret("gemini")},
    provider_names=("gemini",),
    enable_network=True,
)
```

Các biến được hỗ trợ:

```text
GEMINI_API_KEY=...
GEMINI_API_KEYS=key_one,key_two
DEEPSEEK_API_KEY=...
DEEPSEEK_API_KEYS=key_one;key_two
GROQ_API_KEY=...
OPENROUTER_API_KEY=...
NVIDIA_NIM_API_KEY=...
CHATANYWHERE_API_KEY=...
MISTRAL_API_KEY=...
```

Dạng plural chấp nhận dấu phẩy, chấm phẩy và dòng mới. Raw key không xuất hiện trong route attempts, state store hay dashboard export.

## Chế độ không có key

Không có key vẫn dùng được offline tests, fake providers, segmentation, SQLite jobs, quota policy, metrics và static dashboard. Cloud provider sẽ bị bỏ qua cho đến khi có key. Local OpenAI-compatible provider có thể chạy không cần key khi base URL là local.

## File live-test local

Chỉ trong repo phát triển này, `scripts/live_smoke.py` và `scripts/discover_models.py` mặc định dùng `API Key.txt` ở root repo. `.gitignore` có rule chính xác `/API Key.txt`, do đó file không bị stage bởi lệnh Git thông thường. Không dùng force-add và không copy file vào release.

```powershell
py scripts/live_smoke.py --provider gemini --test-all-models
py scripts/discover_models.py --provider deepseek --only-new
```

Có thể override bằng file ngoài repo:

```powershell
py scripts/live_smoke.py --provider gemini --key-file "D:\path\to\provider_keys.txt"
```

Key file hỗ trợ `KEY=value` hoặc nhãn provider rồi đến value ở dòng tiếp theo. Output live script đã sanitize và không được dùng để in/lưu raw key.

## Quét model lúc khởi động

Cung cấp key và bật cả hai cờ để refresh catalog trong bộ nhớ lúc router khởi động:

```python
router = create_router_from_env(
    provider_names=("gemini", "deepseek"),
    enable_network=True,
    refresh_models_on_startup=True,
)
```

Tính năng là tùy chọn. Gemini được quét qua endpoint model gốc; cloud provider khác được quét qua endpoint OpenAI-compatible `GET /models`. Chat model phát hiện được merge lên trước static defaults trong router instance hiện tại. Nếu quét lỗi, router giữ static defaults và vẫn khởi động.

## Xử lý sự cố

- Thiếu key: set environment variable của provider hoặc truyền `env` mapping riêng.
- Key sai: thay key qua secret manager của ứng dụng hoặc console provider.
- Quota/429: chờ hoặc cấu hình key/provider khác.
- Network disabled: set `enable_network=True` trong SDK code.
- Refresh bị chặn: phải bật đồng thời `enable_network=True` và `refresh_models_on_startup=True`.
