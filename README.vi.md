# Nakazasen AI Router

## API key và cập nhật

Xem [docs/provider_keys.vi.md](docs/provider_keys.vi.md) để cấu hình API key, [examples/key_setup_static/index.html](examples/key_setup_static/index.html) cho helper local-only tạo key file, và [docs/install_update.vi.md](docs/install_update.vi.md) cho lệnh cập nhật/gỡ cài đặt.

## Cài bản stable

```powershell
pip install git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.4.0
```

Ghi chú phát hành: [0.4.0.md](docs/releases/0.4.0.md)

Nakazasen AI Router là lớp cung cấp năng lực AI đa nhiệm cho ứng dụng Python. Thư viện định tuyến request qua provider local/cloud, quản lý trạng thái provider/model/key và cho phép repo khác tích hợp AI mà không gắn core với một domain riêng. Dịch chương chỉ là một ví dụ về workload tổng quát.

Mặc định dự án theo hướng mock-first: unit test không gọi mạng và không cần API key thật.

## Khả năng chính

- Điều phối giữa các provider tương thích OpenAI.
- Fallback giữa provider, model và API key khi có lỗi.
- Theo dõi health/cooldown theo provider + model + key.
- Hỗ trợ `route_outcome()` cho job queue bền vững.
- Hỗ trợ state JSON hoặc SQLite và API sync/async.
- Định tuyến có trọng số, giải thích được với các mode cân bằng, nhanh, rẻ, chất lượng và bảo toàn quota.
- Hỗ trợ pool quota dùng chung và cửa sổ cố định linh hoạt, thread-safe trong một process.
- Chuẩn hóa token usage, ghi nguồn catalog và ước tính chi phí thận trọng.
- Catalog free-tier có nguồn kiểm chứng, chống đếm trùng shared pool và ưu tiên free-first ở mode `cheap`/`quota`.
- Kiểm tra phiên bản theo opt-in và cập nhật tường minh có xác nhận; import/routing không bao giờ tự update.
- Hỗ trợ quét catalog model mới lúc khởi động theo cơ chế opt-in.

## Nhận biết phiên bản và kiểm toán free-tier

Chương trình đã cài sẽ giữ nguyên phiên bản cho đến khi chủ ứng dụng chủ động nâng cấp. Các lệnh:

```powershell
nakazasen-ai-router version
nakazasen-ai-router update --check
nakazasen-ai-router update --apply
nakazasen-ai-router free-tiers --json
```

`update --apply` hiển thị trước chính xác lệnh `sys.executable -m pip` và hỏi xác nhận. Chỉ dùng `--yes` trong môi trường tự động hóa đã được kiểm soát. SDK không gọi mạng để kiểm tra version theo mặc định và không tự sửa môi trường khi import, tạo router hay xử lý request.

Báo cáo free-tier chỉ cộng quota định kỳ dạng số, có nguồn, còn mới và đã loại đếm trùng shared pool. Credit một lần và gói unlimited/dynamic nằm ở nhóm riêng. Catalog tích hợp hiện báo **0 token định kỳ/tháng đã kiểm toán**, vì các provider đang công bố giới hạn động chứ không phải grant token cố định theo tháng có thể tái lập. Vì vậy Nakazasen không tuyên bố con số `1.53B` của OmniRoute.

## Provider hiện hỗ trợ

Gemini, OpenRouter, Groq, DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral và local OpenAI-compatible server.

## Cài đặt cho phát triển

```powershell
py -m pip install -e .[dev]
py -m pytest -q
```

Cài native async transport khi cần:

```powershell
py -m pip install -e .[async]
```

## Tích hợp từ chương trình khác

**Có.** Chương trình tích hợp tự truyền API key qua environment variables hoặc secret manager của chính chương trình đó, sau đó bật mạng tường minh. Không nhúng key vào source code.

```python
import os
from nakazasen_ai_router import AIRequest, create_router_from_env

os.environ["GEMINI_API_KEY"] = load_secret_from_your_secret_manager()
router = create_router_from_env(
    provider_names=("gemini", "deepseek"),
    enable_network=True,
)
result = router.route(AIRequest(prompt="Reply with OK."))
print(result.text)
```

Dùng `GEMINI_API_KEYS` hoặc `DEEPSEEK_API_KEYS` để truyền pool nhiều key, phân cách bằng dấu phẩy, chấm phẩy hoặc dòng mới. Router tự fallback giữa key/model nhưng không đưa raw key vào attempt metadata hay state bền vững.

## Tự động quét model mới khi khởi động

Model tĩnh trong registry luôn là fallback an toàn. Ứng dụng tích hợp chỉ bật quét catalog khi chủ động cho phép kết nối mạng:

```python
router = create_router_from_env(
    provider_names=("gemini", "deepseek", "groq"),
    enable_network=True,
    refresh_models_on_startup=True,
)
```

Khi khởi động, Gemini được quét qua endpoint catalog gốc; các provider cloud khác được quét qua endpoint OpenAI-compatible `GET /models`. Model chat mới quét được sẽ được merge đứng trước danh sách fallback **chỉ trong router instance đang chạy**. Nếu endpoint không hỗ trợ, response lỗi hoặc sai định dạng, router vẫn khởi động và dùng danh sách model tĩnh. Tính năng tắt mặc định và sẽ báo `ValueError` nếu bật `refresh_models_on_startup=True` nhưng không bật `enable_network=True`.

## Live test local

Trong repo này, `scripts/live_smoke.py` và `scripts/discover_models.py` mặc định dùng file local `API Key.txt`. File này được Git ignore bằng `/API Key.txt`, không được commit/push. Script chỉ đọc file khi bạn chạy lệnh live rõ ràng và output đã được sanitize.

```powershell
# Mặc định dùng API Key.txt đã ignore.
py scripts/live_smoke.py --provider gemini --test-all-models

# Hoặc dùng một file key local khác.
py scripts/discover_models.py --provider deepseek --key-file "D:\path\to\provider_keys.txt" --only-new
```

File key hỗ trợ dạng nhãn rồi đến value hoặc `KEY=value`. Xem [docs/provider_keys.vi.md](docs/provider_keys.vi.md) để biết hướng dẫn tích hợp và quản lý bí mật.

## Kiến trúc và vận hành release

- Bản bàn giao hệ thống cho người/AI, bản đồ thư mục và sơ đồ Mermaid: [ARCHITECTURE.md](ARCHITECTURE.md)
- Quy trình chuẩn đóng gói, quản lý phiên bản và phát hành: [docs/releasing.vi.md](docs/releasing.vi.md)
- Contract SDK public: [docs/public_api.md](docs/public_api.md)

## Nguyên tắc bảo mật

- Không commit API key, bao gồm `API Key.txt`.
- Không in API key hoặc Authorization header.
- Ứng dụng tích hợp giữ key trong environment variables hoặc secret manager.
- Gọi provider live, kiểm tra/cài update và quét model lúc khởi động đều là opt-in.
- Unit test mặc định offline.
