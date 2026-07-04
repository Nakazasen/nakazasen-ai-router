# Quy tắc Vận hành Dự án (Operation Rules)

Tài liệu này quy định các nguyên tắc hợp tác phát triển và kiểm soát chất lượng mã nguồn áp dụng cho các thành viên và trợ lý AI tham gia dự án Nakazasen AI Router.

## Quy trình làm việc và phân vai trợ lý AI

1. **Gemini (Mô hình sáng tạo nội dung):** Được phân vai soạn thảo các tài liệu hướng dẫn, giải thích cấu trúc kiến trúc bằng tiếng Việt sáng tỏ, ngắn gọn, dễ hiểu và thân thiện với người dùng không chuyên.
2. **Codex (Mô hình kỹ thuật):** Thực hiện kiểm tra tính đúng đắn kỹ thuật, chạy thử nghiệm (pytest), rà soát lỗi mã nguồn, quét mã khóa (secret scan) và áp dụng các thay đổi vào kho chứa mã nguồn.

## Quy tắc xử lý tệp tin văn bản và mã hóa (Encoding Rules)

Để ngăn ngừa tuyệt đối lỗi hiển thị ký tự lạ (mojibake) trên các nền tảng quản lý mã nguồn (như GitHub), mọi tệp tin văn bản phải tuân thủ nghiêm ngặt các quy tắc sau:

1. **Không sử dụng công cụ dòng lệnh không an toàn:** Tuyệt đối không dùng lệnh điều hướng dòng chảy (piping/redirecting) của PowerShell để ghi các tệp tin chứa văn bản tiếng Việt Unicode dài (ví dụ: `Out-File`, `Set-Content` không chỉ định rõ encoding).
2. **Ưu tiên sử dụng Python ghi tệp:** Mọi thao tác tạo hoặc chỉnh sửa nội dung văn bản nên được thực hiện qua các đoạn mã Python chỉ định rõ chuẩn mã hóa UTF-8 không có ký hiệu đánh dấu đầu tệp (BOM):
   ```python
   from pathlib import Path
   Path(file_path).write_text(content, encoding="utf-8", newline="\n")
   ```
3. **Kiểm tra mã hóa bắt buộc (Encoding Audit):** Trước khi commit, toàn bộ các tệp tin tài liệu công khai (`*.md`, `*.py`, `*.toml`, `*.txt`, `*.yml`, `*.yaml`) phải chạy qua công cụ kiểm tra tự động:
   ```bash
   py scripts/audit_text_encoding.py
   ```
   Nếu công cụ phát hiện bất kỳ mẫu ký tự lạ nghi ngờ nào, thao tác commit sẽ bị chặn để sửa lại.

## Nguyên tắc bàn giao kết quả (Gate Delivery Rules)

Mỗi cột mốc phát triển (Gate) chỉ được phép coi là hoàn thành (PASS) khi và chỉ khi:

1. **Kết quả kiểm thử đạt 100%:** Lệnh `py -m pytest -q` chạy thành công không có lỗi.
2. **Biên dịch thử đạt 100%:** Lệnh `py -m compileall src scripts` không phát hiện lỗi cú pháp.
3. **Không rò rỉ mã khóa dịch vụ (Secret Scan):** Chạy lệnh kiểm tra từ khóa nhạy cảm trên toàn bộ tệp tin dự án và không có kết quả trùng khớp:
   ```powershell
   # Quét khóa dịch vụ cơ bản
   Select-String -Path README.md,CHANGELOG.md,ARCHITECTURE.md,ROADMAP.md,pyproject.toml -Pattern "sk-|AIza|GEMINI_API_KEY=.*[A-Za-z0-9]" -CaseSensitive:$false
   ```
4. **Trạng thái Git sạch sẽ:** Không có tệp tin chưa được theo dõi nằm ngoài danh mục mong muốn, các tệp chỉnh sửa đều được commit rõ ràng.
