import logging
from typing import List, Dict, Any
from .provider import ModelProvider

logger = logging.getLogger(__name__)

class MockProvider(ModelProvider):
    async def analyze_segment(self, context: dict[str, Any]) -> dict[str, Any]:
        logger.info(f"analyze_segment called with {context}")
        return {"result": "mock"}

    async def score_candidates(self, candidates: List[dict[str, Any]], context: dict[str, Any]) -> List[dict[str, Any]]:
        logger.info(f"score_candidates called with {len(candidates)} candidates")
        return [{"id": c.get("id"), "score": 1.0} for c in candidates]

    async def summarize_chapter(self, transcript: str, events: List[dict[str, Any]]) -> dict[str, Any]:
        logger.info("summarize_chapter called")
        return {"summary": "mock summary"}

    async def build_story_graph(self, chapters: List[dict[str, Any]], candidates: List[dict[str, Any]]) -> dict[str, Any]:
        logger.info("build_story_graph called")
        return {"nodes": [], "edges": []}

    async def generate_edit_plan(self, story_graph: dict[str, Any], candidates: List[dict[str, Any]], rules: List[str]) -> dict[str, Any]:
        logger.info("generate_edit_plan called")
        return {"plan": "mock"}

    async def critique_edit(self, edit_plan: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        logger.info("critique_edit called")
        return {"critique": "mock"}

    async def analyze_reference(self, segments: List[dict[str, Any]]) -> dict[str, Any]:
        logger.info("analyze_reference called")
        return {"analysis": "mock"}
