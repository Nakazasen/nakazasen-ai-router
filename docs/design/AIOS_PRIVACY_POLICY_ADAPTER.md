# AIOS Privacy Policy Adapter Design

Gate 14 defines the policy boundary only. It does not integrate AIOS_habbit and does not inspect raw AIOS evidence.

## Responsibility split

- AIOS decides the privacy label and sanitizes prompts/evidence before calling Nakazasen AI Router.
- Nakazasen AI Router enforces safe routing from metadata and policy.
- The router should never receive raw confidential evidence, raw company documents, API keys, or Authorization headers.

## Policy labels

| Label | Cloud routing decision | Reason |
|---|---|---|
| `local_only` | Deny cloud | Caller explicitly requires local processing. |
| `confidential` | Deny cloud | Raw confidential data must not leave the machine. |
| `unknown` | Deny cloud | Unknown sensitivity should fail closed. |
| `machine_only` | Deny cloud unless `allow_cloud=True` | Needs explicit consent before cloud. |
| `cloud_safe` | Allow cloud | AIOS has sanitized the prompt for cloud. |
| `public` | Allow cloud | Public or non-sensitive content. |

## Required metadata proposal

```python
{
    "privacy_label": "cloud_safe",
    "allow_cloud": False,
    "sanitized_by": "aios",
    "contains_raw_evidence": False,
    "contains_confidential_files": False,
}
```

## Hard rules

- `local_only` denies cloud providers.
- `confidential` denies cloud providers.
- `unknown` denies cloud providers.
- `machine_only` requires explicit `allow_cloud=True`.
- `cloud_safe` and `public` may use cloud providers.
- Do not pass raw evidence to the router.
- Do not pass raw company docs to the router.
- Do not pass prompts containing confidential file contents to the router.
- Do not store raw prompts, raw responses, evidence, API keys, or headers in traces or health cache.

## Future implementation sketch

- Add `PrivacyDecision(allowed: bool, reason: str, require_local: bool)`.
- Add `evaluate_privacy(metadata, provider_is_cloud)`.
- Enforce before provider selection.
- Include only sanitized decision reason in attempt trace.
