import os
from .provider import ModelProvider
from .mock_provider import MockProvider
from .gemini_provider import GeminiProvider
from .anthropic_provider import AnthropicProvider

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
