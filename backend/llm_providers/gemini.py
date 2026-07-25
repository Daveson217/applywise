from collections.abc import AsyncIterator

from .base import LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    name = "gemini"
    models = ["gemini-2.5-flash", "gemini-2.0-pro"]

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model

    async def generate(self, prompt: str, context: dict, **kwargs) -> LLMResponse:
        import google.generativeai as genai
        from django.conf import settings

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(self.model)

        system_instruction = context.get("system", "")
        full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt

        response = model.generate_content(full_prompt)

        input_tokens = response.usage_metadata.prompt_token_count
        output_tokens = response.usage_metadata.candidates_token_count

        return LLMResponse(
            text=response.text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            provider=self.name,
        )

    async def stream(self, prompt: str, context: dict, **kwargs) -> AsyncIterator[str]:
        import google.generativeai as genai
        from django.conf import settings

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(self.model)

        system_instruction = context.get("system", "")
        full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt

        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
