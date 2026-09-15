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
# M4 Story Graph contracts
# ---------------------------------------------------------------------------

class StoryNodeType(str, Enum):
    """All recognized narrative node types in the Story Graph."""
    candidate = "candidate"          # directly backed by an M3 CandidateSegment
    setup = "setup"
    payoff = "payoff"
    callback = "callback"
    introduction = "introduction"
    explanation = "explanation"
    decision = "decision"
    action = "action"
    consequence = "consequence"
    question = "question"
    answer = "answer"
    emotional_beat = "emotional_beat"
    running_joke = "running_joke"
    unresolved_thread = "unresolved_thread"
    topic = "topic"
    development = "development"
    climax = "climax"
    reference = "reference"

    # Directional constraints:
    # setup_for / payoff_of / callback_to / caused_by / consequence_of / answers
    # require source to appear AFTER target temporally (i.e. target is earlier).
    # same_thread / references / continues / contrasts_with are non-directional.


class EdgeRelationType(str, Enum):
    """Typed directed narrative relationship between two StoryNodes.

    Source → target semantics:
      depends_on:       source cannot be understood without target context
      setup_for:        source is setup leading to target payoff
      payoff_of:        source is the payoff of target setup
      callback_to:      source is a callback referencing target earlier event
      references:       source mentions/references target (looser than callback)
      explains:         source explains the meaning/context of target
      caused_by:        source resulted from target earlier action
      consequence_of:   source is a consequence of target event
      answers:          source answers a question posed in target
      introduces:       source introduces a person/concept used in target
      continues:        source continues the same narrative thread as target
      contrasts_with:   source contrasts thematically with target
      same_thread:      source and target are part of the same narrative thread
    """
    depends_on = "depends_on"
    setup_for = "setup_for"
    payoff_of = "payoff_of"
    callback_to = "callback_to"
    references = "references"
    explains = "explains"
    caused_by = "caused_by"
    consequence_of = "consequence_of"
    answers = "answers"
    introduces = "introduces"
    continues = "continues"
    contrasts_with = "contrasts_with"
    same_thread = "same_thread"


# Relations that require source to come AFTER target (source is temporally later)
TEMPORALLY_DIRECTED_RELATIONS: frozenset[EdgeRelationType] = frozenset({
    EdgeRelationType.payoff_of,
    EdgeRelationType.callback_to,
    EdgeRelationType.caused_by,
    EdgeRelationType.consequence_of,
    EdgeRelationType.answers,
    EdgeRelationType.depends_on,
})

# Relations that should generally not form cycles
ACYCLIC_RELATIONS: frozenset[EdgeRelationType] = frozenset({
    EdgeRelationType.setup_for,
    EdgeRelationType.payoff_of,
    EdgeRelationType.caused_by,
    EdgeRelationType.consequence_of,
    EdgeRelationType.answers,
})


class DependencyStrength(str, Enum):
    """
    How essential is the target context for understanding the source?

    critical: clip cannot be understood without the context
    helpful:  clip is richer with context but can stand alone
    optional: minor enrichment only
    """
    critical = "critical"
    helpful = "helpful"
    optional = "optional"


class ContextRequirement(BaseModel):
    """
    Narrative context assessment for a single StoryNode.
    Produced as part of M4 graph generation. Never overrides M3 scores.
    """
    standalone_understandable: bool
    required_predecessors: list[str] = Field(default_factory=list)   # node IDs
    helpful_predecessors: list[str] = Field(default_factory=list)    # node IDs
    confidence: float


class ProposedRelationship(BaseModel):
    """
    A single relationship proposed by the narrative reasoning model.
    Model may only reference application-supplied candidate/node IDs.
    No chain-of-thought stored — only concise evidence summary.
    """
    source_candidate: str   # candidate or node ID supplied in prompt
    target_candidate: str
    relation: EdgeRelationType
    confidence: float
    dependency_strength: DependencyStrength
    dependency_strength_score: float = Field(ge=0.0, le=1.0)
    evidence_summary: str   # concise, no hidden reasoning


