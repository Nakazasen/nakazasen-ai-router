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
        default_models=("gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash-preview", "gemini-flash-latest", "gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-robotics-er-1.5-preview", "gemini-robotics-er-1.6-preview", "gemma-3-1b-it", "gemma-3-4b-it", "gemma-3-12b-it", "gemma-3-27b-it", "gemma-3n-e4b-it", "gemma-3n-e2b-it"),
        is_cloud=True,
        note="Gemini API qua endpoint OpenAI-compatible.",
    ),
    "openrouter": ProviderProfile(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env_var="OPENROUTER_API_KEY",
        default_models=("meta-llama/llama-3.3-70b-instruct:free",),
        is_cloud=True,
        note="OpenRouter gom nhi鬨ｾ・ｶ繝ｻ・ｻ驍ｵ・ｲ郢晢ｽｻmodel OpenAI-compatible qua m鬨ｾ・ｶ繝ｻ・ｻ髯ｷﾂ繝ｻ・ｲ endpoint.",
    ),
    "groq": ProviderProfile(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env_var="GROQ_API_KEY",
        default_models=("llama-3.1-8b-instant",),
        is_cloud=True,
        note="Groq ph郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｹ h鬨ｾ・ｶ繝ｻ・ｻ郢晢ｽｻ繝ｻ・｣p t郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・｡c v鬨ｾ・ｶ繝ｻ・ｻ郢晢ｽｻ繝ｻ・･ c鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｧn ph鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・｣n h鬨ｾ・ｶ繝ｻ・ｻ髯橸ｽｯ繝ｻ・ｬ nhanh.",
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
        note="NVIDIA NIM cung c鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・･p nhi鬨ｾ・ｶ繝ｻ・ｻ驍ｵ・ｲ郢晢ｽｻmodel inference qua API t郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｰ郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・｡ng th郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｭch OpenAI.",
    ),
    "chatanywhere": ProviderProfile(
        name="chatanywhere",
        base_url="https://api.chatanywhere.tech/v1",
        api_key_env_var="CHATANYWHERE_API_KEY",
        default_models=("gpt-4o-mini",),
        is_cloud=True,
        note="ChatAnyWhere l郢晢ｽｻ郢晢ｽｻ繝ｻ・｣繝ｻ・ｰ endpoint OpenAI-compatible b郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｪn th鬨ｾ・ｶ繝ｻ・ｻ郢晢ｽｻ繝ｻ・ｩ ba.",
    ),
    "mistral": ProviderProfile(
        name="mistral",
        base_url="https://api.mistral.ai/v1",
        api_key_env_var="MISTRAL_API_KEY",
        default_models=("mistral-small-latest",),
        is_cloud=True,
        note="Mistral API d郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｹng 郢晢ｽｻ郢晢ｽｻ雎悟現繝ｻ繝ｻ・ｰ鬨ｾ・ｶ繝ｻ・ｻ郢晢ｽｻ繝ｻ・｣c qua adapter OpenAI-compatible.",
    ),
    "local_openai_compatible": ProviderProfile(
        name="local_openai_compatible",
        base_url="http://localhost:8000/v1",
        api_key_env_var="LOCAL_OPENAI_COMPATIBLE_API_KEY",
        base_url_env_var="LOCAL_OPENAI_COMPATIBLE_BASE_URL",
        default_models=("local-model",),
        is_cloud=False,
        note="Server local t郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｰ郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・｡ng th郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｭch OpenAI, c郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｳ th鬨ｾ・ｶ繝ｻ・ｻ驛｢譎｢・ｽ・ｻd郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｹng kh郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｴng c鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｧn API key.",
    ),
}
