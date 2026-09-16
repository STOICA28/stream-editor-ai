import json

from stream_editor.contracts.editorial import (
    CandidateAnalysisResult,
    LocalFeatures,
    ScoreComponents,
)
from stream_editor.editorial.prompts.v1_candidate_analysis import (
    build_prompt as build_candidate_prompt,
)
from stream_editor.editorial.prompts.v1_chapter_summary import build_prompt as build_chapter_prompt

from pydantic import BaseModel, Field

from stream_editor.models.antigravity_client import AntigravityClient, AIProviderUnavailable


class EditorialAnalysisOutput(BaseModel):
    summary: str = Field(..., description="A concise summary of what happens in this clip")
    signals: ScoreComponents
    confidence: float = Field(..., description="Overall confidence in analysis (0.0 to 1.0)")
    reasoning_summary: list[str] = Field(default_factory=list, description="Bullet points explaining scores")


class ChapterSummaryOutput(BaseModel):
    summary: str = Field(...)
    key_events: list[str] = Field(default_factory=list)


class AntigravityEditorialProvider:
    def __init__(self, client: AntigravityClient):
        self.client = client

    async def analyze_candidate(
        self,
        *,
        candidate_id: str,
        transcript_excerpt: str,
        local_features: LocalFeatures,
        nearby_events: list[dict[str, object]],
        local_summary: str | None,
        chapter_summary: str | None,
        prompt_version: str,
    ) -> CandidateAnalysisResult:
        
        prompt = build_candidate_prompt(
            transcript_excerpt=transcript_excerpt,
            local_features=local_features.model_dump() if hasattr(local_features, "model_dump") else local_features,
            nearby_events=nearby_events,
            local_summary=local_summary,
            chapter_summary=chapter_summary
        )
        
        prompt = (
            "Analyze only the provided evidence.\n"
            "Return the required structured output.\n"
            "Do not modify repository files.\n"
            "Do not execute commands.\n"
            "Do not invoke tools.\n"
            "Do not change project state.\n\n"
            + prompt
        )
        
        try:
            data = await self.client.generate_structured(prompt, EditorialAnalysisOutput)
            
            return CandidateAnalysisResult(
                summary=data.summary,
                signals=data.signals,
                confidence=data.confidence,
                reasoning_summary=data.reasoning_summary,
                input_tokens=0, # Client handles telemetry
                output_tokens=0,
                latency_ms=0,
                cache_hit=False
            )
        except AIProviderUnavailable as e:
            raise RuntimeError(f"Antigravity unavailable: {e}")

    async def summarize_window(
        self,
        *,
        transcript: str,
        start_time: float,
        end_time: float,
        level: str,
        prompt_version: str,
    ) -> dict[str, object]:
        prompt = build_chapter_prompt(
            transcript=transcript,
            start_time=start_time,
            end_time=end_time,
            level=level
        )
        
        prompt = (
            "Analyze only the provided evidence.\n"
            "Return the required structured output.\n"
            "Do not modify repository files.\n"
            "Do not execute commands.\n"
            "Do not invoke tools.\n"
            "Do not change project state.\n\n"
            + prompt
        )
        
        try:
            data = await self.client.generate_structured(prompt, ChapterSummaryOutput)
            return data.model_dump()
        except AIProviderUnavailable as e:
            raise RuntimeError(f"Antigravity unavailable: {e}")

