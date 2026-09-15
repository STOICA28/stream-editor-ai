import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    description = Column(String, nullable=True)
    status = Column(String, default="created")
    source_video_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MediaAsset(Base):
    __tablename__ = "media_assets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    name = Column(String)
    path = Column(String)
    media_type = Column(String)
    file_size_bytes = Column(Integer)
    media_info = Column(JSON)
    
    # Provenance
    parent_asset_id = Column(String, ForeignKey("media_assets.id"), nullable=True)
    derivation_signature = Column(String, nullable=True)
    producer = Column(String, nullable=True)
    producer_version = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    status = Column(String)
    current_stage = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

class JobStep(Base):
    __tablename__ = "job_steps"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("processing_jobs.id"))
    stage = Column(String)
    status = Column(String)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    input_hash = Column(String, nullable=True)
    output_hash = Column(String, nullable=True)
    algorithm_version = Column(String)
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    output_paths = Column(JSON)

class TranscriptRun(Base):
    __tablename__ = "transcript_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    provider = Column(String)
    model = Column(String)
    language = Column(String, nullable=True)
    configuration = Column(JSON)
    derivation_signature = Column(String, unique=True)
    status = Column(String, default="running") # running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("transcript_runs.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    status = Column(String, default="pending")
    result_path = Column(String, nullable=True)

