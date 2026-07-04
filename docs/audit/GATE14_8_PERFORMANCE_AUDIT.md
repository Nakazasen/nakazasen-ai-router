# Gate 14.8 Performance and Low-Spec Readiness Audit

## A. Executive decision

**PASS_READY_FOR_AIOS_DESIGN**

The router is fast enough for low-spec development machines and is suitable for **AIOS_habbit integration design**.
Measured offline overhead is very small: package import is about 100 ms, mock route calls are far below 1 ms, and scoreboard/discovery operations are comfortably below proposed thresholds.

This is not a production performance certification. It is an offline readiness audit. Real provider latency will dominate runtime behavior once live calls are enabled.

## B. Benchmark summary

Measured with `py scripts/benchmark_router.py` on the current Windows workstation. All benchmarks are offline, use mock providers/mock HTTP clients, and do not use API keys.

| Case | Measured | Threshold | Status | Notes |
|---|---:|---:|---|---|
| Import package | 100.526 ms | 500 ms | PASS | No heavy runtime dependency is imported. |
| create_router_from_env | 0.006 ms | 100 ms | PASS | Fake env + mock HTTP client. |
| create_router_from_env live_free_first | 0.014 ms | 100 ms | PASS | Strategy reorder is negligible. |
| Single mock route | 0.020 ms | 50 ms | PASS | One provider, one model. |
| 10-model mock route | 0.026 ms | 100 ms | PASS | Candidate list overhead is tiny. |
| Fallback many-provider route | 0.051 ms | 100 ms | PASS | One mock failure, then fallback success. |
| Scoreboard record 1,000 | 1.426 ms | n/a | PASS | Dict/dataclass only. |
| Scoreboard rank 10 | 0.009 ms | n/a | PASS | Negligible. |
| Scoreboard rank 100 | 0.095 ms | n/a | PASS | Negligible. |
| Scoreboard rank 1,000 | 0.673 ms | 300 ms | PASS | O(n log n), still tiny for 1,000 models. |
| Scoreboard save/load 1,000 | 14.611 ms | 500 ms | PASS | JSON file IO is acceptable. |
| Discovery parse 100 | 0.452 ms | n/a | PASS | Mock Gemini payload. |
| Discovery parse 1,000 | 4.688 ms | 500 ms | PASS | Pagination parser is fast. |
| audit_text_encoding | 86.741 ms | n/a | PASS | Repo-size scan is fast. |
| audit_docs_quality | 111.589 ms | n/a | PASS | Includes text audit. |

Full test suite measured separately:

```text
py -m pytest -q
72 passed, 1 skipped in 0.27s
```

Threshold: 10 s. Status: PASS.

## C. Low-spec readiness

### Can it run on weak machines?

Yes, for local routing logic, tests, docs checks, and offline workflows.

Reasons:

- No heavy dependencies in `pyproject.toml` runtime dependencies.
- Package import is around 100 ms.
- Router creation is near-zero cost.
- Mock routing overhead is far below network/provider latency.
- Scoreboard ranking and JSON cache operations are small even at 1,000 entries.
- Discovery parsing is fast; actual network calls, not parsing, would dominate.

### Where lag can appear

1. Real provider calls.
   - Network latency and provider latency will dominate; router overhead is not the bottleneck.

2. `live_smoke --test-all-models`.
   - It can call every configured model for a provider. With real APIs, this can be slow and quota-expensive.

3. Discovery.
   - Parser is fast, but live discovery can require multiple paginated HTTP requests.

4. Health cache if used per request with disk save/load.
   - Saving/loading 1,000 entries is still only about 15 ms here, but doing disk IO on every AIOS request is unnecessary overhead.

5. Logs during repeated failures.
   - Router logs a warning per failed provider attempt. This is fine normally, but can become noisy in tight loops or benchmarks.

### Heavy dependencies

None observed. Runtime dependencies are empty.

### Auto network calls

No. `create_router_from_env` does not call internet by default. Network transport requires explicit `enable_network=True` or an injected real client.

## D. Correctness/ranking audit

### Model ranking reliability

`HealthScoreboard.rank_models` is simple and fast. It prioritizes recent successes and demotes failure streaks, cooldown, and quota-like errors. This is acceptable as an MVP.

Risks:

- Sparse health data can over-prioritize a single lucky success.
- Quota-like errors are demoted even after cooldown expiry until a success clears the status.
- Ranking does not include cost, context size, capability, privacy label, or provider health.

