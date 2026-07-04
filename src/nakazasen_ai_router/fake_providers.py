"""Fake providers used by tests only.

These providers never call external AI services.
"""

from __future__ import annotations

from .core import AIRequest, AIResult, ProviderAuthError, ProviderBase, ProviderCandidate, ProviderQuotaError, ProviderTimeoutError


class FakeProvider(ProviderBase):
    def __init__(self, name: str, *, mode: str, is_cloud: bool = False, candidates: list[ProviderCandidate] | None = None) -> None:
        super().__init__(name, is_cloud=is_cloud)
        self.mode = mode
        self.calls = 0
        self._candidates = candidates

    def iter_candidates(self) -> list[ProviderCandidate]:
        return self._candidates or super().iter_candidates()

    def generate(self, request: AIRequest, candidate: ProviderCandidate | None = None) -> AIResult:
        self.calls += 1
        if self.mode == "success":
            return AIResult(text=f"fake response from {self.name}", provider_name=self.name)
        if self.mode == "quota":
            raise ProviderQuotaError("fake quota exhausted")
        if self.mode == "auth":
            raise ProviderAuthError("fake auth rejected")
        if self.mode == "timeout":
            raise ProviderTimeoutError("fake timeout")
        raise ValueError(f"Unknown fake provider mode: {self.mode}")


def provider_success(name: str = "provider_success", *, is_cloud: bool = False) -> FakeProvider:
    return FakeProvider(name, mode="success", is_cloud=is_cloud)


def provider_fail_quota(name: str = "provider_fail_quota", *, is_cloud: bool = False) -> FakeProvider:
    return FakeProvider(name, mode="quota", is_cloud=is_cloud)


def provider_fail_auth(name: str = "provider_fail_auth", *, is_cloud: bool = False) -> FakeProvider:
    return FakeProvider(name, mode="auth", is_cloud=is_cloud)


def provider_timeout(name: str = "provider_timeout", *, is_cloud: bool = False) -> FakeProvider:
    return FakeProvider(name, mode="timeout", is_cloud=is_cloud)
