from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, UTC


class DatasetSplit(str, Enum):
    REFERENCE = "REFERENCE"      # Used for training / style extraction (never tested against)
    VALIDATION = "VALIDATION"    # Used for tuning and validation
    TEST = "TEST"                # Held-out unseen benchmark pairs


class ClipMatchClassification(str, Enum):
    MATCHED = "MATCHED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    MISSED = "MISSED"
    UNRESOLVED = "UNRESOLVED"


class AISegmentClassification(str, Enum):
    REFERENCE_SUPPORTED = "REFERENCE_SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    AI_ONLY = "AI_ONLY"
    UNRESOLVED = "UNRESOLVED"


class FalseNegativeReason(str, Enum):
    MISSED_HUMOR = "MISSED_HUMOR"
    MISSED_REACTION = "MISSED_REACTION"
    MISSED_IMPORTANT_EVENT = "MISSED_IMPORTANT_EVENT"
    MISSING_CONTEXT = "MISSING_CONTEXT"
    MISSING_SETUP = "MISSING_SETUP"
    MISSING_PAYOFF = "MISSING_PAYOFF"
    MISSED_CALLBACK = "MISSED_CALLBACK"
    MISSING_CHAT_CONTEXT = "MISSING_CHAT_CONTEXT"
    MISSING_VISUAL_EVENT = "MISSING_VISUAL_EVENT"
    LOW_SCORE = "LOW_SCORE"
    BUDGET_EXCLUSION = "BUDGET_EXCLUSION"
    REDUNDANCY_EXCLUSION = "REDUNDANCY_EXCLUSION"
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"
    UNKNOWN = "UNKNOWN"


class FalsePositiveReason(str, Enum):
    DEAD_AIR = "DEAD_AIR"
    REPETITIVE = "REPETITIVE"
    LOW_INFORMATION = "LOW_INFORMATION"
    UNNECESSARY_CONTEXT = "UNNECESSARY_CONTEXT"
    WEAK_REACTION = "WEAK_REACTION"
    FAILED_HUMOR = "FAILED_HUMOR"
    OFF_TOPIC = "OFF_TOPIC"
    OVERLONG_SETUP = "OVERLONG_SETUP"
    OVERLONG_PAYOFF = "OVERLONG_PAYOFF"
    VALID_ALTERNATIVE = "VALID_ALTERNATIVE"
    HUMAN_REFERENCE_UNCERTAIN = "HUMAN_REFERENCE_UNCERTAIN"
    UNKNOWN = "UNKNOWN"


class PipelineStage(str, Enum):
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"
    M6 = "M6"
    M7 = "M7"
    M8 = "M8"
    M9 = "M9"
    UNKNOWN = "UNKNOWN"


class EffectAgreementCategory(str, Enum):
    SAME_EFFECT = "SAME_EFFECT"
    SIMILAR_EFFECT = "SIMILAR_EFFECT"
    DIFFERENT_EFFECT = "DIFFERENT_EFFECT"
    AI_EFFECT_ONLY = "AI_EFFECT_ONLY"
    HUMAN_EFFECT_ONLY = "HUMAN_EFFECT_ONLY"
    NO_COMPARISON = "NO_COMPARISON"


class ExperimentStatus(str, Enum):
    PROPOSED = "PROPOSED"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"
    PROMOTED = "PROMOTED"


# ---------------------------------------------------------------------------
# Timeline Interval Representations
# ---------------------------------------------------------------------------

