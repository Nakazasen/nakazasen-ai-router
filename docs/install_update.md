# Install, update, and uninstall

## Install a pinned release

```powershell
py -m pip install "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.2.3"
```

## Update to 0.2.3

The previous release tags were `v0.2.1` and `v0.2.2`.

```powershell
py -m pip install --upgrade --force-reinstall "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.2.3"
```

## Uninstall then reinstall

```powershell
py -m pip uninstall nakazasen-ai-router
py -m pip install "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.2.3"
```

## Check installed version

```powershell
py -c "import importlib.metadata as m; print(m.version('nakazasen-ai-router'))"
```

Key files and local SQLite state remain outside the Python package. `API Key.txt` is an ignored local development convention and is never part of a package release.
