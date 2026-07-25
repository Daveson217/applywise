from collections.abc import AsyncIterator

from .base import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    models = ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"]

    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.model = model

    async def generate(self, prompt: str, context: dict, **kwargs) -> LLMResponse:
        import anthropic
        from django.conf import settings

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        system = context.get("system", "")

        response = await client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 2048),
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        return LLMResponse(
            text=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=self.model,
            provider=self.name,
        )

    async def stream(self, prompt: str, context: dict, **kwargs) -> AsyncIterator[str]:
        import anthropic
        from django.conf import settings

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        system = context.get("system", "")

        async with client.messages.stream(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 2048),
            system=system,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
