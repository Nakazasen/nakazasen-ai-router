from datetime import date

from nakazasen_ai_router import (
    AIRouter,
    AIRequest,
    AIResult,
    FreeTierCatalog,
    FreeTierPlan,
    ModelCapability,
    ProviderBase,
    ProviderCandidate,
    RouterPolicy,
    RoutingScore,
    ScoreWeights,
    calculate_free_tier_budget,
)


TODAY = date(2026, 7, 24)


def plan(provider, pool, tokens, **kwargs):
    return FreeTierPlan(
        provider,
        pool,
        recurring_tokens=tokens,
        source_url="https://example.test/source",
        verified_at="2026-07-23",
        confidence="high",
        status="verified",
        **kwargs,
    )


def test_shared_pool_is_counted_once_and_uses_conservative_allowance():
    budget = calculate_free_tier_budget(
        [plan("a", "shared", 1000), plan("b", "shared", 1200)],
        usage_by_pool={"shared": 250},
        as_of=TODAY,
    )
    assert budget.audited_recurring_tokens_month == 1000
    assert budget.used_tokens == 250
    assert budget.remaining_tokens == 750
    assert budget.audited_pools == ("shared",)


def test_signup_unlimited_unknown_and_stale_do_not_inflate_headline():
    plans = [
        plan("one", "one", 100, signup_credit_tokens=50),
        plan("local", "local", None, unlimited=True),
        FreeTierPlan("unknown", "unknown", status="uncertain"),
        FreeTierPlan("stale", "stale", recurring_tokens=900, source_url="https://example.test", verified_at="2020-01-01", confidence="high", status="verified"),
    ]
    budget = calculate_free_tier_budget(plans, as_of=TODAY)
    assert budget.audited_recurring_tokens_month == 100
    assert budget.one_time_signup_tokens == 50
    assert budget.unlimited_or_uncountable_pools == ("local",)
    assert set(budget.excluded_or_stale_pools) == {"stale", "unknown"}


def test_card_or_terms_flagged_plan_is_not_routing_eligible():
    assert plan("card", "card", 100, requires_card_or_topup=True).is_routing_eligible(as_of=TODAY) is False
    assert plan("terms", "terms", 100, terms_warning="review terms").is_routing_eligible(as_of=TODAY) is False


def test_shared_pool_routing_headroom_uses_conservative_allowance():
    catalog = FreeTierCatalog([plan("a", "shared", 1000), plan("b", "shared", 1200)])
    assert catalog.routing_headroom("b", usage_by_pool={"shared": 750}, as_of=TODAY) == 0.25


def test_routing_dataclasses_preserve_v030_positional_construction():
    weights = ScoreWeights(0.35, 0.20, 0.15, 0.10, 0.15, 0.05)
    assert weights.priority == 0.05
    assert weights.free_tier == 0.0

    score = RoutingScore(1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, "balanced")
    assert score.priority == 0.4
    assert score.mode == "balanced"
    assert score.free_tier == 0.0


class Provider(ProviderBase):
    def __init__(self, name):
        super().__init__(name, is_cloud=True)
        self.calls = 0

    def iter_candidates(self):
        return [ProviderCandidate(self, priority=0, model="m")]

    def generate(self, request, candidate=None):
        self.calls += 1
        return AIResult("ok", self.name)


def test_free_first_signal_prefers_audited_pool_only_in_opt_in_modes():
    free = Provider("free")
    paid = Provider("paid")
    catalog = FreeTierCatalog([plan("free", "free-pool", 1000)])
    overrides = {
        ("free", "m"): ModelCapability("free", "m", cost_tier="standard"),
        ("paid", "m"): ModelCapability("paid", "m", cost_tier="standard"),
    }
    balanced = AIRouter([paid, free], policy=RouterPolicy(capability_overrides=overrides), free_tier_catalog=catalog)
    assert balanced.route(AIRequest("x")).provider_name == "paid"

    router = AIRouter([paid, free], policy=RouterPolicy(routing_mode="cheap", capability_overrides=overrides), free_tier_catalog=catalog)
    assert router.route(AIRequest("x")).provider_name == "free"

    restricted = AIRouter([free, paid], policy=RouterPolicy(routing_mode="cheap", allowed_providers=("paid",), capability_overrides=overrides), free_tier_catalog=catalog)
    assert restricted.route(AIRequest("x")).provider_name == "paid"
    assert restricted.free_tier_budget().usage_scope == "estimated_local"


def test_router_records_local_monthly_usage_without_quota_profile():
    provider = Provider("free")
    provider.generate = lambda request, candidate=None: AIResult(
        "ok",
        provider.name,
        metadata={"token_usage": {"input_tokens": 4, "output_tokens": 2, "total_tokens": 6}},
    )
    catalog = FreeTierCatalog([plan("free", "free-pool", 1000)])
    router = AIRouter([provider], free_tier_catalog=catalog)

    router.route(AIRequest("x", metadata={"estimated_total_tokens": 99}))

    budget = router.free_tier_budget()
    assert budget.used_tokens == 6
    assert budget.remaining_tokens == 994
