import pytest

from llm_providers.base import LLMProvider
from llm_providers.registry import PROVIDER_INFO, get_llm_provider


class TestLLMRegistry:
    def test_get_gemini_provider(self):
        provider = get_llm_provider("gemini")
        assert provider.name == "gemini"
        assert isinstance(provider, LLMProvider)

    def test_get_openai_provider(self):
        provider = get_llm_provider("openai")
        assert provider.name == "openai"

    def test_get_anthropic_provider(self):
        provider = get_llm_provider("anthropic")
        assert provider.name == "anthropic"

    def test_get_with_model(self):
        provider = get_llm_provider("gemini", "gemini-2.0-pro")
        assert provider.model == "gemini-2.0-pro"

    def test_get_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm_provider("nonexistent")

    def test_provider_info_structure(self):
        assert len(PROVIDER_INFO) == 3
        for info in PROVIDER_INFO:
            assert "name" in info
            assert "display_name" in info
            assert "models" in info
            assert len(info["models"]) >= 1

    def test_estimate_tokens(self):
        provider = get_llm_provider("gemini")
        tokens = provider.estimate_tokens("Hello world, this is a test.")
        assert tokens > 0
        assert isinstance(tokens, int)