class LocalGraphProposal(BaseModel):
    """
    Structured output from the narrative reasoning model for a local chapter.
    Application generates all real IDs — model only uses supplied identifiers.
    """
    relationships: list[ProposedRelationship] = Field(default_factory=list)
    entities_detected: list[str] = Field(default_factory=list)   # normalized labels
    chapter_summary: str = ""
    prompt_version: str = "v1"


class StoryGraphConfig(BaseModel):
    """
    Configuration for a StoryGraphRun. Hashed into derivation_signature.
    These are infrastructure knobs — NOT canonical editorial rules.
    """
    # Chapter grouping
    chapter_duration_seconds: float = 600.0   # 10 min fallback chapters
    # Retrieval
    max_retrieval_candidates: int = 10         # max plausible pairs per node
    min_tfidf_similarity: float = 0.15         # retrieval threshold
    # Model routing
    flash_model: str = "gemini-1.5-flash"
    pro_model: str = "gemini-1.5-pro"
    use_critic: bool = True
    # Versions
    prompt_version: str = "v1"
    generator_version: str = "1.0.0"
    editorial_rules_version: str = "1.0"

    def get_signature(self, candidate_run_signature: str) -> str:
        data = self.model_dump()
        data["candidate_run_signature"] = candidate_run_signature
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class NarrativeThreadContract(BaseModel):
    """Contract representation of a NarrativeThread for API responses."""
    id: str
    story_graph_run_id: str
    title: str
    summary: str | None = None
    thread_type: str | None = None
    first_occurrence_time: float | None = None
    last_occurrence_time: float | None = None
    is_resolved: bool = True
    importance: float | None = None
    confidence: float
    node_ids: list[str] = Field(default_factory=list)


class StoryNodeContract(BaseModel):
    """Contract representation of a StoryNode for API responses."""
    id: str
    story_graph_run_id: str
    node_type: StoryNodeType
    start_time: float
    end_time: float
    candidate_id: str | None = None
    title: str | None = None
    summary: str | None = None
    confidence: float
    context_requirement: ContextRequirement | None = None
    graph_narrative_value: float | None = None
    chapter_index: int | None = None
    provider: str
    model: str | None = None
    thread_ids: list[str] = Field(default_factory=list)


class StoryEdgeContract(BaseModel):
    """Contract representation of a StoryEdge for API responses."""
    id: str
    story_graph_run_id: str
    source_node_id: str
    target_node_id: str
    relation_type: EdgeRelationType
    confidence: float
    dependency_strength: DependencyStrength
    dependency_strength_score: float | None = None
    evidence_summary: str | None = None
    provider: str
    model: str | None = None
    validated: int = 0


@runtime_checkable
class NarrativeAnalysisProvider(Protocol):
    """
    Protocol for narrative reasoning providers.
    Gemini and Mock implementations must satisfy this interface.
    Provider-specific response structures must NOT leak into the domain model.
    """

    def build_local_graph(
        self,
        chapter_candidates: list[dict[str, object]],
        chapter_summary: str,
        element_index: list[dict[str, object]],
        config: StoryGraphConfig,
    ) -> LocalGraphProposal:
        """
        Analyze candidates within a chapter and propose local narrative relationships.
        Uses Flash model. Returns structured proposal — no free-form node IDs.
        """
        ...

    def link_story_elements(
        self,
        candidate_pairs: list[tuple[dict[str, object], dict[str, object]]],
        element_index: list[dict[str, object]],
        config: StoryGraphConfig,
    ) -> LocalGraphProposal:
        """
        Evaluate plausible cross-chapter link candidates proposed by retrieval.
        Uses Pro model. Only called with bounded, curated pairs from retrieval.
        """
        ...

    def review_graph(
        self,
        nodes: list[dict[str, object]],
        edges: list[dict[str, object]],
        threads: list[dict[str, object]],
        config: StoryGraphConfig,
    ) -> list[ProposedRelationship]:
        """
        Critic pass: review assembled graph for missing links, contradictions, orphans.
        Uses Pro model selectively. Returns proposed corrections only.
        """
        ...


# ---------------------------------------------------------------------------
# Backward-compat aliases for M3 code that imported old stub names
# ---------------------------------------------------------------------------
NarrativeNodeType = StoryNodeType       # type: ignore[assignment]
NarrativeEdgeType = EdgeRelationType    # type: ignore[assignment]