class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transcript_run_id = Column(String, ForeignKey("transcript_runs.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    text = Column(String)
    speaker = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    sequence = Column(Integer)

class TranscriptWord(Base):
    __tablename__ = "transcript_words"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    segment_id = Column(String, ForeignKey("transcript_segments.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    text = Column(String)
    confidence = Column(Float, nullable=True)

class Scene(Base):
    __tablename__ = "scenes"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    duration = Column(Float)
    detector = Column(String)
    detector_config = Column(JSON)
    confidence = Column(Float, nullable=True)

class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    event_type = Column(String) # speech, scene_change, silence, high_energy
    start_time = Column(Float)
    end_time = Column(Float)
    producer = Column(String)
    producer_version = Column(String)
    confidence = Column(Float, nullable=True)
    data = Column(JSON, nullable=True)

class CandidateRun(Base):
    """Versioned run of the candidate generation pipeline."""
    __tablename__ = "candidate_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    # M2 analysis version references (JSON dict of {transcript_run_id, scene_config_sig, audio_config_sig})
    analysis_versions = Column(JSON)
    # Provider & model config
    provider = Column(String)             # mock | gemini
    model = Column(String, nullable=True) # e.g. gemini-2.0-flash
    generator_version = Column(String)    # semver of CandidateGenerator
    candidate_config = Column(JSON)       # CandidateWindowConfig serialized
    prompt_version = Column(String)       # e.g. v1
    # Idempotency
    derivation_signature = Column(String, unique=True)
    # Lifecycle
    status = Column(String, default="running")  # running | completed | failed
    candidate_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)


class CandidateSegment(Base):
    """A candidate segment representing a portion of the livestream with explainable scores."""
    __tablename__ = "candidate_segments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("candidate_runs.id"))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))

    # Temporal boundaries
    # core_start/core_end: the detected interesting event
    # start/end: expanded context window (setup + reaction)
    core_start = Column(Float)
    core_end = Column(Float)
    start_time = Column(Float)            # = core_start - preroll
    end_time = Column(Float)              # = core_end + postroll

    # Source triggers that caused this candidate to be generated (list of strings)
    source_signals = Column(JSON)         # e.g. ["high_energy", "laughter", "scene_change"]

    # Transcript summary of core content
    transcript_excerpt = Column(String, nullable=True)
    summary = Column(String, nullable=True)

    # Cheap local features (computed without model)
    local_features = Column(JSON, nullable=True)  # LocalFeatures serialized

    # Multi-dimensional score components (all Optional[float] — null = unknown)
    score_humor = Column(Float, nullable=True)
    score_reaction = Column(Float, nullable=True)
    score_importance = Column(Float, nullable=True)
    score_visual_interest = Column(Float, nullable=True)
    score_chat_relevance = Column(Float, nullable=True)
    score_novelty = Column(Float, nullable=True)
    score_emotional_intensity = Column(Float, nullable=True)
    score_story_value = Column(Float, nullable=True)
    score_repetition = Column(Float, nullable=True)

    # Model confidence (separate from editorial value)
    confidence = Column(Float, nullable=True)

    # Reasoning/evidence (concise, no hidden chain-of-thought)
    reasoning_summary = Column(JSON, nullable=True)  # List[str]

    # Experimental ranking score (clearly labelled, NOT canonical)
    experimental_rank = Column(Float, nullable=True)
    ranking_profile = Column(String, nullable=True)   # e.g. "balanced"

    # Semantic analysis provenance
    analysis_provider = Column(String, nullable=True)
    analysis_model = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    semantic_cache_hit = Column(String, nullable=True)  # "hit" | "miss" | null

    # Token/cost metadata
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    analysis_latency_ms = Column(Integer, nullable=True)

    # Escalation tracking
    escalated = Column(String, nullable=True)   # null | "eligible" | "sent"

    # Debug label (NOT final editorial decision)
    debug_label = Column(String, nullable=True)  # interesting | uncertain | low-signal

    # Idempotency
    derivation_signature = Column(String)

    # Lifecycle
    status = Column(String, default="pending")  # pending | analyzed | failed
    created_at = Column(DateTime, default=datetime.utcnow)


class CandidateEvidenceLink(Base):
    """Links a CandidateSegment to the M2 evidence that supports it."""
    __tablename__ = "candidate_evidence_links"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String, ForeignKey("candidate_segments.id"))
    evidence_type = Column(String)   # timeline_event | transcript_segment | scene | audio_event
    evidence_id = Column(String)     # FK to the relevant table (stored as string for polymorphism)
    relevance = Column(String, nullable=True)  # why this evidence is linked


class TranscriptWindow(Base):
    """Hierarchical transcript summary for efficient context supply to models."""
    __tablename__ = "transcript_windows"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    transcript_run_id = Column(String, ForeignKey("transcript_runs.id"))
    # Window boundaries
    start_time = Column(Float)
    end_time = Column(Float)
    # Level: local | chapter | topic
    level = Column(String)
    # Parent chapter/topic ID for hierarchical lookup
    parent_window_id = Column(String, ForeignKey("transcript_windows.id"), nullable=True)
    # Content
    summary = Column(String, nullable=True)
    key_topics = Column(JSON, nullable=True)   # List[str]
    # Provenance
    provider = Column(String)
    model = Column(String, nullable=True)
    prompt_version = Column(String)
    derivation_signature = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelResultCache(Base):
    """Caches AI model responses for candidate analysis by deterministic signature."""
    __tablename__ = "model_result_cache"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Cache key: hash of (provider + model + prompt_version + input_content_hash + editorial_rules_version)
    cache_key = Column(String, unique=True)
    provider = Column(String)
    model = Column(String)
    prompt_version = Column(String)
    editorial_rules_version = Column(String, nullable=True)
    # Cached output
    result = Column(JSON)
    # Cost metadata
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# M5 - Global Editorial Selection & Edit Plan
# ---------------------------------------------------------------------------

class EditPlanRun(Base):
    """
    Versioned Edit Plan generation run.
    Idempotent by derivation_signature.
    """
    __tablename__ = "edit_plan_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    candidate_run_id = Column(String, ForeignKey("candidate_runs.id"), nullable=True)
    story_graph_run_id = Column(String, ForeignKey("story_graph_runs.id"), nullable=True)
    
    # Target duration constraints
    target_duration_seconds = Column(Float, nullable=True)
    tolerance_seconds = Column(Float, nullable=True)
    
    # Configuration / Provenance
    planning_profile = Column(String) # compact | balanced | comprehensive
    provider = Column(String)         # mock | gemini
    model = Column(String)            
    prompt_version = Column(String)
    planner_version = Column(String)
    
    derivation_signature = Column(String, unique=True)
    status = Column(String, default="running") # running | completed | failed
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class EditPlan(Base):
    __tablename__ = "edit_plans"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    run_id = Column(String, ForeignKey("edit_plan_runs.id"))
    
    version = Column(Integer, default=1)
    status = Column(String, default="proposed") # proposed | accepted | rejected | modified
    
    # Stats / diagnostics
    original_duration = Column(Float)
    selected_duration = Column(Float)
    compression_ratio = Column(Float)
    clip_count = Column(Integer)
    
    # Optional constraints
    locked = Column(Boolean, default=False)


    # M6 Revisions
    parent_plan_id = Column(String, ForeignKey("edit_plans.id"), nullable=True)
    revision_number = Column(Integer, default=1)
    origin = Column(String, default="ai")  # ai | human | hybrid
    revision_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    clips = relationship("EditClip", back_populates="plan", cascade="all, delete-orphan")


class EditClip(Base):
    __tablename__ = "edit_clips"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String, ForeignKey("edit_plans.id"))
    
    plan = relationship("EditPlan", back_populates="clips")
    
    # Source boundaries
    source_start = Column(Float)
    source_end = Column(Float)
    
    # Optional sub-boundaries for "core" vs "context" (M5 concept)
    core_start = Column(Float, nullable=True)
    core_end = Column(Float, nullable=True)
    

    # M6 Review State
    review_state = Column(String, default="proposed")  # proposed | accepted | rejected | modified
    
    # Output timeline boundaries (calculated by compiler)
    output_start = Column(Float)
    output_end = Column(Float)
    
    # Traceability
    candidate_id = Column(String, ForeignKey("candidate_segments.id"), nullable=True)
    narrative_thread_id = Column(String, nullable=True)  # Free string for now, could FK to threads
    story_node_id = Column(String, ForeignKey("story_nodes.id"), nullable=True)
    
    # Editorial justification
    selection_reason = Column(String)
    priority = Column(String) # essential | high | medium | low | context_only
    confidence = Column(Float, nullable=True)
    
    # Constraints
    locked = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class FeedbackEvent(Base):
    __tablename__ = "feedback_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    edit_plan_id = Column(String, ForeignKey("edit_plans.id"))
    edit_clip_id = Column(String, ForeignKey("edit_clips.id"), nullable=True)
    
    feedback_type = Column(String)
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    
    reason_category = Column(String, nullable=True)
    reason_text = Column(String, nullable=True)
    
    candidate_id = Column(String, nullable=True)
    story_node_ids = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class AudioEvent(Base):
    __tablename__ = "audio_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    event_type = Column(String)
    analyzer = Column(String)
    analyzer_config = Column(JSON)


# ---------------------------------------------------------------------------
# M4 — Story Graph models
# ---------------------------------------------------------------------------

class StoryGraphRun(Base):
    """
    Versioned Story Graph generation run.
    Idempotent by derivation_signature — same config + candidates → reuse run.
    """
    __tablename__ = "story_graph_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    candidate_run_id = Column(String, ForeignKey("candidate_runs.id"))
    # Provider / model tracking
    provider = Column(String)           # "mock" | "gemini"
    flash_model = Column(String, nullable=True)
    pro_model = Column(String, nullable=True)
    prompt_version = Column(String)
    generator_version = Column(String)
    configuration = Column(JSON)        # StoryGraphConfig.model_dump()
    derivation_signature = Column(String, unique=True)
    # Status
    status = Column(String, default="running")   # running | completed | failed | partial
    error_message = Column(String, nullable=True)
    # Metrics
    node_count = Column(Integer, nullable=True)
    edge_count = Column(Integer, nullable=True)
    thread_count = Column(Integer, nullable=True)
    callback_count = Column(Integer, nullable=True)
    setup_payoff_pairs = Column(Integer, nullable=True)
    orphan_node_count = Column(Integer, nullable=True)
    # Cost telemetry
    flash_requests = Column(Integer, nullable=True)
    pro_requests = Column(Integer, nullable=True)
    total_input_tokens = Column(Integer, nullable=True)
    total_output_tokens = Column(Integer, nullable=True)
    total_latency_ms = Column(Integer, nullable=True)
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class StoryNode(Base):
    """
    A single narrative element within the Story Graph.
    May represent a candidate segment, a topic, a setup, payoff, callback, etc.
    """
    __tablename__ = "story_nodes"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    story_graph_run_id = Column(String, ForeignKey("story_graph_runs.id"))
    project_id = Column(String, ForeignKey("projects.id"))
    # Node identity
    node_type = Column(String)          # StoryNodeType enum value
    # Temporal position (seconds in source media)
    start_time = Column(Float)
    end_time = Column(Float)
    # Link to M3 candidate (optional — some nodes are purely narrative constructs)
    candidate_id = Column(String, ForeignKey("candidate_segments.id"), nullable=True)
    # Content
    title = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    # Quality
    confidence = Column(Float)
    # Context requirement assessment (JSON)
    # { standalone_understandable: bool, required_predecessors: [id], helpful_predecessors: [id], confidence: float }
    context_requirement = Column(JSON, nullable=True)
    # M4-derived narrative value (separate from M3 story_value, never overwrites it)
    graph_narrative_value = Column(Float, nullable=True)
    # Provenance
    provider = Column(String)
    model = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    chapter_index = Column(Integer, nullable=True)   # which chapter this was built in
    node_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StoryEdge(Base):
    """
    A typed directed narrative relationship between two StoryNodes.
    Direction: source → target, e.g. callback_to means source is a callback TO target.
    """
    __tablename__ = "story_edges"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    story_graph_run_id = Column(String, ForeignKey("story_graph_runs.id"))
    source_node_id = Column(String, ForeignKey("story_nodes.id"))
    target_node_id = Column(String, ForeignKey("story_nodes.id"))
    relation_type = Column(String)          # EdgeRelationType enum value
    # Quality
    confidence = Column(Float)
    dependency_strength = Column(String)    # DependencyStrength: critical | helpful | optional
    dependency_strength_score = Column(Float, nullable=True)  # 0.0–1.0
    # Explainability (concise, no chain-of-thought)
    evidence_summary = Column(String, nullable=True)
    # Provenance
    provider = Column(String)
    model = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    # Validation
    validated = Column(Integer, default=0)   # 0 = pending, 1 = passed, -1 = rejected
    validation_errors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class NarrativeThread(Base):
    """
    A named narrative arc that groups related StoryNodes.
    Examples: "trying to beat boss X", "running joke about blue car", "argument with chat".
    """
    __tablename__ = "narrative_threads"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    story_graph_run_id = Column(String, ForeignKey("story_graph_runs.id"))
    project_id = Column(String, ForeignKey("projects.id"))
    title = Column(String)
    summary = Column(String, nullable=True)
    thread_type = Column(String, nullable=True)   # running_joke | arc | callback_chain | unresolved
    first_occurrence_time = Column(Float, nullable=True)
    last_occurrence_time = Column(Float, nullable=True)
    is_resolved = Column(Integer, default=1)   # 0 = unresolved thread (no payoff found)
    importance = Column(Float, nullable=True)
    confidence = Column(Float)
    provider = Column(String)
    model = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class NodeThreadMembership(Base):
    """M2M join: which nodes belong to which narrative threads."""
    __tablename__ = "node_thread_memberships"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = Column(String, ForeignKey("story_nodes.id"))
    thread_id = Column(String, ForeignKey("narrative_threads.id"))
    role_in_thread = Column(String, nullable=True)  # setup | occurrence | callback | payoff | resolution
    created_at = Column(DateTime, default=datetime.utcnow)


class NarrativeElement(Base):
    """
    Lightweight searchable index of narrative concepts/entities detected in the stream.
    Allows later candidates to query: "does this reference something previously established?"
    NOT a full knowledge graph — simple normalized labels.
    """
    __tablename__ = "narrative_elements"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    story_graph_run_id = Column(String, ForeignKey("story_graph_runs.id"))
    project_id = Column(String, ForeignKey("projects.id"))
    # The concept/entity
    label = Column(String)              # e.g. "boss fight attempt", "blue car joke", "pepe123"
    element_type = Column(String)       # person | place | item | joke | promise | event | topic | phrase
    # First time this element appears
    first_seen_time = Column(Float)
    last_seen_time = Column(Float, nullable=True)
    # Description for retrieval
    description = Column(String, nullable=True)
    # Source node IDs (JSON list of node IDs where this element appears)
    node_ids = Column(JSON, nullable=True)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# M7 - Visual Understanding models
# ---------------------------------------------------------------------------

class VisualAnalysisRun(Base):
    __tablename__ = "visual_analysis_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    source_asset_id = Column(String, ForeignKey("media_assets.id"))
    proxy_asset_id = Column(String, ForeignKey("media_assets.id"), nullable=True)
    
    # Provider & Config
    provider = Column(String)  # mock | gemini
    configuration = Column(JSON)  # sampler settings, thresholds
    derivation_signature = Column(String, unique=True)
    
    # Status & Telemetry
    status = Column(String, default="running")  # running | completed | failed | partial
    error_message = Column(String, nullable=True)
    flash_requests = Column(Integer, default=0)
    pro_requests = Column(Integer, default=0)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_latency_ms = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class VisualRegion(Base):
    __tablename__ = "visual_regions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_analysis_run_id = Column(String, ForeignKey("visual_analysis_runs.id"))
    project_id = Column(String, ForeignKey("projects.id"))
    
    region_type = Column(String)  # facecam | chat | gameplay | browser | desktop | alert | webcam | subtitle | hud | unknown
    start_time = Column(Float)
    end_time = Column(Float)
    
    # Bounding Box (normalized 0-1)
    x = Column(Float)
    y = Column(Float)
    width = Column(Float)
    height = Column(Float)
    
    confidence = Column(Float)
    detector = Column(String)  # e.g. "mediapipe", "gemini-flash"
    track_id = Column(String, nullable=True)  # stable temporal identifier e.g. FACE_TRACK_01
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class StreamLayout(Base):
    __tablename__ = "stream_layouts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_analysis_run_id = Column(String, ForeignKey("visual_analysis_runs.id"))
    project_id = Column(String, ForeignKey("projects.id"))
    
    start_time = Column(Float)
    end_time = Column(Float)
    
    layout_name = Column(String)  # e.g., "Gameplay + BottomRight Facecam"
    description = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class VisualEvent(Base):
    __tablename__ = "visual_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_analysis_run_id = Column(String, ForeignKey("visual_analysis_runs.id"))
    project_id = Column(String, ForeignKey("projects.id"))
    
    event_type = Column(String)  # layout_change | facecam_appears | facecam_disappears | chat_appears | large_motion | focus_shift | visual_event | strong_face_reaction
    start_time = Column(Float)
    end_time = Column(Float)
    
    confidence = Column(Float)
    description = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class FocusTarget(Base):
    __tablename__ = "focus_targets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_analysis_run_id = Column(String, ForeignKey("visual_analysis_runs.id"))
    project_id = Column(String, ForeignKey("projects.id"))
    
    start_time = Column(Float)
    end_time = Column(Float)
    
    target_type = Column(String)  # facecam | chat | screen_region | text_region | game_region | alert | full_frame | unknown
    
    # Bounding Box (normalized 0-1)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    
    priority = Column(String, nullable=True)
    confidence = Column(Float)
    evidence_summary = Column(String, nullable=True)
    provenance = Column(String)
    
    sequence_id = Column(String, nullable=True)  # Grouping for screen_event -> reaction sequences
    sequence_order = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------------------------------------------------------------------------
# M8 - Effect Planning models
# ---------------------------------------------------------------------------

class EffectPlanRun(Base):
    __tablename__ = "effect_plan_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    edit_plan_id = Column(String, ForeignKey("edit_plans.id"))
    visual_analysis_run_id = Column(String, ForeignKey("visual_analysis_runs.id"), nullable=True)
    
    # Provider & Config
    provider = Column(String)  # mock | gemini
    model = Column(String, nullable=True)
    configuration = Column(JSON, nullable=True)
    prompt_version = Column(String, nullable=True)
    editorial_rule_versions = Column(String, nullable=True)
    derivation_signature = Column(String, unique=True)
    
    # Status & Telemetry
    status = Column(String, default="running")  # running | completed | failed | partial
    error_message = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class EffectInstruction(Base):
    __tablename__ = "effect_instructions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    effect_plan_run_id = Column(String, ForeignKey("effect_plan_runs.id"))
    edit_clip_id = Column(String, ForeignKey("edit_clips.id"), nullable=True)
    
    source_start = Column(Float)
    source_end = Column(Float)
    output_start = Column(Float, nullable=True)
    output_end = Column(Float, nullable=True)
    
    effect_type = Column(String)  # none | zoom_region | zoom_face | zoom_chat | crop_focus | grayscale | freeze_frame | slow_motion | speed_up | text_emphasis | highlight_region | audio_duck | audio_gain | fade
    target_type = Column(String)  # full_frame | facecam | chat | screen_region | text_region | content_region | visual_event | unknown
    
    # Bounding Box (normalized 0-1) - Optional
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    
    parameters = Column(JSON, nullable=True)
    
    confidence = Column(Float)
    priority = Column(String)  # critical | high | normal | low
    reason = Column(String, nullable=True)
    evidence_references = Column(JSON, nullable=True)
    
    provider = Column(String)
    review_state = Column(String, default="proposed")  # proposed | accepted | rejected | modified
    
    created_at = Column(DateTime, default=datetime.utcnow)
