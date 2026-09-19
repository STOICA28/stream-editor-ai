import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Integer, Boolean, JSON
from sqlalchemy.orm import relationship

from ..database import Base


class EditorialBenchmarkCaseModel(Base):
    __tablename__ = "benchmark_cases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    source_asset_id = Column(String, ForeignKey("media_assets.id"), nullable=False)
    human_edit_asset_id = Column(String, ForeignKey("media_assets.id"), nullable=False)
    reference_project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    editor_label = Column(String, default="human_reference")
    style_policy_id = Column(String, nullable=True)
    duration_source = Column(Float, nullable=False)
    duration_human_edit = Column(Float, nullable=False)
    authorization_status = Column(String, default="authorized")
    split = Column(String, default="TEST")  # REFERENCE, VALIDATION, TEST
    tags = Column(JSON, default=list)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    runs = relationship("EditorialBenchmarkRunModel", back_populates="case", cascade="all, delete-orphan")


class EditorialBenchmarkRunModel(Base):
    __tablename__ = "benchmark_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    benchmark_case_id = Column(String, ForeignKey("benchmark_cases.id"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    streameditor_version = Column(String, default="0.1.0")
    build_commit = Column(String, default="HEAD")
    policy_version = Column(String, default="v1")
    prompt_versions = Column(JSON, default=dict)
    provider_versions = Column(JSON, default=dict)
    style_policy_id = Column(String, nullable=True)
    configuration = Column(JSON, default=dict)
    started_at = Column(DateTime, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="running")
    is_baseline = Column(Boolean, default=False)

    case = relationship("EditorialBenchmarkCaseModel", back_populates="runs")
    result = relationship("EditorialBenchmarkResultModel", uselist=False, back_populates="run", cascade="all, delete-orphan")
    failures = relationship("EditorialFailureModel", back_populates="run", cascade="all, delete-orphan")


class EditorialBenchmarkResultModel(Base):
    __tablename__ = "benchmark_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("benchmark_runs.id"), nullable=False, unique=True)
    case_id = Column(String, ForeignKey("benchmark_cases.id"), nullable=False)
    split = Column(String, nullable=False)

    # Overlap metrics
    overlap_at_05s = Column(JSON, nullable=False)
    overlap_at_10s = Column(JSON, nullable=False)
    overlap_at_20s = Column(JSON, nullable=False)

    # Subsystem dimensions
    context_metrics = Column(JSON, nullable=False)
    narrative_metrics = Column(JSON, nullable=False)
    pacing_metrics = Column(JSON, nullable=False)
    effect_metrics = Column(JSON, nullable=False)

    # Segment counts
    matched_segments_count = Column(Integer, default=0)
    missed_segments_count = Column(Integer, default=0)
    ai_only_segments_count = Column(Integer, default=0)
    valid_alternatives_count = Column(Integer, default=0)

    # Root cause distribution
    root_cause_distribution = Column(JSON, default=dict)

    # Telemetry
    editor_model = Column(String, default="gemini-3.1-pro-high")
    evaluator_model = Column(String, default="gemini-3.1-pro-high")
    model_parity_flag = Column(Boolean, default=True)
    manual_audit_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    run = relationship("EditorialBenchmarkRunModel", back_populates="result")


class EditorialFailureModel(Base):
    __tablename__ = "benchmark_failures"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    benchmark_run_id = Column(String, ForeignKey("benchmark_runs.id"), nullable=False)
    case_id = Column(String, ForeignKey("benchmark_cases.id"), nullable=False)
    failure_type = Column(String, nullable=False)
    root_cause_stage = Column(String, nullable=False)
    source_start = Column(Float, nullable=False)
    source_end = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    evidence_trace = Column(JSON, default=dict)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    run = relationship("EditorialBenchmarkRunModel", back_populates="failures")


class EditorialExperimentModel(Base):
    __tablename__ = "benchmark_experiments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    hypothesis = Column(String, nullable=False)
    baseline_run_id = Column(String, ForeignKey("benchmark_runs.id"), nullable=False)
    target_stage = Column(String, nullable=False)
    proposed_change = Column(String, nullable=False)
    status = Column(String, default="PROPOSED")
    results_comparison = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)
