# Changelog

## Unreleased

## 0.3.0 - 2026-07-23

### Added

- Explainable weighted auto-routing with built-in `balanced`, `fast`, `cheap`, `quality`, and `quota` mode packs and optional custom weights.
- Thread-safe, process-local shared quota pools, named fixed windows, atomic reservations, headroom scoring, and estimated-to-actual token reconciliation.
- Normalized provider token usage, catalog provenance fields, and conservative cost estimates that remain unknown when verified inputs are missing.
- Bilingual release/packaging runbooks, an offline release consistency checker, and expanded human/AI architecture handoff documentation.

### Changed

- Sync and async routing now apply quota gates immediately before provider invocation and attach safe routing, provenance, and cost metadata to successful results.
- OpenAI-compatible provider responses retain normalized usage only, not raw provider response data.
- Public SDK exports now include routing mode/score types, quota windows, and usage/cost helpers.

### Security

- Quota snapshots explicitly report `process_local` scope and route attempts expose only coarse quota reasons.
- Accounting and provenance metadata exclude raw keys, Authorization headers, prompts, and raw provider payloads.

### Limitations

- Shared quota pools are not distributed or multi-process coordination; profiles in one pool should use compatible policies.
- Flexible quota windows are fixed windows rather than rolling/sliding windows.

## 0.2.3 - 2026-07-22

### Added

- Opt-in startup provider-model refresh for Gemini and OpenAI-compatible `GET /models` catalogs.
- Safe process-local merge of discovered chat models before static fallback models.
- Repository-local ignored `API Key.txt` default for explicit live smoke and discovery scripts.
- Host-application API key injection guidance using environment variables, private `env` mappings, and secret managers.

### Changed

- Gemini and DeepSeek registry defaults, aliases, capability metadata, and regression tests now use current supported model identifiers.
- Gemini catalog discovery sends the key in `X-Goog-Api-Key` request headers instead of query parameters.

### Security

- Added exact Git ignore protection for `/API Key.txt`, plus key-file and discovery regression coverage.

## 0.2.2 - 2026-07-05

- Add provider key onboarding docs, local-only key setup helpers, and install/update guidance.
- Add local path leak guard for machine-specific paths and key file names.

All notable changes to `nakazasen-ai-router` will be documented in this file.

This project follows pre-1.0 semantic versioning: public root exports are documented, but breaking changes may still happen before 1.0 and should be called out here.

## 0.2.1 - 2026-07-05

### Added

- General-purpose use-case index docs in English and Vietnamese.
- Generic worker integration recipes in English and Vietnamese.
- Multi-domain offline examples for summarization, JSON extraction, and content generation.
- Generic workload aliases such as `long_context`, `cheap_batch`, `structured_json`, `low_latency`, `premium_reasoning`, and `private_local`.
- Positioning audit script and tests to prevent translation-only narrative drift.
- Opt-in live provider conformance script and docs with sanitized leak checks.
- Generic segmentation/aggregation primitives, docs, tests, and offline segmented batch demo.
- Persistent generic SQLite job queue adapter, docs, tests, and offline worker demo.
- Metrics/observability snapshots with sanitized router/job queue JSON and CLI.
- Provider quota/capacity policy primitives, in-memory tracker, fallback sorting, docs, tests, and offline demo.
- SDK-first external integration hardening with wheel install smoke, full-stack SDK demo, and integration blueprints.
- Static local dashboard prototype with sample metrics, paste/upload JSON rendering, docs, and tests.

### Changed

- README and architecture docs now state that translation is one use case, not the core domain.


## 0.2.0 - 2026-07-05

### Added

- Multi-key provider routing with per `provider + model + key_id` state.
- `route_outcome()` and `aroute_outcome()` for durable job queues.
- Safe admin/dashboard state export through `export_state()`.
- JSON state store and SQLite state store.
- Native async routing path with optional `httpx` async transport extra.
- Task/capability based routing with `ModelCapability` and `RouterPolicy.task_type`.
- Budget guard using `estimated_input_tokens` and `estimated_output_tokens` metadata.
- Exponential retry/backoff controls with `Retry-After` minimum handling.
- Streaming foundation with `AIStreamChunk`, `stream()`, and `astream()`.
- Offline translation worker demo in `examples/translation_worker_demo.py`.
- Public API contract documentation in `docs/public_api.md`.
- Public API import tests.
- Package metadata suitable for sdist/wheel builds.

### Changed

- Provider routing now considers candidate health, key/model cooldowns, task capability score, and policy priority.
- Async APIs remain additive while sync APIs stay stable.
- README English documentation now matches the Vietnamese feature coverage.

### Security

- State stores, attempts, and dashboard exports avoid raw API keys, Authorization headers, prompts, and raw provider responses.
- Live provider calls remain explicit opt-in.
- Unit tests remain offline by default.

## 0.1.0 - Initial skeleton

### Added

- Initial provider router skeleton.
- OpenAI-compatible provider adapter foundation.
- Provider registry and mock-first tests.
- Gemini catalog/discovery and live smoke scripts.
