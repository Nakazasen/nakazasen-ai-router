# Cài đặt, cập nhật và gỡ cài đặt

## Cài release 0.4.0 cố định

```powershell
py -m pip install "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.4.0"
nakazasen-ai-router version
```

Ứng dụng tích hợp sẽ giữ nguyên version đã cài/pin. Việc Nakazasen phát hành tag mới không âm thầm thay đổi virtual environment của ứng dụng đó.

Các stable tag trước gồm `v0.2.1`, `v0.2.2`, `v0.2.3` và `v0.3.0`. Ứng dụng có thể nâng thẳng từ các version đó lên `v0.4.0` sau khi chạy compatibility test của chính ứng dụng.

## Cập nhật thủ công an toàn

```powershell
# Chỉ kiểm tra qua mạng, không chạy pip.
nakazasen-ai-router update --check

# Kiểm tra, in trước lệnh chính xác, rồi hỏi xác nhận.
nakazasen-ai-router update --apply

# Override non-interactive rõ ràng, chỉ dùng trong CI đã kiểm soát.
nakazasen-ai-router update --apply --yes
```

Lệnh dùng đúng interpreter hiện tại qua `sys.executable -m pip` và cài một Git tag cụ thể. Import SDK, tạo router và routing request không bao giờ tự kiểm tra hay cài package mới.

Lệnh trực tiếp tương đương:

```powershell
py -m pip install --upgrade --force-reinstall "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.4.0"
```

## Pull request cập nhật tự động cho repo tích hợp

Nên dùng PR dependency có thể review thay vì tự sửa package khi chương trình đang chạy. Với repo khai báo Git dependency trong `pyproject.toml`, cấu hình Dependabot hoặc Renovate kiểm tra định kỳ, chạy test của repo đó và chỉ merge sau khi review. Production nên pin tag/commit bất biến, không bám `main`.

## Báo cáo free-tier có kiểm toán

```powershell
nakazasen-ai-router free-tiers
nakazasen-ai-router free-tiers --json
```

Tổng định kỳ dạng số chỉ tính allowance cố định, có nguồn, còn mới và đã loại shared pool trùng. Credit đăng ký một lần, gói dynamic/unlimited và plan bị loại/stale là trường riêng. Usage được ghi `estimated_local`; dashboard provider mới là nguồn authoritative.

## Gỡ rồi cài lại

```powershell
py -m pip uninstall nakazasen-ai-router
py -m pip install "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.4.0"
```

Key file và SQLite state local nằm ngoài Python package. `API Key.txt` là quy ước phát triển local đã được ignore, không bao giờ nằm trong package release.
