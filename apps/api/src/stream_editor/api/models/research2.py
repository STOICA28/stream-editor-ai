import uuid

from datetime import datetime

from stream_editor.api.models.mixins import JobLeaseMixin
from stream_editor.api.models.states import JobState
from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, JSON, DateTime, Enum

from sqlalchemy.orm import relationship

from stream_editor.api.database import Base



class ReferenceProject(Base):

    __tablename__ = "reference_projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    name = Column(String, nullable=False)

    description = Column(String, nullable=True)

    status = Column(String, nullable=False, default="active")

    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



    pairs = relationship("ReferenceVideoPair", back_populates="project")

    findings = relationship("ResearchFinding", back_populates="project")

    style_profiles = relationship("StyleProfile", back_populates="project")





class ReferenceVideoPair(Base):

    __tablename__ = "reference_pairs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    project_id = Column(String, ForeignKey("reference_projects.id"), nullable=False)

    source_asset_id = Column(String, ForeignKey("media_assets.id"), nullable=False)

    edited_asset_id = Column(String, ForeignKey("media_assets.id"), nullable=False)

    analysis_status = Column(String, nullable=False, default=JobState.PENDING.value)



    project = relationship("ReferenceProject", back_populates="pairs")

    source_asset = relationship("MediaAsset", foreign_keys=[source_asset_id])

    edited_asset = relationship("MediaAsset", foreign_keys=[edited_asset_id])

    alignment_runs = relationship("ReferenceAlignmentRun", back_populates="pair")

    decisions = relationship("ObservedEditorialDecision", back_populates="pair")

    effects = relationship("ObservedEffect", back_populates="pair")





class ReferenceAlignmentRun(JobLeaseMixin, Base):

    __tablename__ = "reference_alignment_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    pair_id = Column(String, ForeignKey("reference_pairs.id"), nullable=False)

    signature = Column(String, nullable=False)

    status = Column(String, nullable=False, default=JobState.SUCCEEDED.value)

    metrics = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)



    pair = relationship("ReferenceVideoPair", back_populates="alignment_runs")

    blocks = relationship("AlignmentBlock", back_populates="run")





class AlignmentBlock(Base):

    __tablename__ = "alignment_blocks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    run_id = Column(String, ForeignKey("reference_alignment_runs.id"), nullable=False)

    source_start = Column(Float, nullable=False)

    source_end = Column(Float, nullable=False)

    edit_start = Column(Float, nullable=False)

    edit_end = Column(Float, nullable=False)

    audio_confidence = Column(Float, nullable=True)

    transcript_confidence = Column(Float, nullable=True)

    visual_confidence = Column(Float, nullable=True)

    combined_confidence = Column(Float, nullable=False)

    speed_ratio = Column(Float, nullable=False, default=1.0)

    method = Column(String, nullable=False)

    is_manual_override = Column(Boolean, nullable=False, default=False)



    run = relationship("ReferenceAlignmentRun", back_populates="blocks")





class ObservedEditorialDecision(Base):

    __tablename__ = "observed_editorial_decisions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    pair_id = Column(String, ForeignKey("reference_pairs.id"), nullable=False)

    decision_type = Column(String, nullable=False)

    source_start = Column(Float, nullable=True)

    source_end = Column(Float, nullable=True)

    edit_start = Column(Float, nullable=True)

    edit_end = Column(Float, nullable=True)

    context_before = Column(Float, nullable=True)

    context_after = Column(Float, nullable=True)

    evidence = Column(JSON, nullable=True)



    pair = relationship("ReferenceVideoPair", back_populates="decisions")





class ObservedEffect(Base):

    __tablename__ = "observed_effects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    pair_id = Column(String, ForeignKey("reference_pairs.id"), nullable=False)

    alignment_block_id = Column(String, ForeignKey("alignment_blocks.id"), nullable=True)

    effect_type = Column(String, nullable=False)

    target = Column(String, nullable=True)

    source_start = Column(Float, nullable=False)

    source_end = Column(Float, nullable=False)

    edit_start = Column(Float, nullable=False)

    edit_end = Column(Float, nullable=False)

    scale = Column(Float, nullable=True)

    center_x = Column(Float, nullable=True)

    center_y = Column(Float, nullable=True)

    confidence = Column(Float, nullable=False)

    detection_method = Column(String, nullable=False)

    is_manual_override = Column(Boolean, nullable=False, default=False)

    is_false_positive = Column(Boolean, nullable=False, default=False)



    pair = relationship("ReferenceVideoPair", back_populates="effects")





class StyleProfile(Base):

    __tablename__ = "style_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    project_id = Column(String, ForeignKey("reference_projects.id"), nullable=False)

    version = Column(Integer, nullable=False, default=1)

    evidence_count = Column(Integer, nullable=False, default=0)

    metrics = Column(JSON, nullable=False)

    generated_at = Column(DateTime, default=datetime.utcnow)



    project = relationship("ReferenceProject", back_populates="style_profiles")





class ResearchFinding(Base):

    __tablename__ = "research_findings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    project_id = Column(String, ForeignKey("reference_projects.id"), nullable=False)

    pair_id = Column(String, ForeignKey("reference_pairs.id"), nullable=True)

    finding_type = Column(String, nullable=False)

    status = Column(String, nullable=False, default=JobState.PENDING.value)

    description = Column(String, nullable=False)

    evidence = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



    project = relationship("ReferenceProject", back_populates="findings")

