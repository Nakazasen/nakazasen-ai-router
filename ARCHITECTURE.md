# Kiến trúc Nakazasen AI Router

## Mục tiêu dễ hiểu

Router giống như người điều phối. Khi app cần gọi AI, router chọn provider phù hợp. Nếu provider đầu tiên lỗi, router thử provider tiếp theo theo chính sách đã đặt.

## Thành phần chính

- `AIRequest`: yêu cầu đầu vào, ví dụ prompt và metadata.
- `AIResult`: kết quả trả về từ provider được chọn.
- `ProviderBase`: lớp nền cho mọi provider.
- `ProviderCandidate`: thông tin provider trong danh sách lựa chọn.
- `ProviderHealth`: trạng thái provider: đang bật, cooldown đến khi nào, lỗi gần nhất.
- `RouterPolicy`: chính sách router, ví dụ `local_only`.
- `AIRouter`: bộ điều phối chính.

## Luồng xử lý

1. App tạo `AIRequest`.
2. `AIRouter` lọc provider không hợp lệ:
   - Provider bị disable.
   - Provider đang cooldown.
   - Provider cloud khi `local_only=True`.
3. Router gọi provider theo thứ tự ưu tiên.
4. Nếu provider quota lỗi, router đưa provider vào cooldown.
5. Nếu provider auth lỗi, router disable provider.
6. Nếu còn provider khác, router fallback.
7. Nếu không provider nào thành công, router báo lỗi tổng hợp.

## Bảo mật

- Không có provider thật trong giai đoạn này.
- Không có API key thật trong repo.
- Log request sẽ che các trường nhạy cảm như `api_key`, `token`, `secret`, `authorization`.
