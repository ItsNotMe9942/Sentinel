from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelRequest:
    prompt: str


@dataclass(frozen=True)
class ModelResponse:
    content: str


class ModelProvider(Protocol):
    def generate(self, request: ModelRequest) -> ModelResponse:
        ...


class ModelGateway:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def request(self, prompt: str) -> ModelResponse:
        if not prompt.strip():
            raise ValueError("Model prompt must not be empty.")

        request = ModelRequest(prompt=prompt)

        return self.provider.generate(request)