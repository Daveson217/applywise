from collections.abc import AsyncIterator

from .base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    name = "openai"
    models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

    async def generate(self, prompt: str, context: dict, **kwargs) -> LLMResponse:
        from django.conf import settings
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        messages = []
        if context.get("system"):
            messages.append({"role": "system", "content": context["system"]})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )

        return LLMResponse(
            text=response.choices[0].message.content or "",
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            model=self.model,
            provider=self.name,
        )

    async def stream(self, prompt: str, context: dict, **kwargs) -> AsyncIterator[str]:
        from django.conf import settings
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        messages = []
        if context.get("system"):
            messages.append({"role": "system", "content": context["system"]})
        messages.append({"role": "user", "content": prompt})

        stream = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
