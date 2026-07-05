"""Nakazasen AI Router public API."""

from .capabilities import ModelCapability, capability_for, score_candidate_for_task
from .config import create_live_free_first_router_from_env, create_router_from_env
from .core import (
    AIRouteOutcome,
    AIRouter,
    AIRequest,
    AIResult,
    AIStreamChunk,
    AttemptRecord,
    ProviderAuthError,
    ProviderBase,
    ProviderCandidate,
    ProviderError,
    ProviderHealth,
    ProviderQuotaError,
    ProviderTimeoutError,
    RouterError,
    RouterPolicy,
)
from .state import JsonStateStore, KeyModelState, MemoryStateStore
from .storage_sqlite import SQLiteStateStore

__all__ = [
    "create_router_from_env",
    "create_live_free_first_router_from_env",
    "AIRouteOutcome",
    "AIRouter",
    "AIRequest",
    "AIResult",
    "AIStreamChunk",
    "AttemptRecord",
    "ProviderAuthError",
    "ProviderBase",
    "ProviderCandidate",
    "ProviderError",
    "ProviderHealth",
    "ProviderQuotaError",
    "ProviderTimeoutError",
    "RouterError",
    "RouterPolicy",
    "JsonStateStore",
    "KeyModelState",
    "MemoryStateStore",
    "SQLiteStateStore",
    "ModelCapability",
    "capability_for",
    "score_candidate_for_task",
]
