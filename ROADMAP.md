# Roadmap

## Current status

Nakazasen AI Router 0.3.0 has completed the focused capacity-layer upgrade:

- Core sync/async routing and provider/model/key fallback.
- Explainable weighted routing with balanced, fast, cheap, quality, and quota mode packs.
- Thread-safe, process-local shared quota pools and named fixed windows.
- Normalized token usage, catalog provenance, and conservative cost accounting.
- OpenAI-compatible provider adapter and opt-in startup catalog discovery.
- Environment-driven provider registry, key pools, health/cooldown state, and durable outcomes.
- JSON/SQLite state, generic jobs, segmentation, metrics, and scoreboard foundations.
- Mock-first offline tests plus bounded opt-in live smoke tooling.
- Bilingual release runbooks and architecture handoff documentation for human and AI contributors.

## Next gates

### Gate 15 - AIOS_habbit integration design

Define the integration boundary before touching AIOS_habbit:

- Request metadata contract.
- Privacy labels and enforcement plan.
- Mock integration plan.
- Acceptance tests for local-only, cloud-safe, confidential, and unknown prompts.

### Gate 16 - AIOS_habbit MVP mock integration

Build a mock-first integration path with no real provider calls by default.

### Gate 17 - AIOS_habbit real-work pilot

Run a controlled real-work pilot after privacy and mock tests pass.

## Backlog

- translation_app integration.
- External atomic quota backend only when a multi-process/distributed deployment actually requires it.
- Verified provider pricing ingestion with explicit source/version/terms review.
- Optional proxy server only if an integration truly needs it.
