import os

from .anthropic_provider import AnthropicProvider
from .mock_provider import MockProvider
from .provider import ModelProvider


def get_provider(name: str | None = None) -> ModelProvider:
    if name is None:
        name = os.environ.get("MODEL_PROVIDER", "mock")
    
    if name == "mock":
        return MockProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "antigravity":
        # Placeholder for antigravity if needed directly via factory
        raise NotImplementedError("Antigravity uses specific domain providers rather than a monolithic ModelProvider")
    else:
        raise ValueError(f"Unknown provider: {name}")
