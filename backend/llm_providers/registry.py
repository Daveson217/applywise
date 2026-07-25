from .anthropic_provider import AnthropicProvider
from .base import LLMProvider
from .gemini import GeminiProvider
from .openai_provider import OpenAIProvider

PROVIDERS = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

PROVIDER_INFO = [
    {
        "name": "gemini",
        "display_name": "Google Gemini",
        "models": GeminiProvider.models,
    },
    {
        "name": "openai",
        "display_name": "OpenAI",
        "models": OpenAIProvider.models,
    },
    {
        "name": "anthropic",
        "display_name": "Anthropic Claude",
        "models": AnthropicProvider.models,
    },
]


def get_llm_provider(provider_name: str, model_name: str | None = None) -> LLMProvider:
    provider_class = PROVIDERS.get(provider_name)
    if not provider_class:
        raise ValueError(f"Unknown LLM provider: {provider_name}")

    if model_name:
        return provider_class(model=model_name)
    return provider_class()
