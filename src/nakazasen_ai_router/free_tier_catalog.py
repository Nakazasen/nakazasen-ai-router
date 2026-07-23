"""Conservative free-tier catalog for providers supported by Nakazasen."""

from __future__ import annotations

from .free_tiers import FreeTierCatalog, FreeTierPlan

# These entries document availability, but deliberately avoid inventing monthly
# token totals where providers publish dynamic model/account rate limits instead.
DEFAULT_FREE_TIER_CATALOG = FreeTierCatalog(
    (
        FreeTierPlan(
            "gemini",
            "google-ai-studio-free",
            recurring_tokens=None,
            unlimited=False,
            source_url="https://ai.google.dev/gemini-api/docs/rate-limits",
            verified_at="2026-07-23",
            confidence="high",
            status="verified",
            notes="Free-tier limits vary by model and project; no fixed monthly token allowance is claimed.",
        ),
        FreeTierPlan(
            "openrouter",
            "openrouter-free-models",
            models=("meta-llama/llama-3.3-70b-instruct:free",),
            recurring_tokens=None,
            source_url="https://openrouter.ai/docs/features/usage-limits",
            verified_at="2026-07-23",
            confidence="high",
            status="verified",
            notes="Free-model request limits are dynamic and are not converted into a 24/7 token headline.",
        ),
        FreeTierPlan(
            "groq",
            "groq-free-plan",
            recurring_tokens=None,
            source_url="https://console.groq.com/docs/rate-limits",
            verified_at="2026-07-23",
            confidence="high",
            status="verified",
            notes="Rate limits vary by model; no fixed monthly token allowance is claimed.",
        ),
        FreeTierPlan(
            "nvidia_nim",
            "nvidia-api-catalog",
            recurring_tokens=None,
            source_url="https://build.nvidia.com/",
            verified_at="2026-07-23",
            confidence="medium",
            status="verified",
            notes="Catalog access is represented separately from a recurring monthly token entitlement.",
        ),
        FreeTierPlan(
            "mistral",
            "mistral-experiment-plan",
            recurring_tokens=None,
            source_url="https://docs.mistral.ai/deployment/laplateforme/tier/",
            verified_at="2026-07-23",
            confidence="medium",
            status="verified",
            notes="Experiment-plan limits are not advertised here as a fixed monthly token grant.",
        ),
        FreeTierPlan(
            "deepseek",
            "deepseek-account",
            recurring_tokens=None,
            source_url="https://api-docs.deepseek.com/quick_start/pricing",
            verified_at="2026-07-23",
            confidence="medium",
            status="excluded",
            notes="No recurring free monthly allowance is asserted.",
        ),
        FreeTierPlan(
            "chatanywhere",
            "chatanywhere-community",
            recurring_tokens=None,
            source_url="https://github.com/chatanywhere/GPT_API_free",
            verified_at="2026-07-23",
            confidence="low",
            status="uncertain",
            terms_warning="Third-party community service; review its terms before use.",
        ),
        FreeTierPlan(
            "local_openai_compatible",
            "local-compute",
            recurring_tokens=None,
            unlimited=True,
            requires_account=False,
            source_url="https://github.com/Nakazasen/nakazasen-ai-router",
            verified_at="2026-07-23",
            confidence="high",
            status="verified",
            notes="No provider token charge; local compute and electricity still have cost.",
        ),
    )
)