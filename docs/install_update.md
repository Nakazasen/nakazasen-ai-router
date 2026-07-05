# Install, update, and uninstall

## Install a pinned release

```powershell
py -m pip install "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.2.2"
```

## Update to a newer tag

To refresh the current stable tag or move from `v0.2.1` to `v0.2.2`:

```powershell
py -m pip install --upgrade --force-reinstall "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.2.2"
```

## Uninstall then reinstall

```powershell
py -m pip uninstall nakazasen-ai-router
py -m pip install "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.2.2"
```

## Check installed version

```powershell
py -c "import importlib.metadata as m; print(m.version('nakazasen-ai-router'))"
```

Key files and local SQLite state are not removed by pip uninstall if you store them outside the Python package.
