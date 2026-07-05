# Cài đặt, cập nhật và gỡ cài đặt

## Cài bản release cố định

```powershell
py -m pip install "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.2.1"
```

## Cập nhật lên tag mới

Khi có `v0.2.2`:

```powershell
py -m pip install --upgrade --force-reinstall "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.2.2"
```

## Gỡ rồi cài lại

```powershell
py -m pip uninstall nakazasen-ai-router
py -m pip install "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.2.2"
```

## Kiểm tra version đang cài

```powershell
py -c "import importlib.metadata as m; print(m.version('nakazasen-ai-router'))"
```

Key file và SQLite state local không bị pip uninstall xóa nếu bạn lưu chúng ngoài Python package.
