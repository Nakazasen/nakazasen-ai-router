# Gate 13 — AI Gateway / Router Research

## Scope

This audit reviewed public documentation and summaries for LiteLLM Router/Proxy, Portkey Gateway, OpenRouter provider routing, Vercel AI SDK/Gateway, and adjacent health-check routing patterns. The goal is to learn features worth copying conceptually into Nakazasen AI Router without rewriting architecture or adding heavy dependencies.

## Source notes

- LiteLLM Router/Proxy: model groups, fallbacks, retry policy, load balancing strategies, health checks, cooldown and budgets.
- Portkey Gateway: JSON gateway configs, fallback chains, retry, caching, observability, budgets, rate/token limits.
- OpenRouter: provider routing controls (`provider.sort`, `order`, `only`, `ignore`), default provider failover, opt-in model fallback.
- Vercel AI SDK/Gateway: provider registry with `providerId:modelId`, gateway abstraction, middleware wrappers, observability/spend monitoring.
- Extra reference: LiteLLM health-check routing discussions because Nakazasen already has provider health state and cooldown concepts.

## Feature evaluation matrix

| Feature | Source learned from | Copy? | Reason | Proposed gate | Risk | Smallest MVP |
|---|---|---:|---|---|---|---|
| Provider fallback | LiteLLM, Portkey, OpenRouter | Yes | Already exists conceptually; improve trace and ordering rather than rewrite. | 14 | Over-retry can increase cost. | Keep current router but expose attempt trace and selection reason. |
| Model fallback inside provider | OpenRouter fallbacks, LiteLLM model groups | Yes | Gemini now has multi-model catalog; model-level fallback is natural. | 14 | Bad model can loop or mask quality issues. | Try next model only on classified transient/model_unavailable errors. |
| Retry with backoff | LiteLLM, Portkey | Yes, small | Useful for 5xx/transport/timeouts. | 15 | Latency spikes and double billing if unsafe. | One retry for retryable transport/5xx with capped sleep and opt-out. |
| Circuit breaker | LiteLLM health/cooldown | Later | Valuable but needs persistent health semantics. | 16 | Incorrect breaker can blackhole good providers. | In-memory breaker based on failure streak and cooldown until. |
| Quota cooldown | LiteLLM cooldown, current router | Yes | Repo already classifies quota/rate limit. | 14 | Over-cooling temporary 429s. | Add scoreboard field for quota cooldown until. |
| Last known good model | Production gateway pattern | Yes | Simple, high leverage for Gemini model catalog. | 14 | Stale preference can hide better models. | Persist/load optional JSON cache keyed provider -> model. |
| Latency score | LiteLLM latency routing, OpenRouter sort latency | Yes | Helps choose among live PASS models. | 14 | Noisy with few samples. | Track last latency and moving average from smoke/router attempts. |
| Success rate | Portkey analytics, LiteLLM health | Yes | Better than static order. | 14 | Needs sample count to avoid false confidence. | In-memory counters: success, failure, streak. |
| Failure streak | LiteLLM health cache | Yes | Already aligned with cooldown. | 14 | Needs reset policy. | Increment on fail, reset on success, show in CLI. |
| Quota status | LiteLLM budget/cooldown | Yes | Prevent repeat calls to quota-exhausted provider. | 14 | Quota can recover quickly. | Store last quota error and cooldown reason. |
| Model/provider health cache | LiteLLM DeploymentHealthCache | Yes | Foundational for ranking. | 14 | Persistence format churn. | JSON export/import; default in-memory. |
| Health scoreboard CLI | LiteLLM admin/observability, Portkey analytics | Yes | Most useful immediate operator tool. | 14 | Might imply authority from sparse data. | `scripts/health_scoreboard.py` reads cache or smoke result JSON. |
| Cost estimate | LiteLLM budgets, Vercel spend monitoring | Later | Important but requires pricing metadata. | 17 | Wrong pricing is worse than none. | Registry optional price fields, no enforcement. |
| Token accounting | Portkey/Vercel observability | Later | Useful if provider returns usage. | 17 | Providers differ. | Normalize usage from responses when present. |
| Budget cap | LiteLLM/Portkey | Not now | Bigger product feature, needs identity/project scopes. | Later | False sense of spend safety. | Design only after token/cost accounting. |
| Free-first policy | OpenRouter price sort, current live_free_first | Yes | Already implemented provider order; can mature. | 15 | Free models can be slow/low quality. | Strategy that sorts by cost tier then health. |
| Avoid expensive by default | LiteLLM budgets, OpenRouter price | Yes, design | Fits user preference for practical/free-first routing. | 15 | Price metadata stale. | Mark models `cost_tier`: free/low/standard/high. |
| `providerId:modelId` | Vercel AI SDK registry | Yes | Clean public selection syntax. | 14 | Backward compatibility with provider-only config. | Parser for `gemini:gemini-3.5-flash`. |
| Model alias | Vercel registry, OpenRouter model names | Yes | Useful for stable app config. | 14 | Alias drift. | `fast`, `free`, `gemini-default` aliases in registry. |
| Model family | Registry/provider patterns | Yes | Helps policy select flash/pro/robotics/gemma. | 15 | Taxonomy churn. | Optional string tags on ProviderProfile/model metadata. |
| Discovered vs enabled model | Current Gate 11 discovery, gateway catalogs | Already yes | Preserve safety: discovery does not enable. | 14 | Docs can become stale. | Candidate workflow doc + test that enabled list is explicit. |
| Candidate model workflow | Current Gate 11/12 | Yes | The project now needs a repeatable workflow. | 14 | Manual process overhead. | `docs/model_candidates.md` or report format. |
| Request id | Portkey tracing, Vercel middleware | Yes | Low-risk observability. | 14 | None if sanitized. | Generate UUID per route request and include in metadata. |
| Attempt trace | Portkey tracing, existing metadata | Yes | Already present but should be standardized. | 14 | Could leak prompt/key if careless. | Strict sanitized schema: provider/model/error/latency. |
| Sanitized error | Portkey observability, current scripts | Yes | Security critical. | 14 | Over-sanitizing hides debugging clues. | Central `sanitize_error()` helper. |
| Latency in result metadata | LiteLLM/OpenRouter latency sort | Yes | Enables health ranking. | 14 | Timing noise. | Add per-attempt elapsed_ms. |
| Provider/model chosen | Vercel middleware/Portkey traces | Yes | User needs explainability. | 14 | None. | Add chosen provider/model to metadata. |
| Why selected | OpenRouter routing controls | Yes | Key for debugging policy. | 14 | Verbose output. | `selection_reason`: default_order, last_known_good, health_score. |
| local_only hard block | Privacy gateway patterns | Yes, design now | Critical for future AIOS integration. | 14 design, 16 code | Incorrect classification can block useful calls. | Policy object that can deny cloud providers before routing. |
| confidential hard block | Privacy gateway patterns | Yes, design now | Prevent raw sensitive evidence leakage. | 14 design, 16 code | Needs caller metadata discipline. | Define request metadata fields and deny behavior. |
| machine_only explicit consent | Privacy policy adapter | Yes, design now | Matches AIOS safety needs without integration now. | 14 design | UX ambiguity. | Spec only: require `allow_cloud=True`. |
| cloud-safe prompt metadata | Privacy adapters | Yes, design now | Enables future safe routing. | 14 design | Metadata can be missing. | Add proposed metadata schema in docs. |
| No raw evidence leakage | Portkey sanitized logs, privacy rules | Yes | Must-have for logs/traces. | 14 | Hard to enforce across app. | Ensure traces never store prompt/body by default. |
| Semantic cache | Portkey | No for now | Heavy, privacy-sensitive, needs embeddings. | Later/never | Leaks sensitive prompts; adds deps. | Skip. |
| Full proxy server | LiteLLM/Portkey | No for now | Out of scope; library-first repo. | Later | Big architecture rewrite. | Skip. |
| Distributed Redis health cache | LiteLLM | No for now | Too heavy for current package. | Later | Dependency/ops burden. | Local JSON/in-memory only. |
| Full budget hierarchy org/team/key | LiteLLM/Portkey | No for now | Product-layer concern. | Later | Complexity explosion. | Defer. |

## Recommended Gate 14 scope: choose only 5

1. Health scoreboard.
2. Last known good model.
3. Model ranking from live smoke results.
4. Provider/model alias registry.
5. AIOS privacy policy adapter design.

## Features not recommended for immediate implementation

- Semantic cache: useful but privacy-sensitive and dependency-heavy.
- Full proxy/gateway server: would rewrite architecture.
- Distributed health cache/Redis: operational complexity is premature.
- Full cost/budget enforcement: needs token accounting, pricing data, and identity scopes.
- Complex load balancing (`least-busy`, throughput routing): needs concurrency metrics and production traffic.

## Key design principles for Nakazasen

- Stay library-first and mock-first.
- Keep provider calls opt-in.
- Separate discovered models from enabled runtime models.
- Prefer small, inspectable JSON state over databases or Redis.
- Never store raw prompts, API keys, Authorization headers, or provider raw responses in traces.
