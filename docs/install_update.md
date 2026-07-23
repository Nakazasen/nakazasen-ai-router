# Install, update, and uninstall

## Install the pinned 0.4.0 release

```powershell
py -m pip install "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.4.0"
nakazasen-ai-router version
```

A consuming application remains on its installed/pinned version. Publishing a newer Nakazasen tag does not silently mutate its virtual environment.

Previous stable tags include `v0.2.1`, `v0.2.2`, `v0.2.3`, and `v0.3.0`. An application may upgrade directly from those versions to `v0.4.0` after running its own compatibility tests.

## Safe manual update

```powershell
# Network check only; does not run pip.
nakazasen-ai-router update --check

# Checks, prints an exact command preview, then asks for confirmation.
nakazasen-ai-router update --apply

# Explicit non-interactive override for controlled CI only.
nakazasen-ai-router update --apply --yes
```

The command uses the current interpreter via `sys.executable -m pip` and installs an exact Git tag. Importing the SDK, creating a router, and routing requests never run an update check or package installation.

Direct equivalent:

```powershell
py -m pip install --upgrade --force-reinstall "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.4.0"
```

## Automated update pull requests for consuming repositories

Prefer reviewable dependency PRs over runtime self-mutation. For a consumer that declares this Git dependency in `pyproject.toml`, configure Dependabot or Renovate to check Python dependencies on a schedule, run that repository's tests, and merge only after review. Pin production to an immutable tag or commit; do not track `main` for production reproducibility.

## Audited free-tier report

```powershell
nakazasen-ai-router free-tiers
nakazasen-ai-router free-tiers --json
```

Numeric recurring capacity includes only fresh, sourced, fixed allowances and deduplicates shared pools. Signup credits, dynamic/unlimited plans, and excluded/stale plans are separate fields. Usage is labeled `estimated_local`; provider dashboards remain the authority.

## Uninstall then reinstall

```powershell
py -m pip uninstall nakazasen-ai-router
py -m pip install "nakazasen-ai-router @ git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.4.0"
```

Key files and local SQLite state remain outside the Python package. `API Key.txt` is an ignored local development convention and is never part of a package release.
