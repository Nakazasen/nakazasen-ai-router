# Provider keys

Nakazasen AI Router never ships API keys. Users provide their own keys through environment variables or a key file stored outside this repository.

## No key mode

Without keys you can still use offline tests, fake providers, segmentation, SQLite jobs, quota policy, metrics, install smoke, and the static dashboard.

## Get keys

- Gemini: create an API key in Google AI Studio.
- Groq: create an API key in Groq Console.
- OpenRouter: create an API key in OpenRouter Keys.

## Environment variables

```powershell
$env:GEMINI_API_KEY=""
$env:GROQ_API_KEY=""
$env:OPENROUTER_API_KEY=""
```

## Key file outside the repo

Copy `docs/provider_keys.example.env` outside the repository and fill only the providers you use:

```text
GEMINI_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=
```

Test a key:

```powershell
py scripts/live_smoke.py --provider gemini --key-file "D:\path\to\provider_keys.txt"
```

## Guided setup

```powershell
py scripts/key_setup.py --out "D:\path\to\provider_keys.txt"
```

The helper masks input and refuses to write inside this repository unless you explicitly pass `--allow-inside-repo`.

## Troubleshooting

- Missing key: set env var or pass `--key-file`.
- Invalid key: regenerate it in the provider console.
- Quota/429: wait or use another provider profile.
- Network disabled: set `enable_network=True` in SDK code.
- Wrong file path: use an absolute path outside the repository.
