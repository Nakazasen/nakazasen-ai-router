"""Provider registry for OpenAI-compatible services."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderProfile:
    name: str
    base_url: str
    api_key_env_var: str
    default_models: tuple[str, ...]
    is_cloud: bool
    note: str
    base_url_env_var: str = ""


PROVIDER_REGISTRY: dict[str, ProviderProfile] = {
    "gemini": ProviderProfile(
        name="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        api_key_env_var="GEMINI_API_KEY",
        default_models=("gemini-3.5-flash", "gemini-flash-latest", "gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-3.1-flash-lite-preview", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash-preview", "gemini-robotics-er-1.6-preview", "gemma-4-31b-it"),
        is_cloud=True,
        note="Gemini API via the OpenAI-compatible endpoint.",
    ),
    "openrouter": ProviderProfile(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env_var="OPENROUTER_API_KEY",
        default_models=("meta-llama/llama-3.3-70b-instruct:free",),
        is_cloud=True,
        note="OpenRouter aggregates multiple OpenAI-compatible models through one endpoint.",
    ),
    "groq": ProviderProfile(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env_var="GROQ_API_KEY",
        default_models=("llama-3.1-8b-instant",),
        is_cloud=True,
        note="Groq provides fast OpenAI-compatible inference endpoints.",
    ),
    "deepseek": ProviderProfile(
        name="deepseek",
        base_url="https://api.deepseek.com/v1",
        api_key_env_var="DEEPSEEK_API_KEY",
        default_models=("deepseek-chat",),
        is_cloud=True,
        note="DeepSeek OpenAI-compatible endpoint for chat and code.",
    ),
    "nvidia_nim": ProviderProfile(
        name="nvidia_nim",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key_env_var="NVIDIA_NIM_API_KEY",
        default_models=("meta/llama-3.1-8b-instruct",),
        is_cloud=True,
        note="NVIDIA NIM provides OpenAI-compatible inference APIs.",
    ),
    "chatanywhere": ProviderProfile(
        name="chatanywhere",
        base_url="https://api.chatanywhere.tech/v1",
        api_key_env_var="CHATANYWHERE_API_KEY",
        default_models=("gpt-4o-mini",),
        is_cloud=True,
        note="ChatAnyWhere is a third-party OpenAI-compatible endpoint.",
    ),
    "mistral": ProviderProfile(
        name="mistral",
        base_url="https://api.mistral.ai/v1",
        api_key_env_var="MISTRAL_API_KEY",
        default_models=("mistral-small-latest",),
        is_cloud=True,
        note="Mistral API can be used through the OpenAI-compatible adapter.",
    ),
    "local_openai_compatible": ProviderProfile(
        name="local_openai_compatible",
        base_url="http://localhost:8000/v1",
        api_key_env_var="LOCAL_OPENAI_COMPATIBLE_API_KEY",
        base_url_env_var="LOCAL_OPENAI_COMPATIBLE_BASE_URL",
        default_models=("local-model",),
        is_cloud=False,
        note="Local OpenAI-compatible server. Can be used without a cloud provider key.",
    ),
}
