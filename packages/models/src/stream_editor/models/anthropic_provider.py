from typing import List, Dict, Any
from .provider import ModelProvider

class AnthropicProvider(ModelProvider):
    async def analyze_segment(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("AnthropicProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
    async def score_candidates(self, candidates: List[dict[str, Any]], context: dict[str, Any]) -> List[dict[str, Any]]:
        raise NotImplementedError("AnthropicProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
    async def summarize_chapter(self, transcript: str, events: List[dict[str, Any]]) -> dict[str, Any]:
        raise NotImplementedError("AnthropicProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
    async def build_story_graph(self, chapters: List[dict[str, Any]], candidates: List[dict[str, Any]]) -> dict[str, Any]:
        raise NotImplementedError("AnthropicProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
    async def generate_edit_plan(self, story_graph: dict[str, Any], candidates: List[dict[str, Any]], rules: List[str]) -> dict[str, Any]:
        raise NotImplementedError("AnthropicProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
    async def critique_edit(self, edit_plan: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("AnthropicProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
    async def analyze_reference(self, segments: List[dict[str, Any]]) -> dict[str, Any]:
        raise NotImplementedError("AnthropicProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
