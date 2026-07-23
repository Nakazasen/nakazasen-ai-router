# Nakazasen AI Router

## Provider keys and updates

See [docs/provider_keys.md](docs/provider_keys.md) for API key setup, [examples/key_setup_static/index.html](examples/key_setup_static/index.html) for a local-only key file helper, and [docs/install_update.md](docs/install_update.md) for update/uninstall commands.

## Stable install

```powershell
pip install git+https://github.com/Nakazasen/nakazasen-ai-router.git@v0.4.0
```

Release notes: [0.4.0.md](docs/releases/0.4.0.md)

Vietnamese documentation: [README.vi.md](README.vi.md)

Nakazasen AI Router is a general-purpose AI capacity layer for Python applications. It routes AI requests across local and cloud providers, manages provider/model/key health, and gives other repositories durable access to AI capacity without tying the core to any single domain.

The default development and test path is mock-first, offline, and safe: unit tests do not call the internet and do not require real API keys.

Translation is intentionally only one example of a general-purpose workload.

## What it does

- Routes requests across OpenAI-compatible providers.
- Falls back across providers, models, and API keys when a candidate fails.
- Tracks provider/model/key health and cooldowns.
- Supports durable `route_outcome()` results for job queues.
- Supports JSON or SQLite state storage.
- Provides sync and async routing APIs.
- Provides explainable weighted routing with balanced, fast, cheap, quality, and quota mode packs.
- Supports thread-safe, process-local shared quota pools and named fixed windows.
- Normalizes token usage and reports catalog provenance plus conservative cost estimates.
- Provides an audited free-tier catalog, shared-pool deduplication, and free-first preference in `cheap`/`quota` modes.
- Provides opt-in release checks and an explicit, confirmed update command; imports and routing never self-update.
- Provides budget guard and exponential retry backoff.
- Supports opt-in provider model catalog refresh at router startup.

## Safe version awareness and free-tier audit

Installed applications remain pinned until their owner explicitly upgrades them. Check or apply an update with:

```powershell
nakazasen-ai-router version
nakazasen-ai-router update --check
nakazasen-ai-router update --apply
nakazasen-ai-router free-tiers --json
```

`update --apply` previews the exact `sys.executable -m pip` command and asks for confirmation. Use `--yes` only in a deliberately controlled non-interactive environment. The SDK performs no default version network request and never mutates an environment during import, router construction, or request routing.

The free-tier report counts only sourced, fresh, numeric recurring allowances, deduplicated by shared pool. One-time credits and unlimited/dynamic plans are reported separately. The built-in catalog currently reports **0 audited recurring tokens/month** because supported providers publish dynamic limits rather than reproducible fixed monthly token grants. Nakazasen therefore does not claim OmniRoute's `1.53B` figure.

## Supported providers

The provider registry currently includes Gemini, OpenRouter, Groq, DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral, and local OpenAI-compatible servers.

## Install for local development

```powershell
py -m pip install -e .[dev]
py -m pytest -q
```

Optional native async network transport:

```powershell
py -m pip install -e .[async]
```

## Integrate from another application

Yes. The integrating application supplies its own provider key through environment variables and enables networking explicitly. Do not embed keys in source code.

```python
import os
from nakazasen_ai_router import AIRequest, create_router_from_env

os.environ["GEMINI_API_KEY"] = load_secret_from_your_secret_manager()
router = create_router_from_env(
    provider_names=("gemini", "deepseek"),
    enable_network=True,
)
result = router.route(AIRequest(prompt="Reply with OK."))
print(result.text)
```

Use plural variables such as `GEMINI_API_KEYS` or `DEEPSEEK_API_KEYS` for a comma-, semicolon-, or newline-separated key pool. The router falls back across keys and models while keeping raw keys out of attempt metadata and durable state.

## Opt-in startup model catalog refresh

Static registry models are always available as a safe fallback. An integrating application may request a fresh catalog only when it explicitly allows networking:

```python
router = create_router_from_env(
    provider_names=("gemini", "deepseek", "groq"),
    enable_network=True,
    refresh_models_on_startup=True,
)
```

At startup, Gemini is queried through its native model catalog endpoint. Other cloud providers use their OpenAI-compatible `GET /models` endpoint. Newly discovered chat-capable IDs are merged ahead of the static fallback list for the lifetime of that router instance only. A missing endpoint, malformed response, or provider error does not prevent startup: the static model list remains active. The refresh is disabled by default and raises `ValueError` if `enable_network=True` is not also set.

## Local live-provider testing

For this repository, `scripts/live_smoke.py` and `scripts/discover_models.py` default to the local file `API Key.txt`. It is ignored by Git (`/API Key.txt`) and must never be committed. The scripts read it only when an explicit live command runs, and their output is sanitized.

```powershell
# Uses the ignored repository-local API Key.txt by default.
py scripts/live_smoke.py --provider gemini --test-all-models

# Explicitly use another local secret file instead.
py scripts/discover_models.py --provider deepseek --key-file "D:\path\to\provider_keys.txt" --only-new
```

A key file can use either a label followed by a value or `KEY=value` format. See [docs/provider_keys.md](docs/provider_keys.md) for integration and secret-handling guidance.

## Architecture and release operations

- Human/AI system handoff, folder map, and Mermaid models: [ARCHITECTURE.md](ARCHITECTURE.md)
- Standard packaging/version/release process: [docs/releasing.md](docs/releasing.md)
- Public SDK contract: [docs/public_api.md](docs/public_api.md)

## Security and privacy principles

- Never commit API keys, including `API Key.txt`.
- Never print API keys or Authorization headers.
- Keep application keys in environment variables or an external secret manager.
- Network/live provider calls, update checks, update application, and startup model refresh are explicit opt-in.
- Unit tests are offline by default.
