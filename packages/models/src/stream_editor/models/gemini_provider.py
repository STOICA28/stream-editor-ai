from typing import Any

from .provider import ModelProvider


class GeminiProvider(ModelProvider):
    async def analyze_segment(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("GeminiProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
    async def score_candidates(self, candidates: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
        raise NotImplementedError("GeminiProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
    async def summarize_chapter(self, transcript: str, events: list[dict[str, Any]]) -> dict[str, Any]:
        raise NotImplementedError("GeminiProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
    async def build_story_graph(self, chapters: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> dict[str, Any]:
        raise NotImplementedError("GeminiProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
    async def generate_edit_plan(self, story_graph: dict[str, Any], candidates: list[dict[str, Any]], rules: list[str]) -> dict[str, Any]:
        raise NotImplementedError("GeminiProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
    async def critique_edit(self, edit_plan: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("GeminiProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
    async def analyze_reference(self, segments: list[dict[str, Any]]) -> dict[str, Any]:
        raise NotImplementedError("GeminiProvider not yet implemented. Set MODEL_PROVIDER=mock for testing.")
