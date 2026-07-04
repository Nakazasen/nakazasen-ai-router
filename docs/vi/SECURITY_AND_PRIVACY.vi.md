# Chính sách An ninh và Bảo mật riêng tư (Security and Privacy)

Tài liệu này trình bày các nguyên tắc an ninh dữ liệu và bảo mật quyền riêng tư được áp dụng trong Nakazasen AI Router.

## Nguyên tắc xử lý khóa dịch vụ và dữ liệu nhạy cảm

1. **Không lưu khóa dịch vụ (API key):** Hệ thống không ghi nhận khóa dịch vụ vào bất kỳ tệp nhật ký (logs), tệp kiểm tra cấu hình, hay tệp lưu sức khỏe (health scoreboard cache) nào.
2. **Không in tiêu đề xác thực (Authorization headers):** Khi thực hiện các cuộc gọi API thực tế tới nhà cung cấp, thông tin tiêu đề chứa mã khóa xác thực sẽ bị lọc bỏ khỏi màn hình dòng lệnh và nhật ký lỗi.
3. **Không lưu câu lệnh yêu cầu (prompt) và phản hồi thô (raw response):** Cơ chế ghi nhật ký hoạt động (attempt traces) và bảng điểm sức khỏe chỉ lưu lại các thông số kỹ thuật (mã phản hồi HTTP, thời gian chạy, loại lỗi) và tuyệt đối không lưu lại nội dung câu lệnh yêu cầu của người dùng hoặc phản hồi chi tiết từ AI.

## Các nhãn phân loại quyền riêng tư (Privacy Labels)

Để chuẩn bị cho việc tích hợp điều phối dữ liệu an toàn, dự án đưa ra thiết kế phân loại mức độ bảo mật cho các yêu cầu đầu vào:

| Nhãn bảo mật | Hành động điều phối đám mây | Giải thích chi tiết |
|---|---|---|
| `local_only` | **TỪ CHỐI** (Deny cloud) | Người dùng yêu cầu xử lý hoàn toàn cục bộ, không gửi bất kỳ dữ liệu nào qua mạng internet. |
| `confidential` | **TỪ CHỐI** (Deny cloud) | Chứa thông tin mật của doanh nghiệp hoặc dữ liệu cá nhân nhạy cảm, không được phép tải lên máy chủ bên ngoài. |
| `unknown` | **TỪ CHỐI** (Deny cloud) | Chưa xác định mức độ nhạy cảm. Hệ thống áp dụng nguyên tắc an toàn tối đa (fail-closed) để chặn cuộc gọi. |
| `machine_only` | **TỪ CHỐI** trừ khi có sự đồng ý | Dữ liệu chỉ dùng nội bộ trừ khi người dùng bật tham số cho phép gửi đám mây (`allow_cloud=True`). |
| `cloud_safe` | **CHO PHÉP** (Allow cloud) | Dữ liệu đã được kiểm duyệt hoặc đã qua bước lọc/khử trùng dữ liệu nhạy cảm trước khi gửi đi. |
| `public` | **CHO PHÉP** (Allow cloud) | Thông tin công cộng hoặc dữ liệu không nhạy cảm. |

## Ranh giới trách nhiệm với AIOS_habbit

Mô hình tích hợp an ninh được phân định rõ ràng như sau:

- **AIOS_habbit (Hệ điều hành AI):** Chịu trách nhiệm thực hiện việc phân loại, gán nhãn dữ liệu (`privacy_label`) và tiến hành lọc bỏ các nội dung nhạy cảm khỏi câu lệnh (prompt sanitize) trước khi chuyển tiếp yêu cầu đến Router.
- **Nakazasen AI Router (Bộ điều phối):** Không tự phân tích nội dung văn bản để gán nhãn. Router chỉ đóng vai trò là bên thực thi chính sách (enforcement point) dựa trên các thẻ metadata nhãn bảo mật được gửi kèm theo yêu cầu. Nếu nhãn bảo mật yêu cầu xử lý cục bộ, Router sẽ lập tức từ chối và chặn cuộc gọi đến các nhà cung cấp đám mây.
