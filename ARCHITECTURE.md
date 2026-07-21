# Architecture

Nakazasen AI Router is a library-first Python router for selecting AI providers and models safely.

## Core and provider registry

`core.py` exposes request/result types and a router that tries provider candidates in policy order. `registry.py` defines Gemini, OpenRouter, Groq, DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral, and local OpenAI-compatible profiles with safe metadata: base URLs, key-variable names, static fallback models, and notes.

The project is mock-first: tests do not call the internet unless a test explicitly injects a mock transport.

## Configuration and keys

`create_router_from_env()` accepts an explicit `env` mapping or reads `os.environ`. This lets a host application source keys from its own secret manager. Cloud providers require a key; local OpenAI-compatible providers may run keyless against a local URL. Singular and plural key environment variables are supported, and no raw key is included in router attempts or durable state.

## OpenAI-compatible adapter and transport

`providers/openai_compatible.py` adapts chat completion endpoints. Network access is dependency-injected; `UrllibHTTPClient` is created only when `enable_network=True`. Optional async networking uses the `async` extra.

## Startup model catalog refresh

`discovery.py` provides explicit provider model discovery. Gemini uses its native models endpoint with `X-Goog-Api-Key`; the remaining cloud providers use OpenAI-compatible `GET /models`. `create_router_from_env(..., enable_network=True, refresh_models_on_startup=True)` merges discovered chat-capable IDs before static fallback models for that process-local provider instance. Discovery is disabled by default, does not persist changes to source or the registry, and failures retain static defaults without blocking startup.

## Capability, health, and state

`capabilities.py` defines safe capability metadata. `RouterPolicy.task_type` and request metadata guide candidate scoring; unknown discovered models receive safe defaults.

The router records health by provider/model/key candidate. Quota and transient errors use cooldown/backoff. The default store is in-memory; callers may select JSON or SQLite state without persisting prompts, raw API keys, Authorization headers, raw provider responses, or evidence.

## Routing contract

`AIRouter.route()` returns an `AIResult` or raises `RouterError`. `route_outcome()` returns non-throwing `success`, `retry_later`, or `failed` outcomes for durable jobs. Sync, async, streaming fallback, state export, quota controls, and capability scoring are supported.

## Local live testing

The repository-local `API Key.txt` file is ignored by the exact `/API Key.txt` Git rule. `scripts/live_smoke.py` and `scripts/discover_models.py` use it only during an explicit live command and sanitize their output. It is a developer-local convention, not part of the library runtime API.

## Privacy boundary

The router is a general capacity layer. Applications own payload storage, domain validation, privacy classification, and secret management. The router owns provider/model/key selection, cooldowns, outcomes, and safe operational snapshots.
