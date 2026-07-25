from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: str


class LLMProvider(ABC):
    name: str = ""
    models: list[str] = []

    @abstractmethod
    async def generate(self, prompt: str, context: dict, **kwargs) -> LLMResponse: ...

    @abstractmethod
    async def stream(self, prompt: str, context: dict, **kwargs) -> AsyncIterator[str]: ...

    @abstractmethod
    def estimate_tokens(self, text: str) -> int: ...
