# Release and Packaging Runbook

This runbook is the source of truth for preparing, validating, and publishing a Nakazasen AI Router release. Run commands from the repository root with PowerShell.

Vietnamese version: [releasing.vi.md](releasing.vi.md)

## Version policy

The project uses Semantic Versioning while it is pre-1.0:

- **Patch** (`0.3.0` → `0.3.1`): backward-compatible fixes and documentation.
- **Minor** (`0.3.0` → `0.4.0`): backward-compatible features or intentional public API additions.
- **Major** (`0.x` → `1.0.0`): stable API commitment; after 1.0, breaking changes increment the major version.

A release version must match in all of these places:

1. `pyproject.toml` → `[project].version`
2. `CHANGELOG.md` → version heading and date
3. `docs/releases/<version>.md`
4. README stable-install tag and release-note link
5. Git annotated tag `v<version>`

## Release gates

A release may be committed, tagged, and pushed only when every applicable gate passes:

1. **Repository hygiene**
   - Confirm the intended branch and remote.
   - Review every changed/untracked file.
   - Confirm `API Key.txt`, `.env*`, build output, and local state are ignored and untracked.
2. **Offline correctness**
   - Run the full test suite.
   - Compile the package and scripts.
   - Run documentation, local-path, positioning, and encoding audits.
3. **Metadata consistency**
   - Run `scripts/release_check.py <version>`.
   - Confirm public API additions are documented and tested.
4. **Package correctness**
   - Remove old `build/`, `dist/`, and package `*.egg-info` output.
   - Build both sdist and wheel.
   - Install the wheel into a fresh virtual environment.
   - Run `scripts/install_smoke.py` from that environment.
5. **Live compatibility**
   - Opt-in only, with a local ignored key file.
   - Review each provider result, not only the process exit code.
6. **Publication**
   - Commit the verified release.
   - Create an annotated tag.
   - Push the branch, then the tag.

> **Important:** A passing live call does not replace offline tests. A passing `--provider all` command means at least one provider succeeded; inspect the per-provider report before declaring all configured providers healthy.

## Standard command sequence

Replace `0.3.0` with the target version.

```powershell
# 1. Offline gates
py -m pytest -q
py -m compileall -q src scripts
py scripts/audit_docs_quality.py
py scripts/audit_local_paths.py
py scripts/audit_positioning.py
py scripts/audit_text_encoding.py
py scripts/release_check.py 0.3.0

# 2. Build clean artifacts
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Get-ChildItem src -Directory -Filter *.egg-info | Remove-Item -Recurse -Force
py -m build

# 3. Local wheel verification
$releaseVenv = Join-Path $env:TEMP "nakazasen-ai-router-release-venv"
Remove-Item -Recurse -Force $releaseVenv -ErrorAction SilentlyContinue
py -m venv $releaseVenv
& "$releaseVenv\Scripts\python.exe" -m pip install --upgrade pip
& "$releaseVenv\Scripts\python.exe" -m pip install .\dist\nakazasen_ai_router-0.3.0-py3-none-any.whl
& "$releaseVenv\Scripts\python.exe" -I scripts\install_smoke.py

# 4. Explicit live smoke (never print or stage the key file)
py scripts/live_smoke.py --provider all --key-file ".\API Key.txt" --stop-on-first-pass

# 5. Review before publication
git status --short
git diff --check
git diff --stat
git ls-files -- "API Key.txt" ".env" ".env.*"

# 6. Publish only after all gates pass
git add <reviewed-files-only>
git commit -m "feat: release v0.3.0"
git tag -a v0.3.0 -m "Nakazasen AI Router 0.3.0"
git push origin main
git push origin v0.3.0
```

Delete the external `$releaseVenv` after verification; it is local build infrastructure, not a release artifact. Keeping the venv outside the repository also prevents repository-wide audits from scanning third-party packages.

## Failure and rollback rules

- **Test/build failure:** fix the issue, discard stale artifacts, and restart at the offline gates.
- **Live-provider failure:** do not expose the error payload or key; classify whether it is auth, quota, model availability, or transport. Do not tag until the bounded smoke requirement is satisfied.
- **Commit created but not pushed:** amend or create a corrective commit, then recreate the local tag if needed.
- **Tag pushed with wrong content:** do not silently rewrite a public tag. Publish a patch release unless repository owners explicitly approve a coordinated tag correction.
- **Secret appears in Git:** stop immediately. Remove it from staging/history as appropriate and rotate the credential before any push.

## Release evidence

Record these facts in the release note or handoff:

- exact version and commit;
- offline test count and skipped tests;
- audit results;
- package filenames;
- isolated install result;
- sanitized live-smoke provider outcomes;
- known limitations and residual risks.