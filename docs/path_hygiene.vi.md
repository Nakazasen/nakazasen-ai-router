# Vệ sinh đường dẫn

Repo phải giữ tính portable. Không commit đường dẫn riêng của máy, artifact local hoặc API key.

`API Key.txt` ở root repo là ngoại lệ có chủ ý cho live test local: nó bị Git ignore bằng rule `/API Key.txt`, không được force-add hoặc copy vào package/release. Không ghi path tuyệt đối tới file đó trong source hoặc tài liệu.

Ví dụ bị chặn:

- `<drive>:\local-project-folder\...`
- `<drive>:\Users\<name>\...`
- `file:///<drive>:/...`
- temporary install smoke folders

Placeholder docs được phép:

- `D:\path\to\provider_keys.txt`
- `D:\duong_dan_ngoai\provider_keys.txt`
- `path\to\provider_keys.txt`

Chạy:

```powershell
py scripts/audit_local_paths.py
py -m pytest tests/test_local_path_leaks.py -q
```