# Nakazasen AI Router

Nakazasen AI Router là một lớp cung cấp năng lực AI đa nhiệm cho ứng dụng Python. Nó điều phối request AI qua nhiều provider local/cloud, quản lý sức khỏe provider/model/key và giúp repo khác dùng AI bền vững mà không buộc core vào một domain cụ thể.
Thư viện được thiết kế theo triết lý giả lập trước (mock-first) để các hoạt động kiểm thử (test) mặc định không cần kết nối mạng và không yêu cầu mã khóa dịch vụ (API key) thật.

## Dùng để làm gì?

Thư viện này giúp các ứng dụng Python khác:
1. Tự động chọn nhà cung cấp AI và mô hình phù hợp dựa trên chính sách điều phối.
2. Tự động chuyển hướng dự phòng (fallback) sang nhà cung cấp hoặc mô hình khác nếu nhà cung cấp chính gặp lỗi hoặc hết hạn ngạch (quota).
3. Theo dõi trạng thái hoạt động (sức khỏe) của các nhà cung cấp nhằm tối ưu hóa lựa chọn cuộc gọi tiếp theo.
4. Giới hạn truy cập mạng của các cuộc gọi AI theo chính sách bảo mật thông tin.

## Hiện hỗ trợ nhà cung cấp nào?

Mặc định, bộ đăng ký cấu hình (registry) của thư viện hỗ trợ các nhà cung cấp tương thích giao thức OpenAI (OpenAI-compatible):
- **Gemini** (Google AI Studio)
- **OpenRouter**
- **Groq**
- **DeepSeek**
- **NVIDIA NIM**
- **ChatAnyWhere**
- **Mistral**
- **Server cục bộ** (Local server tương thích OpenAI)

## Các mô hình Gemini đang bật mặc định

Danh mục mô hình Gemini hoạt động chính thức (được bật mặc định trong cấu hình):
- `gemini-3.5-flash` (Được xếp đầu tiên vì có hiệu năng ổn định và đã vượt qua bài kiểm tra thực tế)
- `gemini-flash-latest` (Tên bí danh động - alias - tiện lợi để luôn trỏ tới bản Flash mới nhất)
- `gemini-flash-lite-latest`
- `gemini-3.1-flash-lite`
- `gemini-3.1-flash-lite-preview`
- `gemini-2.5-flash`
- `gemini-2.5-flash-lite`
- `gemini-3-flash-preview`
- `gemini-robotics-er-1.6-preview`
- `gemma-4-31b-it` (Được xếp cuối cùng do mô hình nặng hơn và đôi khi gặp lỗi tạm thời từ nhà cung cấp)

## Cách cài đặt nội bộ

Cài đặt thư viện ở chế độ chỉnh sửa (development mode):
```bash
py -m pip install -e .
```

## Cách chạy kiểm thử (Unit Test)

Chạy bộ kiểm thử mặc định (hoàn toàn không gọi mạng, không cần API key):
```bash
py -m pytest -q
```

## Cách chạy kiểm tra thực tế (Live Smoke Test)

Để kiểm tra kết nối tới nhà cung cấp thật bằng khóa dịch vụ thật, bạn phải lưu khóa dịch vụ trong một tệp tin nằm **ngoài thư mục dự án này** để tránh rò rỉ mã khóa.

```bash
# Kiểm thử một mô hình cụ thể
py scripts/live_smoke.py --provider gemini --key-file "D:\duong_dan_ngoai\provider_keys.txt" --model gemini-3.5-flash

# Kiểm thử toàn bộ mô hình trong danh mục mặc định của nhà cung cấp
py scripts/live_smoke.py --provider gemini --key-file "D:\duong_dan_ngoai\provider_keys.txt" --test-all-models
```

Kết quả in ra sẽ được lược bỏ thông tin nhạy cảm (sanitized), chỉ hiển thị tên nhà cung cấp, mô hình, trạng thái ĐẠT/LỖI (PASS/FAIL) và độ dài phản hồi.

