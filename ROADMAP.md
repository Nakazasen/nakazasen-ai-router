# Roadmap

## Gate 14 proposal

1. Health scoreboard for provider/model status.
2. Last known good model cache.
3. Model ranking from live smoke results.
4. Provider/model alias registry with `providerId:modelId` parsing.
5. AIOS privacy policy adapter design, without AIOS integration.

## Later gates

- Gate 15: retry with capped backoff and cost/free-first policy metadata.
- Gate 16: circuit breaker and privacy enforcement hooks.
- Gate 17: token accounting and cost estimate metadata.
- Later: optional proxy server only if a real integration requires it.

## Gate 14 done scope

- Health scoreboard with safe JSON cache.
- Last known good model lookup.
- Model ranking from health/smoke metadata.
- Provider/model alias parser with `providerId:modelId` syntax.
- AIOS privacy policy adapter design without AIOS_habbit integration.

## Gate 15 proposal

AIOS_habbit integration design gate: define integration boundary, request metadata contract, privacy enforcement plan, and local/cloud routing acceptance tests before touching the external app.