### Fallback reliability

Fallback is fast and works at provider/candidate level, but behavior needs clarification before real AIOS runtime:

- `max_attempts` is per provider candidate list, not a global attempt budget.
- A provider cooldown after one failure can skip remaining models for that provider.
- Some model errors should probably advance to the next model without cooling down the entire provider.

### Last-known-good reliability

`last_known_good` returns the most recent successful model per provider. This is useful as a hint, not as an authoritative routing decision.

Risks:

- It ignores whether the model is still configured.
- It ignores cooldown/quota state.
- It does not check whether capability matches the current request.

### live_free_first strategy

The strategy is cheap and deterministic. It is suitable for live smoke/default ordering experiments, but it is not enough for production-grade routing by itself.

### Aliases

Aliases point to current Gemini runtime catalog entries and parse quickly. Risk remains that free-form model ids containing `-` or `/` are accepted without validating provider existence/capability.

### Discovery

Discovery remains opt-in and does not auto-enable new models. This is correct and safe for catalog hygiene.

## E. Findings

| ID | Severity | Area | Finding | Evidence | Fix recommendation | Must fix before AIOS? |
|---|---|---|---|---|---|---|
| G14.8-001 | MEDIUM | Live smoke | `--test-all-models` can create many sequential live API calls, causing slow runs/quota burn. | `scripts/live_smoke.py` loops over every configured model. | Add max-count, confirm flag, or rate-limit/backoff for live validation. | before live-heavy use |
| G14.8-002 | MEDIUM | Scoreboard/runtime IO | Health cache save/load is fast but should not happen on every AIOS request path. | Save/load 1,000 entries ~14.6 ms. | Keep scoreboard in memory during request handling; flush periodically or on session end. | before runtime integration |
| G14.8-003 | MEDIUM | Routing correctness | `max_attempts` semantics can produce more attempts than expected and cooldown can suppress model fallback. | Core audit from Gate 14.7 plus benchmark fallback path. | Clarify global vs per-provider attempts; test model-fallback behavior. | before real pilot |
| G14.8-004 | LOW | Logging overhead | Repeated failure paths log warnings per attempt; tight loops can produce noisy output. | Initial benchmark produced many warning lines until logger was suppressed. | Keep default logs reasonable; add benchmark/script suppression where appropriate. | no |
| G14.8-005 | LOW | Ranking data quality | Ranking is fast but based on limited health metrics. | `rank_models` uses status, failure streak, last success, cooldown/quota. | Add capability/cost/privacy and minimum sample handling later. | no |
| G14.8-006 | LOW | Discovery pagination | Parsing is fast, but live pagination can still be slow due to network, and no retry/backoff exists. | `discovery.py` loops by `nextPageToken`. | Add retry/backoff and clear timeout policy when live discovery becomes routine. | no |

No BLOCKER or HIGH performance finding was found.

## F. Gate 14.9 fix plan

Gate 14.9 is recommended but not mandatory before AIOS design.

Suggested scope:

1. Add script guardrails:
   - `live_smoke --max-models`.
   - Optional `--require-pass` for CI.
   - Clear warning when `--test-all-models` would call many models.

2. Clarify routing attempt semantics:
   - Rename `max_attempts` or add global budget.
   - Add tests for multi-provider and multi-model fallback.

3. Scoreboard runtime usage policy:
   - Keep in memory per session.
   - Add schema version and atomic write.
   - Do not save/load on every request.

4. Discovery live hardening:
   - Add retry/backoff.
   - Sanitize URL/key in errors.
   - Add max pages or timeout budget.

5. Ranking correctness:
   - Treat health score as hint, not hard override.
   - Include capability/privacy/cost once AIOS design defines metadata.

## Verification

```text
py scripts/benchmark_router.py
PASS

py scripts/audit_text_encoding.py
PASS

py scripts/audit_docs_quality.py
PASS

py -m pytest -q
72 passed, 1 skipped

py -m compileall src scripts
PASS

git diff --check
PASS
```

Secret scan found only safe matches in `scripts/audit_docs_quality.py`, where the audit regex and forbidden key-file marker are intentionally defined. No real secret or key path was found.

## Final answer

**PASS_READY_FOR_AIOS_DESIGN**

The repo is fast enough for low-spec local development and AIOS_habbit integration design. The next performance risk is not router overhead; it is live provider/network behavior and how often scripts or AIOS runtime choose to perform discovery, full-model smoke tests, or health-cache disk IO.