## Cấu hình nhiều API key cho cùng provider

Router hỗ trợ biến môi trường dạng singular và plural. Dạng plural được đọc trước, sau đó merge thêm singular nếu chưa trùng:

```text
GEMINI_API_KEYS -> <gemini_key_1>,<gemini_key_2>,<gemini_key_3>
OPENROUTER_API_KEYS -> <openrouter_key_1>,<openrouter_key_2>
GROQ_API_KEYS -> <groq_key_1>,<groq_key_2>,<groq_key_3>

# Vẫn tương thích cấu hình cũ
GEMINI_API_KEY -> <single_gemini_key>
```

Khi một key/model gặp lỗi quota hoặc rate limit, router ghi cooldown theo candidate `provider + model + key_id` để có thể thử key khác cùng provider thay vì chặn toàn bộ provider ngay.

## Task based routing và capability catalog

Router có catalog năng lực model để chọn provider/model phù hợp hơn với từng loại tác vụ. Ví dụ, tác vụ dịch chương dài ưu tiên context dài và chất lượng ổn định; tác vụ sinh rẻ ưu tiên free/cheap model.

```python
from nakazasen_ai_router import AIRequest, AIRouter, RouterPolicy

router = AIRouter(providers, policy=RouterPolicy(task_type="translation_longform"))
result = router.route(AIRequest(prompt="Translate chapter 12..."))
```

Request có thể override task của policy:

```python
request = AIRequest(
    prompt="Write a short blurb",
    metadata={"task_type": "cheap_generation"},
)
```

Các task type ban đầu gồm `translation_longform`, `summarization`, `cheap_generation`, `analysis`, `premium_quality`, `local_only`, và `json_structured`. Catalog là heuristic an toàn: nếu thiếu metadata cho model lạ, router fallback về điểm mặc định thay vì fail.

## Budget guard và backoff nâng cao

Router có thể chặn job quá lớn trước khi gọi provider, dựa trên token estimate do app truyền vào:

```python
router = create_router_from_env(
    policy=RouterPolicy(
        max_estimated_input_tokens=120_000,
        max_estimated_output_tokens=8_000,
    ),
)

outcome = router.route_outcome(
    AIRequest(
        prompt="Translate long chapter...",
        metadata={
            "estimated_input_tokens": 130_000,
            "estimated_output_tokens": 4_000,
        },
    )
)

assert outcome.status == "failed"
assert outcome.error_type == "budget_exceeded"
```

Retry/cooldown cũng dùng exponential backoff theo failure streak, có giới hạn trần và jitter cấu hình được:

```python
RouterPolicy(
    backoff_base_seconds=15,
    backoff_max_seconds=3600,
    backoff_jitter_ratio=0.2,
)
```

Nếu provider trả `Retry-After`, router tôn trọng giá trị đó như mức tối thiểu.

## Streaming foundation và demo worker

Router có API streaming nền tảng. Nếu provider chưa hỗ trợ streaming thật, router fallback thành một chunk chứa full result:

```python
for chunk in router.stream(AIRequest(prompt="Translate chapter...")):
    print(chunk.text, chunk.done)
```

Async cũng có fallback tương tự:

```python
async for chunk in router.astream(AIRequest(prompt="Translate chapter...")):
    print(chunk.text, chunk.done)
```

Repo có nhiều demo offline/mock-first cho nhiều domain. Dịch chương chỉ là một ví dụ workload context dài:

```powershell
py examples/summarization_batch_demo.py --base-dir .demo_summarization
py examples/json_extraction_demo.py --base-dir .demo_json_extraction
py examples/content_generation_demo.py --base-dir .demo_content_generation
py examples/translation_worker_demo.py --offline-demo
```

