# Quy trình đóng gói và phát hành

Đây là tài liệu chuẩn để chuẩn bị, kiểm thử và phát hành Nakazasen AI Router. Chạy các lệnh PowerShell từ thư mục gốc repository.

Bản tiếng Anh: [releasing.md](releasing.md)

## Chính sách phiên bản

Dự án dùng Semantic Versioning khi vẫn ở giai đoạn pre-1.0:

- **Patch** (`0.4.0` → `0.4.1`): sửa lỗi tương thích ngược hoặc cập nhật tài liệu.
- **Minor** (`0.4.0` → `0.5.0`): thêm tính năng/API public tương thích ngược.
- **Major** (`0.x` → `1.0.0`): cam kết API ổn định; sau 1.0, thay đổi breaking tăng major.

Phiên bản phải đồng nhất tại:

1. `pyproject.toml` → `[project].version`
2. heading và ngày trong `CHANGELOG.md`
3. `docs/releases/<version>.md`
4. tag cài stable và link release note trong README
5. annotated Git tag `v<version>`

## Các cổng bắt buộc

Chỉ commit/tag/push release khi mọi cổng áp dụng đều đạt:

1. **Vệ sinh repository**
   - Xác nhận đúng branch và remote.
   - Review mọi file thay đổi/untracked.
   - Xác nhận `API Key.txt`, `.env*`, build output và state local được ignore, không tracked.
2. **Đúng chức năng offline**
   - Chạy toàn bộ test.
   - Compile package và scripts.
   - Chạy audit tài liệu, local path, positioning và encoding.
3. **Nhất quán metadata**
   - Chạy `scripts/release_check.py <version>`.
   - API public mới phải có tài liệu và test.
4. **Đóng gói đúng**
   - Xóa output `build/`, `dist/`, `*.egg-info` cũ.
   - Build cả sdist và wheel.
   - Cài wheel vào virtual environment mới hoàn toàn.
   - Chạy `scripts/install_smoke.py` bằng interpreter đó.
5. **Tương thích live**
   - Chỉ chạy opt-in với key file local đã ignore.
   - Đọc kết quả từng provider, không chỉ nhìn exit code.
6. **Xuất bản**
   - Commit release đã xác minh.
   - Tạo annotated tag.
   - Push branch rồi push tag.

> **Quan trọng:** Live call thành công không thay thế offline tests. `--provider all` exit thành công chỉ có nghĩa ít nhất một provider pass; phải đọc báo cáo từng provider trước khi kết luận tất cả provider đã cấu hình đều khỏe.

## Chuỗi lệnh chuẩn

Thay `0.4.0` bằng phiên bản cần phát hành.

```powershell
# 1. Offline gates
py -m pytest -q
py -m compileall -q src scripts
py scripts/audit_docs_quality.py
py scripts/audit_local_paths.py
py scripts/audit_positioning.py
py scripts/audit_text_encoding.py
py scripts/release_check.py 0.4.0

# 2. Build artifact sạch
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Get-ChildItem src -Directory -Filter *.egg-info | Remove-Item -Recurse -Force
py -m build

# 3. Kiểm thử wheel độc lập
$releaseVenv = Join-Path $env:TEMP "nakazasen-ai-router-release-venv"
Remove-Item -Recurse -Force $releaseVenv -ErrorAction SilentlyContinue
py -m venv $releaseVenv
& "$releaseVenv\Scripts\python.exe" -m pip install --upgrade pip
& "$releaseVenv\Scripts\python.exe" -m pip install .\dist\nakazasen_ai_router-0.4.0-py3-none-any.whl
& "$releaseVenv\Scripts\python.exe" -I scripts\install_smoke.py

# 4. Live smoke tường minh (không in hoặc stage key file)
py scripts/live_smoke.py --provider all --key-file ".\API Key.txt" --stop-on-first-pass

# 5. Review trước khi phát hành
git status --short
git diff --check
git diff --stat
git ls-files -- "API Key.txt" ".env" ".env.*"

# 6. Chỉ phát hành sau khi mọi gate đạt
git add <chỉ-các-file-đã-review>
git commit -m "feat: release v0.4.0"
git tag -a v0.4.0 -m "Nakazasen AI Router 0.4.0"
git push origin main
git push origin v0.4.0
```

Xóa `$releaseVenv` nằm ngoài repository sau khi kiểm thử; đây là hạ tầng build local, không phải release artifact. Đặt venv ngoài repo cũng ngăn audit toàn repository quét dependency bên thứ ba.

## Quy tắc khi lỗi và rollback

- **Test/build lỗi:** sửa lỗi, bỏ artifact cũ và chạy lại từ offline gates.
- **Live provider lỗi:** không làm lộ error payload/key; phân loại auth, quota, model availability hoặc transport. Không tạo tag cho đến khi đạt yêu cầu smoke có giới hạn.
- **Đã commit nhưng chưa push:** amend hoặc tạo corrective commit, rồi tạo lại local tag nếu cần.
- **Đã push tag sai:** không âm thầm rewrite public tag. Phát hành bản patch, trừ khi owner đồng ý rõ ràng cho việc sửa tag có phối hợp.
- **Secret xuất hiện trong Git:** dừng ngay; bỏ khỏi staging/history phù hợp và rotate credential trước mọi push.

## Bằng chứng release

Release note hoặc biên bản bàn giao cần ghi:

- phiên bản và commit chính xác;
- số test pass/skip;
- kết quả audit;
- tên package artifact;
- kết quả isolated install;
- kết quả live smoke đã sanitize theo provider;
- giới hạn và rủi ro còn lại.