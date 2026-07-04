# Gate 13 AI Gateway Research

## Scope

This audit reviewed LiteLLM Router/Proxy, Portkey Gateway, OpenRouter provider routing, Vercel AI SDK/Gateway, and related health routing patterns.
The goal was to identify small features worth copying conceptually into Nakazasen AI Router without rewriting the architecture or adding heavy dependencies.

## Sources reviewed

- LiteLLM Router and Proxy: fallbacks, retries, health checks, cooldown, routing strategies, and budgets.
- Portkey Gateway: fallback chains, retries, caching, observability, tracing, budgets, and rate limits.
- OpenRouter: provider routing, provider sort/order, provider allow/ignore lists, and model fallbacks.
- Vercel AI SDK and AI Gateway: provider registry, `providerId:modelId` references, middleware, observability, and spend monitoring.
- LiteLLM health-check routing discussions: useful because Nakazasen already tracks provider health.

## Feature evaluation

| Feature | Source learned from | Copy? | Reason | Proposed gate | Risk | Smallest MVP |
|---|---|---:|---|---|---|---|
| Provider fallback | LiteLLM, Portkey, OpenRouter | Yes | Already matches current router direction. | 14 | Cost from too many attempts. | Keep current behavior and expose safe trace. |
| Model fallback | OpenRouter, LiteLLM | Yes | Gemini now has multiple enabled models. | 14 | May hide quality issues. | Try next model only on safe failure classes. |
| Retry with backoff | LiteLLM, Portkey | Later | Useful for transient 5xx and timeouts. | 15 | Latency and double billing. | One capped retry for retryable failures. |
| Circuit breaker | LiteLLM | Later | Useful after health cache matures. | 16 | Can block healthy providers. | In-memory breaker and cooldown. |
| Quota cooldown | LiteLLM | Yes | Avoid repeated quota failures. | 14 | Quota can recover quickly. | Store cooldown metadata. |
| Last known good model | Gateway operations pattern | Yes | Simple and high value. | 14 | Can become stale. | JSON-backed safe health cache. |
| Latency score | LiteLLM, OpenRouter | Yes | Helps rank live models. | 14 | Noisy with small samples. | Track last latency. |
| Success rate and failure streak | Portkey, LiteLLM | Yes | Better than static order only. | 14 | Needs sample counts. | In-memory counters and JSON save/load. |
| Health scoreboard CLI | Portkey, LiteLLM | Yes | Operator-friendly and low risk. | 14 | Sparse data can mislead. | Print safe table from JSON cache. |
| Cost estimate | LiteLLM, Vercel | Later | Needs pricing metadata. | 17 | Wrong cost data is dangerous. | Optional cost tier metadata. |
| Token accounting | Portkey, Vercel | Later | Useful when provider returns usage. | 17 | Provider differences. | Normalize usage if present. |
| Budget cap | LiteLLM, Portkey | Not now | Needs identity and pricing layers. | Later | False sense of safety. | Defer. |
| Provider/model alias | Vercel AI SDK | Yes | Clean public model references. | 14 | Alias drift. | `provider:model` parser and tests. |
| Discovered vs enabled models | OpenRouter catalogs, current project | Yes | Prevents unsafe auto-enabling. | 14 | Documentation drift. | Keep explicit enabled catalog. |
| Request id and attempt trace | Portkey, Vercel | Yes | Improves debugging. | Later | Trace must be sanitized. | Safe metadata only. |
| Privacy policy adapter | Privacy gateway design | Yes | Needed before AIOS integration. | 14 design | Metadata must be reliable. | Design doc only. |
| Semantic cache | Portkey | No for now | Heavy and privacy-sensitive. | Later | Prompt leakage. | Skip. |
| Full proxy server | LiteLLM, Portkey | No for now | Would rewrite architecture. | Later | Scope explosion. | Skip. |
| Redis health cache | LiteLLM | No for now | Operationally heavy. | Later | Dependency burden. | Local JSON only. |

## Gate 14 recommendation

Gate 14 should implement only:

1. Health scoreboard.
2. Last known good model.
3. Model ranking from live smoke/router result metadata.
4. Provider/model alias registry.
5. AIOS privacy policy adapter design.

## Not recommended immediately

- Semantic cache.
- Full proxy server.
- Redis or distributed health cache.
- Full budget hierarchy.
- Complex least-busy or throughput routing.

## Principles

- Stay library-first and mock-first.
- Keep provider calls opt-in.
- Separate discovered models from enabled runtime models.
- Prefer small inspectable JSON over databases.
- Never store raw prompts, API keys, Authorization headers, raw provider responses, or evidence in traces.
