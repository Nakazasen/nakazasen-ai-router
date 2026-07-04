# Lộ trình phát triển (Roadmap)

Tài liệu này tổng hợp các cột mốc phát triển của dự án Nakazasen AI Router và định hướng các bước tiếp theo.

## Các cột mốc đã hoàn thành (Tính đến Gate 14.5)

- **Gate 0 - 6:** Thiết lập nền tảng dự án, xây dựng bộ điều phối thông minh (`AIRouter`), thiết kế các nhà cung cấp tương thích giao thức OpenAI, xây dựng cơ chế tự động chuyển hướng dự phòng (fallback) và phát hành phiên bản nội bộ `v0.1.0`.
- **Gate 7 - 10:** Tối ưu hóa chính sách ưu tiên mô hình miễn phí trước (`live_free_first`), sửa lỗi kết nối của nhà cung cấp Groq, tích hợp API Google Gemini và kiểm thử chất lượng các mô hình Gemini.
- **Gate 11 - 12:** Xây dựng cơ chế tự quét tìm mô hình mới (model discovery) của nhà cung cấp, và bật danh mục mô hình mở rộng hoạt động ổn định (gồm `gemini-flash-lite-latest`, `gemini-3.1-flash-lite-preview` và `gemma-4-31b-it`).
- **Gate 13 - 14:** Nghiên cứu kiến trúc các AI Gateway/Router lớn (LiteLLM, Portkey, Vercel), phát triển bảng điểm sức khỏe an toàn (health scoreboard), bộ phân giải bí danh mô hình (model alias registry) và thiết kế sơ bộ ranh giới bảo mật thông tin với AIOS.
- **Gate 14.5:** Kiểm tra và khắc phục triệt để lỗi hiển thị phông chữ/ký tự lạ (mojibake) trên tài liệu công khai của kho chứa mã nguồn (repository).

## Các bước phát triển tiếp theo

### Gate 14.6 - Hoàn thiện tài liệu song ngữ và quy trình kiểm tra
- Cung cấp toàn bộ tài liệu vận hành chính thức bằng tiếng Việt giúp người dùng không chuyên dễ dàng tiếp cận.
- Thiết lập kịch bản tự động kiểm tra định dạng mã hóa ký tự (encoding audit) để ngăn chặn lỗi hiển thị ký tự lạ trong tương lai.

### Gate 15 - Thiết kế tích hợp AIOS_habbit (AIOS Integration Design)
Xác định cụ thể giao thức giao tiếp giữa Router và hệ điều hành AIOS:
- Đặc tả cấu trúc metadata bảo mật được truyền đi kèm yêu cầu.
- Thiết kế kịch bản thử nghiệm khả năng ngăn chặn dữ liệu đám mây đối với các nhãn dữ liệu nhạy cảm (`local_only`, `confidential`).

### Gate 16 - Xây dựng bản thử nghiệm tích hợp giả lập (AIOS Mock Integration)
- Thực hiện lập trình và tích hợp với hệ thống AIOS thông qua các mô hình giả lập (mocking) để kiểm duyệt hoạt động của chính sách bảo mật mà không cần chạy kết nối mạng thật.

### Gate 17 - Triển khai thí nghiệm thực tế (Real-work Pilot)
- Chạy thử nghiệm hệ thống tích hợp trong môi trường thực tế quy mô nhỏ có kiểm soát chặt chẽ sau khi đã vượt qua các bước kiểm thử an toàn và kiểm thử giả lập.

## Danh sách công việc chờ xử lý (Backlog)

- **Tích hợp ứng dụng dịch thuật (translation_app):** Đang tạm hoãn để ưu tiên thiết lập hạ tầng bảo mật dữ liệu.
- **Cơ chế tự động thử lại (Retry with backoff):** Hỗ trợ tự động gọi lại mô hình với thời gian giãn cách tăng dần khi gặp lỗi đường truyền tạm thời.
- **Thống kê chi phí và số lượng thẻ mã hóa (Token accounting & cost estimation):** Phục vụ việc theo dõi và kiểm soát ngân sách cuộc gọi AI.
