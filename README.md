# Nakazasen AI Router

Nakazasen AI Router is a small, privacy-aware, free-first AI provider router for Python applications.
It is designed to route requests across local and cloud providers while keeping tests mock-first and network-free by default.

## Current status

- Core router with provider health tracking.
- OpenAI-compatible provider adapter.
- Environment-based provider registry.
- Optional live smoke testing for real providers.
- Gemini provider and curated runtime model catalog.
- Opt-in Gemini model discovery.
- Safe health scoreboard and model alias parser.
- AIOS privacy policy adapter design, not yet integrated with AIOS_habbit.

## Supported providers

OpenAI-compatible providers currently represented in the registry:

- Gemini
- OpenRouter
- Groq
- DeepSeek
- NVIDIA NIM
- ChatAnyWhere
- Mistral
- Local OpenAI-compatible server

Unit tests do not call the internet and do not require real API keys.

## Gemini models enabled

The default Gemini runtime catalog is:

- `gemini-3.5-flash`
- `gemini-flash-latest`
- `gemini-flash-lite-latest`
- `gemini-3.1-flash-lite`
- `gemini-3.1-flash-lite-preview`
- `gemini-2.5-flash`
- `gemini-2.5-flash-lite`
- `gemini-3-flash-preview`
- `gemini-robotics-er-1.6-preview`
- `gemma-4-31b-it`

Notes:

- `gemini-3.5-flash` is first because it has been stable in live smoke tests.
- `*-latest` aliases are convenient but should be rechecked with discovery over time.
- `gemma-4-31b-it` is last because it can be heavier/slower and previously had a transient HTTP 500 before later passing.

## Install for local development

```powershell
py -m pip install -e .
py -m pytest -q
```

## Quick usage

```python
from nakazasen_ai_router import AIRequest, create_router_from_env

router = create_router_from_env(provider_names=("gemini",), enable_network=True)
result = router.route(AIRequest(prompt="Reply with OK."))
print(result.text)
```

Network access is opt-in. The default test path remains mock-first.

## Live smoke test

Keep key files outside the repository.

```powershell
py scripts/live_smoke.py --provider gemini --key-file "D:\path\to\API Key.txt" --model gemini-3.5-flash
py scripts/live_smoke.py --provider gemini --key-file "D:\path\to\API Key.txt" --test-all-models
```

Live output is sanitized and should only show provider, model, status, short error metadata, and short text previews.

## Gemini model discovery

Discovery is opt-in and does not enable new models automatically.

```powershell
py scripts/discover_models.py --provider gemini --key-file "D:\path\to\API Key.txt"
py scripts/discover_models.py --provider gemini --key-file "D:\path\to\API Key.txt" --validate-live --only-new
```

A discovered model must live PASS and be manually reviewed before it is added to the runtime catalog.

## Health scoreboard

Health cache is optional and stores only safe metadata: success/failure counts, failure streak, status, error type, latency, timestamps, and cooldown time.
It must not contain prompts, API keys, Authorization headers, raw provider responses, or evidence.

```powershell
py scripts/live_smoke.py --provider gemini --key-file "D:\path\to\API Key.txt" --model gemini-3.5-flash --health-cache local_cases/router_health.json
py scripts/health_scoreboard.py --health-cache local_cases/router_health.json --provider gemini --rank-configured
```

## Model aliases

The alias parser supports `provider:model` references, including:

- `gemini:default` -> `gemini-3.5-flash`
- `gemini:fast` -> `gemini-3.5-flash`
- `gemini:latest` -> `gemini-flash-latest`
- `gemini:lite` -> `gemini-flash-lite-latest`
- `gemini:cheap` -> `gemini-flash-lite-latest`
- `gemini:robotics` -> `gemini-robotics-er-1.6-preview`
- `gemini:gemma` -> `gemma-4-31b-it`

## Security and privacy principles

- Never commit API keys.
- Never copy external key files into this repository.
- Never print API keys or Authorization headers.
- Do not store raw prompts, raw provider responses, raw evidence, or confidential documents in traces or health cache.
- Network/live provider calls are explicit opt-in.
- AIOS_habbit integration is intentionally deferred until the privacy boundary is reviewed.