Các demo không gọi API live và không cần API key thật. Xem thêm `docs/use_cases.vi.md`, `docs/integration_generic_worker.vi.md` và `docs/integration_translation_worker.vi.md`.

## API nhúng cho job queue bền vững

`route()` vẫn là API cũ: thành công thì trả `AIResult`, thất bại thì raise `RouterError`.

Với worker dịch chương dài, nên dùng `route_outcome()` để nhận trạng thái không-throwing:

```python
from nakazasen_ai_router import AIRequest, RouterPolicy, create_router_from_env

router = create_router_from_env(
    enable_network=True,
    state_path="router_state.json",
    policy=RouterPolicy(max_attempts=3),
)

outcome = router.route_outcome(AIRequest(prompt="Translate this chapter..."))

if outcome.status == "success":
    print(outcome.result.text)
elif outcome.status == "retry_later":
    # App bên ngoài nên lưu job và thử lại sau outcome.retry_after_seconds
    print("Retry later:", outcome.retry_after_seconds)
else:
    print("Failed:", outcome.error_type)
```

State JSON chỉ lưu metadata vận hành an toàn: provider, model, key_id đã mask, loại lỗi, số lần thành công/thất bại và cooldown. Nó không lưu prompt, raw API key, header xác thực hay response thô.

### Dashboard/admin state export

App ngoài có thể gọi `export_state()` để lấy JSON-safe snapshot cho dashboard:

```python
snapshot = router.export_state()
print(snapshot["summary"])
```

Snapshot gồm `summary` và danh sách `candidates`; không chứa prompt, raw key, header xác thực hoặc response thô.

### Async worker/FastAPI

Trong môi trường async, dùng API async để không block event loop của app:

```python
outcome = await router.aroute_outcome(AIRequest(prompt="Translate this chapter..."))
result = await router.aroute(AIRequest(prompt="Summarize this text..."))
```

P2 hỗ trợ native async HTTP transport qua optional extra. Nếu muốn dùng transport async thật, cài:

```powershell
pip install nakazasen-ai-router[async]
```

Sau đó có thể bật async network trong factory:

```python
router = create_router_from_env(
    enable_network=True,
    enable_async_network=True,
)
```

Nếu provider/caller không cấu hình async HTTP client, async API vẫn fallback an toàn qua worker thread để giữ tương thích.

### SQLite state store cho nhiều worker local

Nếu có nhiều worker/process trên cùng máy hoặc cùng filesystem, dùng SQLite thay JSON:

```python
router = create_router_from_env(
    enable_network=True,
    state_path="router_state.sqlite3",
    state_backend="sqlite",
    policy=RouterPolicy(max_attempts=3),
)
```

SQLite store chỉ lưu current state của `provider + model + key_id`. Nó không lưu attempt log để tránh phình DB và giảm rủi ro lộ metadata.

## Metrics snapshot

Xem [docs/metrics.vi.md](docs/metrics.vi.md) và `scripts/router_metrics.py` để xuất JSON observability an toàn cho router/job queue.

## Job queue bền vững

Xem [docs/job_queue.vi.md](docs/job_queue.vi.md) để dùng SQLite queue adapter tùy chọn cho enqueue, claim, lease, retry, success/fail mà không lưu raw payload.

## Primitive segmentation

Xem [docs/segmentation.vi.md](docs/segmentation.vi.md) để dùng helper chia/gộp chunk trung lập domain trước `route_outcome()`.

## Live provider conformance

Xem [docs/live_conformance.vi.md](docs/live_conformance.vi.md) để chạy kiểm chứng provider thật opt-in và đã sanitize.

## Cách tự quét tìm mô hình mới (Gemini Model Discovery)

Tính năng tự quét mô hình mới là tự nguyện (opt-in). Nó giúp bạn truy vấn danh sách mô hình hiện có từ nhà cung cấp nhưng **không** tự động đưa các mô hình mới quét được vào danh mục chạy mặc định.

