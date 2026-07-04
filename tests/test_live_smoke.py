"""Optional live smoke tests.

These tests are skipped unless RUN_LIVE_AI_TESTS=1. They never run in the
normal unit-test path and do not require real API keys by default.
"""

from __future__ import annotations

import os

import pytest

from nakazasen_ai_router import AIRequest, create_router_from_env


pytestmark = pytest.mark.skipif(os.getenv("RUN_LIVE_AI_TESTS") != "1", reason="live AI tests disabled")


def test_live_openrouter_smoke():
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY is not set")

    router = create_router_from_env(provider_names=("openrouter",), enable_network=True)
    result = router.route(AIRequest(prompt="Reply with OK."))

    assert result.text.strip()
