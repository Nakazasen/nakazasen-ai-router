# Gate 14.7 Code Quality and Repo Readiness Audit

## A. Executive decision

**PASS_READY_FOR_AIOS_DESIGN**

The repository is usable as a small Python library and is ready for the next gate: **AIOS_habbit integration design**.
It is not yet ready for direct production traffic or real AIOS runtime integration without Gate 14.8/15 hardening.

Reasoning:

- Current automated checks pass.
- Packaging and imports work.
- Default unit tests are offline and mock-first.
- Secret scan found no real key leak.
- Documentation encoding and docs quality audits pass.
- Core privacy posture is directionally correct: no network by default, sanitized attempt traces, and no raw prompt/key persistence in health cache.

However, several issues should be fixed before any AIOS real-work pilot:

- Public API does not export new Gate 14 modules.
- Router attempt budget semantics are ambiguous.
- Discovery places the Gemini API key in a query string URL internally.
- Scoreboard persistence is non-atomic and has no schema version.
- AIOS privacy enforcement is design-only, not implemented.

## B. Evidence

### Repo state

```text
git status -sb
## main...origin/main

git rev-parse HEAD
0d36668f1453b31cba88990044b023ec4c83e227

git branch --show-current
main

git log --oneline -8
0d36668 Add Vietnamese documentation and docs quality audit
9a0ee9c Add Vietnamese documentation for Nakazasen AI Router
6e488a6 Fix mojibake in public documentation
cf04b88 Add health scoreboard and model aliases
ff07f0c Document AI gateway research findings
de238a4 Enable additional Gemini live-pass models
fa44577 Clean Gemini catalog and add model discovery
a86ccd1 Test additional Gemini candidate models
```

### Verification

```text
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

### Packaging and import

```text
py -m pip install -e .
Successfully installed nakazasen-ai-router-0.1.0

py -c "from nakazasen_ai_router import AIRequest, create_router_from_env; print('IMPORT_OK')"
IMPORT_OK

