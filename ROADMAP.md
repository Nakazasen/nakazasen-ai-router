# Roadmap

## Giai đoạn 1: Nền móng hiện tại

- Tạo cấu trúc repo Python sạch.
- Định nghĩa API router tối thiểu.
- Tạo provider giả lập để chứng minh hành vi fallback và bảo mật.
- Chưa gọi AI thật.

## Giai đoạn 2: Port từ translation_app

- Port Provider Router hiện có sang package này.
- Chuẩn hoá lỗi provider thành nhóm: quota, auth, timeout, transient.
- Bổ sung cấu hình ưu tiên provider theo mục đích sử dụng.

## Giai đoạn 3: Provider thật

- Thêm adapter provider thật sau khi có thiết kế bảo mật riêng.
- Đọc API key từ biến môi trường hoặc secret manager, không đọc từ file commit vào repo.
- Bổ sung test tích hợp có thể bật/tắt bằng cờ riêng.

## Giai đoạn 4: Vận hành

- Theo dõi health provider.
- Ghi metric an toàn, không log prompt nhạy cảm hoặc API key.
- Tài liệu hoá cách debug cho non-tech user.
