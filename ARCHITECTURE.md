# Architecture

Nakazasen AI Router is a library-first Python router for selecting AI providers and models safely.

## Core

The core package exposes request/result types and a router that tries provider candidates in policy order.
The router is designed to be mock-first: unit tests do not call the internet.

## Provider registry

`registry.py` defines provider profiles such as Gemini, OpenRouter, Groq, DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral, and local OpenAI-compatible servers.
Each profile stores safe metadata: provider id, base URL, API key environment variable, default models, and notes.

## OpenAI-compatible adapter

`providers/openai_compatible.py` adapts OpenAI-style chat completions endpoints.
Network access is dependency-injected through an HTTP client so tests can use mocks.

## Optional transport

Real HTTP transport is optional and only used when callers enable network access.
The default test path does not require provider keys.

## Discovery

`discovery.py` supports opt-in provider model discovery, currently focused on Gemini.
Discovery lists provider models but does not automatically enable them in the runtime catalog.

## Capability catalog and task based routing

`capabilities.py` defines safe model capability metadata such as context window, output limit, cost tier, speed tier, quality tier, JSON support, streaming support, and recommended task types.

`RouterPolicy.task_type` and request metadata `task_type` let callers describe workload intent, for example `translation_longform` or `cheap_generation`. The router scores candidates with the capability catalog before falling back to priority order. Unknown models receive safe default capability metadata and do not fail routing.

## Budget guard and retry backoff

`RouterPolicy.max_estimated_input_tokens` and `RouterPolicy.max_estimated_output_tokens` let applications fail closed before any provider call when a job estimate exceeds configured limits. `route_outcome()` reports this as `status="failed"` and `error_type="budget_exceeded"`.

Transient and quota failures use exponential backoff based on per-key/model failure streaks. Provider `Retry-After` values are treated as minimum cooldowns, while `backoff_max_seconds` caps runaway delays.

## Streaming foundation and demo worker

`AIStreamChunk`, `AIRouter.stream(...)`, and `AIRouter.astream(...)` provide a streaming API foundation. Providers may implement `stream_generate` or `astream_generate`; otherwise the router falls back to a single sanitized full-result chunk.

`examples/translation_worker_demo.py` is an offline/mock-first long-running translation worker demo. It processes chapter files, uses `route_outcome()`, persists SQLite state, writes translated outputs, and exports a dashboard-safe summary without requiring API keys or live network calls.

## Health and state

`scoreboard.py` stores safe provider/model health metadata for live smoke and ranking helpers:

- success count
- failure count
- failure streak
- last status
- last error type
- latency
- timestamps
- cooldown time

`state.py` stores runtime routing state for provider/model/key candidates. The default store is in-memory. Callers can pass `state_path` to use a JSON-backed store for single-process durable cooldowns across restarts.

`storage_sqlite.py` provides `SQLiteStateStore` for multiple local workers/processes sharing the same router state. It uses SQLite WAL/busy-timeout settings and stores only current operational state, not prompts, raw API keys, Authorization headers, raw responses, or attempt logs.

The router records per-key/model success and failure state so one exhausted key does not automatically block every other key for the same provider. State files must not store prompts, API keys, Authorization headers, raw responses, or evidence.

## Route outcome and operations contract

`AIRouter.route(...)` remains the legacy success-or-raise API. `AIRouter.route_outcome(...)` is the non-throwing integration API for durable job queues. It returns `success`, `retry_later`, or `failed` plus safe structured attempts and `retry_after_seconds` when the caller should persist a job and resume later.

`AIRouter.aroute(...)` and `AIRouter.aroute_outcome(...)` provide async-friendly entry points. Providers with `agenerate(...)` are called through the native async path; sync-only providers fall back to a worker thread. The OpenAI-compatible adapter supports optional native async HTTP via injected async clients or the `nakazasen-ai-router[async]` extra.

`AIRouter.export_state(...)` returns a dashboard-safe snapshot with `summary` and `candidates`, suitable for app-level admin panels.

## Alias registry

`aliases.py` parses `provider:model` references and resolves friendly aliases such as `gemini:fast`, `gemini:lite`, and `gemini:gemma`.

## Privacy boundary

AIOS_habbit integration is not implemented yet.
The design is that AIOS assigns privacy labels and sanitizes prompts before calling the router.
The router will enforce metadata-based policy and must fail closed for unknown or confidential content.

## No network by default

Network calls require explicit opt-in through live scripts or router creation options.
Unit tests stay offline.
