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
        default_models=("gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash-preview", "gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-robotics-er-1.5-preview", "gemini-robotics-er-1.6-preview", "gemma-3-1b-it", "gemma-3-4b-it", "gemma-3-12b-it", "gemma-3-27b-it", "gemma-3n-e4b-it", "gemma-3n-e2b-it"),
        is_cloud=True,
        note="Gemini API qua endpoint OpenAI-compatible.",
    ),
    "openrouter": ProviderProfile(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env_var="OPENROUTER_API_KEY",
        default_models=("meta-llama/llama-3.3-70b-instruct:free",),
        is_cloud=True,
        note="OpenRouter gom nhi騾ｶ・ｻ邵ｲ繝ｻmodel OpenAI-compatible qua m騾ｶ・ｻ陷・ｲ endpoint.",
    ),
    "groq": ProviderProfile(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env_var="GROQ_API_KEY",
        default_models=("llama-3.1-8b-instant",),
        is_cloud=True,
        note="Groq ph繝ｻ繝ｻ・ｽ・ｹ h騾ｶ・ｻ繝ｻ・｣p t繝ｻ繝ｻ・ｽ・｡c v騾ｶ・ｻ繝ｻ・･ c髯ゑｽｯ繝ｻ・ｧn ph髯ゑｽｯ繝ｻ・｣n h騾ｶ・ｻ陞ｯ・ｬ nhanh.",
    ),
    "deepseek": ProviderProfile(
        name="deepseek",
        base_url="https://api.deepseek.com/v1",
        api_key_env_var="DEEPSEEK_API_KEY",
        default_models=("deepseek-chat",),
        is_cloud=True,
        note="DeepSeek OpenAI-compatible cho chat/code.",
    ),
    "nvidia_nim": ProviderProfile(
        name="nvidia_nim",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key_env_var="NVIDIA_NIM_API_KEY",
        default_models=("meta/llama-3.1-8b-instruct",),
        is_cloud=True,
        note="NVIDIA NIM cung c髯ゑｽｯ繝ｻ・･p nhi騾ｶ・ｻ邵ｲ繝ｻmodel inference qua API t繝ｻ繝ｻ・ｽ・ｰ繝ｻ繝ｻ・ｽ・｡ng th繝ｻ繝ｻ・ｽ・ｭch OpenAI.",
    ),
    "chatanywhere": ProviderProfile(
        name="chatanywhere",
        base_url="https://api.chatanywhere.tech/v1",
        api_key_env_var="CHATANYWHERE_API_KEY",
        default_models=("gpt-4o-mini",),
        is_cloud=True,
        note="ChatAnyWhere l繝ｻ繝ｻ・｣・ｰ endpoint OpenAI-compatible b繝ｻ繝ｻ・ｽ・ｪn th騾ｶ・ｻ繝ｻ・ｩ ba.",
    ),
    "mistral": ProviderProfile(
        name="mistral",
        base_url="https://api.mistral.ai/v1",
        api_key_env_var="MISTRAL_API_KEY",
        default_models=("mistral-small-latest",),
        is_cloud=True,
        note="Mistral API d繝ｻ繝ｻ・ｽ・ｹng 繝ｻ繝ｻ豌医・・ｰ騾ｶ・ｻ繝ｻ・｣c qua adapter OpenAI-compatible.",
    ),
    "local_openai_compatible": ProviderProfile(
        name="local_openai_compatible",
        base_url="http://localhost:8000/v1",
        api_key_env_var="LOCAL_OPENAI_COMPATIBLE_API_KEY",
        base_url_env_var="LOCAL_OPENAI_COMPATIBLE_BASE_URL",
        default_models=("local-model",),
        is_cloud=False,
        note="Server local t繝ｻ繝ｻ・ｽ・ｰ繝ｻ繝ｻ・ｽ・｡ng th繝ｻ繝ｻ・ｽ・ｭch OpenAI, c繝ｻ繝ｻ・ｽ・ｳ th騾ｶ・ｻ郢晢ｽｻd繝ｻ繝ｻ・ｽ・ｹng kh繝ｻ繝ｻ・ｽ・ｴng c髯ゑｽｯ繝ｻ・ｧn API key.",
    ),
}
