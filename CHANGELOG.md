# Changelog

All notable changes to `nakazasen-ai-router` will be documented in this file.

This project follows pre-1.0 semantic versioning: public root exports are documented, but breaking changes may still happen before 1.0 and should be called out here.

## 0.2.1 - Unreleased

### Added

- General-purpose use-case index docs in English and Vietnamese.
- Generic worker integration recipes in English and Vietnamese.
- Multi-domain offline examples for summarization, JSON extraction, and content generation.
- Generic workload aliases such as `long_context`, `cheap_batch`, `structured_json`, `low_latency`, `premium_reasoning`, and `private_local`.
- Positioning audit script and tests to prevent translation-only narrative drift.
- Opt-in live provider conformance script and docs with sanitized leak checks.
- Generic segmentation/aggregation primitives, docs, tests, and offline segmented batch demo.

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