class RetainedInterval(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_start: float
    source_end: float
    edit_start: Optional[float] = None
    edit_end: Optional[float] = None
    confidence: float = 1.0
    is_transformed: bool = False
    is_external_insert: bool = False
    transformation_notes: Optional[str] = None
    ordering_index: int = 0
    tags: list[str] = Field(default_factory=list)


class HumanReferenceTimeline(BaseModel):
    case_id: str
    retained_intervals: list[RetainedInterval] = Field(default_factory=list)
    removed_intervals: list[RetainedInterval] = Field(default_factory=list)
    transformed_intervals: list[RetainedInterval] = Field(default_factory=list)
    external_inserts: list[RetainedInterval] = Field(default_factory=list)
    total_retained_duration: float = 0.0
    total_source_duration: float = 0.0
    total_edit_duration: float = 0.0
    alignment_confidence_avg: float = 1.0


class StreamEditorTimelineSegment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_start: float
    source_end: float
    output_start: float
    output_end: float
    clip_id: str
    candidate_id: Optional[str] = None
    story_node_id: Optional[str] = None
    narrative_thread_id: Optional[str] = None
    selection_reason: Optional[str] = None
    priority: str = "medium"
    effects: list[dict[str, Any]] = Field(default_factory=list)


class StreamEditorTimeline(BaseModel):
    project_id: str
    plan_id: str
    segments: list[StreamEditorTimelineSegment] = Field(default_factory=list)
    total_selected_duration: float = 0.0
    clip_count: int = 0
    is_styled: bool = False
    style_policy_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Metrics Contracts
# ---------------------------------------------------------------------------

class TemporalTolerance(BaseModel):
    tolerance_seconds: float = 1.0  # Default 1.0s, also evaluated at 0.5s and 2.0s


class SelectionOverlapMetrics(BaseModel):
    tolerance_seconds: float
    precision: float = Field(..., description="AI-selected overlap / total AI duration")
    recall: float = Field(..., description="AI-selected overlap / total Human duration")
    f1: float = Field(..., description="Harmonic mean of precision and recall")
    intersection_duration: float
    human_retained_duration: float
    ai_retained_duration: float
    sample_count: int = Field(default=0, description="N intervals evaluated")


class QuantileStats(BaseModel):
    p10: float = 0.0
    p25: float = 0.0
    median: float = 0.0
    p75: float = 0.0
    p90: float = 0.0
    mean: float = 0.0
    std: float = 0.0


class ContextMetrics(BaseModel):
    pre_context_diff_quantiles: QuantileStats = Field(default_factory=QuantileStats)
    post_context_diff_quantiles: QuantileStats = Field(default_factory=QuantileStats)
    context_too_short_count: int = 0
    context_too_long_count: int = 0
    good_context_match_count: int = 0
    sample_count: int = 0


class SetupPayoffResult(BaseModel):
    story_node_id: str
    setup_start: float
    setup_end: float
    payoff_start: float
    payoff_end: float
    setup_retained_by_human: bool
    payoff_retained_by_human: bool
    setup_retained_by_ai: bool
    payoff_retained_by_ai: bool
    status: str  # "BOTH_RETAINED", "SETUP_ONLY", "PAYOFF_ONLY", "NEITHER", "NOT_IN_HUMAN"


class NarrativeMetrics(BaseModel):
    setup_payoff_total: int = 0
    setup_payoff_intact: int = 0
    setup_payoff_completeness: float = 0.0
    callback_total: int = 0
    callback_retained: int = 0
    callback_retention_rate: float = 0.0
    shared_thread_ids: list[str] = Field(default_factory=list)
    human_only_thread_ids: list[str] = Field(default_factory=list)
    ai_only_thread_ids: list[str] = Field(default_factory=list)
    thread_duration_distribution: dict[str, float] = Field(default_factory=dict)
    sample_count: int = 0


class PacingMetrics(BaseModel):
    cuts_per_minute: float = 0.0
    human_cuts_per_minute: float = 0.0
    clip_duration_stats: QuantileStats = Field(default_factory=QuantileStats)
    human_clip_duration_stats: QuantileStats = Field(default_factory=QuantileStats)
    time_between_cuts_stats: QuantileStats = Field(default_factory=QuantileStats)
    human_time_between_cuts_stats: QuantileStats = Field(default_factory=QuantileStats)
    compression_ratio_ai: float = 0.0
    compression_ratio_human: float = 0.0
    content_density_events_per_min: float = 0.0
    dead_air_seconds: float = 0.0
    dead_air_percentage: float = 0.0


class EffectComparisonRecord(BaseModel):
    source_start: float
    source_end: float
    human_effect_type: Optional[str] = None
    ai_effect_type: Optional[str] = None
    category: EffectAgreementCategory
    onset_difference_seconds: Optional[float] = None
    duration_difference_seconds: Optional[float] = None
    is_appropriate: Optional[bool] = None
    reason: Optional[str] = None


class EffectMetrics(BaseModel):
    total_comparisons: int = 0
    same_effect_count: int = 0
    similar_effect_count: int = 0
    different_effect_count: int = 0
    ai_effect_only_count: int = 0
    human_effect_only_count: int = 0
    effect_agreement_rate: float = 0.0
    onset_diff_stats: QuantileStats = Field(default_factory=QuantileStats)
    effects_per_minute_ai: float = 0.0
    effects_per_minute_human: float = 0.0
    over_effected_flag: bool = False
    under_effected_flag: bool = False
    records: list[EffectComparisonRecord] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Failures and Diagnoses
# ---------------------------------------------------------------------------

class EditorialFailure(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    benchmark_run_id: str
    case_id: str
    failure_type: str  # FalseNegativeReason or FalsePositiveReason or custom
    root_cause_stage: PipelineStage
    source_start: float
    source_end: float
    description: str
    evidence_trace: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0


# ---------------------------------------------------------------------------
# Benchmark Case, Run, and Result
# ---------------------------------------------------------------------------

class EditorialBenchmarkCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    source_asset_id: str
    human_edit_asset_id: str
    reference_project_id: Optional[str] = None
    editor_label: str = "human_reference"
    style_policy_id: Optional[str] = None
    duration_source: float
    duration_human_edit: float
    authorization_status: str = "authorized"
    split: DatasetSplit = DatasetSplit.TEST
    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EditorialBenchmark(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "StreamEditor Core Benchmark"
    version: str = "1.0"
    cases: list[EditorialBenchmarkCase] = Field(default_factory=list)


class EditorialBenchmarkRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    benchmark_case_id: str
    project_id: str
    streameditor_version: str = "0.1.0"
    build_commit: str = "HEAD"
    policy_version: str = "v1"
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    provider_versions: dict[str, str] = Field(default_factory=dict)
    style_policy_id: Optional[str] = None
    configuration: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None
    status: str = "running"
    is_baseline: bool = False


class EditorialBenchmarkResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    case_id: str
    split: DatasetSplit
    
    # Tolerances
    overlap_at_05s: SelectionOverlapMetrics
    overlap_at_10s: SelectionOverlapMetrics
    overlap_at_20s: SelectionOverlapMetrics
    
    # Subsystem Dimensions
    context: ContextMetrics
    narrative: NarrativeMetrics
    pacing: PacingMetrics
    effects: EffectMetrics
    
    # Categorization counts
    matched_segments_count: int = 0
    missed_segments_count: int = 0
    ai_only_segments_count: int = 0
    valid_alternatives_count: int = 0
    
    # Failures
    failures: list[EditorialFailure] = Field(default_factory=list)
    root_cause_distribution: dict[str, int] = Field(default_factory=dict)
    
    # Audit telemetry
    editor_model: str = "gemini-3.1-pro-high"
    evaluator_model: str = "gemini-3.1-pro-high"
    model_parity_flag: bool = True
    manual_audit_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EditorialExperiment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    hypothesis: str
    baseline_run_id: str
    target_stage: PipelineStage
    proposed_change: str
    status: ExperimentStatus = ExperimentStatus.PROPOSED
    results_comparison: Optional[dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None
