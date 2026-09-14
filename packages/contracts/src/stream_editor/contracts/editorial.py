"""
M3 Editorial Contracts.

Defines configuration models, score schemas, and provider protocols for the
Candidate Generation & Editorial Scoring pipeline.

All score dimensions are Optional[float] - null means "unknown/not evaluated",
not zero. Never conflate absence of evidence with zero score.

NOTE: The NarrativeNode/StoryGraph types are retained below for future M4 Story Graph
implementation but are NOT part of M3 scope.
"""
from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Protocol, runtime_checkable
from uuid import UUID

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration models
# ---------------------------------------------------------------------------

class CandidateWindowConfig(BaseModel):
    """
    Infrastructure parameters for temporal windowing.
    These are NOT canonical editorial rules - they are configurable pipeline knobs.
    """
    min_duration: float = 8.0          # seconds - minimum candidate core duration
    max_duration: float = 120.0        # seconds - maximum candidate core duration
    preroll: float = 5.0               # seconds - context before core start
    postroll: float = 5.0              # seconds - context after core end
    merge_gap: float = 3.0             # seconds - merge clusters closer than this
    overlap_threshold: float = 0.5     # fraction - merge if overlap > this
    generator_version: str = "1.0.0"

    def get_signature(self, source_fingerprint: str) -> str:
        data = self.model_dump()
        data["source_fingerprint"] = source_fingerprint
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class RankingProfile(BaseModel):
    """
    EXPERIMENTAL ranking weights. Clearly marked as non-canonical.
    Used only for UI sorting - NOT for editorial KEEP/CUT decisions.
    """
    name: str
    weights: dict[str, float] = Field(default_factory=dict)
    version: str = "1.0.0"

    model_config = {"frozen": True}


# Default experimental profiles - NOT canonical editorial rules
RANKING_PROFILES: dict[str, RankingProfile] = {
    "balanced": RankingProfile(
        name="balanced",
        weights={
            "humor": 0.15,
            "reaction": 0.15,
            "importance": 0.15,
            "visual_interest": 0.10,
            "novelty": 0.10,
            "emotional_intensity": 0.10,
            "story_value": 0.15,
            "repetition": -0.10,
        },
    ),
    "humor-biased": RankingProfile(
        name="humor-biased",
        weights={
            "humor": 0.35,
            "reaction": 0.25,
            "importance": 0.10,
            "visual_interest": 0.05,
            "novelty": 0.10,
            "emotional_intensity": 0.10,
            "story_value": 0.05,
            "repetition": -0.10,
        },
    ),
    "story-biased": RankingProfile(
        name="story-biased",
        weights={
            "humor": 0.05,
            "reaction": 0.10,
            "importance": 0.20,
            "visual_interest": 0.10,
            "novelty": 0.15,
            "emotional_intensity": 0.10,
            "story_value": 0.30,
            "repetition": -0.10,
        },
    ),
}


# ---------------------------------------------------------------------------
# Score schemas
# ---------------------------------------------------------------------------

class ScoreComponents(BaseModel):
    """
    Multi-dimensional editorial score components.

    All fields are Optional[float]. null means the dimension was not evaluated
    (e.g., visual_interest=null when no scene data exists). Do NOT substitute 0.0.

    Score semantics (all in range 0.0-1.0):
    - humor: Likelihood of intentionally or naturally funny material.
    - reaction: Strength/significance of visible or audible human reaction.
    - importance: Relevance of the event to ongoing activity/conversation.
    - visual_interest: Visual dynamism (computed from scene change density in M3).
    - chat_relevance: Degree to which chat/audience engaged with this moment.
    - novelty: How unique/unexpected this content is relative to nearby segments.
    - emotional_intensity: Strength of emotional expression/tone.
    - story_value: Likelihood the segment contributes to understanding other content.
    - repetition: Likelihood this repeats information already covered (PENALTY signal).
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

    def to_dict(self) -> dict[str, float | None]:
        return self.model_dump()


class LocalFeatures(BaseModel):
    """
    Cheap deterministic features computed without any model calls.
    Stored as evidence - not used directly as scores.
    """
    speech_density: float | None = None          # fraction of window with speech
    silence_ratio: float | None = None            # fraction of window with silence
    speaker_turn_frequency: float | None = None   # turns per minute
    audio_rms_estimate: float | None = None       # normalized energy 0-1
    audio_peaks: int | None = None               # count of energy peaks
    scene_change_rate: float | None = None        # changes per minute in window
    transcript_char_length: int | None = None     # chars in core transcript
    exclamation_density: float | None = None      # exclamation marks per sentence
    lexical_novelty: float | None = None          # TF-IDF novelty vs. surrounding windows
    duration_seconds: float | None = None


# ---------------------------------------------------------------------------
# Model analysis result schema
# ---------------------------------------------------------------------------

class CandidateAnalysisResult(BaseModel):
    """
    Structured output from an editorial analysis model call.
    Must be validated against this schema - never parsed from free-form prose.
    """
    summary: str
    signals: ScoreComponents
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_summary: list[str] = Field(
        default_factory=list,
        description="Concise evidence-based reasons. No hidden chain-of-thought.",
    )
    # Cost metadata (populated by provider)
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    cache_hit: bool = False


# ---------------------------------------------------------------------------
# Provider protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class EditorialAnalysisProvider(Protocol):
    """
    Abstract editorial analysis provider.
    Implementations: MockEditorialProvider, GeminiEditorialProvider.
    """

    def analyze_candidate(
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
        """
        Analyze a candidate and return structured scores.
        Must NOT fail silently - raise on unrecoverable errors.
        """
        ...

    def summarize_window(
        self,
        *,
        transcript: str,
        start_time: float,
        end_time: float,
        level: str,
        prompt_version: str,
    ) -> dict[str, object]:
        """
        Summarize a transcript window (local | chapter | topic).
        Returns dict with 'summary' and 'key_topics'.
        """
        ...


# ---------------------------------------------------------------------------
# Story Graph types (M4 scope - not implemented in M3)
# ---------------------------------------------------------------------------

class NarrativeNodeType(str, Enum):
    setup = "setup"
    event = "event"
    character_intro = "character_intro"
    joke = "joke"
    callback = "callback"
    payoff = "payoff"
    explanation = "explanation"
    decision = "decision"
    consequence = "consequence"


class NarrativeEdgeType(str, Enum):
    depends_on = "depends_on"
    callback_to = "callback_to"
    explains = "explains"
    caused_by = "caused_by"
    follows = "follows"
    contrasts_with = "contrasts_with"


class NarrativeNode(BaseModel):
    id: UUID
    project_id: str
    node_type: NarrativeNodeType
    candidate_segment_id: UUID
    label: str
    description: str


class NarrativeEdge(BaseModel):
    id: UUID
    from_node_id: UUID
    to_node_id: UUID
    edge_type: NarrativeEdgeType
    strength: float


class StoryGraph(BaseModel):
    project_id: str
    nodes: list[NarrativeNode]
    edges: list[NarrativeEdge]
