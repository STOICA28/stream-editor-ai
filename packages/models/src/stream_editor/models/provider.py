from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ModelResponse(BaseModel):
    content: str
    usage: dict[str, Any]
    model: str
    provider: str

class ModelProvider(ABC):
    @abstractmethod
    async def analyze_segment(self, context: dict[str, Any]) -> dict[str, Any]: ...
    @abstractmethod
    async def score_candidates(self, candidates: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]: ...
    @abstractmethod
    async def summarize_chapter(self, transcript: str, events: list[dict[str, Any]]) -> dict[str, Any]: ...
    @abstractmethod
    async def build_story_graph(self, chapters: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> dict[str, Any]: ...
    @abstractmethod
    async def generate_edit_plan(self, story_graph: dict[str, Any], candidates: list[dict[str, Any]], rules: list[str]) -> dict[str, Any]: ...
    @abstractmethod
    async def critique_edit(self, edit_plan: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]: ...
    @abstractmethod
    async def analyze_reference(self, segments: list[dict[str, Any]]) -> dict[str, Any]: ...
