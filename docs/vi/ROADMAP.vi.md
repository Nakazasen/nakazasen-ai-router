# Lộ trình phát triển (Roadmap)

Tài liệu này tổng hợp các cột mốc phát triển của Nakazasen AI Router và định hướng các bước tiếp theo.

## Các cột mốc đã hoàn thành

- **Gate 0 - 10:** Thiết lập router mock-first, provider OpenAI-compatible, fallback, multi-key pool và tích hợp Gemini.
- **Gate 11 - 14.5:** Bổ sung model discovery thủ công, health scoreboard, model aliases, tài liệu song ngữ và kiểm tra chất lượng/encoding.
- **Gate 14.6 / Release 0.2.3:** Cập nhật catalog model Gemini/DeepSeek, quét catalog lúc router khởi động theo cơ chế opt-in, fallback model tĩnh khi quét lỗi, và quy ước `API Key.txt` local được Git ignore.

## Các bước phát triển tiếp theo

### Gate 15 - Thiết kế tích hợp AIOS_habbit

Xác định giao thức giao tiếp giữa Router và AIOS:

- Đặc tả metadata bảo mật đi kèm request.
- Thiết kế chính sách ngăn cloud provider cho nhãn `local_only`/`confidential`.

### Gate 16 - Tích hợp giả lập

- Kiểm duyệt policy qua mock để không phải gọi mạng thật.

### Gate 17 - Thử nghiệm thực tế có kiểm soát

- Chạy pilot quy mô nhỏ sau khi vượt qua kiểm tra an toàn và mock.

## Backlog

- Cache catalog model có TTL và persistence tùy chọn cho startup nhanh hơn.
- Kiểm thử capability chuyên sâu cho model mới phát hiện.
- Token accounting và cost estimation.