```bash
# Chỉ hiển thị danh sách mô hình quét được
py scripts/discover_models.py --provider gemini --key-file "D:\duong_dan_ngoai\provider_keys.txt"

# Quét và chạy thử ngay các mô hình mới để kiểm tra tính khả dụng
py scripts/discover_models.py --provider gemini --key-file "D:\duong_dan_ngoai\provider_keys.txt" --validate-live --only-new
```

Các mô hình mới phát hiện phải vượt qua bài kiểm tra thực tế (live smoke test) và được người vận hành xem xét thủ công trước khi thêm vào danh sách chính thức trong mã nguồn.

## Bảng điểm sức khỏe (Health Scoreboard) là gì?

Đây là cơ chế theo dõi hiệu năng của mô hình một cách an toàn. Khi bạn chạy kiểm tra thực tế với tùy chọn `--health-cache <đường_dẫn_tệp_tin.json>`, hệ thống sẽ ghi lại các thông số:
- Số lần gọi thành công / thất bại.
- Số lần thất bại liên tiếp (failure streak).
- Trạng thái gần nhất và loại lỗi (lỗi hết hạn ngạch - quota, lỗi kết nối - transport).
- Thời gian phản hồi gần nhất (latency) và thời gian tạm khóa mô hình (cooldown).

**Cam kết bảo mật:** Tệp tin ghi nhận sức khỏe này tuyệt đối không lưu nội dung câu lệnh yêu cầu (prompt), khóa dịch vụ (API key), hay nội dung phản hồi chi tiết từ AI.

Xem bảng điểm và xếp hạng mô hình:
```bash
py scripts/health_scoreboard.py --health-cache local_cases/router_health.json --provider gemini --rank-configured
```

## Bí danh mô hình (Model Alias) là gì?

Thư viện hỗ trợ bản đồ ánh xạ giúp ứng dụng gọi mô hình qua bí danh thân thiện dạng `nhà_cung_cấp:bí_danh` thay vì viết đúng mã mô hình gốc. Ví dụ:
- `gemini:default` trỏ tới `gemini-3.5-flash`
- `gemini:fast` trỏ tới `gemini-3.5-flash`
- `gemini:latest` trỏ tới `gemini-flash-latest`
- `gemini:lite` trỏ tới `gemini-flash-lite-latest`
- `gemini:cheap` trỏ tới `gemini-flash-lite-latest`
- `gemini:robotics` trỏ tới `gemini-robotics-er-1.6-preview`
- `gemini:gemma` trỏ tới `gemma-4-31b-it`

## Nguyên tắc bảo mật

1. **Không lưu khóa dịch vụ trong mã nguồn:** Tuyệt đối không commit tệp tin cấu hình chứa API key thật.
2. **Lọc sạch dữ liệu nhạy cảm:** Trình kiểm thử và ghi nhật ký không in tiêu đề xác thực (Authorization headers) hoặc nội dung phản hồi thô của nhà cung cấp.
3. **Không lưu lịch sử hội thoại:** Trạng thái sức khỏe lưu trên ổ đĩa chỉ chứa các thông số số liệu, không lưu câu lệnh (prompt) hay phản hồi (response).

## Vì sao chưa tích hợp AIOS_habbit ngay?

Tích hợp trực tiếp với hệ điều hành AI (AIOS_habbit) đòi hỏi phải xác lập ranh giới bảo mật rõ ràng. AIOS_habbit chịu trách nhiệm gán nhãn bảo mật và khử trùng dữ liệu nhạy cảm trước, còn Router chịu trách nhiệm thực thi chính sách điều phối an toàn (chẳng hạn không gửi dữ liệu mật lên đám mây). Thiết kế ranh giới này cần được kiểm tra kỹ lưỡng qua các mô hình giả lập (mock) trước khi cho phép mã nguồn Router tương tác thực sự với hệ thống AIOS bên ngoài.
