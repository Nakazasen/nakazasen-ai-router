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
        default_models=("gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash-preview", "gemini-flash-latest", "gemini-robotics-er-1.6-preview"),
        is_cloud=True,
        note="Gemini API qua endpoint OpenAI-compatible.",
    ),
    "openrouter": ProviderProfile(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env_var="OPENROUTER_API_KEY",
        default_models=("meta-llama/llama-3.3-70b-instruct:free",),
        is_cloud=True,
        note="OpenRouter gom nhi鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬩搾ｽｵ繝ｻ・ｲ驛｢譎｢・ｽ・ｻmodel OpenAI-compatible qua m鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬮ｯ・ｷ・つ郢晢ｽｻ繝ｻ・ｲ endpoint.",
    ),
    "groq": ProviderProfile(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env_var="GROQ_API_KEY",
        default_models=("llama-3.1-8b-instant",),
        is_cloud=True,
        note="Groq ph驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｹ h鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｣p t驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｡c v鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・･ c鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｧn ph鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｣n h鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬮ｯ讖ｸ・ｽ・ｯ郢晢ｽｻ繝ｻ・ｬ nhanh.",
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
        note="NVIDIA NIM cung c鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・･p nhi鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬩搾ｽｵ繝ｻ・ｲ驛｢譎｢・ｽ・ｻmodel inference qua API t驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｰ驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｡ng th驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｭch OpenAI.",
    ),
    "chatanywhere": ProviderProfile(
        name="chatanywhere",
        base_url="https://api.chatanywhere.tech/v1",
        api_key_env_var="CHATANYWHERE_API_KEY",
        default_models=("gpt-4o-mini",),
        is_cloud=True,
        note="ChatAnyWhere l驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｣郢晢ｽｻ繝ｻ・ｰ endpoint OpenAI-compatible b驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｪn th鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｩ ba.",
    ),
    "mistral": ProviderProfile(
        name="mistral",
        base_url="https://api.mistral.ai/v1",
        api_key_env_var="MISTRAL_API_KEY",
        default_models=("mistral-small-latest",),
        is_cloud=True,
        note="Mistral API d驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｹng 驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ髮取ぁ迴ｾ郢晢ｽｻ郢晢ｽｻ繝ｻ・ｰ鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｣c qua adapter OpenAI-compatible.",
    ),
    "local_openai_compatible": ProviderProfile(
        name="local_openai_compatible",
        base_url="http://localhost:8000/v1",
        api_key_env_var="LOCAL_OPENAI_COMPATIBLE_API_KEY",
        base_url_env_var="LOCAL_OPENAI_COMPATIBLE_BASE_URL",
        default_models=("local-model",),
        is_cloud=False,
        note="Server local t驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｰ驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｡ng th驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｭch OpenAI, c驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｳ th鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻd驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｹng kh驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｴng c鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｧn API key.",
    ),
}
