# Live provider conformance

Live conformance verifies real provider behavior without making live checks part of normal tests or CI.

## Safety rules

- Use a key file outside this repository.
- Do not commit live reports.
- Do not print or store raw API keys.
- Do not store the raw test prompt in router state or attempts.
- Reports are sanitized and include only provider/model/status/error type/latency/short previews.

## Run one provider

```powershell
py scripts/live_conformance.py --provider gemini --key-file "path\to\provider_keys.txt"
```

Optional report path:

```powershell
py scripts/live_conformance.py --provider gemini --key-file "path\to\provider_keys.txt" --json-out local_cases/conformance_gemini.json
```

## Optional checks

```powershell
py scripts/live_conformance.py --provider gemini --key-file "path\to\provider_keys.txt" --include-async --include-stream
```

## All configured providers

```powershell
py scripts/live_conformance.py --all-configured --key-file "path\to\provider_keys.txt"
```

The command exits successfully if at least one configured provider passes. Skipped providers report `missing key`.