py -c "import nakazasen_ai_router; print(nakazasen_ai_router.__all__)"
['create_router_from_env', 'create_live_free_first_router_from_env', 'AIRouter', 'AIRequest', 'AIResult', 'ProviderAuthError', 'ProviderBase', 'ProviderCandidate', 'ProviderError', 'ProviderHealth', 'ProviderQuotaError', 'ProviderTimeoutError', 'RouterError', 'RouterPolicy']
```

Note: pip emitted local environment warnings about unrelated invalid distributions `~` and `~bw-skill`; package install still succeeded.

### Secret scan

Commands completed successfully. Only safe matches were found inside `scripts/audit_docs_quality.py`, where the audit regex and forbidden key-file string are intentionally defined:

```text
scripts\audit_docs_quality.py: SECRET_RE = ...
scripts\audit_docs_quality.py: if "provider_keys.txt" in text:
```

No real API key, Authorization header, or real key-file path was found.

## C. Findings table

| ID | Severity | Area | Finding | Evidence | Recommended fix | Must fix before AIOS? |
|---|---|---|---|---|---|---|
| G14.7-001 | HIGH | AIOS privacy | AIOS privacy policy is only documented; router does not enforce metadata labels yet. | `docs/design/AIOS_PRIVACY_POLICY_ADAPTER.md`; no runtime privacy evaluator in `core.py`. | Gate 15: add explicit privacy decision layer and tests for `local_only`, `confidential`, `unknown`, `machine_only`, `cloud_safe`, and `public`. | yes |
| G14.7-002 | MEDIUM | Public API | New modules are not exported through `nakazasen_ai_router.__all__`. | `__all__` excludes `HealthScoreboard`, `ModelHealth`, `parse_model_ref`, `ModelRef`, discovery types. | Decide public surface and export stable classes/functions or document module-level imports. | no |
| G14.7-003 | MEDIUM | Router core | `max_attempts` applies per provider candidate list, not globally. With many providers/models, total attempts can exceed user expectation. | `AIRouter.route` slices `self._candidate_list(provider, base_candidate)[:max_attempts]` inside each provider loop. | Rename to `max_attempts_per_provider` or implement global attempt budget. | before real pilot |
| G14.7-004 | MEDIUM | Router/model fallback | Model fallback exists through provider `iter_candidates`, but after a failed attempt the provider can enter cooldown, which may skip remaining models for transient/quota errors. | `provider.health.is_available()` is checked before each candidate; `_mark_failure` can set cooldown. | Clarify desired behavior and add tests for multi-model fallback under 400/404/429/5xx. | before real pilot |
| G14.7-005 | MEDIUM | Discovery security | Gemini discovery puts API key in URL query string. It is not logged by current scripts, but URLs are inherently easier to leak through exceptions/proxies/debugging. | `discovery.py` builds `...?key=<api_key>`. | Keep output sanitized; consider accepting provider API requirement as known risk or adding stricter exception redaction. | before live-heavy discovery |
| G14.7-006 | MEDIUM | Scoreboard persistence | Health cache writes are not atomic and schema has no version field. | `HealthScoreboard.save_json` writes JSON directly; `to_dict` returns only `models`. | Add schema version and atomic write via temp file + replace. | before shared/runtime use |
| G14.7-007 | MEDIUM | Error sanitization | Error messages are sanitized only by sensitive key names; raw provider error strings may still include unexpected sensitive fragments if provider returns them in text. | `_safe_error_message` wraps raw string under key `message`, which is not redacted. | Add conservative truncation/redaction patterns for bearer tokens, key-looking strings, URLs with key query params. | before AIOS runtime |
| G14.7-008 | LOW | Packaging metadata | `pyproject.toml` description is ASCII Vietnamese without accents and says “chua goi AI that”, now stale because optional live transport exists. | `pyproject.toml` line 8. | Update metadata description in a docs/packaging cleanup gate. | no |
| G14.7-009 | LOW | Git hygiene | `.gitignore` does not ignore `local_cases/`, `.ai/`, or common local health cache files. | `.gitignore` contains Python basics only. | Add local runtime/doc scratch ignores. | no |
| G14.7-010 | LOW | Scripts | `live_smoke --provider all` can return 0 if all providers SKIP due to missing keys. This is acceptable for safe smoke behavior but may surprise CI users. | `return 0 if any_pass or not any_fail else 2`. | Add `--require-pass` if CI wants strict live validation. | no |
| G14.7-011 | LOW | Aliases | Alias parser accepts any model string containing `-` or `/`, even for unknown providers. | `parse_model_ref` line accepting hyphen/slash model refs. | Decide whether free-form model ids are intended; add stricter provider validation if not. | no |
| G14.7-012 | LOW | Health ranking | `rank_models` demotes quota-like errors permanently until a success clears status, even if cooldown expires. | `quota_like = entry.last_error_type in ...` bucket 3 regardless of `cooldown_until`. | Consider time-decayed quota penalty. | no |

## D. Missing tests

Important missing or under-specified tests:

1. Runtime privacy policy enforcement tests for AIOS labels:
   - `local_only`
   - `confidential`
   - `unknown`
   - `machine_only` with and without `allow_cloud=True`
   - `cloud_safe`
   - `public`

2. Global vs per-provider attempt-budget tests:
   - Multiple providers, multiple models, `max_attempts=1`.
   - Clear expected semantics.

3. Multi-model fallback tests after specific failures:
   - 400 invalid model.
   - 404 model not found.
   - 429 quota/rate limit.
   - 5xx provider error.
   - timeout/transport error.

4. Sanitization hardening tests:
   - Provider error message containing a bearer token.
   - URL containing `?key=...`.
   - Nested metadata lists containing sensitive keys.

5. Discovery hardening tests:
   - Network error from discovery endpoint.
   - Malformed JSON response.
   - URL/key not printed on exception.

6. Scoreboard persistence tests:
   - Corrupt JSON file handling.
   - Schema version migration/future compatibility.
   - Atomic write behavior.

7. Script behavior tests:
   - `live_smoke --provider all` with all SKIP.
   - `health_scoreboard.py` with missing health cache file.
   - `discover_models.py` API failure path.

8. Packaging/public API tests:
   - Assert intended `__all__` exports after deciding what should be public.

## E. Integration readiness

**Ready for AIOS_habbit integration design:** yes.

Reasons:

- Repo is installable and importable.
- Default behavior is offline and mock-first.
- Live provider calls are opt-in.
- Docs are now clean and bilingual enough for human review.
- Existing router already has a policy object where privacy enforcement can be designed cleanly.
- Health cache and traces are intended to store metadata only.

**Ready for AIOS_habbit implementation or real-work pilot:** not yet.

Reasons:

- Privacy labels are not enforced at runtime beyond `RouterPolicy.local_only`.
- Attempt semantics and multi-model fallback behavior need clarification.
- Discovery and error sanitization need additional hardening before heavy live use.
- Health cache needs versioning/atomic persistence before shared use.

## F. Gate 14.8 fix plan

Recommended Gate 14.8 scope before Gate 15 implementation work:

1. Define public API surface.
   - Export or explicitly document `HealthScoreboard`, `ModelHealth`, `parse_model_ref`, `ModelRef`, and discovery helpers.

2. Clarify attempt semantics.
   - Rename or rework `max_attempts`.
   - Add tests for multi-provider and multi-model cases.

3. Harden sanitization.
   - Redact bearer-token-like strings.
   - Redact query params named `key`, `api_key`, `token`.
   - Avoid raw provider message persistence in health state where possible.

4. Harden scoreboard persistence.
   - Add `schema_version`.
   - Add atomic write.
   - Handle corrupt JSON safely.

5. Harden discovery error handling.
   - Wrap network/API errors in sanitized exceptions or CLI messages.
   - Ensure no discovery URL containing key can be printed.

6. Update repo hygiene.
   - Add `.gitignore` entries for `local_cases/`, `.ai/`, and local health cache files.

7. Add missing tests listed above where practical.

## Final answer

**PASS_READY_FOR_AIOS_DESIGN**

The repo is usable for library development and controlled live smoke workflows. It is ready to proceed to AIOS_habbit integration design. It should not proceed directly to real AIOS runtime integration or real-work pilot until the Gate 14.8 hardening items are resolved.
