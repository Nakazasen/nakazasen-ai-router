# Provider keys

Nakazasen AI Router never ships API keys. An integrating application supplies its own key through environment variables, its secret manager, or another process-local configuration source.

## Integration pattern

```python
import os
from nakazasen_ai_router import AIRequest, create_router_from_env

os.environ["GEMINI_API_KEY"] = load_secret("gemini")
os.environ["DEEPSEEK_API_KEY"] = load_secret("deepseek")
router = create_router_from_env(
    provider_names=("gemini", "deepseek"),
    enable_network=True,
)
result = router.route(AIRequest(prompt="Reply with OK."))
```

The router reads singular and plural key variables from the mapping passed as `env`, or from `os.environ` when `env` is omitted. This lets another program inject a private mapping without mutating global process state:

```python
router = create_router_from_env(
    env={"GEMINI_API_KEY": load_secret("gemini")},
    provider_names=("gemini",),
    enable_network=True,
)
```

Supported providers include Gemini, DeepSeek, Groq, OpenRouter, NVIDIA NIM, ChatAnyWhere, and Mistral.

Supported variables include:

```text
GEMINI_API_KEY=...
GEMINI_API_KEYS=key_one,key_two
DEEPSEEK_API_KEY=...
DEEPSEEK_API_KEYS=key_one;key_two
GROQ_API_KEY=...
OPENROUTER_API_KEY=...
NVIDIA_NIM_API_KEY=...
CHATANYWHERE_API_KEY=...
MISTRAL_API_KEY=...
```

Plural values accept commas, semicolons, and newlines. Raw keys are never returned in route attempts, state stores, or dashboard exports.

## No-key mode

Without keys, applications can still use offline tests, fake providers, segmentation, SQLite jobs, quota policy, metrics, and the static dashboard. Cloud provider profiles are skipped until a key is supplied. A local OpenAI-compatible provider may operate without a key when its base URL is local.

## Local live-test file

For local development in this repository only, `scripts/live_smoke.py` and `scripts/discover_models.py` default to `API Key.txt` at the repository root. `.gitignore` contains the exact `/API Key.txt` rule, so the file will not be staged by normal Git commands. Never force-add it and do not copy it into releases.

```powershell
py scripts/live_smoke.py --provider gemini --test-all-models
py scripts/discover_models.py --provider deepseek --only-new
```

You can override the default with an external path:

```powershell
py scripts/live_smoke.py --provider gemini --key-file "D:\path\to\provider_keys.txt"
```

A key file supports either `KEY=value` or a provider label followed by a value on the next line. Live script output is sanitized and must not be used to print or persist raw keys.

## Startup model refresh

Supply a key and set both flags to refresh the in-memory catalog when a router starts:

```python
router = create_router_from_env(
    provider_names=("gemini", "deepseek"),
    enable_network=True,
    refresh_models_on_startup=True,
)
```

The refresh is optional. It queries Gemini's native model endpoint and other cloud providers' OpenAI-compatible `GET /models` endpoint. Discovered chat-capable IDs are merged before static defaults for that router instance. Failures retain static defaults and do not block startup.

## Troubleshooting

- Missing key: set the provider environment variable or pass a private `env` mapping.
- Invalid key: replace it through the application secret manager or provider console.
- Quota/429: wait or configure another key/provider.
- Network disabled: set `enable_network=True` in SDK code.
- Startup refresh blocked: also set `enable_network=True` with `refresh_models_on_startup=True`.
