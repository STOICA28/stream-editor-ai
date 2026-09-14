import os

from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .mock_provider import MockProvider
from .provider import ModelProvider


def get_provider(name: str | None = None) -> ModelProvider:
    if name is None:
        name = os.environ.get("MODEL_PROVIDER", "mock")
    
    if name == "mock":
        return MockProvider()
    elif name == "gemini":
        return GeminiProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    else:
        raise ValueError(f"Unknown provider: {name}")
