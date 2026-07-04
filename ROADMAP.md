# Roadmap

## Current status

Nakazasen AI Router is a small Python router with:

- Core routing and fallback.
- OpenAI-compatible provider adapter.
- Provider registry and environment config.
- Optional live smoke tests.
- Gemini support, curated runtime catalog, and discovery script.
- Health scoreboard and model aliases.
- AIOS privacy policy adapter design.

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
- Retry with capped backoff.
- Budget and cost metadata.
- Token accounting when providers return usage.
- Package release workflow.
- Optional proxy server only if an integration truly needs it.
