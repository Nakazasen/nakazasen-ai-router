# Hướng dẫn nhanh (Quickstart)

Tài liệu này hướng dẫn bạn cài đặt và sử dụng nhanh Nakazasen AI Router trong dự án phát triển phần mềm của mình.

## Cài đặt thư viện

Bạn có thể cài đặt thư viện cục bộ (local) bằng công cụ quản lý gói Python:

```bash
# Cài đặt ở chế độ chỉnh sửa (development mode) để dễ cập nhật mã nguồn
py -m pip install -e .
```

## Tạo và sử dụng Router

Nakazasen AI Router cho phép bạn tải danh sách nhà cung cấp cấu hình sẵn từ biến môi trường (environment variables) thông qua một phương thức khởi tạo duy nhất.

Ví dụ tạo router và gọi dịch vụ bằng Python:

```python
from nakazasen_ai_router import AIRequest, create_router_from_env

# Khởi tạo router cho nhà cung cấp Gemini và cho phép kết nối mạng
# (mặc định các cuộc gọi mạng chỉ được thực hiện khi enable_network=True)
router = create_router_from_env(provider_names=("gemini",), enable_network=True)

# Gửi yêu cầu câu lệnh (prompt)
result = router.route(AIRequest(prompt="Reply with OK."))

# In phản hồi nhận được từ mô hình
print(result.text)
```

## Chạy kiểm thử giả lập (Mock Test)

Chúng tôi cung cấp bộ kiểm thử mặc định giúp xác minh logic hoạt động của router (xoay vòng mô hình, dự phòng khi gặp lỗi, ghi điểm sức khỏe) mà không thực sự gửi yêu cầu qua internet hay yêu cầu khóa dịch vụ (API key) thật.

Hãy chạy lệnh sau để kiểm tra:

```bash
py -m pytest -q
```

## Chạy kiểm tra thực tế bằng khóa dịch vụ bên ngoài

Để kiểm thử kết nối thật tới API của nhà cung cấp, bạn cần chuẩn bị một tệp cấu hình chứa mã khóa thật, đặt **bên ngoài thư mục của dự án này** (ví dụ: `D:\Sandbox\AIOS_habbit\API Key.txt`) để đảm bảo an toàn tuyệt đối.

Cấu trúc dòng trong tệp khóa dịch vụ:
```text
GEMINI_API_KEY
mã_khóa_gemini_thật_của_bạn
```

Chạy lệnh kiểm tra thực tế:

```bash
# Chạy với mô hình mặc định hàng đầu
py scripts/live_smoke.py --provider gemini --key-file "D:\Sandbox\AIOS_habbit\API Key.txt"

# Chạy kiểm tra lần lượt tất cả mô hình trong danh mục cấu hình
py scripts/live_smoke.py --provider gemini --key-file "D:\Sandbox\AIOS_habbit\API Key.txt" --test-all-models
```

## Không commit mã khóa dịch vụ (API Key)

> [!IMPORTANT]
> Tuyệt đối không copy tệp tin chứa API key thật vào trong thư mục dự án `nakazasen-ai-router`.
> Hãy cấu hình tệp tin đó nằm ở thư mục ngoài và chỉ truyền tham số qua dòng lệnh.
> Luôn chạy kiểm tra an toàn (secret scan) trước khi thực hiện commit mã nguồn.
