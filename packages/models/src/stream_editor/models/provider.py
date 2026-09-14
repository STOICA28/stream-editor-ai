from abc import ABC, abstractmethod
from typing import List, Dict, Any
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
    async def score_candidates(self, candidates: List[dict[str, Any]], context: dict[str, Any]) -> List[dict[str, Any]]: ...
    @abstractmethod
    async def summarize_chapter(self, transcript: str, events: List[dict[str, Any]]) -> dict[str, Any]: ...
    @abstractmethod
    async def build_story_graph(self, chapters: List[dict[str, Any]], candidates: List[dict[str, Any]]) -> dict[str, Any]: ...
    @abstractmethod
    async def generate_edit_plan(self, story_graph: dict[str, Any], candidates: List[dict[str, Any]], rules: List[str]) -> dict[str, Any]: ...
    @abstractmethod
    async def critique_edit(self, edit_plan: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]: ...
    @abstractmethod
    async def analyze_reference(self, segments: List[dict[str, Any]]) -> dict[str, Any]: ...
