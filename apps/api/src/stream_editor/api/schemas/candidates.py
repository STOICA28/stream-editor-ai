"""M3 Candidate Pydantic response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class GenerateCandidatesRequest(BaseModel):
    provider: str | None = "mock"           # mock | gemini
    ranking_profile: str | None = "balanced"


class GenerateCandidatesResponse(BaseModel):
    task_id: str
    project_id: str
    asset_id: str
    message: str


class CandidateRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    source_asset_id: str | None
    provider: str
    generator_version: str
    prompt_version: str
    status: str
    candidate_count: int | None
    created_at: datetime | None
    completed_at: datetime | None
    error_message: str | None


class ScoreBreakdown(BaseModel):
    """
    Multi-dimensional scores. All Optional[float] - null means unknown.
    IMPORTANT: Do NOT treat null as 0. They are distinct.
    """
    humor: float | None = None
    reaction: float | None = None
    importance: float | None = None
    visual_interest: float | None = None
    chat_relevance: float | None = None
    novelty: float | None = None
    emotional_intensity: float | None = None
    story_value: float | None = None
    repetition: float | None = None


class CandidateSegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str | None
    project_id: str
    source_asset_id: str | None

    # Time boundaries
    core_start: float | None
    core_end: float | None
    start_time: float | None
    end_time: float | None

    # Content
    transcript_excerpt: str | None
    summary: str | None
    source_signals: Any | None
    local_features: Any | None

    # Scores (multi-dimensional, all nullable)
    score_humor: float | None
    score_reaction: float | None
    score_importance: float | None
    score_visual_interest: float | None
    score_chat_relevance: float | None
    score_novelty: float | None
    score_emotional_intensity: float | None
    score_story_value: float | None
    score_repetition: float | None

    # Confidence and reasoning
    confidence: float | None
    reasoning_summary: Any | None

    # EXPERIMENTAL rank - clearly labelled, NOT canonical
    experimental_rank: float | None
    ranking_profile: str | None

    # Debug label (NOT final editorial decision)
    debug_label: str | None

    # Analysis provenance
    analysis_provider: str | None
    analysis_model: str | None
    prompt_version: str | None
    semantic_cache_hit: str | None

    # Cost metadata
    input_tokens: int | None
    output_tokens: int | None
    analysis_latency_ms: int | None

    # Escalation
    escalated: str | None

    status: str | None
    created_at: datetime | None
