# Cài đặt, cập nhật và gỡ cài đặt

## Cài bản release cố định

```powershell
py -m pip install "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.2.3"
```

## Cập nhật lên 0.2.3

Các release tag trước là `v0.2.1` và `v0.2.2`.

```powershell
py -m pip install --upgrade --force-reinstall "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.2.3"
```

## Gỡ rồi cài lại

```powershell
py -m pip uninstall nakazasen-ai-router
py -m pip install "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.2.3"
```

## Kiểm tra version đang cài

```powershell
py -c "import importlib.metadata as m; print(m.version('nakazasen-ai-router'))"
```

Key file và SQLite state local nằm ngoài Python package. `API Key.txt` là quy ước phát triển local đã được ignore, không bao giờ nằm trong package release.
