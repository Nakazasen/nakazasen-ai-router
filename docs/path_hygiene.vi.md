# Vệ sinh đường dẫn

Repo này phải giữ tính portable. Không commit đường dẫn riêng của máy, tên file API key thật, thư mục install smoke local hoặc artifact local sinh ra khi chạy thử.

Ví dụ bị chặn:

- `<drive>:\local-project-folder\...`
- `<drive>:\Users\<name>\...`
- `file:///<drive>:/...`
- a private key filename such as a personal API-key text file
- temporary install smoke folders

Placeholder docs được phép:

- `D:\path\to\provider_keys.txt`
- `D:\duong_dan_ngoai\provider_keys.txt`
- `path\to\provider_keys.txt`

Quy ước output local được phép gồm các thư mục demo `.demo_*` và `local_cases/` cho report opt-in. Các output này không nên commit trừ khi được ghi rõ là sample data an toàn.

Chạy:

```powershell
py scripts/audit_local_paths.py
py -m pytest tests/test_local_path_leaks.py -q
```
