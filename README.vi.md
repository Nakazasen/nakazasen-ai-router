# Nakazasen AI Router

Nakazasen AI Router là một thư viện Python nhỏ gọn, ưu tiên bảo mật quyền riêng tư (privacy-aware) và ưu tiên sử dụng mô hình miễn phí trước (free-first) để điều phối cuộc gọi đến các nhà cung cấp dịch vụ trí tuệ nhân tạo (AI providers).
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
py scripts/live_smoke.py --provider gemini --key-file "D:\đường_dẫn_ngoài\API Key.txt" --model gemini-3.5-flash

# Kiểm thử toàn bộ mô hình trong danh mục mặc định của nhà cung cấp
py scripts/live_smoke.py --provider gemini --key-file "D:\đường_dẫn_ngoài\API Key.txt" --test-all-models
```

Kết quả in ra sẽ được lược bỏ thông tin nhạy cảm (sanitized), chỉ hiển thị tên nhà cung cấp, mô hình, trạng thái ĐẠT/LỖI (PASS/FAIL) và độ dài phản hồi.

## Cách tự quét tìm mô hình mới (Gemini Model Discovery)

Tính năng tự quét mô hình mới là tự nguyện (opt-in). Nó giúp bạn truy vấn danh sách mô hình hiện có từ nhà cung cấp nhưng **không** tự động đưa các mô hình mới quét được vào danh mục chạy mặc định.

```bash
# Chỉ hiển thị danh sách mô hình quét được
py scripts/discover_models.py --provider gemini --key-file "D:\đường_dẫn_ngoài\API Key.txt"

# Quét và chạy thử ngay các mô hình mới để kiểm tra tính khả dụng
py scripts/discover_models.py --provider gemini --key-file "D:\đường_dẫn_ngoài\API Key.txt" --validate-live --only-new
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

Tích hợp trực tiếp với hệ điều hành AI (AIOS_habbit) đòi hỏi phải xác lập ranh giới bảo mật rõ ràng. AIOS_habbit chịu trách nhiệm gán nhãn bảo mật và khử trùng dữ liệu nhạy cảm trước, còn Router chịu trách nhiệm thực thi chính sách điều phối an toàn (chẳng hạn không gửi dữ liệu mật lên đám mây). Thiết kế ranh giới này cần được kiểm tra kỹ lượng qua các mô hình giả lập (mock) trước khi cho phép mã nguồn Router tương tác thực sự với hệ thống AIOS bên ngoài.
